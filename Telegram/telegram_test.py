import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Import location fetcher
import sys
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR))
from backend.location_handler import get_current_location

# Load environment variables
env_file = PROJECT_DIR / ".env"
load_dotenv(env_file)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_IDS")

def send_emergency_alert(custom_msg="DISTRESS DETECTED!"):
    # Get current location details
    loc_info = get_current_location()
    
    maps_link = loc_info.get("maps_url", "N/A")
    city = loc_info.get("city", "Unknown")
    
    alert_text = (
        f"🚨 **EMERGENCY ALERT - Women Safety MVP** 🚨\n\n"
        f"**Status:** {custom_msg}\n"
        f"**Location:** {city}\n"
        f"**Google Maps:** {maps_link}"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": alert_text,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        res_data = response.json()
        if res_data.get("ok"):
            print("✅ Emergency Alert sent successfully with location!")
            return True
        else:
            print("❌ Error from Telegram API:", res_data)
            return False
    except Exception as e:
        print("❌ Failed to send request:", e)
        return False

if __name__ == "__main__":
    send_emergency_alert("Voice Trigger Activated Test")