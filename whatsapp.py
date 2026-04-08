from twilio.rest import Client
import os
import time

# ─── CONFIG ──────────────────────────────────────────────────────────────────

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # e.g. "whatsapp:+14155238886"
TO_NUMBER = os.getenv("YOUR_WHATSAPP_NUMBER")       # e.g. "whatsapp:+919876543210"

_client = None


def _get_client() -> Client:
    """Lazy-init Twilio client — only fails at send time, not import time."""
    global _client
    if _client is None:
        if not all([ACCOUNT_SID, AUTH_TOKEN]):
            raise EnvironmentError(
                "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in .env"
            )
        _client = Client(ACCOUNT_SID, AUTH_TOKEN)
    return _client


def send_whatsapp_message(message: str, to: str = None, retries: int = 2) -> bool:
    """
    Send a WhatsApp message via Twilio.

    Args:
        message: Text to send.
        to:      Recipient (defaults to YOUR_WHATSAPP_NUMBER env var).
        retries: Number of retry attempts on failure.

    Returns:
        True if sent successfully, False otherwise.
    """
    recipient = to or TO_NUMBER
    if not recipient:
        print("[WhatsApp] ❌ No recipient number set (YOUR_WHATSAPP_NUMBER missing)")
        return False

    for attempt in range(1, retries + 2):
        try:
            client = _get_client()
            msg = client.messages.create(
                body=message,
                from_=FROM_NUMBER,
                to=recipient,
            )
            print(f"[WhatsApp] ✅ Sent to {recipient} | SID: {msg.sid}")
            return True

        except Exception as e:
            print(f"[WhatsApp] ❌ Attempt {attempt} failed: {e}")
            if attempt <= retries:
                time.sleep(2 * attempt)  # exponential backoff

    print(f"[WhatsApp] ❌ All {retries + 1} attempts failed for message: {message[:50]}")
    return False
