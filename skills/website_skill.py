import webbrowser
import re
from skills.base import BaseSkill
from loguru import logger

class WebsiteSkill(BaseSkill):

    TRIGGERS = [
        "open", "go to", "launch", "take me to",
        "browse", "navigate to", "visit", "load"
    ]

    # Known sites — handles common ones instantly without guessing
    SITE_MAP = {
        # Google services
        "youtube":          "https://youtube.com",
        "gmail":            "https://mail.google.com",
        "google":           "https://google.com",
        "google maps":      "https://maps.google.com",
        "google drive":     "https://drive.google.com",
        "google docs":      "https://docs.google.com",
        "google sheets":    "https://sheets.google.com",
        "google translate": "https://translate.google.com",

        # Social
        "instagram":        "https://instagram.com",
        "twitter":          "https://twitter.com",
        "x":                "https://x.com",
        "facebook":         "https://facebook.com",
        "linkedin":         "https://linkedin.com",
        "reddit":           "https://reddit.com",
        "whatsapp":         "https://web.whatsapp.com",
        "telegram":         "https://web.telegram.org",
        "pinterest":        "https://pinterest.com",
        "snapchat":         "https://snapchat.com",

        # Dev tools
        "github":           "https://github.com",
        "stack overflow":   "https://stackoverflow.com",
        "replit":           "https://replit.com",
        "codepen":          "https://codepen.io",

        # Entertainment
        "netflix":          "https://netflix.com",
        "spotify":          "https://open.spotify.com",
        "hotstar":          "https://hotstar.com",
        "prime video":      "https://primevideo.com",
        "disney plus":      "https://disneyplus.com",
        "twitch":           "https://twitch.tv",

        # News
        "bbc":              "https://bbc.com/news",
        "times of india":   "https://timesofindia.indiatimes.com",
        "ndtv":             "https://ndtv.com",
        "the hindu":        "https://thehindu.com",
        "cricbuzz":         "https://cricbuzz.com",
        "espn":             "https://espn.com",

        # Shopping
        "amazon":           "https://amazon.in",
        "flipkart":         "https://flipkart.com",
        "meesho":           "https://meesho.com",
        "myntra":           "https://myntra.com",

        # Productivity
        "notion":           "https://notion.so",
        "trello":           "https://trello.com",
        "canva":            "https://canva.com",
        "figma":            "https://figma.com",

        # AI tools
        "chatgpt":          "https://chat.openai.com",
        "claude":           "https://claude.ai",
        "gemini":           "https://gemini.google.com",
        "perplexity":       "https://perplexity.ai",

        # Other
        "wikipedia":        "https://wikipedia.org",
        "weather":          "https://weather.com",
        "maps":             "https://maps.google.com",
        "translate":        "https://translate.google.com",
    }

    def can_handle(self, user_input: str) -> bool:
        text = user_input.lower()
        return any(t in text for t in self.TRIGGERS)

    def execute(self, user_input: str) -> str:
        text = user_input.lower()

        # Step 1 — check known sites first (longest match wins)
        for site in sorted(self.SITE_MAP, key=len, reverse=True):
            if site in text:
                url = self.SITE_MAP[site]
                webbrowser.open(url)
                logger.success(f"Opened known site: {url}")
                return f"Opening {site} for you boss."

        # Step 2 — try to build a URL from what they said
        site_name = self._extract_site_name(text)

        if site_name:
            # Try direct .com URL first
            guessed_url = f"https://www.{site_name}.com"
            try:
                webbrowser.open(guessed_url)
                logger.success(f"Opened guessed URL: {guessed_url}")
                return f"Opening {site_name} for you boss."
            except Exception as e:
                logger.warning(f"Guessed URL failed: {e}")

        # Step 3 — fall back to Google search for anything else
        query = self._extract_search_query(text)
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        logger.info(f"Opened Google search for: {query}")
        return f"I'm not sure of the exact site boss, so I've searched Google for {query}."

    def _extract_site_name(self, text: str) -> str | None:
        """
        Pulls out the website name from what the user said.
        Handles patterns like:
        - "open facebook"
        - "go to amazon"
        - "open the bbc website"
        - "take me to stackoverflow"
        """
        # Remove trigger words
        for trigger in sorted(self.TRIGGERS, key=len, reverse=True):
            text = text.replace(trigger, "").strip()

        # Remove filler words
        for filler in ["the", "website", "site", "page", "web", "dot com", ".com"]:
            text = text.replace(filler, "").strip()

        # What's left should be the site name
        site = text.strip()

        # Must be a single word or short phrase — reject long sentences
        if site and len(site.split()) <= 3 and len(site) > 1:
            # Convert to URL-friendly format
            return site.replace(" ", "")

        return None

    def _extract_search_query(self, text: str) -> str:
        """Extracts a clean search query from the user's request."""
        for trigger in sorted(self.TRIGGERS, key=len, reverse=True):
            text = text.replace(trigger, "").strip()
        return text.strip() or "website"