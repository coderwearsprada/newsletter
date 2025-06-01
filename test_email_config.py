import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Load environment variables
load_dotenv()

# Get email configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')

print(f"Email Configuration:")
print(f"Sender: {EMAIL_SENDER}")
print(f"Recipient: {EMAIL_RECIPIENT}")
print(f"SendGrid API Key: {SENDGRID_API_KEY[:5]}..." if SENDGRID_API_KEY else "Not set")

# Create test email
message = Mail(
    from_email=Email(EMAIL_SENDER, "Test Sender"),
    to_emails=To(EMAIL_RECIPIENT),
    subject='Test Email from Newsletter App',
    plain_text_content='This is a test email to verify the configuration.'
)

# Send email
try:
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    print(f"\nEmail sent successfully!")
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
except Exception as e:
    print(f"\nError sending email: {str(e)}")
    if hasattr(e, 'body'):
        print(f"Error details: {e.body}") 