from twilio.rest import Client
import os

# 🔐 Load environment variables
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
TO_NUMBER = os.getenv("YOUR_WHATSAPP_NUMBER")

# 📲 Initialize client
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp_message(message):
    try:
        # 🔍 Debug info
        print("Sending WhatsApp message...")
        print("From:", FROM_NUMBER)
        print("To:", TO_NUMBER)

        msg = client.messages.create(
            body=message,
            from_=FROM_NUMBER,
            to=TO_NUMBER
        )

        print("Message SID:", msg.sid)

    except Exception as e:
        print("❌ WhatsApp Error:", str(e))