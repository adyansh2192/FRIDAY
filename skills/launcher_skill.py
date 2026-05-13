import subprocess
import os
from skills.base import BaseSkill
from loguru import logger

class LauncherSkill(BaseSkill):

    OPEN_TRIGGERS = [
        "open", "launch", "start", "run"
    ]

    CLOSE_TRIGGERS = [
        "close", "kill", "shut", "terminate",
        "quit", "exit", "end"
    ]

    APP_MAP = {
        "chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox":       r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge":          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "vs code":       r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "vscode":        r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "notepad":       "notepad.exe",
        "terminal":      "cmd.exe",
        "spotify":       r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
        "vlc":           r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        "calculator":    "calc.exe",
        "file explorer": "explorer.exe",
        "task manager":  "taskmgr.exe",
        "settings":      "ms-settings:",
        "paint":         "mspaint.exe",
        "discord":       r"C:\Users\{user}\AppData\Local\Discord\Update.exe",
        "whatsapp":      r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe",
    }

    PROCESS_MAP = {
        "chrome":        "chrome.exe",
        "firefox":       "firefox.exe",
        "edge":          "msedge.exe",
        "vs code":       "Code.exe",
        "vscode":        "Code.exe",
        "notepad":       "notepad.exe",
        "spotify":       "Spotify.exe",
        "vlc":           "vlc.exe",
        "calculator":    "CalculatorApp.exe",
        "task manager":  "Taskmgr.exe",
        "paint":         "mspaint.exe",
        "discord":       "Discord.exe",
        "whatsapp":      "WhatsApp.exe",
        "word":          "WINWORD.EXE",
        "excel":         "EXCEL.EXE",
        "powerpoint":    "POWERPNT.EXE",
    }

    def can_handle(self, user_input: str) -> bool:
        text = user_input.lower()

        has_open  = any(t in text for t in self.OPEN_TRIGGERS)
        has_close = any(t in text for t in self.CLOSE_TRIGGERS)
        has_app   = any(app in text for app in self.APP_MAP) or \
                    any(app in text for app in self.PROCESS_MAP)

        return (has_open or has_close) and has_app

    def execute(self, user_input: str) -> str:
        text = user_input.lower()

        if any(t in text for t in self.CLOSE_TRIGGERS):
            return self._close_app(text)
        return self._open_app(text)

    def _open_app(self, text: str) -> str:
        username = os.getenv("USERNAME", "User")

        for app, path in self.APP_MAP.items():
            if app in text:
                real_path = path.replace("{user}", username)
                try:
                    if real_path.startswith("ms-"):
                        os.startfile(real_path)
                    elif not os.path.isabs(real_path):
                        subprocess.Popen(real_path, shell=True)
                    elif os.path.exists(real_path):
                        subprocess.Popen(real_path)
                    else:
                        return f"I found {app} in my list but couldn't locate it on your PC boss. Check the path in launcher_skill.py."

                    logger.success(f"Opened: {app}")
                    return f"Opening {app} for you boss."

                except Exception as e:
                    logger.error(f"Open failed: {e}")
                    return f"Ran into an issue opening {app} boss."

        return "I couldn't figure out which app to open boss."

    def _close_app(self, text: str) -> str:
        for app, process in self.PROCESS_MAP.items():
            if app in text:
                try:
                    result = subprocess.run(
                        ["taskkill", "/F", "/IM", process],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        logger.success(f"Closed: {app}")
                        return f"Closed {app} boss."
                    else:
                        return f"{app} doesn't seem to be running boss."

                except Exception as e:
                    logger.error(f"Close failed: {e}")
                    return f"Couldn't close {app} boss."

        return "I couldn't figure out which app to close boss."