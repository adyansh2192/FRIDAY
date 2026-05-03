import subprocess
import os
from skills.base import BaseSkill
from loguru import logger

class LauncherSkill(BaseSkill):

    TRIGGERS = [
        "open", "launch", "start", "run"
    ]

    # Add or change any of these to match YOUR installed apps
    APP_MAP = {
        # Browsers
        "chrome":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox":      r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge":         r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

        # Dev tools
        "vs code":      r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "vscode":       r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "notepad":      "notepad.exe",
        "terminal":     "cmd.exe",

        # Media
        "spotify":      r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
        "vlc":          r"C:\Program Files\VideoLAN\VLC\vlc.exe",

        # System
        "calculator":   "calc.exe",
        "file explorer": "explorer.exe",
        "task manager": "taskmgr.exe",
        "settings":     "ms-settings:",
        "paint":        "mspaint.exe",
    }

    def can_handle(self, user_input: str) -> bool:
        text = user_input.lower()
        has_trigger = any(t in text for t in self.TRIGGERS)
        has_app = any(app in text for app in self.APP_MAP.keys())
        return has_trigger and has_app

    def execute(self, user_input: str) -> str:
        text = user_input.lower()
        username = os.getenv("USERNAME", "User")

        # Find which app was mentioned
        matched_app = None
        matched_path = None

        for app, path in self.APP_MAP.items():
            if app in text:
                matched_app = app
                # Fill in the actual Windows username
                matched_path = path.replace("{user}", username)
                break

        if not matched_app:
            return "I couldn't figure out which app to open, boss."

        try:
            if matched_path.startswith("ms-"):
                # Windows Settings URI
                os.startfile(matched_path)
            elif matched_path.endswith(".exe") and not os.path.isabs(matched_path):
                # System app like calc.exe — Windows finds it automatically
                subprocess.Popen(matched_path, shell=True)
            else:
                # Full path app
                if os.path.exists(matched_path):
                    subprocess.Popen(matched_path)
                else:
                    logger.warning(f"App path not found: {matched_path}")
                    return f"I found {matched_app} in my list but couldn't locate it on your PC. Check the path in launcher_skill.py."

            logger.success(f"Launched: {matched_app}")
            return f"Opening {matched_app} for you, boss."

        except Exception as e:
            logger.error(f"Launch failed: {e}")
            return f"I ran into an issue opening {matched_app}."