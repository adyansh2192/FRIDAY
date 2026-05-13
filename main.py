import sys
import threading
from loguru import logger
from core.logger import setup_logger
from core.config import load_config, get_env
from voice.speaker import speak
from voice.listener import listen_for_command
from voice.wake_word import listen_for_wake_word, play_chime
from brain.mind import think, reset_memory
from skills.router import route
from ui.window import launch_ui, signals
from ui.tray_icon import create_tray


def handle_command(user_input: str) -> bool:
    if not user_input:
        return True

    # Shutdown
    if any(w in user_input for w in ["shutdown", "exit", "goodbye", "quit", "power off"]):
        speak("Shutting down. Goodbye boss.")
        signals.friday_replied.emit("Shutting down. Goodbye boss.")
        return False

    # Memory reset
    if any(w in user_input for w in ["reset memory", "forget everything", "clear memory"]):
        reset_memory()
        speak("Memory cleared. Starting fresh boss.")
        signals.friday_replied.emit("Memory cleared. Starting fresh boss.")
        return True

    # Personality check
    from brain.personality import handle_personality
    personality_response = handle_personality(user_input)
    if personality_response:
        signals.status_changed.emit("speaking")
        signals.friday_replied.emit(personality_response)
        speak(personality_response)
        signals.status_changed.emit("sleeping")
        return True

    # Show thinking
    signals.status_changed.emit("thinking")
    signals.show_typing.emit()

    # Route to skill or brain
    response = route(user_input)

    if response is None:
        # Brain handles it
        response = think(user_input)
        signals.hide_typing.emit()
        signals.status_changed.emit("speaking")
        signals.friday_replied.emit(response)
        speak(response)
        signals.status_changed.emit("sleeping")
        return True

    signals.hide_typing.emit()

    # Detect music responses — set music state
    music_keywords = ["playing", "opening", "spotify", "youtube", "paused", "stopped", "music"]
    is_music = any(w in response.lower() for w in music_keywords)

    if is_music:
        signals.status_changed.emit("music")
        signals.friday_replied.emit(response)
        speak(response)
        # Use plain Python thread to reset state — no QTimer needed
        def _reset_state():
            import time
            time.sleep(4)
            signals.status_changed.emit("sleeping")
        threading.Thread(target=_reset_state, daemon=True).start()
    else:
        signals.status_changed.emit("speaking")
        signals.friday_replied.emit(response)
        speak(response)
        signals.status_changed.emit("sleeping")

    return True

def _get_wake_response() -> str:
    """Returns a varied wake response based on time of day."""
    import random
    from datetime import datetime

    hour = datetime.now().hour

    # Late night — 11pm to 5am
    if hour >= 23 or hour < 5:
        responses = [
            "What is it this late boss?",
            "Still up boss? What do you need?",
            "Burning the midnight oil boss?",
            "It's late boss, what can I do for you?",
        ]

    # Early morning — 5am to 9am
    elif 5 <= hour < 9:
        responses = [
            "Good morning boss, what do you need?",
            "Early start today boss?",
            "Morning boss, at your service.",
            "Rise and shine boss, what is it?",
        ]

    # Daytime — 9am to 6pm
    elif 9 <= hour < 18:
        responses = [
            "Yes boss?",
            "At your service boss.",
            "Greetings boss, what is it?",
            "What can I do for you boss?",
            "Ready boss, go ahead.",
            "Standing by boss.",
        ]

    # Evening — 6pm to 11pm
    else:
        responses = [
            "Good evening boss, what do you need?",
            "Yes boss?",
            "Evening boss, at your service.",
            "What is it boss?",
            "Here boss, go ahead.",
        ]

    return random.choice(responses)

def friday_loop():
    """Runs in background thread — FRIDAY's full logic."""
    setup_logger(debug=True)
    load_config()

    version = get_env("VERSION", "0.1.0")
    logger.success(f"FRIDAY v{version} online.")

    startup_msg = f"FRIDAY online. Say Hey FRIDAY to wake me up."
    signals.status_changed.emit("sleeping")
    signals.friday_replied.emit(startup_msg)
    speak(startup_msg)

    running = True
    while running:
        signals.status_changed.emit("sleeping")

        # ── Passive mode — wait for wake word ──
        if not listen_for_wake_word(timeout=3):
            continue

        # ── Woken up ──
        logger.success("Wake word detected!")
        play_chime()
        signals.status_changed.emit("listening")
        wake_response = _get_wake_response()
        speak(wake_response)
        signals.friday_replied.emit(wake_response)

        # ── Active conversation mode ──
        # Stay awake for multiple back-and-forth exchanges
        # Only go back to sleep after 2 missed listens in a row
        missed = 0
        while running and missed < 2:
            command = listen_for_command()

            if command is None:
                missed += 1
                if missed == 1:
                    # One miss — give a gentle nudge
                    signals.status_changed.emit("listening")
                    continue
                else:
                    # Two misses — go back to sleep
                    msg = "Going back to sleep. Say Hey FRIDAY when you need me."
                    speak(msg)
                    signals.friday_replied.emit(msg)
                    signals.status_changed.emit("sleeping")
                    break

            # Reset miss counter on successful hear
            missed = 0
            signals.user_spoke.emit(command)
            running = handle_command(command)

            # Stay in active listening mode after responding
            signals.status_changed.emit("listening")

    logger.info("FRIDAY loop ended.")


def main():
    # Launch UI on main thread
    app, window = launch_ui()

    # Start system tray icon
    tray = create_tray(app, window)

    # Run FRIDAY logic in background thread
    friday_thread = threading.Thread(target=friday_loop, daemon=True)
    friday_thread.start()

    # Qt takes over main thread
    sys.exit(app.exec())


if __name__ == "__main__":
    main()