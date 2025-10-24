import sys
import time
import json
from ctypes import POINTER, cast

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtNetwork import QUdpSocket, QHostAddress

# Audio peak meter via pycaw (Windows WASAPI loopback)
try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
except Exception as e:
    AudioUtilities = None
    IAudioMeterInformation = None


class AudioPeakMeter:
    def __init__(self):
        self._meter = None
        self._last_ok = 0.0
        if AudioUtilities and IAudioMeterInformation:
            try:
                speakers = AudioUtilities.GetSpeakers()
                interface = speakers.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
                self._meter = cast(interface, POINTER(IAudioMeterInformation))
            except Exception:
                self._meter = None

    def get_peak(self) -> float:
        """Return current audio peak [0.0, 1.0]. 0.0 if unavailable."""
        if not self._meter:
            return 0.0
        try:
            peak = float(self._meter.GetPeakValue())
            # Clamp and smooth minimal floor
            if not (0.0 <= peak <= 1.0):
                peak = 0.0
            self._last_ok = peak
            return peak
        except Exception:
            return 0.0


class AvatarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RamX Avatar")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(240, 240)

        self._drag_pos: QtCore.QPoint | None = None
        self._level = 0.0
        self._smoothed = 0.0
        self._meter = AudioPeakMeter()
        self._expr = "neutral"
        self._expr_until = 0.0

        # Update timer (approx 60 FPS)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(16)

        self._udp = QUdpSocket(self)
        self._udp.bind(QHostAddress.LocalHost, 8765)
        self._udp.readyRead.connect(self._on_udp)

    def _on_tick(self):
        # Read audio peak
        level = self._meter.get_peak()
        # Smooth attack/decay for nicer motion
        attack = 0.4
        decay = 0.15
        if level > self._smoothed:
            self._smoothed = self._smoothed * (1 - attack) + level * attack
        else:
            self._smoothed = self._smoothed * (1 - decay) + level * decay
        self._level = max(0.0, min(1.0, self._smoothed))
        if self._expr != "neutral" and time.time() >= self._expr_until:
            self._expr = "neutral"
        self.update()

    def set_expression(self, expr: str, duration: float = 1.2):
        self._expr = expr
        self._expr_until = time.time() + max(0.1, duration)

    def _on_udp(self):
        while self._udp.hasPendingDatagrams():
            datagram = self._udp.receiveDatagram()
            try:
                payload = json.loads(bytes(datagram.data()).decode("utf-8", errors="ignore"))
                expr = str(payload.get("expr", "")).strip().lower()
                dur = float(payload.get("duration", 1.2))
                if expr in {"wink", "smile_open", "neutral"}:
                    self.set_expression(expr, dur)
            except Exception:
                pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)

        # Create a centered square within rect and clip to a circle
        size = min(rect.width(), rect.height())
        face_rect = QtCore.QRectF(
            rect.center().x() - size / 2,
            rect.center().y() - size / 2,
            size,
            size,
        )
        circle_clip = QtGui.QPainterPath()
        circle_clip.addEllipse(face_rect)
        painter.setClipPath(circle_clip)

        # Draw circular face background
        face_color = QColor(30, 30, 35, 230)
        painter.setBrush(QBrush(face_color))
        painter.setPen(QPen(QColor(200, 200, 220, 180), 2))
        painter.drawEllipse(face_rect)

        # Eyes
        eye_w, eye_h = 22, 12
        eye_y = face_rect.top() + face_rect.height() * 0.33
        eye_gap = 44
        cx = face_rect.center().x()
        left_h = eye_h
        right_h = eye_h
        if self._expr == "wink":
            right_h = 2
        left_eye = QtCore.QRectF(cx - eye_gap - eye_w/2, eye_y, eye_w, left_h)
        right_eye = QtCore.QRectF(cx + eye_gap - eye_w/2, eye_y, eye_w, right_h)
        painter.setBrush(QBrush(QColor(240, 240, 255)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(left_eye, 6, 6)
        painter.drawRoundedRect(right_eye, 6, 6)

        pupil_w, pupil_h = 8, 8
        pupil_offset_y = 2
        painter.setBrush(QBrush(QColor(60, 90, 255)))
        painter.drawEllipse(QtCore.QPointF(left_eye.center().x(), left_eye.center().y()+pupil_offset_y), pupil_w/2, pupil_h/2)
        painter.drawEllipse(QtCore.QPointF(right_eye.center().x(), right_eye.center().y()+pupil_offset_y), pupil_w/2, pupil_h/2)

        # Mouth - height based on audio level
        mouth_width = face_rect.width() * 0.5
        base_height = 8
        max_extra = 42
        mouth_h = base_height + self._level * max_extra
        mouth_x = face_rect.center().x() - mouth_width/2
        mouth_y = face_rect.top() + face_rect.height() * 0.62 - mouth_h/2
        mouth_rect = QtCore.QRectF(mouth_x, mouth_y, mouth_width, mouth_h)
        if self._expr == "smile_open":
            mouth_width = face_rect.width() * 0.62
            mouth_h = base_height + max_extra
            mouth_x = face_rect.center().x() - mouth_width/2
            mouth_y = face_rect.top() + face_rect.height() * 0.6 - mouth_h/2
            mouth_rect = QtCore.QRectF(mouth_x, mouth_y, mouth_width, mouth_h)

        painter.setBrush(QBrush(QColor(255, 80, 100)))
        painter.setPen(QPen(QColor(220, 40, 70), 1))
        painter.drawRoundedRect(mouth_rect, 14, 14)

        # Subtle outer glow ring
        glow = QPen(QColor(80, 120, 255, 80), 6)
        painter.setPen(glow)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(face_rect.adjusted(3, 3, -3, -3))

    # Drag window
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self._drag_pos and (event.buttons() & Qt.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self._drag_pos = None


def main():
    app = QApplication(sys.argv)
    w = AvatarWidget()
    # Position bottom-right-ish of the primary screen
    screen = app.primaryScreen().availableGeometry()
    w.move(screen.right() - w.width() - 24, screen.bottom() - w.height() - 24)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
