import threading
import re
from skills.base import BaseSkill
from loguru import logger

reminders = []

class ReminderSkill(BaseSkill):

    TRIGGERS = [
        "remind", "reminder", "alert", "notify",
        "don't let me forget", "remember to"
    ]

    def can_handle(self, user_input: str) -> bool:
        return any(t in user_input.lower() for t in self.TRIGGERS)

    def execute(self, user_input: str) -> str:
        text = user_input.lower()

        minutes = self._extract_minutes(text)
        if minutes is None:
            return "I didn't catch how long from now. Try saying 'remind me in 5 minutes to...'"

        message = self._extract_message(user_input)
        self._schedule_reminder(minutes, message)

        if minutes == 1:
            return f"Got it boss. I'll remind you to {message} in 1 minute."
        return f"Got it boss. I'll remind you to {message} in {minutes} minutes."

    def _extract_minutes(self, text: str) -> int | None:
        # "in X minutes"
        match = re.search(r'in (\d+)\s*min', text)
        if match:
            return int(match.group(1))

        # "in X hours"
        match = re.search(r'in (\d+)\s*hour', text)
        if match:
            return int(match.group(1)) * 60

        # "in X seconds"
        match = re.search(r'in (\d+)\s*sec', text)
        if match:
            return max(1, int(match.group(1)) // 60)

        # Word numbers
        word_map = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "fifteen": 15, "twenty": 20, "thirty": 30, "forty five": 45,
            "sixty": 60
        }
        for word, num in word_map.items():
            if f"in {word} minute" in text:
                return num
            if f"in {word} hour" in text:
                return num * 60

        return None

    def _extract_message(self, text: str) -> str:
        for keyword in [" to ", " about ", " that ", " for "]:
            if keyword in text.lower():
                idx = text.lower().index(keyword)
                reminder_text = text[idx + len(keyword):].strip()
                reminder_text = re.sub(
                    r'\s+in \d+\s*(minute|hour|second)s?.*', '', reminder_text
                )
                if reminder_text:
                    return reminder_text
        return "that thing you asked"

    def _schedule_reminder(self, minutes: int, message: str):
        """Fire the reminder in a background thread with its own event loop."""

        def _fire():
            import time
            import asyncio
            import edge_tts
            import pygame
            import tempfile
            import os

            time.sleep(minutes * 60)
            logger.info(f"Firing reminder: {message}")

            reminder_text = f"Boss, this is your reminder to {message}."

            # Show in UI
            try:
                from ui.window import signals
                signals.friday_replied.emit(f"⏰ Reminder: {message}")
            except Exception:
                pass

            # Speak with a fresh event loop — safe from threads
            async def _say():
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp_path = tmp.name
                try:
                    communicate = edge_tts.Communicate(reminder_text, "en-GB-SoniaNeural")
                    await communicate.save(tmp_path)
                    pygame.mixer.music.load(tmp_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                    await asyncio.sleep(0.3)
                finally:
                    try:
                        pygame.mixer.music.unload()
                        os.remove(tmp_path)
                    except Exception:
                        pass

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_say())
            finally:
                loop.close()

        thread = threading.Thread(target=_fire, daemon=True)
        thread.start()
        reminders.append(thread)
        logger.info(f"Reminder set: '{message}' in {minutes} minutes")