import threading
import pystray
from PIL import Image, ImageDraw
from loguru import logger


def _create_icon_image() -> Image.Image:
    """
    Draws a simple cyan circle icon for the tray.
    You can replace this with any 64x64 .png later.
    """
    size  = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw  = ImageDraw.Draw(image)

    # Outer circle — dark background
    draw.ellipse([2, 2, size - 2, size - 2], fill=(13, 13, 26, 255))

    # Inner circle — cyan
    draw.ellipse([12, 12, size - 12, size - 12], fill=(0, 212, 255, 255))

    # Small dot in center — white
    draw.ellipse([28, 28, size - 28, size - 28], fill=(255, 255, 255, 255))

    return image


def create_tray(app, window):
    """
    Creates and starts the system tray icon.
    Runs in its own thread so it doesn't block FRIDAY.
    """

    def show_window(icon, item):
        """Bring the FRIDAY window back to screen."""
        window.show()
        window.raise_()
        window.activateWindow()
        logger.info("Window restored from tray.")

    def hide_window(icon, item):
        """Hide FRIDAY window to tray."""
        window.hide()
        logger.info("Window minimized to tray.")

    def exit_friday(icon, item):
        """Clean shutdown from tray."""
        logger.info("Exit triggered from tray.")
        icon.stop()
        app.quit()

    # Build the right-click menu
    menu = pystray.Menu(
        pystray.MenuItem("Show FRIDAY",  show_window, default=True),
        pystray.MenuItem("Hide to Tray", hide_window),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit",         exit_friday),
    )

    icon = pystray.Icon(
        name    = "FRIDAY",
        icon    = _create_icon_image(),
        title   = "FRIDAY — Online",   # tooltip on hover
        menu    = menu
    )

    # Run tray in background thread
    tray_thread = threading.Thread(target=icon.run, daemon=True)
    tray_thread.start()
    logger.info("System tray icon started.")

    return icon