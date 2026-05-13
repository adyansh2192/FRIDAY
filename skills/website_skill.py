import webbrowser
import re
from skills.base import BaseSkill
from loguru import logger

class WebsiteSkill(BaseSkill):

    TRIGGERS = [
        "open", "go to", "launch", "take me to",
        "browse", "navigate to", "visit", "load",
        "show me", "watch", "find on", "search on",
        "play on", "look up on"
    ]

    SITE_MAP = {
        "youtube":          "https://youtube.com",
        "gmail":            "https://mail.google.com",
        "google":           "https://google.com",
        "google maps":      "https://maps.google.com",
        "google drive":     "https://drive.google.com",
        "google docs":      "https://docs.google.com",
        "google sheets":    "https://sheets.google.com",
        "google translate": "https://translate.google.com",
        "instagram":        "https://instagram.com",
        "twitter":          "https://twitter.com",
        "facebook":         "https://facebook.com",
        "linkedin":         "https://linkedin.com",
        "reddit":           "https://reddit.com",
        "whatsapp":         "https://web.whatsapp.com",
        "telegram":         "https://web.telegram.org",
        "github":           "https://github.com",
        "stack overflow":   "https://stackoverflow.com",
        "netflix":          "https://netflix.com",
        "spotify":          "https://open.spotify.com",
        "hotstar":          "https://hotstar.com",
        "prime video":      "https://primevideo.com",
        "disney plus":      "https://disneyplus.com",
        "twitch":           "https://twitch.tv",
        "bbc":              "https://bbc.com/news",
        "times of india":   "https://timesofindia.indiatimes.com",
        "ndtv":             "https://ndtv.com",
        "cricbuzz":         "https://cricbuzz.com",
        "amazon":           "https://amazon.in",
        "flipkart":         "https://flipkart.com",
        "notion":           "https://notion.so",
        "canva":            "https://canva.com",
        "chatgpt":          "https://chat.openai.com",
        "claude":           "https://claude.ai",
        "wikipedia":        "https://wikipedia.org",
    }

    SEARCH_URLS = {
        "youtube":   "https://www.youtube.com/results?search_query=",
        "spotify":   "spotify:search:",
        "netflix":   "https://www.netflix.com/search?q=",
        "amazon":    "https://www.amazon.in/s?k=",
        "flipkart":  "https://www.flipkart.com/search?q=",
        "google":    "https://www.google.com/search?q=",
        "reddit":    "https://www.reddit.com/search/?q=",
        "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search=",
        "github":    "https://github.com/search?q=",
        "cricbuzz":  "https://www.cricbuzz.com/search?q=",
        "hotstar":   "https://www.hotstar.com/in/search?q=",
        "prime video": "https://www.primevideo.com/search/ref=atv_sr_sug_1?phrase=",
    }

    def can_handle(self, user_input: str) -> bool:
        text = user_input.lower()

        # Always handle "X on Platform" pattern — most specific
        for platform in self.SEARCH_URLS:
            if f"on {platform}" in text:
                return True

        # Only handle "open X" if X is a known website — not an app
        for site in self.SITE_MAP:
            if site in text:
                return True

        # Handle generic browse/navigate/visit/watch triggers
        # but NOT "open" or "launch" alone — those belong to LauncherSkill
        web_only_triggers = [
            "go to", "take me to", "browse", "navigate to",
            "visit", "load", "show me", "watch", "find on",
            "search on", "play on", "look up on"
        ]
        return any(t in text for t in web_only_triggers)

    def execute(self, user_input: str) -> str:
        text = user_input.lower().strip()

        # ── Priority 1: "X on Platform" pattern ──
        # Catches: "play Kesariya on YouTube"
        #          "search dark knight on Netflix"
        #          "open bohemian rhapsody on Spotify"
        for platform, search_url in self.SEARCH_URLS.items():
            pattern = rf'(?:play|open|watch|find|search|look up|put on|show)\s+(.+?)\s+on\s+{platform}'
            match   = re.search(pattern, text)
            if match:
                content = match.group(1).strip()
                return self._open_content(content, platform, search_url)

        # ── Priority 2: Known sites ──
        for site in sorted(self.SITE_MAP, key=len, reverse=True):
            if site in text:
                webbrowser.open(self.SITE_MAP[site])
                logger.success(f"Opened site: {site}")
                return f"Opening {site} for you boss."

        # ── Priority 3: Build URL from name ──
        site_name = self._extract_site_name(text)
        if site_name:
            url = f"https://www.{site_name}.com"
            webbrowser.open(url)
            return f"Opening {site_name} for you boss."

        # ── Priority 4: Google search fallback ──
        query = self._clean_query(text)
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return f"Searching Google for {query} boss."

    def _open_content(self, content: str, platform: str, search_url: str) -> str:
        try:
            encoded = content.replace(" ", "+")

            if platform == "spotify":
                url = f"spotify:search:{content.replace(' ', '%20')}"
            else:
                url = f"{search_url}{encoded}"

            webbrowser.open(url)
            logger.success(f"Opened '{content}' on {platform}")
            return f"Opening {content} on {platform} for you boss."

        except Exception as e:
            logger.error(f"Content open error: {e}")
            return f"Couldn't open {content} on {platform} boss."

    def _extract_site_name(self, text: str) -> str | None:
        for trigger in sorted(self.TRIGGERS, key=len, reverse=True):
            text = text.replace(trigger, "").strip()
        for filler in ["the", "website", "site", "page", "web", "dot com", ".com"]:
            text = text.replace(filler, "").strip()
        site = text.strip()
        if site and len(site.split()) <= 3 and len(site) > 1:
            return site.replace(" ", "")
        return None

    def _clean_query(self, text: str) -> str:
        for trigger in sorted(self.TRIGGERS, key=len, reverse=True):
            text = text.replace(trigger, "").strip()
        return text.strip() or "website"