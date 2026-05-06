"""
SMS / OTP sending service.

DEV MODE:
  - OTP is printed to the terminal
  - OTP is returned in the API response (so frontend dev can see it)

PRODUCTION:
  - Replace `_send_via_terminal()` with your SMS provider
    e.g. Twilio, Unifonic, Taqnyat, MSegment, etc.
  - Remove otp_code from API responses
"""

import logging
import random
import string

logger = logging.getLogger(__name__)


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length."""
    return "".join(random.choices(string.digits, k=length))


def send_otp_sms(phone: str, otp_code: str, purpose: str) -> bool:
    """
    Send OTP to a phone number.

    Args:
        phone: Phone number with country code e.g. +966501234567
        otp_code: The OTP to send
        purpose: 'registration' | 'login' | 'phone_change'

    Returns:
        True if sent successfully, False otherwise.
    """
    purpose_labels = {
        "registration": "Registration",
        "login": "Login",
        "phone_change": "Phone Change",
    }
    label = purpose_labels.get(purpose, "Verification")
    message = f"[Karam] Your {label} OTP is: {otp_code}. Valid for 10 minutes. Do not share."

    # --- DEV: Print to terminal ---
    _send_via_terminal(phone, otp_code, message)

    # --- PRODUCTION: Uncomment and use your SMS provider ---
    # return _send_via_twilio(phone, message)
    # return _send_via_unifonic(phone, message)

    return True


def _send_via_terminal(phone: str, otp_code: str, message: str):
    """
    DEV ONLY — prints OTP to terminal so frontend dev doesn't need real SMS.
    """
    print("\n" + "=" * 50)
    print(f"📱  SMS OTP [DEV MODE]")
    print(f"    To     : {phone}")
    print(f"    OTP    : {otp_code}")
    print(f"    Message: {message}")
    print("=" * 50 + "\n")
    logger.info(f"[DEV OTP] phone={phone} otp={otp_code}")


# ── FUTURE PROVIDER STUBS ──────────────────────────────────────────────────────

def _send_via_twilio(phone: str, message: str) -> bool:
    """Twilio SMS — swap in when client approves."""
    # from twilio.rest import Client
    # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    # client.messages.create(body=message, from_=settings.TWILIO_FROM, to=phone)
    raise NotImplementedError("Twilio not configured yet.")


def _send_via_unifonic(phone: str, message: str) -> bool:
    """Unifonic SMS (popular in Saudi Arabia) — swap in when client approves."""
    # import requests
    # requests.post("https://api.unifonic.com/rest/Messages/Send", data={
    #     "AppSid": settings.UNIFONIC_APP_SID,
    #     "Recipient": phone,
    #     "Body": message,
    #     "SenderID": settings.UNIFONIC_SENDER_ID,
    # })
    raise NotImplementedError("Unifonic not configured yet.")