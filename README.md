# News Aggregator

A Python application that aggregates and summarizes news articles from trusted sources using the Perplexity API. The application sends daily email digests with relevant news articles based on predefined topics.

## Features

- Fetches news from trusted sources within the last 24 hours
- Uses Perplexity API for news search and summarization
- Verifies article relevance to specified topics
- Sends daily email digests with article summaries and links using SendGrid
- Configurable topics and trusted sources
- Scheduled daily updates

## Setup

1. Clone the repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with the following variables:
   ```
   PERPLEXITY_API_KEY=your_perplexity_api_key
   SENDGRID_API_KEY=your_sendgrid_api_key
   EMAIL_SENDER=your_verified_sender_email@example.com
   EMAIL_RECIPIENT=recipient_email@example.com
   ```

   Note: For SendGrid:
   - You'll need to create a SendGrid account and get an API key
   - The sender email must be verified in your SendGrid account
   - You can verify your sender email in the SendGrid dashboard under Settings > Sender Authentication

4. Configure your topics and trusted sources in `config.py`

## Usage

Run the application:
```bash
python news_aggregator.py
```

The application will:
1. Run immediately on startup
2. Schedule daily updates at 8:00 AM
3. Send email digests with relevant news articles

## Customization

You can customize the following in `config.py`:
- `TRUSTED_SOURCES`: List of trusted news sources
- `DEFAULT_TOPICS`: List of topics/keywords to track
- `NEWS_TIME_WINDOW`: Time window for news articles (in hours)

## Requirements

- Python 3.7+
- Perplexity API key
- SendGrid account and API key 