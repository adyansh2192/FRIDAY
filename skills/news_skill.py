from skills.base import BaseSkill
from loguru import logger

class NewsSkill(BaseSkill):

    TRIGGERS = [
        "news", "headlines", "what's happening",
        "latest news", "top stories", "current events",
        "what happened today", "tell me the news",
        "any news", "update me"
    ]

    # Category keywords mapped to search queries
    CATEGORIES = {
        "sports":     "latest sports news today",
        "cricket":    "latest cricket news today",
        "ipl":        "IPL 2025 latest news today",
        "football":   "football soccer latest news today",
        "tech":       "technology news today",
        "technology": "technology news today",
        "business":   "business finance news today",
        "finance":    "stock market finance news today",
        "india":      "India news today",
        "world":      "world news today",
        "politics":   "politics news today",
        "science":    "science news today",
        "health":     "health medical news today",
        "bollywood":  "bollywood entertainment news today",
        "movies":     "movies entertainment news today",
    }

    def can_handle(self, user_input: str) -> bool:
        return any(t in user_input.lower() for t in self.TRIGGERS)

    def execute(self, user_input: str) -> str:
        text = user_input.lower()

        # Detect category from what user said
        query    = "top news India today"  # default
        category = "general"

        for keyword, search_query in self.CATEGORIES.items():
            if keyword in text:
                query    = search_query
                category = keyword
                break

        logger.info(f"Fetching {category} news...")
        return self._fetch_news(query, category)

    def _fetch_news(self, query: str, category: str) -> str:
        try:
            from ddgs import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))

            if not results:
                return "I couldn't pull up any news right now boss. Try again in a moment."

            # Pick top 3 unique headlines
            headlines = []
            seen      = set()

            for r in results:
                title = r.get("title", "").strip()
                # Skip duplicates and very short titles
                if title and title not in seen and len(title) > 20:
                    headlines.append(title)
                    seen.add(title)
                if len(headlines) == 3:
                    break

            if not headlines:
                return "Couldn't find clear headlines right now boss."

            # Format into a spoken response
            label = f"{category.capitalize()} news" if category != "general" else "Top news"

            if len(headlines) == 1:
                return f"{label} — {headlines[0]}."

            elif len(headlines) == 2:
                return (
                    f"Here are your {label} headlines boss. "
                    f"First — {headlines[0]}. "
                    f"Second — {headlines[1]}."
                )

            else:
                return (
                    f"Here are your top {label} headlines boss. "
                    f"First — {headlines[0]}. "
                    f"Second — {headlines[1]}. "
                    f"And third — {headlines[2]}."
                )

        except Exception as e:
            logger.error(f"News fetch error: {e}")
            return "News is unavailable right now boss. Try again shortly."