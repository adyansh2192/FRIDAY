import sys
import math
import random
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QFont, QRadialGradient,
    QPainterPath, QBrush
)
from datetime import datetime
from loguru import logger


# ── Signals ───────────────────────────────────────────────────────────────────
class FridaySignals(QObject):
    status_changed = pyqtSignal(str)
    user_spoke     = pyqtSignal(str)
    friday_replied = pyqtSignal(str)
    show_typing    = pyqtSignal()
    hide_typing    = pyqtSignal()
    skill_used     = pyqtSignal(str)

signals = FridaySignals()

# ── State colour map ──────────────────────────────────────────────────────────
STATE_COLORS = {
    "sleeping":  QColor(50,  50,  50),
    "listening": QColor(0,   255, 136),
    "thinking":  QColor(255, 170, 0),
    "speaking":  QColor(0,   212, 255),
    "music":     QColor(255, 68,  68),
    "searching": QColor(167, 139, 250),
}

STATE_LABELS = {
    "sleeping":  "SLEEPING",
    "listening": "LISTENING",
    "thinking":  "THINKING",
    "speaking":  "SPEAKING",
    "music":     "MUSIC",
    "searching": "SEARCHING",
}

STATE_INTENSITY = {
    "sleeping":  0.08,
    "listening": 0.55,
    "thinking":  0.35,
    "speaking":  0.75,
    "music":     0.90,
    "searching": 0.45,
}

STATE_SPEED = {
    "sleeping":  0.3,
    "listening": 1.8,
    "thinking":  2.5,
    "speaking":  2.0,
    "music":     3.0,
    "searching": 4.0,
}


# ── Circular waveform widget ──────────────────────────────────────────────────
class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 300)

        self._state      = "sleeping"
        self._phase      = 0.0
        self._t          = 0.0
        self._cur_r      = 50.0
        self._cur_g      = 50.0
        self._cur_b      = 50.0
        self._bars       = 80
        self._r_inner    = 85
        self._r_outer    = 130

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps

    def set_state(self, state: str):
        self._state = state

    def _tick(self):
        st = self._state
        speed     = STATE_SPEED.get(st, 1.0)
        self._phase += speed * 0.016
        self._t     += 0.016

        # Lerp colour toward target
        target = STATE_COLORS.get(st, QColor(50, 50, 50))
        self._cur_r += (target.red()   - self._cur_r) * 0.06
        self._cur_g += (target.green() - self._cur_g) * 0.06
        self._cur_b += (target.blue()  - self._cur_b) * 0.06

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        W  = self.width()
        H  = self.height()
        CX = W / 2
        CY = H / 2

        r  = int(self._cur_r)
        g  = int(self._cur_g)
        b  = int(self._cur_b)

        color       = QColor(r, g, b)
        st          = self._state
        intensity   = STATE_INTENSITY.get(st, 0.1)
        state_label = STATE_LABELS.get(st, "")

        # Background
        painter.fillRect(0, 0, W, H, QColor(8, 8, 20))

        # Outer glow
        glow = QRadialGradient(CX, CY, self._r_outer + 20)
        glow.setColorAt(0,   QColor(r, g, b, 0))
        glow.setColorAt(0.6, QColor(r, g, b, 12))
        glow.setColorAt(1,   QColor(r, g, b, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            int(CX - self._r_outer - 20),
            int(CY - self._r_outer - 20),
            int((self._r_outer + 20) * 2),
            int((self._r_outer + 20) * 2)
        )

        # Waveform bars
        for i in range(self._bars):
            angle   = (i / self._bars) * math.pi * 2 - math.pi / 2
            wave1   = math.sin(self._phase + i * 0.18) * 0.5 + 0.5
            wave2   = math.sin(self._phase * 1.3 + i * 0.35) * 0.3 + 0.3
            wave3   = math.sin(self._phase * 0.7 + i * 0.08) * 0.2 + 0.2
            combined = wave1 * 0.5 + wave2 * 0.3 + wave3 * 0.2
            bar_len  = intensity * combined * (self._r_outer - self._r_inner)
            alpha    = int((0.3 + combined * 0.7) * 255)

            x1 = CX + math.cos(angle) * self._r_inner
            y1 = CY + math.sin(angle) * self._r_inner
            x2 = CX + math.cos(angle) * (self._r_inner + bar_len)
            y2 = CY + math.sin(angle) * (self._r_inner + bar_len)

            pen = QPen(QColor(r, g, b, alpha))
            pen.setWidthF(2.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(x1, y1),
                QPointF(x2, y2)
            )

        # Inner ring
        pen = QPen(QColor(r, g, b, 60))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            QPointF(CX, CY),
            float(self._r_inner - 2),
            float(self._r_inner - 2)
        )

        # Tick marks
        for i in range(32):
            angle    = (i / 32) * math.pi * 2
            tick_len = 6 if i % 8 == 0 else 3
            r_start  = self._r_outer + 6
            pen = QPen(QColor(r, g, b, 70))
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(
                    CX + math.cos(angle) * r_start,
                    CY + math.sin(angle) * r_start
                ),
                QPointF(
                    CX + math.cos(angle) * (r_start + tick_len),
                    CY + math.sin(angle) * (r_start + tick_len)
                )
            )

        # Rotating accent arc
        arc_angle  = self._phase * 0.4
        arc_rect_x = int(CX - self._r_outer - 10)
        arc_rect_y = int(CY - self._r_outer - 10)
        arc_size   = int((self._r_outer + 10) * 2)

        pen = QPen(QColor(r, g, b, 130))
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawArc(
            arc_rect_x, arc_rect_y, arc_size, arc_size,
            int(-arc_angle * 180 / math.pi * 16),
            int(72 * 16)
        )

        pen = QPen(QColor(r, g, b, 70))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.drawArc(
            arc_rect_x, arc_rect_y, arc_size, arc_size,
            int((-arc_angle + math.pi) * 180 / math.pi * 16),
            int(36 * 16)
        )

        # Dark centre fill
        painter.setBrush(QBrush(QColor(8, 8, 20)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            QPointF(CX, CY),
            float(self._r_inner - 4),
            float(self._r_inner - 4)
        )

        # Centre pulse dot
        pulse = 0.6 + math.sin(self._t * 2) * 0.4 * intensity
        dot_r = 6 * pulse
        painter.setBrush(QBrush(QColor(r, g, b, 230)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            QPointF(CX, CY),
            dot_r, dot_r
        )

        # FRIDAY label
        painter.setPen(QPen(QColor(r, g, b, 230)))
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            int(CX - 50), int(CY - 14),
            100, 20,
            Qt.AlignmentFlag.AlignCenter,
            "F · R · I · D · A · Y"
        )

        # State label
        painter.setPen(QPen(QColor(r, g, b, 120)))
        font2 = QFont("Segoe UI", 7)
        painter.setFont(font2)
        painter.drawText(
            int(CX - 50), int(CY + 6),
            100, 16,
            Qt.AlignmentFlag.AlignCenter,
            state_label
        )


# ── Chat bubble ───────────────────────────────────────────────────────────────
class Bubble(QFrame):
    def __init__(self, text: str, is_friday: bool):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(3)

        header = QHBoxLayout()
        speaker = QLabel("FRIDAY" if is_friday else "YOU")
        speaker.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        speaker.setStyleSheet(
            "color: #00d4ff;" if is_friday else "color: #aaaaaa;"
        )
        header.addWidget(speaker)
        header.addStretch()
        ts = QLabel(datetime.now().strftime("%I:%M %p"))
        ts.setFont(QFont("Segoe UI", 7))
        ts.setStyleSheet("color: #333;")
        header.addWidget(ts)
        layout.addLayout(header)

        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setFont(QFont("Segoe UI", 10))
        msg.setStyleSheet("color: #e8e8e8;")
        msg.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        layout.addWidget(msg)

        bg     = "#0f1e2e" if is_friday else "#0f0f1e"
        border = "#1e3a5a" if is_friday else "#2a2a4a"
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: 10px;
                border: 1px solid {border};
                margin: 2px 6px;
            }}
        """)


# ── Main Window ───────────────────────────────────────────────────────────────
class FridayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._typing_bubble = None
        self._build_window()
        self._connect_signals()

    def _build_window(self):
        self.setWindowTitle("FRIDAY")
        self.setFixedWidth(340)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

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
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(0, 0, 0, 12)
        outer.addWidget(card)

        # ── Orb ──
        orb_container = QFrame()
        orb_container.setStyleSheet("background: transparent;")
        orb_layout = QVBoxLayout(orb_container)
        orb_layout.setContentsMargins(20, 16, 20, 0)
        orb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.orb = OrbWidget()
        orb_layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(orb_container)

        # ── Chat area ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(200)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                width: 3px; background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #1e2a3a; border-radius: 2px;
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

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #1a2a3a; margin: 8px 12px;")
        card_layout.addWidget(div)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(10, 0, 10, 0)
        btn_row.setSpacing(6)

        self.mute_btn = QPushButton("🎙 Active")
        self.mute_btn.setCheckable(True)
        self.mute_btn.clicked.connect(self._toggle_mute)
        self.mute_btn.setStyleSheet(self._btn("#0f1e2e", "#00d4ff"))

        tray_btn = QPushButton("⬇ Tray")
        tray_btn.clicked.connect(self.hide)
        tray_btn.setStyleSheet(self._btn("#0f0f1e", "#888"))

        exit_btn = QPushButton("✕ Exit")
        exit_btn.clicked.connect(self._exit)
        exit_btn.setStyleSheet(self._btn("#1e0f0f", "#ff4444"))

        btn_row.addWidget(self.mute_btn)
        btn_row.addWidget(tray_btn)
        btn_row.addWidget(exit_btn)
        card_layout.addLayout(btn_row)

        self._drag_pos = None

    def _btn(self, bg, color):
        return f"""
            QPushButton {{
                background: {bg};
                color: {color};
                border: 1px solid {color}44;
                border-radius: 8px;
                padding: 5px 10px;
                font-family: 'Segoe UI';
                font-size: 10px;
            }}
            QPushButton:hover {{ background: {color}22; }}
        """

    def _connect_signals(self):
        signals.status_changed.connect(self._on_status)
        signals.user_spoke.connect(lambda t: self._add_bubble(t, False))
        signals.friday_replied.connect(self._on_reply)
        signals.show_typing.connect(self._show_typing)
        signals.hide_typing.connect(self._hide_typing)

    def _on_status(self, status: str):
        self.orb.set_state(status)

    def _show_typing(self):
        if not self._typing_bubble:
            self._typing_bubble = Bubble("thinking...", True)
            self.chat_layout.insertWidget(
                self.chat_layout.count() - 1,
                self._typing_bubble
            )
            self._scroll_bottom()

    def _hide_typing(self):
        if self._typing_bubble:
            self._typing_bubble.setParent(None)
            self._typing_bubble = None

    def _on_reply(self, text: str):
        self._hide_typing()
        self._add_bubble(text, True)

    def _add_bubble(self, text: str, is_friday: bool):
        bubble = Bubble(text, is_friday)
        self.chat_layout.insertWidget(
            self.chat_layout.count() - 1,
            bubble
        )
        self._scroll_bottom()

    def _scroll_bottom(self):
        QTimer.singleShot(60, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def _toggle_mute(self, checked: bool):
        self.mute_btn.setText("🔇 Muted" if checked else "🎙 Active")

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
    window.move(screen.width() - 360, screen.height() - 620)
    window.show()
    return app, window