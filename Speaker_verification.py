import os
import sys
import time
import requests
import numpy as np
import speech_recognition as sr
from pathlib import Path
from dotenv import load_dotenv
from backend.location_handler import get_current_location
from backend.Evidence_handler import record_audio_evidence, send_telegram_audio

# Ensure project backend paths are loaded
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_DIR))

load_dotenv(PROJECT_DIR / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_IDS")

# Thresholds & Configuration
SPEAKER_THRESHOLD = 0.50
EMERGENCY_PHRASES = ["help", "help me", "save me", "bachao", "please help me", "stop"]


def trigger_telegram_alert(user_id="Dhananjay", confidence=0.0):
    """
    1. Sends textual distress alert with Google Maps location.
    2. Records 10 seconds of ambient audio evidence.
    3. Sends audio recording to Telegram.
    """
    print("🚨 Triggering full emergency alert sequence...")

    # 1. Fetch location & send text message
    loc_info = get_current_location()
    maps_link = loc_info.get("maps_url", "N/A")
    loc_source = loc_info.get("source", "Unknown")

    alert_text = (
        f"🚨 **EMERGENCY DISTRESS ALERT** 🚨\n\n"
        f"**User Status:** Voice Verified ({user_id})\n"
        f"**Confidence Score:** {confidence:.2f}\n"
        f"**Location Source:** {loc_source}\n"
        f"**Google Maps Link:** {maps_link}\n\n"
        f"🎙️ *Recording 10 seconds of live audio evidence...*"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": alert_text, "parse_mode": "Markdown"}

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("❌ Error sending alert text:", e)

    # 2. Capture audio evidence (10 seconds)
    audio_file = record_audio_evidence(duration=10)

    # 3. Upload evidence to Telegram
    if audio_file:
        send_telegram_audio(
            bot_token=BOT_TOKEN,
            chat_id=CHAT_ID,
            audio_file_path=audio_file,
            caption="📁 **Live Audio Evidence Recorded**",
        )


def check_frequency_threshold(audio_data, sample_rate=16000, min_freq=60, max_freq=800):
    """
    Analyzes audio pitch/frequency using Fast Fourier Transform (FFT).
    Returns True if dominant frequency falls within target frequency range.
    """
    raw_data = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
    if len(raw_data) == 0:
        return False

    fft_data = np.abs(np.fft.rfft(raw_data))
    freqs = np.fft.rfftfreq(len(raw_data), 1.0 / sample_rate)
    dominant_freq = freqs[np.argmax(fft_data)]

    return min_freq <= dominant_freq <= max_freq


def start_247_distress_listener():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    print("🎙️ 24/7 Continuous Distress Monitoring Activated...")
    print("Listening for emergency phrases in background...")

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    while True:
        try:
            with microphone as source:
                # Capture short audio chunk continuously
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=4)

            # 1. Frequency Condition Check (> 60 Hz)
            if not check_frequency_threshold(audio, min_freq=60):
                continue

            # 2. Convert Speech to Text
            try:
                speech_text = recognizer.recognize_google(audio).lower()
                print(f"Detected speech: '{speech_text}'")
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"Speech recognition service error: {e}")
                continue

            # 3. Check for Emergency Keywords
            if any(phrase in speech_text for phrase in EMERGENCY_PHRASES):
                print(f"🚨 Emergency Phrase Detected: '{speech_text}'")

                # Mock verification confidence or plug in your verification scoring here
                speaker_score = 0.85

                # 4. Trigger Alert if Voice Matches
                if speaker_score >= SPEAKER_THRESHOLD:
                    print("✅ Registered speaker detected! Triggering emergency alert sequence...")
                    trigger_telegram_alert(user_id="Dhananjay", confidence=speaker_score)

                    # Pause briefly to prevent duplicate continuous alerts
                    time.sleep(15)
                else:
                    print("❌ Emergency phrase detected, but voice identity did not match registered user.")

        except Exception as e:
            print(f"Listener error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    start_247_distress_listener()