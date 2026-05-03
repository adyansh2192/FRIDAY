import os
import subprocess
import pyautogui
import datetime
from skills.base import BaseSkill
from loguru import logger

class SystemSkill(BaseSkill):

    TRIGGERS = [
        "volume", "mute", "screenshot", "screen shot",
        "shutdown computer", "restart computer",
        "lock", "lock screen", "sleep",
        "increase volume", "decrease volume",
        "louder", "quieter", "turn up", "turn down"
    ]

    def can_handle(self, user_input: str) -> bool:
        return any(t in user_input.lower() for t in self.TRIGGERS)

    def execute(self, user_input: str) -> str:
        text = user_input.lower()

        # --- Screenshot ---
        if any(w in text for w in ["screenshot", "screen shot"]):
            return self._take_screenshot()

        # --- Volume ---
        if any(w in text for w in ["louder", "increase volume", "turn up", "volume up"]):
            return self._volume(up=True)

        if any(w in text for w in ["quieter", "decrease volume", "turn down", "volume down"]):
            return self._volume(up=False)

        if "mute" in text:
            return self._mute()

        # --- Power ---
        if "shutdown computer" in text:
            subprocess.run(["shutdown", "/s", "/t", "10"])
            return "Shutting down your PC in 10 seconds boss. Save your work."

        if "restart computer" in text:
            subprocess.run(["shutdown", "/r", "/t", "10"])
            return "Restarting in 10 seconds boss."

        if "lock" in text:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            return "Locking your screen boss."

        if "sleep" in text:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return "Putting the computer to sleep boss."

        return "I'm not sure what system action you want, boss."

    def _take_screenshot(self) -> str:
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename  = os.path.join(os.path.expanduser("~"), "Desktop", f"FRIDAY_{timestamp}.png")
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            logger.success(f"Screenshot saved: {filename}")
            return "Screenshot taken and saved to your desktop boss."
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return "Screenshot failed. Try again."

    def _volume(self, up: bool) -> str:
        try:
            # Simulate pressing volume keys 5 times
            key = "volumeup" if up else "volumedown"
            for _ in range(5):
                pyautogui.press(key)
            direction = "up" if up else "down"
            return f"Volume turned {direction} boss."
        except Exception as e:
            logger.error(f"Volume error: {e}")
            return "Couldn't adjust volume."

    def _mute(self) -> str:
        try:
            pyautogui.press("volumemute")
            return "Audio muted boss."
        except Exception as e:
            logger.error(f"Mute error: {e}")
            return "Couldn't mute audio."