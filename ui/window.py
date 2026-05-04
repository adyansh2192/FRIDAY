import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QPropertyAnimation,
    QEasingCurve, QSize
)
from PyQt6.QtGui import QFont, QColor, QPainter, QPen
from datetime import datetime
from loguru import logger


# ── Signals ───────────────────────────────────────────────────────────────────
class FridaySignals(QObject):
    status_changed  = pyqtSignal(str)
    user_spoke      = pyqtSignal(str)
    friday_replied  = pyqtSignal(str)
    show_typing     = pyqtSignal()
    hide_typing     = pyqtSignal()
    skill_used      = pyqtSignal(str)

signals = FridaySignals()


# ── Pulsing wave widget (shown when FRIDAY speaks) ────────────────────────────
class WaveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 24)
        self._phase    = 0
        self._timer    = QTimer()
        self._timer.timeout.connect(self._animate)
        self._active   = False

    def start(self):
        self._active = True
        self._timer.start(80)
        self.show()

    def stop(self):
        self._active = False
        self._timer.stop()
        self.hide()

    def _animate(self):
        self._phase += 1
        self.update()

    def paintEvent(self, event):
        if not self._active:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 212, 255))
        pen.setWidth(2)
        painter.setPen(pen)

        import math
        bars = 5
        bar_w = 6
        gap   = 4
        for i in range(bars):
            x      = i * (bar_w + gap) + 4
            height = int(8 + 7 * math.sin(self._phase * 0.4 + i * 0.8))
            y      = (24 - height) // 2
            painter.drawLine(x, y, x, y + height)


# ── Typing indicator bubble ───────────────────────────────────────────────────
class TypingBubble(QFrame):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        label = QLabel("FRIDAY")
        label.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        label.setStyleSheet("color: #00d4ff;")
        layout.addWidget(label)

        self._dot_label = QLabel("thinking ●")
        self._dot_label.setFont(QFont("Segoe UI", 10))
        self._dot_label.setStyleSheet("color: #888888;")
        layout.addWidget(self._dot_label)
        layout.addStretch()

        self.setStyleSheet("""
            QFrame {
                background: #1a2a3a;
                border-radius: 10px;
                margin: 2px 8px;
            }
        """)

        # Animate the dots
        self._dots   = 0
        self._timer  = QTimer()
        self._timer.timeout.connect(self._animate_dots)
        self._timer.start(500)

    def _animate_dots(self):
        self._dots = (self._dots + 1) % 4
        self._dot_label.setText("thinking" + "●" * self._dots)


# ── Chat bubble ───────────────────────────────────────────────────────────────
class Bubble(QFrame):
    def __init__(self, text: str, is_friday: bool):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)

        # Header row — speaker + timestamp
        header_row = QHBoxLayout()

        speaker = QLabel("FRIDAY" if is_friday else "YOU")
        speaker.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        speaker.setStyleSheet(
            "color: #00d4ff;" if is_friday else "color: #aaaaaa;"
        )
        header_row.addWidget(speaker)
        header_row.addStretch()

        timestamp = QLabel(datetime.now().strftime("%I:%M %p"))
        timestamp.setFont(QFont("Segoe UI", 7))
        timestamp.setStyleSheet("color: #444444;")
        header_row.addWidget(timestamp)
        layout.addLayout(header_row)

        # Wave animation for FRIDAY bubbles
        if is_friday:
            self._wave = WaveWidget()
            layout.addWidget(self._wave)
            self._wave.start()
            # Stop wave after 3 seconds
            QTimer.singleShot(3000, self._wave.stop)

        # Message
        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setFont(QFont("Segoe UI", 10))
        msg.setStyleSheet("color: #e8e8e8;")
        msg.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        layout.addWidget(msg)

        bg = "#0f1e2e" if is_friday else "#0f0f1e"
        border = "#1e3a5a" if is_friday else "#2a2a4a"
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: 12px;
                border: 1px solid {border};
                margin: 3px 8px;
            }}
        """)


# ── Status bar at bottom ──────────────────────────────────────────────────────
class StatusBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: #0a0a15;
                border-radius: 8px;
                border: 1px solid #1e2a3a;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)

        self._label = QLabel("System ready")
        self._label.setFont(QFont("Segoe UI", 8))
        self._label.setStyleSheet("color: #444444;")
        layout.addWidget(self._label)
        layout.addStretch()

        self._version = QLabel("FRIDAY v0.1.0")
        self._version.setFont(QFont("Segoe UI", 8))
        self._version.setStyleSheet("color: #2a3a4a;")
        layout.addWidget(self._version)

    def update_status(self, text: str):
        self._label.setText(text)


# ── Main Window ───────────────────────────────────────────────────────────────
class FridayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._typing_bubble = None
        self._build_window()
        self._connect_signals()

    def _build_window(self):
        self.setWindowTitle("FRIDAY")
        self.setFixedWidth(380)
        self.setMinimumHeight(560)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Main card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #080814;
                border-radius: 18px;
                border: 1px solid #1a2a3a;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(6)
        card_layout.setContentsMargins(0, 0, 0, 10)
        outer.addWidget(card)

        # ── Header ──
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0a0a18,
                    stop:1 #0d1a2a
                );
                border-radius: 18px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        # Logo
        logo = QLabel("◈")
        logo.setFont(QFont("Segoe UI", 18))
        logo.setStyleSheet("color: #00d4ff;")
        header_layout.addWidget(logo)

        # Name + subtitle
        name_col = QVBoxLayout()
        name_col.setSpacing(0)

        name = QLabel("FRIDAY")
        name.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name.setStyleSheet("color: #ffffff;")
        name_col.addWidget(name)

        subtitle = QLabel("Personal AI Assistant")
        subtitle.setFont(QFont("Segoe UI", 8))
        subtitle.setStyleSheet("color: #2a4a6a;")
        name_col.addWidget(subtitle)

        header_layout.addLayout(name_col)
        header_layout.addStretch()

        # Status indicator
        status_col = QVBoxLayout()
        status_col.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.dot = QLabel("●")
        self.dot.setFont(QFont("Segoe UI", 12))
        self.dot.setStyleSheet("color: #444444;")
        self.dot.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_col.addWidget(self.dot)

        self.status_label = QLabel("Sleeping")
        self.status_label.setFont(QFont("Segoe UI", 8))
        self.status_label.setStyleSheet("color: #444444;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_col.addWidget(self.status_label)

        header_layout.addLayout(status_col)
        card_layout.addWidget(header)

        # ── Chat area ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                width: 3px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #1e2a3a;
                border-radius: 2px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0px; }
        """)

        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setSpacing(4)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_widget)
        card_layout.addWidget(self.scroll)

        # ── Status bar ──
        self.status_bar = StatusBar()
        card_layout.addWidget(self.status_bar)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(10, 0, 10, 0)
        btn_row.setSpacing(6)

        self.mute_btn = QPushButton("🎙 Active")
        self.mute_btn.setCheckable(True)
        self.mute_btn.clicked.connect(self._toggle_mute)
        self.mute_btn.setStyleSheet(self._btn_style("#0f1e2e", "#00d4ff"))

        tray_btn = QPushButton("⬇ Tray")
        tray_btn.clicked.connect(self.hide)
        tray_btn.setStyleSheet(self._btn_style("#0f0f1e", "#888888"))

        exit_btn = QPushButton("✕ Exit")
        exit_btn.clicked.connect(self._exit)
        exit_btn.setStyleSheet(self._btn_style("#1e0f0f", "#ff4444"))

        btn_row.addWidget(self.mute_btn)
        btn_row.addWidget(tray_btn)
        btn_row.addWidget(exit_btn)
        card_layout.addLayout(btn_row)

        self._drag_pos = None

    def _btn_style(self, bg: str, color: str) -> str:
        return f"""
            QPushButton {{
                background: {bg};
                color: {color};
                border: 1px solid {color}33;
                border-radius: 8px;
                padding: 6px 10px;
                font-family: 'Segoe UI';
                font-size: 10px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {color}18;
                border: 1px solid {color}88;
            }}
        """

    def _connect_signals(self):
        signals.status_changed.connect(self._update_status)
        signals.user_spoke.connect(lambda t: self._add_bubble(t, False))
        signals.friday_replied.connect(self._on_friday_reply)
        signals.show_typing.connect(self._show_typing)
        signals.hide_typing.connect(self._hide_typing)
        signals.skill_used.connect(self._on_skill_used)

    def _update_status(self, status: str):
        configs = {
            "sleeping":  ("#333333", "#555555", "Sleeping"),
            "listening": ("#00ff88", "#00cc66", "Listening..."),
            "thinking":  ("#ffaa00", "#cc8800", "Thinking..."),
            "speaking":  ("#00d4ff", "#00a0cc", "Speaking"),
        }
        dot_c, text_c, label = configs.get(status, ("#333333", "#555555", status))
        self.dot.setStyleSheet(f"color: {dot_c};")
        self.status_label.setStyleSheet(f"color: {text_c};")
        self.status_label.setText(label)
        self.status_bar.update_status(f"Status: {label}")

    def _show_typing(self):
        """Show 'FRIDAY is thinking' bubble."""
        if self._typing_bubble:
            return
        self._typing_bubble = TypingBubble()
        self.chat_layout.insertWidget(
            self.chat_layout.count() - 1,
            self._typing_bubble
        )
        self._scroll_to_bottom()

    def _hide_typing(self):
        """Remove the typing bubble."""
        if self._typing_bubble:
            self._typing_bubble.setParent(None)
            self._typing_bubble = None

    def _on_friday_reply(self, text: str):
        """Hide typing indicator then show the real reply."""
        self._hide_typing()
        self._add_bubble(text, is_friday=True)

    def _on_skill_used(self, skill_name: str):
        self.status_bar.update_status(f"Using: {skill_name}")

    def _add_bubble(self, text: str, is_friday: bool):
        bubble = Bubble(text, is_friday)
        self.chat_layout.insertWidget(
            self.chat_layout.count() - 1,
            bubble
        )
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        QTimer.singleShot(60, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def _toggle_mute(self, checked: bool):
        if checked:
            self.mute_btn.setText("🔇 Muted")
        else:
            self.mute_btn.setText("🎙 Active")

    def _exit(self):
        from voice.speaker import speak
        speak("Shutting down. Goodbye boss.")
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

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
    app    = QApplication.instance() or QApplication(sys.argv)
    window = FridayWindow()
    screen = app.primaryScreen().availableGeometry()
    window.move(screen.width() - 400, screen.height() - 600)
    window.show()
    return app, window