import speech_recognition as sr
from loguru import logger

recognizer = sr.Recognizer()

# Make it less aggressive about cutting off speech
recognizer.pause_threshold = 1.2       # wait 1.2s of silence before stopping
recognizer.phrase_threshold = 0.3      # minimum seconds of speaking to count
recognizer.non_speaking_duration = 1.0 # seconds of silence = end of phrase

def listen(timeout: int = 5, phrase_limit: int = 30) -> str | None:
    """
    Standard listen function.
    phrase_limit bumped to 30 seconds to handle long sentences.
    """
    with sr.Microphone() as source:
        logger.info("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        logger.info("Listening...")

        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_limit
            )
            logger.info("Processing speech...")
            text = recognizer.recognize_google(audio)
            logger.success(f"You said: {text}")
            return text.lower()

        except sr.WaitTimeoutError:
            logger.warning("No speech detected within timeout")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"STT service error: {e}")
            return None

def listen_for_command(timeout: int = 8, phrase_limit: int = 45) -> str | None:
    """
    Attentive listen after wake word.
    Long timeout + long phrase limit for natural speech.
    45 seconds is enough for any reasonable command.
    """
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        logger.info("Listening for command...")

        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_limit
            )
            text = recognizer.recognize_google(audio)
            logger.success(f"Command heard: {text}")
            return text.lower()

        except sr.WaitTimeoutError:
            logger.warning("No command heard after wake word")
            return None
        except sr.UnknownValueError:
            logger.warning("Command not understood")
            return None
        except sr.RequestError as e:
            logger.error(f"STT error: {e}")
            return None