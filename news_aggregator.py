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

class NewsAggregator:
    def __init__(self):
        self.perplexity_api_key = PERPLEXITY_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.perplexity_api_key}',
            'Content-Type': 'application/json'
        }
        self.sg = SendGridAPIClient(SENDGRID_API_KEY)

    def search_news(self, topics):
        """Search for news articles using Perplexity API"""
        articles = []
        
        for topic in topics:
            query = f"Find recent news articles from the last {NEWS_TIME_WINDOW} hours about {topic} from these sources: {', '.join(TRUSTED_SOURCES)}"
            
            try:
                response = requests.post(
                    'https://api.perplexity.ai/chat/completions',
                    headers=self.headers,
                    json={
                        'model': 'pplx-7b-online',
                        'messages': [{'role': 'user', 'content': query}]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Process the response and extract articles
                    # This is a simplified version - you'll need to parse the actual response format
                    articles.extend(self._parse_perplexity_response(result, topic))
            except Exception as e:
                print(f"Error searching news for topic {topic}: {str(e)}")
        
        return articles

    def _parse_perplexity_response(self, response, topic):
        """Parse the Perplexity API response and extract relevant articles"""
        articles = []
        try:
            # This is a placeholder - you'll need to adjust based on actual API response format
            content = response['choices'][0]['message']['content']
            
            # Use Perplexity to verify relevance
            verification_query = f"Verify if this article is highly relevant to {topic}: {content}"
            verification_response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=self.headers,
                json={
                    'model': 'pplx-7b-online',
                    'messages': [{'role': 'user', 'content': verification_query}]
                }
            )
            
            if verification_response.status_code == 200:
                verification_result = verification_response.json()
                if self._is_relevant(verification_result):
                    articles.append({
                        'title': self._extract_title(content),
                        'url': self._extract_url(content),
                        'summary': self._generate_summary(content),
                        'topic': topic
                    })
        except Exception as e:
            print(f"Error parsing response: {str(e)}")
        
        return articles

    def _is_relevant(self, verification_result):
        """Determine if an article is relevant based on verification response"""
        # Implement relevance checking logic
        # This is a simplified version
        return True

    def _extract_title(self, content):
        """Extract article title from content"""
        # Implement title extraction logic
        return "Article Title"

    def _extract_url(self, content):
        """Extract article URL from content"""
        # Implement URL extraction logic
        return "https://example.com/article"

    def _generate_summary(self, content):
        """Generate a summary of the article using Perplexity"""
        try:
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=self.headers,
                json={
                    'model': 'pplx-7b-online',
                    'messages': [{'role': 'user', 'content': f"Summarize this article in 2-3 sentences: {content}"}]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
        return "Summary not available"

    def send_email(self, articles):
        """Send email with news summaries using SendGrid"""
        if not articles:
            return

        # Prepare email content
        body = "Here are today's relevant news articles:\n\n"
        
        for article in articles:
            body += f"Topic: {article['topic']}\n"
            body += f"Title: {article['title']}\n"
            body += f"Summary: {article['summary']}\n"
            body += f"Read more: {article['url']}\n\n"
            body += "-" * 80 + "\n\n"

        # Create SendGrid message
        message = Mail(
            from_email=Email(EMAIL_SENDER),
            to_emails=To(EMAIL_RECIPIENT),
            subject=f"Daily News Digest - {datetime.now().strftime('%Y-%m-%d')}",
            plain_text_content=Content("text/plain", body)
        )

        try:
            response = self.sg.send(message)
            print(f"Email sent successfully! Status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending email: {str(e)}")

    def run_daily_digest(self):
        """Run the daily news digest process"""
        print(f"Running daily digest at {datetime.now()}")
        articles = self.search_news(DEFAULT_TOPICS)
        self.send_email(articles)

def main():
    aggregator = NewsAggregator()
    
    # Schedule the daily digest to run at 8 AM
    schedule.every().day.at("08:00").do(aggregator.run_daily_digest)
    
    # Run immediately on startup
    aggregator.run_daily_digest()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 