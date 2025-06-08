import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Perplexity API Configuration
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

# Gmail API Configuration
GMAIL_CREDENTIALS_FILE = os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json')
GMAIL_TOKEN_FILE = os.getenv('GMAIL_TOKEN_FILE', 'token.json')
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Email Configuration
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')

# News Configuration
NEWS_TIME_WINDOW = 24  # hours
TRUSTED_SOURCES = [
    'reuters.com',
    'bloomberg.com',
    'wsj.com',
    'ft.com',
    'economist.com',
    'cnbc.com',
    'bbc.com',
    'nytimes.com',
    'washingtonpost.com',
    'thetimes.co.uk',
    'telegraph.co.uk',
    'theinformation.com',
    'medium.com',
    'techcrunch.com'
]

DEFAULT_TOPICS = [
    'AI powered developer tools'
    'startup funding',
    'crypto'
] 