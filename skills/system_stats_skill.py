import psutil
import platform
import subprocess
import os
from skills.base import BaseSkill
from loguru import logger

class SystemStatsSkill(BaseSkill):

    TRIGGERS = [
        "system stats", "pc stats", "how's the system",
        "cpu usage", "ram usage", "memory usage",
        "battery level", "battery status", "how's my battery",
        "system status", "how is my pc", "check system",
        "pc specification", "pc specs", "system specs",
        "what are my specs", "my specs", "computer specs",
        "how much ram", "storage space", "disk space",
        "processor", "graphics card", "gpu", "check my pc",
        "what processor", "what gpu", "system information",
        "system info", "pc info", "hardware info",
        "battery percentage", "battery charge",
        "what's my battery", "check battery"
    ]

    def can_handle(self, user_input: str) -> bool:
        return any(t in user_input.lower() for t in self.TRIGGERS)

    def execute(self, user_input: str) -> str:
        text = user_input.lower()

        if any(w in text for w in ["battery", "charge", "plugged"]):
            return self._battery_status()

        if any(w in text for w in ["cpu", "processor", "cores"]):
            return self._cpu_status()

        if any(w in text for w in ["ram", "memory"]):
            return self._ram_status()

        if any(w in text for w in ["storage", "disk", "ssd", "space"]):
            return self._storage_status()

        if any(w in text for w in ["gpu", "graphics"]):
            return self._gpu_status()

        if any(w in text for w in [
            "spec", "specs", "specification", "information",
            "info", "hardware", "check my pc", "pc info"
        ]):
            return self._full_specs()

        return self._full_report()

    # ── Battery ───────────────────────────────────────────────────────────────

    def _battery_status(self) -> str:
        try:
            b = psutil.sensors_battery()
            if not b:
                return "This is a desktop PC boss — no battery."

            pct     = int(b.percent)
            plugged = b.power_plugged

            if plugged:
                status = "plugged in and charging" if pct < 100 else "fully charged and plugged in"
            else:
                status = "running on battery"

            # Time remaining
            if not plugged and b.secsleft > 0:
                mins = int(b.secsleft / 60)
                hrs  = mins // 60
                rem  = mins % 60
                if hrs > 0:
                    time_str = f", about {hrs} hour{'s' if hrs > 1 else ''} {rem} minutes remaining"
                else:
                    time_str = f", about {rem} minutes remaining"
            else:
                time_str = ""

            return f"Battery is at {pct} percent, {status}{time_str} boss."

        except Exception as e:
            logger.error(f"Battery read failed: {e}")
            return "Couldn't read battery status boss."

    # ── CPU ───────────────────────────────────────────────────────────────────

    def _cpu_status(self) -> str:
        try:
            usage = psutil.cpu_percent(interval=1)
            cores = psutil.cpu_count(logical=False)
            threads = psutil.cpu_count(logical=True)
            freq  = psutil.cpu_freq()
            name  = platform.processor() or "Unknown processor"

            # Shorten processor name
            if "Intel" in name:
                parts = name.split()
                try:
                    idx  = parts.index("CPU")
                    name = " ".join(parts[:idx])
                except ValueError:
                    name = " ".join(parts[:4])
            elif "AMD" in name:
                name = " ".join(name.split()[:4])

            freq_str = f" at {freq.current:.0f} MHz" if freq else ""
            return (
                f"Running {name}{freq_str}. "
                f"{cores} physical cores, {threads} threads. "
                f"Currently at {usage} percent usage boss."
            )
        except Exception as e:
            logger.error(f"CPU read failed: {e}")
            return "Couldn't read CPU info boss."

    # ── RAM ───────────────────────────────────────────────────────────────────

    def _ram_status(self) -> str:
        try:
            ram   = psutil.virtual_memory()
            used  = round(ram.used  / (1024**3), 1)
            total = round(ram.total / (1024**3), 1)
            avail = round(ram.available / (1024**3), 1)
            pct   = ram.percent
            return (
                f"RAM is {total}GB total. "
                f"Currently using {used}GB at {pct} percent. "
                f"{avail}GB available boss."
            )
        except Exception as e:
            logger.error(f"RAM read failed: {e}")
            return "Couldn't read RAM info boss."

    # ── Storage ───────────────────────────────────────────────────────────────

    def _storage_status(self) -> str:
        try:
            lines = []
            for part in psutil.disk_partitions():
                if "cdrom" in part.opts or part.fstype == "":
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    total = round(usage.total / (1024**3), 1)
                    used  = round(usage.used  / (1024**3), 1)
                    free  = round(usage.free  / (1024**3), 1)
                    lines.append(
                        f"Drive {part.device.replace(':\\\\','')} — "
                        f"{total}GB total, {used}GB used, {free}GB free"
                    )
                except PermissionError:
                    continue

            if not lines:
                return "Couldn't read storage info boss."

            return ". ".join(lines) + " boss."

        except Exception as e:
            logger.error(f"Storage read failed: {e}")
            return "Couldn't read storage info boss."

    # ── GPU ───────────────────────────────────────────────────────────────────

    def _gpu_status(self) -> str:
        try:
            # Windows — use WMIC to get real GPU name
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController",
                 "get", "name", "/value"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("Name="):
                        gpu = line.split("=", 1)[1].strip()
                        if gpu:
                            return f"Your graphics card is {gpu} boss."

            return "Couldn't detect GPU info boss."

        except Exception as e:
            logger.error(f"GPU read failed: {e}")
            return "Couldn't read GPU info boss."

    # ── Full specs ────────────────────────────────────────────────────────────

    def _full_specs(self) -> str:
        """Complete hardware spec readout — the JARVIS-style report."""
        try:
            parts = []

            # OS
            os_name = f"{platform.system()} {platform.release()}"
            parts.append(f"Running {os_name}")

            # CPU
            cpu_name  = platform.processor() or "Unknown CPU"
            cpu_cores = psutil.cpu_count(logical=False)
            cpu_threads = psutil.cpu_count(logical=True)
            if "Intel" in cpu_name or "AMD" in cpu_name:
                cpu_short = " ".join(cpu_name.split()[:5])
            else:
                cpu_short = cpu_name[:40]
            parts.append(f"{cpu_short} with {cpu_cores} cores and {cpu_threads} threads")

            # RAM
            ram_total = round(psutil.virtual_memory().total / (1024**3), 1)
            parts.append(f"{ram_total}GB RAM")

            # Storage
            for part in psutil.disk_partitions():
                if "cdrom" in part.opts or part.fstype == "":
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    total = round(usage.total / (1024**3), 1)
                    parts.append(f"{total}GB on drive {part.device.replace(':\\\\','')}")
                except PermissionError:
                    continue

            # GPU
            try:
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController",
                     "get", "name", "/value"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if line.startswith("Name="):
                        gpu = line.split("=", 1)[1].strip()
                        if gpu:
                            parts.append(f"{gpu} graphics")
                            break
            except Exception:
                pass

            return "Here are your specs boss. " + ". ".join(parts) + "."

        except Exception as e:
            logger.error(f"Full specs failed: {e}")
            return "Couldn't pull full specs boss."

    # ── Live report ───────────────────────────────────────────────────────────

    def _full_report(self) -> str:
        """Live usage snapshot."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            bat = psutil.sensors_battery()

            report = f"CPU at {cpu} percent, RAM at {ram.percent} percent. "

            if bat:
                plugged = "plugged in" if bat.power_plugged else "on battery"
                report += f"Battery at {int(bat.percent)} percent and {plugged}. "

            if cpu < 50 and ram.percent < 70:
                report += "Everything looks healthy boss."
            elif cpu > 80 or ram.percent > 85:
                report += "System is under some load boss."
            else:
                report += "System is running normally boss."

            return report

        except Exception as e:
            logger.error(f"System report failed: {e}")
            return "Couldn't pull system stats right now boss."