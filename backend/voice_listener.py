import time
import collections
import threading
import speech_recognition as sr

TRIGGER_PHRASES = ["help me", "save me", "emergency", "stop it", "back off", "help"]

class ContinuousVoiceListener:
    def __init__(self, callback_function, buffer_seconds=15, sample_rate=16000, chunk_size=1024):
        self.callback_function = callback_function
        self.buffer_seconds = buffer_seconds
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_running = False

        max_chunks = int((sample_rate / chunk_size) * buffer_seconds)
        self.audio_buffer = collections.deque(maxlen=max_chunks)

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def start_listening(self):
        """Starts background thread for continuous voice monitoring."""
        self.is_running = True
        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()
        print("🎙️ 24/7 Background Voice Listener & Rolling Buffer Active.")

    def _listen_loop(self):
        with sr.Microphone(sample_rate=self.sample_rate) as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

            while self.is_running:
                try:
                    audio_data = self.recognizer.listen(source, timeout=3, phrase_time_limit=4)
                    raw_bytes = audio_data.get_raw_data()
                    self.audio_buffer.append(raw_bytes)

                    try:
                        text = self.recognizer.recognize_google(audio_data).lower()
                        print(f"🗣️ Heard: '{text}'")

                        if any(phrase in text for phrase in TRIGGER_PHRASES):
                            print(f"🚨 VOICE TRIGGER MATCHED: '{text}'!")
                            pre_trigger_audio = b"".join(list(self.audio_buffer))
                            
                            self.callback_function(
                                detected_phrase=text,
                                pre_audio_bytes=pre_trigger_audio
                            )
                            time.sleep(10)

                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        print(f"⚠️ Speech Recognition API Error: {e}")

                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print(f"⚠️ Voice loop exception: {e}")
                    time.sleep(1)

    def stop_listening(self):
        self.is_running = False