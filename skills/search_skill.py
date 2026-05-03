from ddgs import DDGS
from skills.base import BaseSkill
from loguru import logger

class SearchSkill(BaseSkill):

    TRIGGERS = [
        "search", "look up", "find", "google",
        "who is", "what is", "how to", "tell me about",
        "latest", "news", "what happened"
    ]

    def can_handle(self, user_input: str) -> bool:
        return any(trigger in user_input.lower() for trigger in self.TRIGGERS)

    def execute(self, user_input: str) -> str:
        query = user_input.lower()
        for filler in ["search for", "search", "look up", "find", "google", "tell me about"]:
            query = query.replace(filler, "").strip()

        logger.info(f"Searching for: {query}")

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))

            if not results:
                return "I couldn't find anything on that, boss."

            top = results[0]
            return f"Here's what I found: {top['body'][:250]}."

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return "Search is unavailable right now. Try again in a moment."