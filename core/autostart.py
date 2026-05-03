import os
import sys
import winreg
from loguru import logger

APP_NAME  = "FRIDAY"
# Gets the full path to whichever python and main.py you're running
PYTHON    = sys.executable
SCRIPT    = os.path.abspath("main.py")
LAUNCH_CMD = f'"{PYTHON}" "{SCRIPT}"'

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def enable_autostart():
    """Add FRIDAY to Windows startup registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, LAUNCH_CMD)
        winreg.CloseKey(key)
        logger.success("FRIDAY added to startup. It will launch on next boot.")
        return True
    except Exception as e:
        logger.error(f"Autostart enable failed: {e}")
        return False

def disable_autostart():
    """Remove FRIDAY from Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        logger.success("FRIDAY removed from startup.")
        return True
    except FileNotFoundError:
        logger.info("FRIDAY wasn't in startup anyway.")
        return True
    except Exception as e:
        logger.error(f"Autostart disable failed: {e}")
        return False

def is_autostart_enabled() -> bool:
    """Check if FRIDAY is currently set to auto-start."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False