import requests
from datetime import datetime
from skills.base import BaseSkill
from core.config import get_env
from loguru import logger

class BriefingSkill(BaseSkill):

    TRIGGERS = [
        "good morning", "morning briefing", "morning update",
        "start my day", "daily briefing", "what's my day look like",
        "good evening", "evening briefing"
    ]

    def can_handle(self, user_input: str) -> bool:
        return any(t in user_input.lower() for t in self.TRIGGERS)

    def execute(self, user_input: str) -> str:
        now = datetime.now()

        # Greeting based on time
        hour = now.hour
        if hour < 12:
            greeting = "Good morning boss"
        elif hour < 17:
            greeting = "Good afternoon boss"
        else:
            greeting = "Good evening boss"

        # Date and time
        date_str = now.strftime("%A, %B %d")
        time_str = now.strftime("%I:%M %p")

        # Weather
        weather_str = self._get_weather()

        # News headline
        news_str = self._get_news()

        # Put it all together
        briefing = (
            f"{greeting}. "
            f"It's {date_str} and the time is {time_str}. "
            f"{weather_str} "
            f"{news_str} "
            f"Have a productive day boss."
        )

        return briefing

    def _get_weather(self) -> str:
        try:
            api_key = get_env("OPENWEATHER_API_KEY")
            city    = get_env("DEFAULT_CITY", "Delhi")

            if not api_key:
                return ""

            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={city}&appid={api_key}&units=metric"
            )
            data = requests.get(url, timeout=5).json()

            if data.get("cod") != 200:
                return ""

            temp        = round(data["main"]["temp"])
            description = data["weather"][0]["description"]
            return f"In {city} it's {temp}°C with {description}."

        except Exception as e:
            logger.warning(f"Briefing weather failed: {e}")
            return ""

    def _get_news(self) -> str:
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text("top news India today", max_results=2))

            if not results:
                return ""

            headline = results[0]["title"]
            return f"Top story today: {headline}."

        except Exception as e:
            logger.warning(f"Briefing news failed: {e}")
            return ""