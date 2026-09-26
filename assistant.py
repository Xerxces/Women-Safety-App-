import speech_recognition as sr
print("Analyzing !")
recognizer = sr.Recognizer()
microphone = sr.Microphone(device_index=0)
print("\nMicrophone selected.")
with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=0)    
    print("Listening !")
    audio = recognizer.listen(source)

print("\nAudio captured!")
print(" Connecting to emergency contacts and service's !")
try:
    text = recognizer.recognize_google(audio)
    print("\n")
    print(text)
except sr.UnknownValueError:
    print("\nI didn't get that !")
except sr.RequestError as error:
    print("\nSpeech recognition service error:")
    print(error) 


    