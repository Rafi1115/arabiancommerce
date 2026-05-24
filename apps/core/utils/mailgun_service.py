import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class MailgunEmailService:
    def __init__(self):
        self.api_key = getattr(settings, 'MAILGUN_API_KEY', None)
        self.domain = getattr(settings, 'MAILGUN_DOMAIN', None)
        self.from_email = getattr(settings, 'MAILGUN_FROM_EMAIL', 'no-reply@example.com')
        self.from_name = getattr(settings, 'MAILGUN_FROM_NAME', 'ArabianCommerce')

    def send_transactional_email(self, to_email, to_name, subject, html_content, text_content, attachment=None):
        logger.info(f"📧 Sending transactional email to {to_email} with subject '{subject}'")
        if not self.api_key or not self.domain:
            logger.warning("⚠️ Mailgun credentials not configured. Logging email instead:")
            logger.info(f"To: {to_name} <{to_email}>")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {text_content}")
            return {"id": "dummy-mailgun-id-since-not-configured"}

        url = f"https://api.mailgun.net/v3/{self.domain}/messages"
        auth = ("api", self.api_key)
        data = {
            "from": f"{self.from_name} <{self.from_email}>",
            "to": [f"{to_name} <{to_email}>"],
            "subject": subject,
            "text": text_content,
            "html": html_content,
        }

        files = []
        if attachment:
            import os
            if os.path.exists(attachment):
                filename = os.path.basename(attachment)
                try:
                    with open(attachment, "rb") as f:
                        files.append(("attachment", (filename, f.read())))
                except Exception as e:
                    logger.error(f"❌ Failed to read attachment {attachment}: {e}")

        try:
            response = requests.post(url, auth=auth, data=data, files=files if files else None)
            if response.status_code == 200:
                logger.info("✅ Email sent successfully via Mailgun")
                return response.json()
            else:
                logger.error(f"❌ Mailgun returned status code {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to send email via Mailgun: {e}")
            return None
