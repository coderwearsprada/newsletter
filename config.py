import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Perplexity API configuration
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

# Email configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')

# News configuration
TRUSTED_SOURCES = [
    'reuters.com',
    'bloomberg.com',
    'wsj.com',
    'ft.com',
    'economist.com',
    'cnbc.com',
    'bbc.com',
    'guardian.com'
]

# Default topics/keywords to track
DEFAULT_TOPICS = [
    'artificial intelligence',
    'startup funding'
]

# Time window for news (in hours)
NEWS_TIME_WINDOW = 24 