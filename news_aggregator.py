import os
import json
import schedule
import time
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from config import *
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class NewsAggregator:
    def __init__(self):
        self.perplexity_api_key = PERPLEXITY_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.perplexity_api_key}',
            'Content-Type': 'application/json'
        }
        self.gmail_service = self._get_gmail_service()
        self.recipient_email = EMAIL_RECIPIENT
        print(f"[DEBUG] Initialized NewsAggregator with Perplexity API key: {self.perplexity_api_key[:5]}...")
        print(f"[DEBUG] Initialized Gmail API client")

    def _get_gmail_service(self):
        """Set up Gmail API service"""
        creds = None
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists(GMAIL_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, GMAIL_SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    GMAIL_CREDENTIALS_FILE, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(GMAIL_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    def _create_message(self, sender, to, subject, html_content, plain_content):
        """Create a message for an email."""
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject

        # Attach both plain text and HTML versions
        message.attach(MIMEText(plain_content, 'plain'))
        message.attach(MIMEText(html_content, 'html'))

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}

    def search_news(self, topics):
        """Search for news articles using Perplexity API"""
        articles = []
        
        for topic in topics:
            print(f"\n[DEBUG] Searching news for topic: {topic}")
            query = f"Find recent news articles from the last {NEWS_TIME_WINDOW} hours about {topic} from these sources: {', '.join(TRUSTED_SOURCES)}"
            print(f"[DEBUG] Perplexity API Query: {query}")
            
            try:
                print("[DEBUG] Making request to Perplexity API...")
                response = requests.post(
                    'https://api.perplexity.ai/chat/completions',
                    headers=self.headers,
                    json={
                        'model': 'sonar',
                        'messages': [{'role': 'user', 'content': query}]
                    }
                )
                
                print(f"[DEBUG] Perplexity API Response Status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"[DEBUG] Perplexity API Response: {json.dumps(result, indent=2)}")
                    articles.extend(self._parse_perplexity_response(result, topic))
                else:
                    print(f"[DEBUG] Error response from Perplexity API: {response.text}")
            except Exception as e:
                print(f"[DEBUG] Error searching news for topic {topic}: {str(e)}")
        
        return articles

    def _parse_perplexity_response(self, response, topic):
        """Parse the Perplexity API response and extract relevant articles"""
        articles = []
        try:
            print(f"\n[DEBUG] Parsing Perplexity response for topic: {topic}")
            content = response['choices'][0]['message']['content']
            print(f"[DEBUG] Extracted content: {content[:200]}...")
            
            # Extract URLs from search_results
            urls = []
            if 'search_results' in response:
                for result in response['search_results']:
                    if 'url' in result and result['url']:
                        # Check if the URL is from a trusted source
                        url = result['url']
                        #if any(source in url.lower() for source in [s.lower() for s in TRUSTED_SOURCES]):
                        urls.append(url)
                        #    print(f"[DEBUG] Found URL from trusted source: {url}")
                        #else:
                        #    print(f"[DEBUG] Skipping URL from untrusted source: {url}")
                print(f"[DEBUG] Found {len(urls)} URLs from trusted sources")
            
            if not urls:
                print("[DEBUG] No articles found from trusted sources")
                return articles
            
            # Use Perplexity to verify relevance
            verification_query = f"Verify if this article is highly relevant to {topic}: {content}"
            print(f"[DEBUG] Making verification request to Perplexity API...")
            verification_response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=self.headers,
                json={
                    'model': 'sonar',
                    'messages': [{'role': 'user', 'content': verification_query}]
                }
            )
            
            print(f"[DEBUG] Verification Response Status: {verification_response.status_code}")
            if verification_response.status_code == 200:
                verification_result = verification_response.json()
                print(f"[DEBUG] Verification Response: {json.dumps(verification_result, indent=2)}")
                if self._is_relevant(verification_result):
                    article = {
                        'title': self._extract_title(content),
                        'url': urls[0],  # Use the first trusted source URL
                        'summary': self._generate_summary(content),
                        'topic': topic
                    }
                    print(f"[DEBUG] Created article: {json.dumps(article, indent=2)}")
                    articles.append(article)
        except Exception as e:
            print(f"[DEBUG] Error parsing response: {str(e)}")
        
        return articles

    def _is_relevant(self, verification_result):
        """Determine if an article is relevant based on semantic similarity"""
        print(f"[DEBUG] Checking relevance with result: {json.dumps(verification_result, indent=2)}")
        try:
            # Extract the verification content and topic
            content = verification_result['choices'][0]['message']['content']
            topic = content.split('Verify if this article is highly relevant to ')[1].split(':')[0].strip()
            
            # Use Perplexity to analyze semantic relevance
            similarity_query = f"""Analyze if this article is semantically relevant to the topic of {topic}.
            Consider:
            1. Main themes and concepts
            2. Direct and indirect relationships
            3. Depth of coverage
            4. Context and implications
            
            Article content: {content}
            
            Respond with a JSON object containing:
            {{
                "relevance_score": float (0-1),
                "reasoning": "explanation of the relevance",
                "key_themes": ["list", "of", "main", "themes"],
                "is_relevant": boolean
            }}"""
            
            print(f"[DEBUG] Making semantic similarity request to Perplexity API...")
            similarity_response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=self.headers,
                json={
                    'model': 'sonar',
                    'messages': [{'role': 'user', 'content': similarity_query}]
                }
            )
            
            if similarity_response.status_code == 200:
                similarity_result = similarity_response.json()
                analysis = similarity_result['choices'][0]['message']['content']
                
                try:
                    # Parse the JSON response
                    analysis_json = json.loads(analysis)
                    
                    print(f"[DEBUG] Semantic analysis results:")
                    print(f"- Relevance score: {analysis_json.get('relevance_score', 0)}")
                    print(f"- Reasoning: {analysis_json.get('reasoning', 'No reasoning provided')}")
                    print(f"- Key themes: {analysis_json.get('key_themes', [])}")
                    print(f"- Is relevant: {analysis_json.get('is_relevant', False)}")
                    
                    # Consider an article relevant if:
                    # 1. The relevance score is above 0.6, or
                    # 2. The analysis explicitly states it's relevant
                    is_relevant = analysis_json.get('relevance_score', 0) > 0.6 or analysis_json.get('is_relevant', False)
                    
                    return is_relevant
                    
                except json.JSONDecodeError:
                    print("[DEBUG] Failed to parse JSON response from semantic analysis")
                    # Fallback to basic relevance check if JSON parsing fails
                    return 'relevant' in analysis.lower() or 'related' in analysis.lower()
            else:
                print(f"[DEBUG] Error in semantic similarity request: {similarity_response.text}")
                return True  # Default to True if API call fails
                
        except Exception as e:
            print(f"[DEBUG] Error in semantic relevance check: {str(e)}")
            return True  # Default to True in case of errors

    def _extract_title(self, content):
        """Extract article title from content"""
        print(f"[DEBUG] Extracting title from content: {content[:100]}...")
        try:
            # Look for title patterns in the content
            # Common patterns: "Title:", "Headline:", or first line of content
            title_patterns = [
                r'Title:\s*(.*?)(?:\n|$)',
                r'Headline:\s*(.*?)(?:\n|$)',
                r'^(.*?)(?:\n|$)'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if title and len(title) > 5:  # Basic validation
                        print(f"[DEBUG] Found title: {title}")
                        return title
            
            print("[DEBUG] No title found in content")
            return "Title not found"
        except Exception as e:
            print(f"[DEBUG] Error extracting title: {str(e)}")
            return "Title extraction failed"

    def _extract_url(self, content):
        """Extract article URL from content"""
        print(f"[DEBUG] Extracting URL from content: {content[:100]}...")
        try:
            # Look for URLs in the content
            # Common patterns: "from [url]", "source: [url]", "read more: [url]", or just a plain URL
            url_patterns = [
                r'from\s+(https?://[^\s]+)',
                r'source:\s*(https?://[^\s]+)',
                r'read more:\s*(https?://[^\s]+)',
                r'(https?://[^\s]+)'
            ]
            
            for pattern in url_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    url = match.group(1).strip('.,;:!?')
                    print(f"[DEBUG] Found URL: {url}")
                    return url
            
            print("[DEBUG] No URL found in content")
            return "URL not found"
        except Exception as e:
            print(f"[DEBUG] Error extracting URL: {str(e)}")
            return "URL extraction failed"

    def _generate_summary(self, content):
        """Generate a summary of the article using Perplexity"""
        try:
            print(f"\n[DEBUG] Generating summary for content: {content[:100]}...")
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=self.headers,
                json={
                    'model': 'sonar',
                    'messages': [{'role': 'user', 'content': f"Summarize this article in 2-3 sentences: {content}"}]
                }
            )
            
            print(f"[DEBUG] Summary API Response Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"[DEBUG] Summary API Response: {json.dumps(result, indent=2)}")
                return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"[DEBUG] Error generating summary: {str(e)}")
        return "Summary not available"

    def send_digest(self, articles):
        """Send email digest with article summaries."""
        if not articles:
            print("[DEBUG] No articles to send")
            return

        print(f"[DEBUG] Preparing to send email with {len(articles)} articles")
        
        # Create HTML email content
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .article { margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
                .topic { font-weight: bold; color: #2c3e50; font-size: 1.2em; }
                .title { font-size: 1.1em; margin: 10px 0; }
                .summary { margin: 10px 0; }
                .source { color: #3498db; text-decoration: none; }
                .source:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h2>Today's News Digest</h2>
        """
        
        for article in articles:
            print(f"[DEBUG] Processing article: {article}")
            html_content += f"""
            <div class="article">
                <div class="topic">Topic: {article['topic']}</div>
                <div class="title">{article['title']}</div>
                <div class="summary">{article['summary']}</div>
                <a href="{article['url']}" class="source">Source</a>
            </div>
            """

        html_content += """
        </body>
        </html>
        """

        # Create plain text version for email clients that don't support HTML
        plain_content = "Here are today's relevant news articles:\n\n"
        for article in articles:
            plain_content += f"Topic: {article['topic']}\n"
            plain_content += f"Title: {article['title']}\n"
            plain_content += f"Summary: {article['summary']}\n"
            plain_content += f"Source: {article['url']}\n\n"
            plain_content += "-" * 80 + "\n\n"

        # Create and send the email
        try:
            message = self._create_message(
                EMAIL_SENDER,
                self.recipient_email,
                f'Daily News Digest - {datetime.now().strftime("%Y-%m-%d")}',
                html_content,
                plain_content
            )
            
            print("[DEBUG] Sending email via Gmail API...")
            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            print(f"[DEBUG] Email sent successfully! Message ID: {sent_message['id']}")
        except Exception as e:
            print(f"[DEBUG] Error sending email: {str(e)}")

    def run_daily_digest(self):
        """Run the daily news digest process"""
        print(f"\n[DEBUG] Running daily digest at {datetime.now()}")
        articles = self.search_news(DEFAULT_TOPICS)
        print(f"[DEBUG] Found {len(articles)} articles")
        self.send_digest(articles)

def main():
    print("[DEBUG] Starting News Aggregator application")
    aggregator = NewsAggregator()
    
    # Schedule the daily digest to run at 8 AM
    print("[DEBUG] Scheduling daily digest for 8:00 AM")
    schedule.every().day.at("08:00").do(aggregator.run_daily_digest)
    
    # Run immediately on startup
    print("[DEBUG] Running initial digest")
    aggregator.run_daily_digest()
    
    # Keep the script running
    print("[DEBUG] Entering main loop")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 