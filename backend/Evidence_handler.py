import os
import time
import requests
import sounddevice as sd
from scipy.io.wavfile import write
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = PROJECT_DIR / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)

def record_audio_evidence(duration=5, sample_rate=44100):
    """
    Records audio for a specified duration and saves it in the evidence folder.
    Returns the file path of the saved recording.
    """
    filename = f"distress_evidence_{int(time.time())}.wav"
    file_path = EVIDENCE_DIR / filename
    
    print(f"🎙️ Recording {duration} seconds of audio evidence...")
    try:
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()  # Wait until recording finishes
        write(file_path, sample_rate, recording)
        print(f"✅ Audio evidence saved at: {file_path}")
        return str(file_path)
    except Exception as e:
        print(f"❌ Audio recording failed: {e}")
        return None

def send_telegram_audio(bot_token, chat_id, audio_file_path, caption=""):
    """
    Uploads and sends an audio/voice file directly to Telegram.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendAudio"
    try:
        with open(audio_file_path, "rb") as audio:
            files = {"audio": audio}
            data = {"chat_id": chat_id, "caption": caption}
            response = requests.post(url, data=data, files=files, timeout=15)
            res = response.json()
            if res.get("ok"):
                print("✅ Audio evidence attached and sent to Telegram!")
                return True
            else:
                print("❌ Failed to send audio to Telegram:", res)
                return False
    except Exception as e:
        print("❌ Error uploading audio evidence:", e)
        return False

if __name__ == "__main__":
    # Test recording
    recorded_file = record_audio_evidence(duration=3)
    print("Recorded file path:", recorded_file)