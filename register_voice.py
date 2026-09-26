import speech_recognition as sr
from pathlib import Path


# =========================================
# VOICE PROFILE FOLDER
# =========================================

VOICE_FOLDER = Path("voice_profile")

# Create folder if it doesn't exist
VOICE_FOLDER.mkdir(exist_ok=True)


# =========================================
# FIND NEXT FILE NUMBER
# =========================================

existing_files = list(VOICE_FOLDER.glob("voice_*.wav"))

numbers = []

for file in existing_files:

    try:
        number = int(file.stem.split("_")[1])
        numbers.append(number)

    except (IndexError, ValueError):
        pass


if numbers:
    next_number = max(numbers) + 1
else:
    next_number = 1


filename = VOICE_FOLDER / f"voice_{next_number:02d}.wav"


# =========================================
# MICROPHONE
# =========================================

recognizer = sr.Recognizer()

microphone = sr.Microphone(
    device_index=0
)


# =========================================
# REGISTRATION
# =========================================

print("========================================")
print("          VOICE REGISTRATION")
print("========================================")

print("\nThis recording will be saved as:")
print(f"  {filename}")

print("\nSpeak naturally for about 8 seconds.")

print("\nExample:")
print("Hello, this is my registered voice.")
print("This voice will be used for the safety system.")
print("Help me, I need emergency assistance.")


input("\nPress ENTER when you are ready...")


# =========================================
# RECORD
# =========================================

with microphone as source:

    print("\nAdjusting microphone...")

    recognizer.adjust_for_ambient_noise(
        source,
        duration=1
    )

    print("\n🎤 Recording...")

    audio = recognizer.listen(
        source,
        timeout=None,
        phrase_time_limit=8
    )


print("\nRecording complete!")


# =========================================
# SAVE RECORDING
# =========================================

with open(filename, "wb") as file:

    file.write(
        audio.get_wav_data()
    )


print("\n✓ Voice recording saved!")
print(f"  {filename}")