import sys
import time
import json
import logging
from ctypes import POINTER, cast

logging.basicConfig(level=logging.INFO)

# Handle PySide6 imports with proper error handling
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QPainter, QColor, QPen, QBrush
    from PySide6.QtWidgets import QApplication, QWidget
    from PySide6.QtNetwork import QUdpSocket, QHostAddress
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QtCore = None
    QtGui = None
    QtWidgets = None
    Qt = None
    QTimer = None
    QPainter = None
    QColor = None
    QPen = None
    QBrush = None
    QApplication = None
    QWidget = None
    QUdpSocket = None
    QHostAddress = None

# Handle pycaw imports with proper error handling
try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False
    CLSCTX_ALL = None
    AudioUtilities = None
    IAudioMeterInformation = None


class AudioPeakMeter:
    def __init__(self):
        self._meter = None
        self._last_ok = 0.0
        if PYCAW_AVAILABLE and AudioUtilities and IAudioMeterInformation:
            try:
                # Get all audio devices and find the default output
                devices = AudioUtilities.GetAllDevices()
                default_device = None
                
                # Find default playback device (output device)
                for device in devices:
                    try:
                        # Check if it's an output device (ID starts with {0.0.0) and is Active
                        if (hasattr(device, 'id') and device.id and device.id.startswith('{0.0.0') and 
                            str(getattr(device, 'state', '')) == 'AudioDeviceState.Active'):
                            default_device = device
                            logging.info(f"Found active output device: {getattr(device, 'FriendlyName', 'Unknown')}")
                            break
                    except Exception as e:
                        logging.debug(f"Error checking device: {e}")
                        continue
                
                # Try the default approach first - get the audio meter interface
                if default_device and CLSCTX_ALL is not None:
                    try:
                        # Check if default_device has _dev attribute with Activate method
                        if hasattr(default_device, '_dev') and hasattr(default_device._dev, 'Activate'):
                            interface = default_device._dev.Activate(
                                IAudioMeterInformation._iid_, CLSCTX_ALL, None
                            )
                            self._meter = cast(interface, POINTER(IAudioMeterInformation))
                            logging.info(f"Audio meter initialized: {getattr(default_device, 'FriendlyName', 'Unknown')}")
                            return
                    except Exception as e:
                        logging.debug(f"Failed to activate default device: {e}")
                        pass
                
                # Fallback: try GetSpeakers
                if AudioUtilities:
                    try:
                        speakers = AudioUtilities.GetSpeakers()
                        # Check if speakers has Activate method before calling it
                        if speakers and hasattr(speakers, '_dev') and hasattr(speakers._dev, 'Activate') and CLSCTX_ALL is not None:
                            interface = speakers._dev.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
                            self._meter = cast(interface, POINTER(IAudioMeterInformation))
                            logging.info("Audio meter initialized (fallback method)")
                            return
                    except Exception as e:
                        logging.debug(f"Failed to activate speakers device: {e}")
                        pass
                
                logging.warning("No audio device found")
                self._meter = None
                    
            except Exception as e:
                logging.error(f"Failed to initialize audio meter: {e}")
                import traceback
                traceback.print_exc()
                self._meter = None
        else:
            logging.warning("pycaw not available - lip-sync disabled")

    def get_peak(self) -> float:
        """Return current audio peak [0.0, 1.0]. 0.0 if unavailable."""
        if not self._meter or not PYCAW_AVAILABLE:
            return 0.0
        try:
            # Check if the meter has the GetPeakValue method
            if self._meter and hasattr(self._meter, 'GetPeakValue'):
                peak = float(self._meter.GetPeakValue())  # type: ignore
                # Clamp and smooth minimal floor
                if not (0.0 <= peak <= 1.0):
                    peak = 0.0
                self._last_ok = peak
                # Debug: log when audio is detected
                if peak > 0.1:
                    logging.debug(f"Audio peak detected: {peak:.3f}")
                return peak
            else:
                return 0.0
        except Exception as e:
            logging.debug(f"Error getting peak: {e}")
            return 0.0

    def get_speech_intensity(self) -> float:
        """Get scaled audio intensity for speech-like animation (0.0-1.0)."""
        if not self._meter or not PYCAW_AVAILABLE:
            return 0.0
        try:
            peak = self.get_peak()
            # Lower threshold for better sensitivity
            if peak < 0.02:
                return 0.0
            # More aggressive scaling for visible speech animation
            return min(1.0, peak * 2.5)
        except Exception:
            return 0.0


class AvatarWidget(QWidget):  # type: ignore
    def __init__(self):
        if not PYSIDE_AVAILABLE or not QWidget:
            raise RuntimeError("PySide6 is not available")
            
        super().__init__()
        self.setWindowTitle("RamX Avatar")
        
        # Set window flags with proper error handling
        if Qt:
            try:
                # Try to use Qt window flags directly
                self.setWindowFlags(
                    Qt.WindowType.WindowStaysOnTopHint | 
                    Qt.WindowType.FramelessWindowHint | 
                    Qt.WindowType.Tool
                )
            except:
                # Fallback to integer values
                window_flags = 0x00000001 | 0x00000800 | 0x00000040  # WindowStaysOnTopHint | FramelessWindowHint | Tool
                # Convert to proper Qt type
                try:
                    from PySide6.QtCore import Qt as QtCoreQt
                    self.setWindowFlags(
                        QtCoreQt.WindowType.WindowStaysOnTopHint | 
                        QtCoreQt.WindowType.FramelessWindowHint | 
                        QtCoreQt.WindowType.Tool
                    )
                except:
                    pass  # If all else fails, continue without special window flags
        
        # Set attribute with proper error handling
        if Qt:
            try:
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            except:
                try:
                    from PySide6.QtCore import Qt as QtCoreQt
                    self.setAttribute(QtCoreQt.WidgetAttribute.WA_TranslucentBackground, True)
                except:
                    pass  # If all else fails, continue without translucent background
                    
        self.resize(240, 240)

        self._drag_pos = None
        self._level = 0.0
        self._smoothed = 0.0
        self._lip_sync = 0.0
        self._meter = AudioPeakMeter()
        self._expr = "neutral"
        self._expr_until = 0.0
        
        # Human-like features
        self._cursor_x = 0.5  # Normalized cursor position (0.0 to 1.0)
        self._cursor_y = 0.5
        self._blink_state = 0  # 0=normal, 1=closing, 2=closed, 3=opening
        self._blink_timer = 0
        self._float_time = 0.0  # For subtle breathing animation
        self.setMouseTracking(True)  # Enable mouse tracking for eye follow

        # Update timer (approx 60 FPS)
        self._timer = QTimer(self) if QTimer else None
        if self._timer:
            self._timer.timeout.connect(self._on_tick)
            self._timer.start(16)

        self._udp = QUdpSocket(self) if QUdpSocket else None
        if self._udp:
            try:
                # Try to use QHostAddress.LocalHost directly
                if QHostAddress:
                    self._udp.bind(QHostAddress.LocalHost, 8765)  # type: ignore
                else:
                    # Fallback to integer value
                    self._udp.bind(1, 8765)  # LocalHost = 1  # type: ignore
            except:
                pass
            self._udp.readyRead.connect(self._on_udp)

    def _on_tick(self):
        # Read audio peak for lip-sync
        level = self._meter.get_peak()
        speech_freq = self._meter.get_speech_intensity()
        
        # Smooth attack/decay for nicer motion
        # Faster attack for responsive lip-sync
        attack = 0.7
        decay = 0.2
        if level > self._smoothed:
            self._smoothed = self._smoothed * (1 - attack) + level * attack
        else:
            self._smoothed = self._smoothed * (1 - decay) + level * decay
        self._level = max(0.0, min(1.0, self._smoothed))
        
        # Update lip-sync based on speech frequency
        self._lip_sync = max(0.0, min(1.0, speech_freq))
        
        if self._expr != "neutral" and time.time() >= self._expr_until:
            self._expr = "neutral"
            
        # Handle blinking animation
        self._blink_timer += 1
        if self._blink_state == 0 and self._blink_timer > 180:  # Start closing
            self._blink_state = 1
            self._blink_timer = 0
        elif self._blink_state == 1 and self._blink_timer > 3:  # Fully closed
            self._blink_state = 2
            self._blink_timer = 0
        elif self._blink_state == 2 and self._blink_timer > 6:  # Start opening
            self._blink_state = 3
            self._blink_timer = 0
        elif self._blink_state == 3 and self._blink_timer > 3:  # Back to normal
            self._blink_state = 0
            self._blink_timer = 0
        
        # Update floating animation time
        import math
        self._float_time += 0.016  # Approx 16ms per frame
        
        self.update()

    def set_expression(self, expr: str, duration: float = 1.2):
        """Set avatar expression. Valid: 'neutral', 'wink', 'smile_open'."""
        valid_expressions = {"neutral", "wink", "smile_open"}
        if expr not in valid_expressions:
            return  # Ignore invalid expressions
        self._expr = expr
        self._expr_until = time.time() + max(0.1, duration)

    def _on_udp(self):
        if not self._udp:
            return
            
        while self._udp.hasPendingDatagrams():
            datagram = self._udp.receiveDatagram()
            try:
                # Convert QByteArray to bytes properly
                data = datagram.data()
                # Use a more robust approach to convert QByteArray to string
                try:
                    # Try to get bytes directly
                    payload_str = data.data().decode("utf-8", errors="ignore")  # type: ignore
                except:
                    # Fallback to convert to bytes first
                    payload_str = bytes(data)  # type: ignore
                    payload_str = payload_str.decode("utf-8", errors="ignore")
                
                payload = json.loads(payload_str)
                expr = str(payload.get("expr", "")).strip().lower()
                dur = float(payload.get("duration", 1.2))
                if expr in {"wink", "smile_open", "neutral"}:
                    self.set_expression(expr, dur)
            except Exception:
                pass

    def paintEvent(self, event):
        if not PYSIDE_AVAILABLE or not QPainter:
            return
            
        import math
        painter = QPainter(self)  # type: ignore
        painter.setRenderHint(QPainter.Antialiasing)  # type: ignore
        rect = self.rect().adjusted(8, 8, -8, -8)

        # Face dimensions
        face_width = rect.width() * 0.7
        face_height = rect.height() * 0.8
        face_center_x = rect.center().x()
        face_center_y = rect.center().y()
        
        # Apply subtle breathing animation
        float_offset = math.sin(self._float_time * 0.5) * 2
        head_tilt = math.sin(self._float_time * 0.3) * 1
        
        face_center_y += float_offset
        
        # Save painter state for rotation
        painter.save()
        painter.translate(face_center_x, face_center_y)
        painter.rotate(head_tilt)
        painter.translate(-face_center_x, -face_center_y)
        
        # Draw face base with realistic skin tone
        face_gradient = QtGui.QRadialGradient(face_center_x, face_center_y - 10, face_width * 0.6)  # type: ignore
        face_gradient.setColorAt(0.0, QColor(255, 220, 190, 240))  # type: ignore # Center: light skin
        face_gradient.setColorAt(0.7, QColor(240, 190, 160, 240))  # type: ignore # Mid: natural skin
        face_gradient.setColorAt(1.0, QColor(220, 170, 140, 240))  # type: ignore # Edge: slightly darker
        painter.setBrush(QBrush(face_gradient))  # type: ignore
        painter.setPen(QPen(QColor(200, 160, 140, 200), 1))  # type: ignore
        
        # Draw face shape (more oval and natural)
        face_path = QtGui.QPainterPath()  # type: ignore
        
        # Chin
        chin_x = face_center_x
        chin_y = face_center_y + face_height/2 - 10
        face_path.moveTo(chin_x, chin_y)  # type: ignore
        
        # Left jaw
        face_path.cubicTo(  # type: ignore
            face_center_x - face_width/2 + 10, face_center_y + face_height/3,
            face_center_x - face_width/2 + 5, face_center_y - face_height/4,
            face_center_x - face_width/2 + 15, face_center_y - face_height/2 + 10
        )
        
        # Forehead
        face_path.cubicTo(  # type: ignore
            face_center_x - face_width/2 + 25, face_center_y - face_height/2 - 5,
            face_center_x + face_width/2 - 25, face_center_y - face_height/2 - 5,
            face_center_x + face_width/2 - 15, face_center_y - face_height/2 + 10
        )
        
        # Right jaw back to chin
        face_path.cubicTo(  # type: ignore
            face_center_x + face_width/2 - 5, face_center_y - face_height/4,
            face_center_x + face_width/2 - 10, face_center_y + face_height/3,
            chin_x, chin_y
        )
        
        painter.drawPath(face_path)  # type: ignore

        # Draw hair
        hair_path = QtGui.QPainterPath()  # type: ignore
        hair_top_y = face_center_y - face_height/2 - 5
        
        # Hairline
        hair_path.moveTo(face_center_x - face_width/2 + 20, hair_top_y)  # type: ignore
        hair_path.cubicTo(  # type: ignore
            face_center_x - face_width/2, hair_top_y + 15,
            face_center_x + face_width/2, hair_top_y + 15,
            face_center_x + face_width/2 - 20, hair_top_y
        )
        
        # Sides of hair
        hair_path.lineTo(face_center_x + face_width/2 - 15, face_center_y - face_height/2 + 40)  # type: ignore
        hair_path.cubicTo(  # type: ignore
            face_center_x + face_width/2 - 5, face_center_y - face_height/2 + 30,
            face_center_x + face_width/2, face_center_y - 10,
            face_center_x + face_width/2 - 10, face_center_y + 10
        )
        
        hair_path.lineTo(face_center_x - face_width/2 + 10, face_center_y + 10)  # type: ignore
        hair_path.cubicTo(  # type: ignore
            face_center_x - face_width/2, face_center_y - 10,
            face_center_x - face_width/2 + 5, face_center_y - face_height/2 + 30,
            face_center_x - face_width/2 + 15, face_center_y - face_height/2 + 40
        )
        
        hair_path.closeSubpath()  # type: ignore
        painter.fillPath(hair_path, QBrush(QColor(40, 40, 40)))  # type: ignore

        # Draw eyes
        eye_width = 22
        eye_height = 16
        eye_y = face_center_y - face_height * 0.1
        eye_gap = 35
        
        # Eye tracking
        max_pupil_offset = 4
        pupil_offset_x = (self._cursor_x - 0.5) * max_pupil_offset * 2
        pupil_offset_y = (self._cursor_y - 0.5) * max_pupil_offset * 2
        
        # Handle blinking
        blink_height = eye_height
        if self._blink_state == 1:  # Closing
            blink_height = eye_height * 0.5
        elif self._blink_state == 2:  # Closed
            blink_height = 2
        elif self._blink_state == 3:  # Opening
            blink_height = eye_height * 0.5
        
        left_eye_h = blink_height
        right_eye_h = blink_height
        if self._expr == "wink":
            right_eye_h = 4  # Squint for wink
        
        # Eye shapes
        left_eye_rect = QtCore.QRectF(  # type: ignore
            face_center_x - eye_gap - eye_width/2, 
            eye_y - eye_height/2, 
            eye_width, 
            left_eye_h
        )
        right_eye_rect = QtCore.QRectF(  # type: ignore
            face_center_x + eye_gap - eye_width/2, 
            eye_y - eye_height/2, 
            eye_width, 
            right_eye_h
        )
        
        # Draw eye whites
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1))  # type: ignore
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))  # type: ignore
        painter.drawEllipse(left_eye_rect)  # type: ignore
        if self._expr != "wink":
            painter.drawEllipse(right_eye_rect)  # type: ignore
        
        # Draw eye pupils
        try:
            painter.setPen(Qt.PenStyle.NoPen)  # type: ignore
        except:
            painter.setPen(0)  # NoPen fallback  # type: ignore
        painter.setBrush(QBrush(QColor(30, 30, 30)))  # type: ignore
        
        # Left pupil
        left_pupil_x = left_eye_rect.center().x() + pupil_offset_x
        left_pupil_y = left_eye_rect.center().y() + pupil_offset_y
        painter.drawEllipse(  # type: ignore
            QtCore.QPointF(left_pupil_x, left_pupil_y),  # type: ignore
            7, 7
        )
        
        # Right pupil (if not winking)
        if self._expr != "wink":
            right_pupil_x = right_eye_rect.center().x() + pupil_offset_x
            right_pupil_y = right_eye_rect.center().y() + pupil_offset_y
            painter.drawEllipse(  # type: ignore
                QtCore.QPointF(right_pupil_x, right_pupil_y),  # type: ignore
                7, 7
            )
        
        # Draw eyebrows
        try:
            painter.setPen(QPen(QColor(30, 30, 30), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))  # type: ignore
        except:
            painter.setPen(QPen(QColor(30, 30, 30), 3, 1, 16))  # SolidLine, RoundCap fallback  # type: ignore
        
        # Left eyebrow
        left_eyebrow_start = QtCore.QPointF(face_center_x - eye_gap - 15, eye_y - 18)  # type: ignore
        left_eyebrow_end = QtCore.QPointF(face_center_x - eye_gap + 10, eye_y - 18)  # type: ignore
        painter.drawLine(left_eyebrow_start, left_eyebrow_end)  # type: ignore
        
        # Right eyebrow
        if self._expr == "wink":
            right_eyebrow_start = QtCore.QPointF(face_center_x + eye_gap - 10, eye_y - 15)  # type: ignore
            right_eyebrow_end = QtCore.QPointF(face_center_x + eye_gap + 10, eye_y - 20)  # type: ignore
        else:
            right_eyebrow_start = QtCore.QPointF(face_center_x + eye_gap - 10, eye_y - 18)  # type: ignore
            right_eyebrow_end = QtCore.QPointF(face_center_x + eye_gap + 15, eye_y - 18)  # type: ignore
        painter.drawLine(right_eyebrow_start, right_eyebrow_end)  # type: ignore

        # Draw nose
        nose_y = face_center_y + face_height * 0.02
        painter.setPen(QPen(QColor(200, 160, 140, 200), 2))  # type: ignore
        
        # Nose bridge
        painter.drawLine(  # type: ignore
            QtCore.QPointF(face_center_x, nose_y - 15),  # type: ignore
            QtCore.QPointF(face_center_x, nose_y)  # type: ignore
        )
        
        # Nostrils
        try:
            painter.setPen(QPen(QColor(180, 140, 120, 220), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))  # type: ignore
        except:
            painter.setPen(QPen(QColor(180, 140, 120, 220), 2, 1, 16))  # SolidLine, RoundCap fallback  # type: ignore
        painter.drawPoint(QtCore.QPointF(face_center_x - 6, nose_y + 3))  # type: ignore
        painter.drawPoint(QtCore.QPointF(face_center_x + 6, nose_y + 3))  # type: ignore

        # Draw mouth
        mouth_width = face_width * 0.3
        base_height = 5
        max_extra = 20
        
        # Combine audio level and lip-sync for natural mouth movement
        combined_level = (self._level * 0.4 + self._lip_sync * 0.6)
        mouth_height = base_height + combined_level * max_extra
        mouth_y = face_center_y + face_height * 0.15
        
        if self._expr == "smile_open":
            mouth_width = face_width * 0.35
            mouth_height = base_height + max_extra * 0.7 + combined_level * max_extra * 0.4
            mouth_y = face_center_y + face_height * 0.13
        
        # Simple mouth shape
        mouth_rect = QtCore.QRectF(  # type: ignore
            face_center_x - mouth_width/2,
            mouth_y - mouth_height/2,
            mouth_width,
            mouth_height
        )
        
        # Draw mouth
        painter.setPen(QPen(QColor(180, 100, 100, 220), 2))  # type: ignore
        painter.setBrush(QBrush(QColor(220, 120, 120, 200)))  # type: ignore
        painter.drawRoundedRect(mouth_rect, 5, 5)  # type: ignore
        
        # Restore painter state
        painter.restore()

    # Drag window
    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:  # type: ignore
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
        except:
            if event.button() == 1:  # LeftButton fallback
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        # Update cursor position for eye tracking (normalized 0-1)
        rect = self.rect()
        if rect.width() > 0 and rect.height() > 0:
            self._cursor_x = max(0.0, min(1.0, event.position().x() / rect.width()))
            self._cursor_y = max(0.0, min(1.0, event.position().y() / rect.height()))
        
        # Handle dragging
        try:
            if self._drag_pos is not None and (event.buttons() & Qt.MouseButton.LeftButton):  # type: ignore
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
        except:
            if self._drag_pos is not None and (event.buttons() & 1):  # LeftButton fallback
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


def main():
    if not PYSIDE_AVAILABLE:
        print("PySide6 is not available. Please install it to run the avatar.")
        return
        
    app = QApplication(sys.argv)  # type: ignore
    w = AvatarWidget()
    # Position bottom-right-ish of the primary screen
    if hasattr(app, 'primaryScreen'):
        screen = app.primaryScreen().availableGeometry()
        w.move(screen.right() - w.width() - 24, screen.bottom() - w.height() - 24)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()