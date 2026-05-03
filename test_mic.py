from voice.listener import listen
from voice.speaker import speak

speak("Microphone test. Say something after this.")

result = listen()

if result:
    speak(f"I heard you say: {result}")
else:
    speak("I did not catch that. Please try again.")