import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv
import json

def test_sendgrid():
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    api_key = os.getenv('SENDGRID_API_KEY')
    sender_email = "yunzhangspotify@gmail.com"
    #os.getenv('EMAIL_SENDER')
    recipient_email = os.getenv('EMAIL_RECIPIENT')
    
    print(f"[DEBUG] Testing SendGrid configuration:")
    print(f"[DEBUG] API Key present: {'Yes' if api_key else 'No'}")
    print(f"[DEBUG] Sender Email: {sender_email}")
    print(f"[DEBUG] Recipient Email: {recipient_email}")
    
    if not all([api_key, sender_email, recipient_email]):
        print("[ERROR] Missing required environment variables")
        return
    
    try:
        # Initialize SendGrid client
        sg = SendGridAPIClient(api_key)
        print("[DEBUG] Successfully initialized SendGrid client")
        
        # Create message with explicit Email objects
        from_email = Email(sender_email, "News Aggregator")
        to_email = To(recipient_email)
        
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject='SendGrid Test Email',
            plain_text_content='This is a test email from SendGrid.'
        )
        
        # Print message details (excluding API key)
        print("[DEBUG] Message details:")
        print(json.dumps({
            'from': {'email': sender_email, 'name': 'News Aggregator'},
            'to': {'email': recipient_email},
            'subject': 'SendGrid Test Email'
        }, indent=2))
        
        # Send email
        print("[DEBUG] Attempting to send email...")
        response = sg.send(message)
        print(f"[DEBUG] Email sent successfully! Status code: {response.status_code}")
        print(f"[DEBUG] Response headers: {response.headers}")
        
    except Exception as e:
        print(f"[ERROR] Failed to send email: {str(e)}")
        if hasattr(e, 'body'):
            print(f"[ERROR] Error details: {e.body}")

if __name__ == "__main__":
    test_sendgrid() 