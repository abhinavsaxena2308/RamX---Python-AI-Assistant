import sys
import time
import json

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtNetwork import QUdpSocket, QHostAddress

# Audio peak meter via pycaw (Windows WASAPI loopback)
try:
    from comtypes import CLSCTX_ALL, cast, POINTER
    from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
    from pycaw.utils import AudioSession
except Exception as e:
    AudioUtilities = None
    IAudioMeterInformation = None
    AudioSession = None


class AudioPeakMeter:
    def __init__(self):
        """Initialize audio meter to capture ONLY system audio output (not microphone)"""
        self._meter = None
        self._last_ok = 0.0
        self._error_logged = False
        
        if not AudioUtilities or not IAudioMeterInformation:
            print("⚠️ pycaw not available - audio meter disabled")
            return
            
        try:
            # ONLY use system speakers/output - never microphone
            print("🔊 Initializing system audio capture (assistant voice only)...")
            
            # Get the default audio output device
            speakers = AudioUtilities.GetSpeakers()
            
            if not speakers:
                print("❌ No audio output device found")
                self._meter = None
                return
            
            # Access the underlying COM device (IMMDevice)
            # AudioDevice wraps the COM object, we need to access it via ._dev
            if hasattr(speakers, '_dev'):
                device = speakers._dev
            elif hasattr(speakers, '_device'):
                device = speakers._device
            else:
                device = speakers
            
            # Get the audio meter interface from the COM device
            interface = device.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
            self._meter = cast(interface, POINTER(IAudioMeterInformation))
            
            # Test if it works
            test_peak = self._meter.GetPeakValue()
            print(f"✅ Audio meter initialized successfully (current level: {test_peak:.3f})")
            print("   Lips will sync to assistant's voice only (not microphone)")
                
        except Exception as e:
            print(f"❌ Audio meter initialization failed: {e}")
            print("   Avatar will run without lip-sync")
            print("   Note: You may need to run as administrator for system audio capture")
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
        except Exception as e:
            if not self._error_logged:
                print(f"⚠️ Error reading audio peak: {e}")
                self._error_logged = True
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
        self._meter = AudioPeakMeter()  # System audio only - no microphone
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
        
        # Amplify the level for more visible movement (boost quiet sounds)
        # Apply a power curve to make small sounds more visible
        if level > 0.01:  # Ignore very quiet noise
            level = min(1.0, level * 2.5)  # Amplify by 2.5x
            level = level ** 0.7  # Power curve for better response
        
        # Smooth attack/decay for nicer motion
        attack = 0.5  # Faster attack for responsiveness
        decay = 0.2   # Slower decay for smoother animation
        
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
                if expr in {"wink", "smile_open", "neutral", "cool", "happy", "sad", "surprised", "angry", "sleepy", "thinking", "love"}:
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

        # Draw circular face background with enhanced gradient
        gradient = QtGui.QRadialGradient(face_rect.center(), size / 2)
        gradient.setColorAt(0, QColor(55, 55, 70, 250))
        gradient.setColorAt(0.7, QColor(40, 40, 55, 245))
        gradient.setColorAt(1, QColor(25, 25, 40, 240))
        painter.setBrush(QBrush(gradient))
        
        # Outer glow border
        painter.setPen(QPen(QColor(120, 170, 255, 150), 4))
        painter.drawEllipse(face_rect)
        
        # Inner subtle highlight
        painter.setPen(QPen(QColor(80, 120, 200, 80), 2))
        painter.drawEllipse(face_rect.adjusted(3, 3, -3, -3))

        # === CUTE EYES ===
        cx = face_rect.center().x()
        eye_y = face_rect.top() + face_rect.height() * 0.35
        eye_gap = 35
        
        # Larger, rounder eyes for cuteness
        eye_w, eye_h = 32, 32
        left_h = eye_h
        right_h = eye_h
        
        # === EXPRESSION-SPECIFIC EYE RENDERING ===
        
        # Cool expression - draw sunglasses instead of eyes
        if self._expr == "cool":
            # Draw cool sunglasses
            glasses_width = 80
            glasses_height = 28
            glasses_y = eye_y - 2
            
            # Left lens
            left_lens = QtCore.QRectF(cx - eye_gap - eye_w/2 - 8, glasses_y, glasses_width/2 - 5, glasses_height)
            # Right lens
            right_lens = QtCore.QRectF(cx + eye_gap - eye_w/2 - 8, glasses_y, glasses_width/2 - 5, glasses_height)
            
            # Draw dark lenses with gradient
            lens_gradient = QtGui.QLinearGradient(left_lens.topLeft(), left_lens.bottomLeft())
            lens_gradient.setColorAt(0, QColor(20, 20, 30, 220))
            lens_gradient.setColorAt(1, QColor(10, 10, 20, 240))
            
            painter.setBrush(QBrush(lens_gradient))
            painter.setPen(QPen(QColor(40, 40, 50), 3))
            painter.drawRoundedRect(left_lens, 8, 8)
            painter.drawRoundedRect(right_lens, 8, 8)
            
            # Draw bridge connecting the lenses
            bridge_y = glasses_y + glasses_height/2 - 2
            painter.setPen(QPen(QColor(40, 40, 50), 3, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(
                QtCore.QPointF(left_lens.right(), bridge_y),
                QtCore.QPointF(right_lens.left(), bridge_y)
            )
            
            # Add cool reflections on lenses
            painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
            painter.setPen(Qt.NoPen)
            # Left lens reflection
            painter.drawEllipse(
                QtCore.QPointF(left_lens.left() + 8, left_lens.top() + 8),
                6, 4
            )
            # Right lens reflection
            painter.drawEllipse(
                QtCore.QPointF(right_lens.left() + 8, right_lens.top() + 8),
                6, 4
            )
        # Wink expression - make right eye smaller
        elif self._expr == "wink":
            right_h = 4
            right_eye_rect = QtCore.QRectF(cx + eye_gap - eye_w/2, eye_y + eye_h/2 - 2, eye_w, right_h)
        # Surprised expression - make eyes bigger
        elif self._expr == "surprised":
            eye_w, eye_h = 40, 40
            left_eye_rect = QtCore.QRectF(cx - eye_gap - eye_w/2, eye_y - 4, eye_w, eye_h)
            right_eye_rect = QtCore.QRectF(cx + eye_gap - eye_w/2, eye_y - 4, eye_w, eye_h)
        # Sleepy expression - half-closed eyes
        elif self._expr == "sleepy":
            eye_h = 12
            left_eye_rect = QtCore.QRectF(cx - eye_gap - eye_w/2, eye_y + 10, eye_w, eye_h)
            right_eye_rect = QtCore.QRectF(cx + eye_gap - eye_w/2, eye_y + 10, eye_w, eye_h)
        # Angry expression - angled eyes
        elif self._expr == "angry":
            # Will draw custom angry eyes below
            pass
        # Love expression - heart eyes
        elif self._expr == "love":
            # Will draw hearts below
            pass
        else:
            right_eye_rect = QtCore.QRectF(cx + eye_gap - eye_w/2, eye_y, eye_w, right_h)
        
        if self._expr not in {"cool", "angry", "love"}:
            left_eye_rect = QtCore.QRectF(cx - eye_gap - eye_w/2, eye_y, eye_w, left_h)
        
        # Add blush for certain expressions
        if self._expr in {"happy", "smile_open", "love", "wink"}:
            blush_color = QColor(255, 150, 180, 100) if self._expr == "love" else QColor(255, 180, 200, 80)
            painter.setBrush(QBrush(blush_color))
            painter.setPen(Qt.NoPen)
            # Left blush
            painter.drawEllipse(
                QtCore.QPointF(cx - eye_gap - 25, eye_y + 35),
                12, 8
            )
            # Right blush
            painter.drawEllipse(
                QtCore.QPointF(cx + eye_gap + 25, eye_y + 35),
                12, 8
            )
        
        # Draw eye shadows for depth (except for special expressions)
        if self._expr not in {"cool", "love"}:
            shadow_color = QColor(0, 0, 0, 40)
            painter.setBrush(QBrush(shadow_color))
            painter.setPen(Qt.NoPen)
            if self._expr != "wink":
                painter.drawEllipse(left_eye_rect.adjusted(0, 2, 0, 2))
                painter.drawEllipse(right_eye_rect.adjusted(0, 2, 0, 2))
            else:
                painter.drawEllipse(left_eye_rect.adjusted(0, 2, 0, 2))
        
        # Draw eye whites (larger circles) - skip for special expressions
        if self._expr == "love":
            # Draw heart eyes with gradient
            heart_size = 30
            
            # Create heart gradient
            heart_gradient = QtGui.QRadialGradient(cx - eye_gap, eye_y + 15, heart_size * 0.6)
            heart_gradient.setColorAt(0, QColor(255, 120, 150))
            heart_gradient.setColorAt(1, QColor(255, 80, 110))
            
            painter.setBrush(QBrush(heart_gradient))
            painter.setPen(QPen(QColor(220, 60, 90), 2.5))
            
            # Left heart
            left_heart_path = QtGui.QPainterPath()
            left_center = QtCore.QPointF(cx - eye_gap, eye_y + 15)
            left_heart_path.moveTo(left_center.x(), left_center.y() + heart_size * 0.3)
            left_heart_path.cubicTo(
                left_center.x() - heart_size * 0.5, left_center.y() - heart_size * 0.3,
                left_center.x() - heart_size * 0.5, left_center.y() + heart_size * 0.1,
                left_center.x(), left_center.y() + heart_size * 0.5
            )
            left_heart_path.cubicTo(
                left_center.x() + heart_size * 0.5, left_center.y() + heart_size * 0.1,
                left_center.x() + heart_size * 0.5, left_center.y() - heart_size * 0.3,
                left_center.x(), left_center.y() + heart_size * 0.3
            )
            painter.drawPath(left_heart_path)
            
            # Right heart with gradient
            heart_gradient2 = QtGui.QRadialGradient(cx + eye_gap, eye_y + 15, heart_size * 0.6)
            heart_gradient2.setColorAt(0, QColor(255, 120, 150))
            heart_gradient2.setColorAt(1, QColor(255, 80, 110))
            painter.setBrush(QBrush(heart_gradient2))
            
            right_heart_path = QtGui.QPainterPath()
            right_center = QtCore.QPointF(cx + eye_gap, eye_y + 15)
            right_heart_path.moveTo(right_center.x(), right_center.y() + heart_size * 0.3)
            right_heart_path.cubicTo(
                right_center.x() - heart_size * 0.5, right_center.y() - heart_size * 0.3,
                right_center.x() - heart_size * 0.5, right_center.y() + heart_size * 0.1,
                right_center.x(), right_center.y() + heart_size * 0.5
            )
            right_heart_path.cubicTo(
                right_center.x() + heart_size * 0.5, right_center.y() + heart_size * 0.1,
                right_center.x() + heart_size * 0.5, right_center.y() - heart_size * 0.3,
                right_center.x(), right_center.y() + heart_size * 0.3
            )
            painter.drawPath(right_heart_path)
            
        elif self._expr == "angry":
            # Draw angry angled eyes
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.NoPen)
            
            # Angled eye rectangles
            angry_eye_w, angry_eye_h = 32, 28
            left_angry = QtCore.QRectF(cx - eye_gap - angry_eye_w/2, eye_y, angry_eye_w, angry_eye_h)
            right_angry = QtCore.QRectF(cx + eye_gap - angry_eye_w/2, eye_y, angry_eye_w, angry_eye_h)
            
            painter.drawEllipse(left_angry)
            painter.drawEllipse(right_angry)
            
            # Draw angry eyebrows
            painter.setPen(QPen(QColor(200, 50, 50), 4, Qt.SolidLine, Qt.RoundCap))
            # Left eyebrow (angled down towards center)
            painter.drawLine(
                QtCore.QPointF(cx - eye_gap - angry_eye_w/2 - 5, eye_y - 8),
                QtCore.QPointF(cx - eye_gap + angry_eye_w/2 + 5, eye_y - 15)
            )
            # Right eyebrow (angled down towards center)
            painter.drawLine(
                QtCore.QPointF(cx + eye_gap - angry_eye_w/2 - 5, eye_y - 15),
                QtCore.QPointF(cx + eye_gap + angry_eye_w/2 + 5, eye_y - 8)
            )
            
        elif self._expr != "cool":
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(left_eye_rect)
            if self._expr != "wink":
                painter.drawEllipse(right_eye_rect)
            else:
                # Draw wink as a curved line
                painter.setPen(QPen(QColor(255, 255, 255), 3, Qt.SolidLine, Qt.RoundCap))
                painter.drawArc(right_eye_rect, 0, 180 * 16)
        
        # Draw pupils (bigger and cuter) - skip for special expressions
        if self._expr == "surprised":
            # Bigger pupils for surprised look
            pupil_size = 18
            pupil_offset_y = 0
            
            painter.setBrush(QBrush(QColor(30, 30, 40)))
            painter.drawEllipse(
                QtCore.QPointF(left_eye_rect.center().x(), left_eye_rect.center().y() + pupil_offset_y),
                pupil_size/2, pupil_size/2
            )
            painter.drawEllipse(
                QtCore.QPointF(right_eye_rect.center().x(), right_eye_rect.center().y() + pupil_offset_y),
                pupil_size/2, pupil_size/2
            )
            
            # Extra sparkle for surprised
            painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
            painter.drawEllipse(
                QtCore.QPointF(left_eye_rect.center().x() - 5, left_eye_rect.center().y() - 4),
                4, 4
            )
            painter.drawEllipse(
                QtCore.QPointF(right_eye_rect.center().x() - 5, right_eye_rect.center().y() - 4),
                4, 4
            )
            
        elif self._expr == "angry":
            # Small intense pupils
            pupil_size = 12
            painter.setBrush(QBrush(QColor(30, 30, 40)))
            painter.drawEllipse(
                QtCore.QPointF(cx - eye_gap, eye_y + 14),
                pupil_size/2, pupil_size/2
            )
            painter.drawEllipse(
                QtCore.QPointF(cx + eye_gap, eye_y + 14),
                pupil_size/2, pupil_size/2
            )
            
        elif self._expr == "sleepy":
            # Droopy pupils
            pupil_size = 10
            painter.setBrush(QBrush(QColor(30, 30, 40)))
            painter.drawEllipse(
                QtCore.QPointF(left_eye_rect.center().x(), left_eye_rect.center().y() + 2),
                pupil_size/2, pupil_size/2
            )
            painter.drawEllipse(
                QtCore.QPointF(right_eye_rect.center().x(), right_eye_rect.center().y() + 2),
                pupil_size/2, pupil_size/2
            )
            
        elif self._expr not in {"wink", "cool", "love", "thinking"}:
            pupil_size = 14
            pupil_offset_y = 3
            
            # Left pupil
            painter.setBrush(QBrush(QColor(30, 30, 40)))
            painter.drawEllipse(
                QtCore.QPointF(left_eye_rect.center().x(), left_eye_rect.center().y() + pupil_offset_y),
                pupil_size/2, pupil_size/2
            )
            
            # Right pupil
            painter.drawEllipse(
                QtCore.QPointF(right_eye_rect.center().x(), right_eye_rect.center().y() + pupil_offset_y),
                pupil_size/2, pupil_size/2
            )
            
            # Add sparkle/highlight to eyes for cuteness
            sparkle_size = 5
            sparkle_offset_x = -4
            sparkle_offset_y = -3
            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
            painter.drawEllipse(
                QtCore.QPointF(
                    left_eye_rect.center().x() + sparkle_offset_x,
                    left_eye_rect.center().y() + pupil_offset_y + sparkle_offset_y
                ),
                sparkle_size/2, sparkle_size/2
            )
            painter.drawEllipse(
                QtCore.QPointF(
                    right_eye_rect.center().x() + sparkle_offset_x,
                    right_eye_rect.center().y() + pupil_offset_y + sparkle_offset_y
                ),
                sparkle_size/2, sparkle_size/2
            )
            
            # Smaller sparkle
            painter.drawEllipse(
                QtCore.QPointF(
                    left_eye_rect.center().x() + sparkle_offset_x + 6,
                    left_eye_rect.center().y() + pupil_offset_y + sparkle_offset_y + 4
                ),
                2, 2
            )
            painter.drawEllipse(
                QtCore.QPointF(
                    right_eye_rect.center().x() + sparkle_offset_x + 6,
                    right_eye_rect.center().y() + pupil_offset_y + sparkle_offset_y + 4
                ),
                2, 2
            )
        elif self._expr == "wink":
            # Left eye pupil when winking
            pupil_size = 14
            pupil_offset_y = 3
            painter.setBrush(QBrush(QColor(30, 30, 40)))
            painter.drawEllipse(
                QtCore.QPointF(left_eye_rect.center().x(), left_eye_rect.center().y() + pupil_offset_y),
                pupil_size/2, pupil_size/2
            )
            # Sparkle
            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
            painter.drawEllipse(
                QtCore.QPointF(left_eye_rect.center().x() - 4, left_eye_rect.center().y()),
                2.5, 2.5
            )
            
        elif self._expr == "thinking":
            # Eyes looking up and to the side
            pupil_size = 14
            painter.setBrush(QBrush(QColor(30, 30, 40)))
            painter.drawEllipse(
                QtCore.QPointF(left_eye_rect.center().x() + 6, left_eye_rect.center().y() - 6),
                pupil_size/2, pupil_size/2
            )
            painter.drawEllipse(
                QtCore.QPointF(right_eye_rect.center().x() + 6, right_eye_rect.center().y() - 6),
                pupil_size/2, pupil_size/2
            )

        # === CUTE MOUTH ===
        mouth_y_base = face_rect.top() + face_rect.height() * 0.68
        
        if self._expr == "happy" or self._expr == "smile_open":
            # Big happy smile with enhanced gradient
            mouth_width = face_rect.width() * 0.45
            mouth_h = 35
            mouth_x = face_rect.center().x() - mouth_width/2
            mouth_y = mouth_y_base - mouth_h/2
            mouth_rect = QtCore.QRectF(mouth_x, mouth_y, mouth_width, mouth_h)
            
            # Draw shadow for depth
            shadow_rect = mouth_rect.adjusted(0, 1, 0, 1)
            painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(shadow_rect, 18, 18)
            
            # Draw smile with enhanced gradient
            mouth_gradient = QtGui.QLinearGradient(mouth_rect.topLeft(), mouth_rect.bottomLeft())
            mouth_gradient.setColorAt(0, QColor(255, 110, 130))
            mouth_gradient.setColorAt(0.5, QColor(255, 90, 115))
            mouth_gradient.setColorAt(1, QColor(240, 70, 100))
            painter.setBrush(QBrush(mouth_gradient))
            painter.setPen(QPen(QColor(220, 50, 80), 2.5))
            painter.drawRoundedRect(mouth_rect, 18, 18)
            
            # Add teeth/tongue hint
            painter.setBrush(QBrush(QColor(255, 200, 200, 150)))
            painter.setPen(Qt.NoPen)
            tongue_rect = QtCore.QRectF(
                mouth_rect.x() + mouth_rect.width() * 0.3,
                mouth_rect.y() + mouth_rect.height() * 0.6,
                mouth_rect.width() * 0.4,
                mouth_rect.height() * 0.3
            )
            painter.drawRoundedRect(tongue_rect, 8, 8)
        elif self._expr == "sad":
            # Sad downturned eyebrows
            painter.setPen(QPen(QColor(100, 130, 180), 3.5, Qt.SolidLine, Qt.RoundCap))
            # Left eyebrow (angled up on outer side)
            painter.drawLine(
                QtCore.QPointF(cx - eye_gap - 20, eye_y - 18),
                QtCore.QPointF(cx - eye_gap + 20, eye_y - 12)
            )
            # Right eyebrow (angled up on outer side)
            painter.drawLine(
                QtCore.QPointF(cx + eye_gap - 20, eye_y - 12),
                QtCore.QPointF(cx + eye_gap + 20, eye_y - 18)
            )
            
            # Teardrop
            teardrop_path = QtGui.QPainterPath()
            tear_x = cx - eye_gap + 8
            tear_y = eye_y + 25
            teardrop_path.moveTo(tear_x, tear_y)
            teardrop_path.quadTo(tear_x - 4, tear_y + 8, tear_x, tear_y + 12)
            teardrop_path.quadTo(tear_x + 4, tear_y + 8, tear_x, tear_y)
            
            tear_gradient = QtGui.QRadialGradient(tear_x, tear_y + 6, 6)
            tear_gradient.setColorAt(0, QColor(150, 200, 255, 180))
            tear_gradient.setColorAt(1, QColor(100, 180, 255, 120))
            painter.setBrush(QBrush(tear_gradient))
            painter.setPen(QPen(QColor(120, 190, 255, 150), 1.5))
            painter.drawPath(teardrop_path)
            
            # Sad frown - downward curve
            mouth_width = face_rect.width() * 0.35
            mouth_h = 18
            mouth_rect = QtCore.QRectF(
                face_rect.center().x() - mouth_width/2,
                mouth_y_base - 8,
                mouth_width,
                mouth_h
            )
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(90, 130, 180), 3.5, Qt.SolidLine, Qt.RoundCap))
            # Draw downward arc (inverted) - starts at 180 degrees (left), goes -180 degrees (downward)
            painter.drawArc(mouth_rect, 180 * 16, -180 * 16)
            
        elif self._expr == "surprised":
            # Open O mouth with gradient
            mouth_size = 28
            mouth_center = QtCore.QPointF(face_rect.center().x(), mouth_y_base + 5)
            
            # Shadow
            painter.setBrush(QBrush(QColor(0, 0, 0, 40)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(mouth_center.x(), mouth_center.y() + 1, mouth_size/2, mouth_size/2)
            
            # Gradient mouth
            surprised_gradient = QtGui.QRadialGradient(mouth_center, mouth_size/2)
            surprised_gradient.setColorAt(0, QColor(200, 70, 90))
            surprised_gradient.setColorAt(1, QColor(255, 100, 120))
            painter.setBrush(QBrush(surprised_gradient))
            painter.setPen(QPen(QColor(220, 50, 80), 2.5))
            painter.drawEllipse(mouth_center, mouth_size/2, mouth_size/2)
            
        elif self._expr == "angry":
            # Angry gritted teeth
            mouth_width = face_rect.width() * 0.3
            mouth_h = 8
            mouth_rect = QtCore.QRectF(
                face_rect.center().x() - mouth_width/2,
                mouth_y_base,
                mouth_width,
                mouth_h
            )
            painter.setBrush(QBrush(QColor(200, 50, 50)))
            painter.setPen(QPen(QColor(150, 30, 30), 2))
            painter.drawRect(mouth_rect)
            # Draw teeth lines
            painter.setPen(QPen(QColor(150, 30, 30), 1))
            for i in range(1, 4):
                x = mouth_rect.left() + (mouth_rect.width() / 4) * i
                painter.drawLine(
                    QtCore.QPointF(x, mouth_rect.top()),
                    QtCore.QPointF(x, mouth_rect.bottom())
                )
                
        elif self._expr == "sleepy":
            # Small yawn
            mouth_width = face_rect.width() * 0.25
            mouth_h = 15
            mouth_rect = QtCore.QRectF(
                face_rect.center().x() - mouth_width/2,
                mouth_y_base,
                mouth_width,
                mouth_h
            )
            painter.setBrush(QBrush(QColor(255, 90, 110)))
            painter.setPen(QPen(QColor(220, 50, 80), 2))
            painter.drawEllipse(mouth_rect)
            
            # Add "zzz" for sleepy effect with better styling
            painter.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
            # Gradient for zzz
            painter.setPen(QPen(QColor(120, 140, 220, 200), 2))
            painter.drawText(
                QtCore.QPointF(face_rect.right() - 45, face_rect.top() + 35),
                "z"
            )
            painter.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
            painter.setPen(QPen(QColor(140, 160, 240, 180), 2))
            painter.drawText(
                QtCore.QPointF(face_rect.right() - 32, face_rect.top() + 22),
                "z"
            )
            painter.setFont(QtGui.QFont("Arial", 18, QtGui.QFont.Bold))
            painter.setPen(QPen(QColor(160, 180, 255, 160), 2))
            painter.drawText(
                QtCore.QPointF(face_rect.right() - 18, face_rect.top() + 8),
                "z"
            )
            
        elif self._expr == "thinking":
            # Small contemplative mouth
            mouth_width = face_rect.width() * 0.25
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(200, 150, 180), 3, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(
                QtCore.QPointF(face_rect.center().x() - mouth_width/2, mouth_y_base),
                QtCore.QPointF(face_rect.center().x() + mouth_width/2, mouth_y_base)
            )
            
            # Add thought bubble with gradient
            bubble_gradient = QtGui.QRadialGradient(face_rect.right() - 15, face_rect.top() + 5, 12)
            bubble_gradient.setColorAt(0, QColor(220, 220, 240, 180))
            bubble_gradient.setColorAt(1, QColor(180, 180, 220, 140))
            painter.setBrush(QBrush(bubble_gradient))
            painter.setPen(QPen(QColor(150, 150, 200), 2))
            
            # Small dots leading to thought
            painter.drawEllipse(
                QtCore.QPointF(face_rect.right() - 38, face_rect.top() + 28),
                4, 4
            )
            painter.drawEllipse(
                QtCore.QPointF(face_rect.right() - 26, face_rect.top() + 16),
                6, 6
            )
            # Main thought bubble
            painter.drawEllipse(
                QtCore.QPointF(face_rect.right() - 15, face_rect.top() + 5),
                10, 10
            )
            
        elif self._expr == "love":
            # Happy upward curved smile for love expression
            mouth_width = face_rect.width() * 0.42
            mouth_h = 25
            mouth_rect = QtCore.QRectF(
                face_rect.center().x() - mouth_width/2,
                mouth_y_base - 5,
                mouth_width,
                mouth_h
            )
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 100, 150), 4, Qt.SolidLine, Qt.RoundCap))
            # Draw upward arc (happy smile) - starts at 0 degrees (right), goes 180 degrees (upward)
            painter.drawArc(mouth_rect, 0, 180 * 16)
            
        else:
            # Animated mouth based on audio level (lip sync) with gradient
            mouth_width = face_rect.width() * 0.35
            base_height = 6
            max_extra = 28
            mouth_h = base_height + self._level * max_extra
            mouth_x = face_rect.center().x() - mouth_width/2
            mouth_y = mouth_y_base - mouth_h/2
            mouth_rect = QtCore.QRectF(mouth_x, mouth_y, mouth_width, mouth_h)
            
            # Shadow for depth
            if mouth_h > 8:
                painter.setBrush(QBrush(QColor(0, 0, 0, 25)))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(mouth_rect.adjusted(0, 1, 0, 1), 12, 12)
            
            # Cute rounded mouth with gradient
            mouth_grad = QtGui.QLinearGradient(mouth_rect.topLeft(), mouth_rect.bottomLeft())
            mouth_grad.setColorAt(0, QColor(255, 100, 120))
            mouth_grad.setColorAt(1, QColor(255, 80, 100))
            painter.setBrush(QBrush(mouth_grad))
            painter.setPen(QPen(QColor(220, 50, 80), 2))
            painter.drawRoundedRect(mouth_rect, 12, 12)

        # Dynamic outer glow based on expression
        glow_color = QColor(100, 150, 255, 60)
        glow_width = 8
        
        if self._expr == "love":
            glow_color = QColor(255, 100, 150, 80)
            glow_width = 10
        elif self._expr == "angry":
            glow_color = QColor(255, 80, 80, 70)
            glow_width = 9
        elif self._expr == "happy" or self._expr == "smile_open":
            glow_color = QColor(255, 200, 100, 70)
            glow_width = 9
        elif self._expr == "sad":
            glow_color = QColor(100, 120, 180, 50)
            glow_width = 6
        elif self._expr == "sleepy":
            glow_color = QColor(120, 120, 180, 40)
            glow_width = 6
        elif self._expr == "surprised":
            glow_color = QColor(150, 200, 255, 80)
            glow_width = 10
        
        painter.setPen(QPen(glow_color, glow_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(face_rect.adjusted(4, 4, -4, -4))

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
    
    def contextMenuEvent(self, event):
        """Right-click menu"""
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        
        # Add menu options
        info_action = menu.addAction("ℹ️ Syncs to Assistant Voice Only")
        info_action.setEnabled(False)  # Just informational
        menu.addSeparator()
        close_action = menu.addAction("❌ Close Avatar")
        
        action = menu.exec(event.globalPos())
        
        if action == close_action:
            self.close()


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
