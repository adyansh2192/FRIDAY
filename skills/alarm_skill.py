import threading
import time
import re
from datetime import datetime, timedelta
from skills.base import BaseSkill
from loguru import logger

active_alarms = []

class AlarmSkill(BaseSkill):

    TRIGGERS = [
        "alarm", "wake me", "wake me up",
        "set timer", "timer for", "timer of",
        "set an alarm", "set a alarm", "set alarm",
    ]

    def can_handle(self, user_input: str) -> bool:
        text = user_input.lower()

        # Cancel commands
        if any(w in text for w in ["cancel alarm", "stop alarm", "delete alarm", "cancel timer"]):
            return True

        # Must have a trigger word
        has_trigger = any(t in text for t in self.TRIGGERS)
        if not has_trigger:
            return False

        # Must have a time reference
        has_time = bool(re.search(r'\d', text)) or any(w in text for w in [
            "minute", "hour", "second", "morning",
            "am", "pm", "a.m", "p.m", "o'clock"
        ])

        return has_time

    def execute(self, user_input: str) -> str:
        text = user_input.lower().strip()

        # Cancel
        if any(w in text for w in ["cancel alarm", "stop alarm", "delete alarm", "cancel timer"]):
            return self._cancel_all()

        # Test alarm — fires in 10 seconds for testing
        if "test alarm" in text:
            self._schedule_alarm(10, "test")
            return "Test alarm set for 10 seconds from now boss."

        # Try relative time first — "in X minutes"
        relative = self._parse_relative(text)
        if relative:
            seconds, label = relative
            self._schedule_alarm(seconds, label)
            return f"Alarm set for {label} from now boss."

        # Try absolute time — "at 7am"
        absolute = self._parse_absolute(text)
        if absolute:
            seconds, label = absolute
            if seconds < 0:
                return "That time has already passed boss. Try again with tomorrow's time."
            self._schedule_alarm(seconds, label)
            return f"Alarm set for {label} boss."

        return "I couldn't figure out the alarm time boss. Try 'set alarm for 7am' or 'wake me in 30 minutes'."

    def _parse_relative(self, text: str):
        """Parse 'in X minutes/hours/seconds'."""
        # Digit numbers
        match = re.search(r'(?:in\s+)?(\d+)\s*(second|sec|minute|min|hour|hr)s?', text)
        if match:
            num  = int(match.group(1))
            unit = match.group(2).lower()
            if unit in ("hour", "hr"):
                secs  = num * 3600
                label = f"{num} hour{'s' if num > 1 else ''}"
            elif unit in ("minute", "min"):
                secs  = num * 60
                label = f"{num} minute{'s' if num > 1 else ''}"
            else:
                secs  = num
                label = f"{num} second{'s' if num > 1 else ''}"
            return secs, label

        # Word numbers
        word_map = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "fifteen": 15, "twenty": 20, "thirty": 30,
            "forty five": 45, "forty-five": 45, "sixty": 60,
        }
        for word, num in word_map.items():
            if f"{word} minute" in text or f"{word} min" in text:
                return num * 60, f"{num} minutes"
            if f"{word} hour" in text:
                return num * 3600, f"{num} hour{'s' if num > 1 else ''}"
            if f"{word} second" in text:
                return num, f"{num} seconds"

        return None

    def _parse_absolute(self, text: str):
        """Parse 'at 7am', 'at 7:30 pm', 'at 7:30 p.m.'"""
        # Normalise am/pm variants
        text = re.sub(r'a\.m\.?', 'am', text)
        text = re.sub(r'p\.m\.?', 'pm', text)

        now = datetime.now()

        patterns = [
            r'(?:at\s+)?(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(?:at\s+)?(\d{1,2})\s*(am|pm)',
            r'(?:at\s+)?(\d{1,2}):(\d{2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue

            groups = match.groups()

            try:
                if len(groups) == 3:
                    hour = int(groups[0])
                    mins = int(groups[1])
                    ampm = groups[2]
                elif len(groups) == 2 and groups[1] in ('am', 'pm'):
                    hour = int(groups[0])
                    mins = 0
                    ampm = groups[1]
                else:
                    hour = int(groups[0])
                    mins = int(groups[1])
                    ampm = None

                if ampm == 'pm' and hour != 12:
                    hour += 12
                if ampm == 'am' and hour == 12:
                    hour = 0

                alarm_dt = now.replace(
                    hour=hour, minute=mins,
                    second=0, microsecond=0
                )

                # If already passed today, schedule for tomorrow
                if alarm_dt <= now:
                    alarm_dt += timedelta(days=1)

                secs  = (alarm_dt - now).total_seconds()
                label = alarm_dt.strftime("%I:%M %p")
                return secs, label

            except Exception as e:
                logger.warning(f"Alarm time parse error: {e}")
                continue

        return None

    def _schedule_alarm(self, seconds: float, label: str):
        """Schedule alarm in background thread."""

        def _fire():
            logger.info(f"Alarm scheduled — firing in {seconds:.0f}s for: {label}")
            time.sleep(seconds)
            logger.success(f"Alarm firing now: {label}")

            # Emit to UI
            try:
                from ui.window import signals
                signals.friday_replied.emit(f"⏰ ALARM — {label}")
                signals.status_changed.emit("speaking")
            except Exception as e:
                logger.warning(f"UI signal failed: {e}")

            # Speak using fresh event loop — safe from threads
            import asyncio
            import edge_tts
            import pygame
            import tempfile
            import os

            alarm_text = f"Boss! Boss! Your alarm is going off! It is {label}!"

            async def _say():
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp_path = tmp.name
                try:
                    communicate = edge_tts.Communicate(alarm_text, "en-US-AriaNeural")
                    await communicate.save(tmp_path)
                    pygame.mixer.music.load(tmp_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                    await asyncio.sleep(0.5)

                    # Ring a second time
                    pygame.mixer.music.load(tmp_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
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

            try:
                signals.status_changed.emit("sleeping")
            except Exception:
                pass

        thread = threading.Thread(target=_fire, daemon=True)
        thread.start()
        active_alarms.append({"label": label, "thread": thread})
        logger.success(f"Alarm set: {label} in {seconds:.0f} seconds")

    def _cancel_all(self) -> str:
        count = len(active_alarms)
        active_alarms.clear()
        if count == 0:
            return "No active alarms to cancel boss."
        return f"Cancelled {count} alarm{'s' if count > 1 else ''} boss."