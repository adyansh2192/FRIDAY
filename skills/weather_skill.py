import requests
from skills.base import BaseSkill
from core.config import get_env
from loguru import logger

class WeatherSkill(BaseSkill):

    TRIGGERS = [
        "weather", "temperature", "hot", "cold",
        "rain", "sunny", "forecast", "humid", "wind"
    ]

    def can_handle(self, user_input: str) -> bool:
        return any(trigger in user_input.lower() for trigger in self.TRIGGERS)

    def execute(self, user_input: str) -> str:
        api_key = get_env("OPENWEATHER_API_KEY")
        city    = get_env("DEFAULT_CITY", "Delhi")

        # Check if user mentioned a specific city
        words = user_input.lower().split()
        for i, word in enumerate(words):
            if word in ["in", "for", "at"] and i + 1 < len(words):
                city = words[i + 1].capitalize()
                break

        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={city}&appid={api_key}&units=metric"
            )
            response = requests.get(url, timeout=5)
            data = response.json()

            if data.get("cod") != 200:
                return f"Couldn't get weather for {city}. Check the city name."

            temp        = round(data["main"]["temp"])
            feels_like  = round(data["main"]["feels_like"])
            description = data["weather"][0]["description"]
            humidity    = data["main"]["humidity"]

            return (
                f"In {city} it's {temp}°C and {description}, "
                f"feels like {feels_like}°C with {humidity}% humidity."
            )

        except Exception as e:
            logger.error(f"Weather error: {e}")
            return "Weather data is unavailable right now, boss."