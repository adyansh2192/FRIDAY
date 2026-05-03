import asyncio
import edge_tts
import pygame
import tempfile
import os
from loguru import logger

VOICE = "en-US-AriaNeural"

# Initialize pygame ONCE when the module loads
# This is the key fix — never call mixer.init() more than once
pygame.mixer.init()
logger.info("Audio system initialized.")

async def _speak_async(text: str):
    """Generates speech and plays it."""
    tmp_path = None
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp_path = tmp.name

        # Generate audio
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(tmp_path)

        # Stop anything currently playing before starting new audio
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        # Play new audio
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()

        # Wait until done
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

        # Small gap between responses so it doesn't feel abrupt
        await asyncio.sleep(0.2)

    except Exception as e:
        logger.error(f"TTS error: {e}")

    finally:
        # Always clean up the temp file
        try:
            if tmp_path and os.path.exists(tmp_path):
                pygame.mixer.music.unload()
                os.remove(tmp_path)
        except Exception as e:
            logger.warning(f"Temp file cleanup failed: {e}")

def speak(text: str):
    """
    Main speak function. Call this from anywhere.
    Usage: speak("Hello boss")
    """
    if not text or not text.strip():
        return

    logger.info(f"FRIDAY: {text}")

    try:
        asyncio.run(_speak_async(text))
    except RuntimeError:
        # If an event loop is already running (shouldn't happen but just in case)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_speak_async(text))
        loop.close()

def stop_speaking():
    """Force stop any current audio."""
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()