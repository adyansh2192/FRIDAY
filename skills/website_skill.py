import webbrowser
from skills.base import BaseSkill
from loguru import logger

class WebsiteSkill(BaseSkill):

    TRIGGERS = [
        "open", "go to", "launch", "take me to",
        "browse", "navigate to", "visit"
    ]

    SITE_MAP = {
        # Google services
        "youtube":        "https://youtube.com",
        "gmail":          "https://mail.google.com",
        "google":         "https://google.com",
        "google maps":    "https://maps.google.com",
        "google drive":   "https://drive.google.com",
        "google docs":    "https://docs.google.com",
        "google sheets":  "https://sheets.google.com",

        # Social
        "instagram":      "https://instagram.com",
        "twitter":        "https://twitter.com",
        "x":              "https://x.com",
        "facebook":       "https://facebook.com",
        "linkedin":       "https://linkedin.com",
        "reddit":         "https://reddit.com",
        "whatsapp":       "https://web.whatsapp.com",

        # Dev
        "github":         "https://github.com",
        "stack overflow": "https://stackoverflow.com",

        # Entertainment
        "netflix":        "https://netflix.com",
        "spotify":        "https://open.spotify.com",
        "hotstar":        "https://hotstar.com",
        "prime video":    "https://primevideo.com",

        # News
        "bbc":            "https://bbc.com/news",
        "times of india": "https://timesofindia.indiatimes.com",
        "ndtv":           "https://ndtv.com",

        # Productivity
        "notion":         "https://notion.so",
        "chatgpt":        "https://chat.openai.com",
        "claude":         "https://claude.ai",
    }

    def can_handle(self, user_input: str) -> bool:
        text = user_input.lower()
        has_trigger = any(t in text for t in self.TRIGGERS)
        has_site    = any(site in text for site in self.SITE_MAP)
        return has_trigger and has_site

    def execute(self, user_input: str) -> str:
        text = user_input.lower()

        matched_site = None
        matched_url  = None

        # Match longest site name first to avoid "x" matching inside "hotstar"
        for site in sorted(self.SITE_MAP, key=len, reverse=True):
            if site in text:
                matched_site = site
                matched_url  = self.SITE_MAP[site]
                break

        if not matched_site:
            return "I couldn't figure out which website to open boss."

        try:
            webbrowser.open(matched_url)
            logger.success(f"Opened: {matched_url}")
            return f"Opening {matched_site} for you boss."
        except Exception as e:
            logger.error(f"Browser error: {e}")
            return f"Couldn't open {matched_site} boss."