import os
import json
import schedule
import time
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import requests
from bs4 import BeautifulSoup
from config import *
import re

class NewsAggregator:
    def __init__(self):
        self.perplexity_api_key = PERPLEXITY_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.perplexity_api_key}',
            'Content-Type': 'application/json'
        }
        self.sg = SendGridAPIClient(SENDGRID_API_KEY)
        self.recipient_email = EMAIL_RECIPIENT
        print(f"[DEBUG] Initialized NewsAggregator with Perplexity API key: {self.perplexity_api_key[:5]}...")
        print(f"[DEBUG] Initialized SendGrid client")

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
                        'url': self._extract_url(content),
                        'summary': self._generate_summary(content),
                        'topic': topic
                    }
                    print(f"[DEBUG] Created article: {json.dumps(article, indent=2)}")
                    articles.append(article)
        except Exception as e:
            print(f"[DEBUG] Error parsing response: {str(e)}")
        
        return articles

    def _is_relevant(self, verification_result):
        """Determine if an article is relevant based on verification response"""
        print(f"[DEBUG] Checking relevance with result: {json.dumps(verification_result, indent=2)}")
        # Implement relevance checking logic
        # This is a simplified version
        return True

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
        
        # Create email content
        content = "Here are today's relevant news articles:\n\n"
        for article in articles:
            print(f"[DEBUG] article: {article}")
            content += f"Topic: {article['topic']}\n"
            content += f"Title: {article['title']}\n"
            content += f"Summary: {article['summary']}\n"
            content += f"Read more: {article['url']}\n\n"
            content += "-" * 80 + "\n\n"

        # Create SendGrid message
        print("[DEBUG] Creating SendGrid message")
        from_email = Email(EMAIL_SENDER, "News Aggregator")
        to_email = To(self.recipient_email)
        
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=f'Daily News Digest - {datetime.now().strftime("%Y-%m-%d")}',
            plain_text_content=content
        )

        # Debug print the email object (excluding API key)
        print("[DEBUG] email:", {
            'from': {'email': from_email.email, 'name': from_email.name},
            'subject': message.subject,
            'personalizations': [{'to': [{'email': to_email.email}]}],
            'content': [{'type': 'text/plain', 'value': content}]
        })

        # Send email
        print("[DEBUG] Sending email via SendGrid...")
        try:
            response = self.sg.send(message)
            print(f"[DEBUG] Email sent successfully! Status code: {response.status_code}")
        except Exception as e:
            print(f"[DEBUG] Error sending email: {str(e)}")
            if hasattr(e, 'body'):
                print(f"[DEBUG] Error details: {e.body}")

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
    #print("[DEBUG] Scheduling daily digest for 8:00 AM")
    #schedule.every().day.at("08:00").do(aggregator.run_daily_digest)
    
    # Run immediately on startup
    print("[DEBUG] Running initial digest")
    aggregator.run_daily_digest()
    
    # Keep the script running
    #print("[DEBUG] Entering main loop")
    #while True:
    #    schedule.run_pending()
    #    time.sleep(60)

if __name__ == "__main__":
    main() 