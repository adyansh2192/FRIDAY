import speech_recognition as sr
import time
from loguru import logger

recognizer = sr.Recognizer()

WAKE_PHRASES = [
    "hey friday",
    "hi friday", 
    "okay friday",
    "friday",
]

def play_chime():
    """Plays the wake chime — uses already-initialized pygame from speaker."""
    try:
        import pygame
        # Don't init again — speaker.py already did it
        pygame.mixer.music.load("chime.wav")
        pygame.mixer.music.play()
        time.sleep(0.3)
    except Exception as e:
        logger.warning(f"Chime failed: {e}")

def listen_for_wake_word(timeout: int = 3) -> bool:
    """
    Passively listens for wake word.
    Returns True if detected, False otherwise.
    """
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            try:
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=3
                )
                text = recognizer.recognize_google(audio).lower()
                logger.debug(f"Passive heard: {text}")

                if any(phrase in text for phrase in WAKE_PHRASES):
                    logger.success(f"Wake word detected: '{text}'")
                    return True

            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass

    except Exception as e:
        logger.error(f"Wake word error: {e}")

    return False