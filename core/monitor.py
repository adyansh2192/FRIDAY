import threading
import time
import psutil
from datetime import datetime
from loguru import logger

# Thresholds
BATTERY_WARN    = 20    # warn below 20%
BATTERY_CRITICAL= 10    # critical below 10%
CPU_WARN        = 85    # warn above 85%
RAM_WARN        = 90    # warn above 90%
CHECK_INTERVAL  = 60    # check every 60 seconds

# Track what we've already warned about
_warned = {
    "battery_low":      False,
    "battery_critical": False,
    "battery_charging": False,
    "cpu_high":         False,
    "ram_high":         False,
}

def _speak_alert(message: str):
    """Thread-safe alert speaker."""
    try:
        from voice.speaker import speak
        from ui.window import signals
        signals.friday_replied.emit(f"⚠️ {message}")
        speak(message)
    except Exception as e:
        logger.error(f"Alert speak failed: {e}")

def _check_battery():
    """Check battery level and charging status."""
    try:
        battery = psutil.sensors_battery()
        if not battery:
            return  # Desktop PC — no battery

        pct      = int(battery.percent)
        plugged  = battery.power_plugged

        # Reset warnings when plugged in
        if plugged:
            if _warned["battery_low"] or _warned["battery_critical"]:
                _warned["battery_low"]      = False
                _warned["battery_critical"] = False
                if not _warned["battery_charging"]:
                    _warned["battery_charging"] = True
                    logger.info("Battery now charging — warnings reset.")
            return

        _warned["battery_charging"] = False

        # Critical warning
        if pct <= BATTERY_CRITICAL and not _warned["battery_critical"]:
            _warned["battery_critical"] = True
            _warned["battery_low"]      = True
            _speak_alert(
                f"Boss, battery is critically low at {pct} percent. "
                f"Please plug in immediately."
            )

        # Low warning
        elif pct <= BATTERY_WARN and not _warned["battery_low"]:
            _warned["battery_low"] = True
            _speak_alert(
                f"Boss, battery is at {pct} percent. "
                f"You might want to plug in soon."
            )

    except Exception as e:
        logger.warning(f"Battery check failed: {e}")

def _check_cpu():
    """Warn if CPU is pegged for too long."""
    try:
        cpu = psutil.cpu_percent(interval=2)
        if cpu >= CPU_WARN and not _warned["cpu_high"]:
            _warned["cpu_high"] = True
            _speak_alert(
                f"Boss, CPU usage is at {int(cpu)} percent. "
                f"Something is working your system hard."
            )
        elif cpu < 70:
            _warned["cpu_high"] = False  # reset once it calms down

    except Exception as e:
        logger.warning(f"CPU check failed: {e}")

def _check_ram():
    """Warn if RAM is nearly full."""
    try:
        ram = psutil.virtual_memory().percent
        if ram >= RAM_WARN and not _warned["ram_high"]:
            _warned["ram_high"] = True
            _speak_alert(
                f"Boss, RAM usage is at {int(ram)} percent. "
                f"You might want to close some applications."
            )
        elif ram < 80:
            _warned["ram_high"] = False

    except Exception as e:
        logger.warning(f"RAM check failed: {e}")

def _check_time_reminders():
    """Proactively mention upcoming reminders."""
    try:
        from brain.memory import _load
        memory = _load()
        # Could expand this later with scheduled events
    except Exception:
        pass

def _monitor_loop():
    """Main monitoring loop — runs every CHECK_INTERVAL seconds."""
    logger.info("System monitor started.")

    while True:
        try:
            _check_battery()
            _check_cpu()
            _check_ram()
        except Exception as e:
            logger.error(f"Monitor loop error: {e}")

        time.sleep(CHECK_INTERVAL)

def start_monitor():
    """Start the background monitor thread."""
    thread = threading.Thread(
        target=_monitor_loop,
        daemon=True,
        name="SystemMonitor"
    )
    thread.start()
    logger.success("Proactive system monitor running.")
    return thread