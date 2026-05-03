import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor
from loguru import logger


# ── Signals (thread-safe bridge between FRIDAY logic and UI) ──────────────────
class FridaySignals(QObject):
    status_changed  = pyqtSignal(str)   # "sleeping" | "listening" | "thinking" | "speaking"
    user_spoke      = pyqtSignal(str)   # what you said
    friday_replied  = pyqtSignal(str)   # what FRIDAY said


signals = FridaySignals()


# ── Chat bubble ───────────────────────────────────────────────────────────────
class Bubble(QFrame):
    def __init__(self, text: str, is_friday: bool):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)

        # Speaker label
        speaker = QLabel("FRIDAY" if is_friday else "YOU")
        speaker.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        speaker.setStyleSheet(
            "color: #00d4ff;" if is_friday else "color: #aaaaaa;"
        )
        layout.addWidget(speaker)

        # Message text
        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setFont(QFont("Segoe UI", 10))
        msg.setStyleSheet("color: #ffffff;")
        layout.addWidget(msg)

        # Bubble background
        bg = "#1a2a3a" if is_friday else "#1a1a2e"
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: 10px;
                margin: 2px 8px;
            }}
        """)


# ── Main Window ───────────────────────────────────────────────────────────────
class FridayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._build_window()
        self._connect_signals()

    def _build_window(self):
        # Window properties
        self.setWindowTitle("FRIDAY")
        self.setFixedWidth(360)
        self.setMinimumHeight(500)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |   # always on top
            Qt.WindowType.FramelessWindowHint       # no title bar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Outer layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Main card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #0d0d1a;
                border-radius: 16px;
                border: 1px solid #1e2a3a;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(0, 0, 0, 12)
        outer.addWidget(card)

        # ── Header ──
        header = QFrame()
        header.setStyleSheet("background: #0a0a15; border-radius: 16px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 14, 10)

        # Logo + name
        logo = QLabel("◈")
        logo.setFont(QFont("Segoe UI", 16))
        logo.setStyleSheet("color: #00d4ff;")
        header_layout.addWidget(logo)

        name = QLabel("FRIDAY")
        name.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(name)
        header_layout.addStretch()

        # Status dot + label
        self.dot = QLabel("●")
        self.dot.setFont(QFont("Segoe UI", 10))
        self.dot.setStyleSheet("color: #444444;")
        header_layout.addWidget(self.dot)

        self.status_label = QLabel("Sleeping")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(self.status_label)

        card_layout.addWidget(header)

        # ── Chat area ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                width: 4px; background: #0d0d1a;
            }
            QScrollBar::handle:vertical {
                background: #1e2a3a; border-radius: 2px;
            }
        """)

        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setSpacing(6)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_widget)
        card_layout.addWidget(self.scroll)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(12, 0, 12, 0)
        btn_row.setSpacing(8)

        self.mute_btn = QPushButton("🎙 Active")
        self.mute_btn.setCheckable(True)
        self.mute_btn.clicked.connect(self._toggle_mute)
        self.mute_btn.setStyleSheet(self._btn_style("#1a2a3a", "#00d4ff"))

        exit_btn = QPushButton("✕ Exit")
        exit_btn.clicked.connect(self._exit)
        exit_btn.setStyleSheet(self._btn_style("#2a1a1a", "#ff4444"))

        btn_row.addWidget(self.mute_btn)
        btn_row.addWidget(exit_btn)
        card_layout.addLayout(btn_row)

        # Allow dragging the window
        self._drag_pos = None

    def _btn_style(self, bg: str, color: str) -> str:
        return f"""
            QPushButton {{
                background: {bg};
                color: {color};
                border: 1px solid {color}44;
                border-radius: 8px;
                padding: 6px 12px;
                font-family: 'Segoe UI';
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {color}22;
            }}
        """

    def _connect_signals(self):
        signals.status_changed.connect(self._update_status)
        signals.user_spoke.connect(lambda t: self._add_bubble(t, is_friday=False))
        signals.friday_replied.connect(lambda t: self._add_bubble(t, is_friday=True))

    def _update_status(self, status: str):
        colors = {
            "sleeping":  ("#444444", "#666666"),
            "listening": ("#00ff88", "#00cc66"),
            "thinking":  ("#ffaa00", "#cc8800"),
            "speaking":  ("#00d4ff", "#0099cc"),
        }
        dot_color, text_color = colors.get(status, ("#444444", "#666666"))
        self.dot.setStyleSheet(f"color: {dot_color};")
        self.status_label.setStyleSheet(f"color: {text_color};")
        self.status_label.setText(status.capitalize())

    def _add_bubble(self, text: str, is_friday: bool):
        bubble = Bubble(text, is_friday)
        # Insert before the stretch at the end
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        # Auto scroll to bottom
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def _toggle_mute(self, checked: bool):
        if checked:
            self.mute_btn.setText("🔇 Muted")
            logger.info("FRIDAY muted by user")
        else:
            self.mute_btn.setText("🎙 Active")
            logger.info("FRIDAY unmuted by user")

    def _exit(self):
        from voice.speaker import speak
        speak("Shutting down. Goodbye boss.")
        QApplication.quit()

    # Allow dragging the frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ── App launcher ──────────────────────────────────────────────────────────────
def launch_ui():
    """Call this to start the Qt app. Returns the QApplication."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = FridayWindow()

    # Position bottom-right corner of screen
    screen = app.primaryScreen().availableGeometry()
    window.move(screen.width() - 380, screen.height() - 560)
    window.show()

    return app, window