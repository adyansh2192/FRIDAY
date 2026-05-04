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

    if any(w in user_input for w in ["shutdown", "exit", "goodbye", "quit", "power off"]):
        speak("Shutting down. Goodbye boss.")
        signals.friday_replied.emit("Shutting down. Goodbye boss.")
        return False

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
        return True

    # Show thinking indicator
    signals.status_changed.emit("thinking")
    signals.show_typing.emit()

    # Skills then brain
    response = route(user_input) or think(user_input)

    # Hide typing, show response
    signals.hide_typing.emit()
    signals.status_changed.emit("speaking")
    signals.friday_replied.emit(response)
    speak(response)

    return True


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
        speak("Yes boss?")
        signals.friday_replied.emit("Yes boss?")

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