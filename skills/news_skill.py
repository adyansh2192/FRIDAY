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
               # Use .news() instead of .text() — returns actual headlines
               results = list(ddgs.news(query, max_results=6))

          if not results:
               return "I couldn't pull up any news right now boss. Try again in a moment."

          headlines = []
          seen      = set()

          for r in results:
               # .news() returns 'title' and 'body' fields
               title = r.get("title", "").strip()
               body  = r.get("body", "").strip()

               # Use body if available — it's the actual story summary
               story = body if body and len(body) > 30 else title

               # Skip navigation garbage and duplicates
               skip_phrases = [
                    "live score", "points table", "schedule", "fixtures",
                    "latest news and updates", "breaking news, world news",
                    "read all", "click here", "subscribe", "sign up",
                    "privacy policy", "terms of service"
               ]

               if story and story not in seen:
                    if not any(p in story.lower() for p in skip_phrases):
                         headlines.append(story[:200])
                         seen.add(story)

               if len(headlines) == 3:
                    break

          if not headlines:
               return "Couldn't find clear headlines right now boss. Try a different category."

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