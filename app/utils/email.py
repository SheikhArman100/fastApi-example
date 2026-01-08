import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from ..core.config import settings

def send_email(to_email: str, html_content: str, subject: str):
    """
    Send HTML email using SMTP

    This implementation uses real SMTP sending with TLS encryption.
    Make sure to configure your SMTP settings in the .env file.
    """

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.smtp_from_email
        msg['To'] = to_email

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Send email using SMTP
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            # Start TLS encryption
            server.starttls()

            # Login to SMTP server
            server.login(settings.smtp_username, settings.smtp_password)

            # Send email
            server.sendmail(settings.smtp_from_email, to_email, msg.as_string())

        print(f"📧 Email sent successfully to: {to_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"SMTP Connection Error: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False
