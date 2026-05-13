from datetime import datetime
from skills.base import BaseSkill

class DateTimeSkill(BaseSkill):

    TRIGGERS = [
        "what time", "what's the time", "current time",
        "what date", "what's the date", "current date",
        "what day", "what's today", "today's date",
    ]

    def can_handle(self, user_input: str) -> bool:
        text = user_input.lower()
        # Use exact phrase matching — not substring
        return any(t in text for t in self.TRIGGERS)

    def execute(self, user_input: str) -> str:
        now = datetime.now()

        # What are they asking — time or date?
        if any(w in user_input for w in ["time", "clock"]):
            return f"It's {now.strftime('%I:%M %p')} right now, boss."

        if any(w in user_input for w in ["date", "today", "day"]):
            return f"Today is {now.strftime('%A, %B %d %Y')}."

        # If both or unclear, give both
        return f"It's {now.strftime('%A, %B %d %Y')} and the time is {now.strftime('%I:%M %p')}."