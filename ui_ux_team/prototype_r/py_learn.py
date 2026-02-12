import random
import sys
import os
import json
import markdown
import threading

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QLabel, QListWidget,
    QStackedWidget, QListWidgetItem, QPushButton, QFileDialog, QSlider
)
from PySide6.QtGui import (
    QPalette, QColor, QPixmap, QCursor, QTransform,
    QPainter, QFont, QPainterPath, QRegion, QCursor,
    QTextDocument
)
from PySide6.QtWidgets import (
    QGraphicsColorizeEffect, QGraphicsOpacityEffect, QSizePolicy, QSpacerItem, 
    QTextBrowser, QPlainTextEdit, QTextEdit
)
from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QEasingCurve, 
    Property, QRect, QSize, QPoint, QTimer, QEvent, QParallelAnimationGroup,
    QThread, Slot
)

from pathlib import Path

# Ensure project root is importable when running the script directly.
if not getattr(sys, 'frozen', False):
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from architects.helpers.miniaudio_player import MiniaudioPlayer
from architects.helpers.transcription_manager import TranscriptionManager
from architects.helpers.tabs_audio import get_display_names
from architects.helpers.managed_mem import ManagedMem
from architects.helpers.gemini_chatbot import GeminiChatbot
from architects.helpers.resource_path import resource_path

# ---- Dark Theme Color Constants ----
COLOR_BG_MAIN        = "#1E1E1E"   # was: "orange"
COLOR_SIDEBAR        = "#2A0A3C"   # was: "purple"
COLOR_SIDEBAR_TOP    = "#3A3A3A"   # was: "gray"
COLOR_SIDEBAR_BOTTOM = "#C0392B"   # was: "red"

# COLOR_COVERS_BG      = "#263238"   # was: "cyan"
COLOR_COVERS_BG      = "#1E1E1E"   # was: "cyan"
COLOR_COVER_IMAGE    = "#2E7D32"   # was: "green"

COLOR_TIMELINE_BG    = "#2A2A2A"   # was: lime

COLOR_BOTTOM_BG      = "#1E1E1E"   # was: "gray"
# COLOR_CONTROLS_BG    = "#3E1F47"   # was: "pink"
COLOR_CONTROLS_BG    = "#1E1E1E"   # was: "pink"
COLOR_CONTROL_BTN    = "#6A1B9A"   # was: "purple"

COLOR_BLUE_BIRD      = "#1565C0"   # was: "blue"

# # ---- Original Color Constants (old colors) ----
# COLOR_BG_MAIN        = "orange"   # original
# COLOR_SIDEBAR        = "purple"   # original
# COLOR_SIDEBAR_TOP    = "gray"     # original
# COLOR_SIDEBAR_BOTTOM = "red"      # original

# COLOR_COVERS_BG      = "cyan"     # original
# COLOR_COVER_IMAGE    = "green"    # original

# COLOR_TIMELINE_BG    = "lime"     # original

# COLOR_BOTTOM_BG      = "gray"     # original
# COLOR_CONTROLS_BG    = "pink"     # original
# COLOR_CONTROL_BTN    = "purple"   # original (control buttons)

# COLOR_BLUE_BIRD      = "blue"     # original

BASE = resource_path("ui_ux_team/prototype_r")
IMAGE_NOT_FOUND = os.path.join(BASE, "assets/image_not_found_white.png")

# Simple Transcript chunk len (in seconds)
T_CHUNK = 30


class ImageButton(QLabel):
    clicked = Signal()

    def __init__(self, path, size=(40, 40), fallback=None):
        super().__init__()
        self.setFixedSize(*size)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAlignment(Qt.AlignCenter)

        self.HOVER_SCALE = 1.10
        self.PRESS_SCALE = 0.94
        margin_factor = 0.06

        margins = [max(size[0], size[1]) * margin_factor] * 4
        self.setContentsMargins(*margins)

        self.base_pixmap = QPixmap(path)
        if self.base_pixmap.isNull() and fallback:
            self.base_pixmap = QPixmap(fallback)

        self._scale = 1.0

        # Animation controller
        self.anim = QPropertyAnimation(self, b"scale_factor", self)
        self.anim.setDuration(120)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)

    def set_image(self, path, fallback=IMAGE_NOT_FOUND):
        # Normalize the path and always fall back to a valid pixmap so the icon never disappears.
        resolved = path
        if not os.path.isabs(resolved):
            resolved = os.path.join(BASE, path)

        pm = QPixmap(resolved)
        if pm.isNull():
            pm = QPixmap(fallback or IMAGE_NOT_FOUND)

        self.base_pixmap = pm
        self.update()

    # ----------------------------
    # Qt Property backing + accessors
    # ----------------------------
    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale_factor = Property(float, get_scale, set_scale)  # ★ IMPORTANT

    # ----------------------------
    # Paint scaled pixmap (centered)
    # ----------------------------
    def paintEvent(self, event):
        if self.base_pixmap.isNull():
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        m = self.contentsMargins()
        inner_w = self.width() - (m.left() + m.right())
        inner_h = self.height() - (m.top() + m.bottom())

        # center scaling
        s = self._scale

        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(s, s)
        painter.translate(-self.width() / 2, -self.height() / 2)

        scaled = self.base_pixmap.scaled(
            inner_w,
            inner_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # center inside margin area
        x = m.left() + (inner_w - scaled.width()) // 2
        y = m.top() + (inner_h - scaled.height()) // 2

        painter.drawPixmap(x, y, scaled)

    # ----------------------------
    # Hover scale-up
    # ----------------------------
    def enterEvent(self, event):
        self.animate_to(self.HOVER_SCALE)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_to(1.00)
        super().leaveEvent(event)

    # ----------------------------
    # Click downscale
    # ----------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.animate_to(self.PRESS_SCALE, fast=True)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            inside = self.rect().contains(event.position().toPoint())
            self.animate_to(self.HOVER_SCALE if inside else 1.00)
            if inside:
                self.clicked.emit()
        super().mouseReleaseEvent(event)

    # ----------------------------
    # Animation helper
    # ----------------------------
    def animate_to(self, value, fast=False):
        self.anim.stop()
        self.anim.setDuration(80 if fast else 140)
        self.anim.setStartValue(self._scale)
        self.anim.setEndValue(value)
        self.anim.start()


class MarqueeLabel(QLabel):
    """Horizontal marquee that scrolls text left to right in a loop."""
    def __init__(self, text="", parent=None, step=1, interval_ms=30, gap=50):
        super().__init__(parent)
        self._offset = 0
        self._text_width = 0
        self._gap = gap
        self._step = step

        self.setText(text)
        self.setContentsMargins(10, 0, 10, 0)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(interval_ms)

    def setText(self, text):
        super().setText(text)
        fm = self.fontMetrics()
        self._text_width = fm.horizontalAdvance(text) if text else 0

    def _tick(self):
        if self._text_width <= 0:
            return
        span = self._text_width + self._gap
        self._offset = (self._offset + self._step) % span
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        fm = self.fontMetrics()
        text = self.text()

        # Vertically center the text
        y = (self.height() + fm.ascent() - fm.descent()) / 2
        if self._text_width <= 0:
            return

        span = self._text_width + self._gap
        x = -self._text_width + self._offset

        while x < self.width():
            painter.drawText(x, y, text)
            x += span

    def changeEvent(self, event):
        if event.type() == QEvent.FontChange:
            self.setText(self.text())
        super().changeEvent(event)


class QueuedMarqueeLabel(QWidget):
    """Wrapper that cycles through queued strings with a soft fade between them."""
    def __init__(self, items=None, parent=None, hold_ms=3000, fade_ms=200, **marquee_kwargs):
        super().__init__(parent)
        self._queue = list(items) if items else []
        self._idx = 0
        self._hold_ms = hold_ms
        self._fade_ms = fade_ms

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = MarqueeLabel("", **marquee_kwargs)
        self._opacity = QGraphicsOpacityEffect(self.label)
        self._opacity.setOpacity(1.0)
        self.label.setGraphicsEffect(self._opacity)
        layout.addWidget(self.label)

        if self._queue:
            self.label.setText(self._queue[0])

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_text)
        if self._queue:
            self._timer.start(self._hold_ms)

    def set_queue(self, items):
        self._queue = list(items) if items else []
        self._idx = 0
        if self._queue:
            self.label.setText(self._queue[0])
            self._timer.start(self._hold_ms)
        else:
            self._timer.stop()

    def enqueue(self, text):
        self._queue.append(text)
        if len(self._queue) == 1:
            self.label.setText(text)
            self._timer.start(self._hold_ms)

    def _next_text(self):
        if not self._queue:
            return
        self._idx = (self._idx + 1) % len(self._queue)
        self._fade_to(self._queue[self._idx])

    def _fade_to(self, text):
        self._timer.stop()
        anim_out = QPropertyAnimation(self._opacity, b"opacity", self)
        anim_out.setDuration(self._fade_ms)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        anim_out.finished.connect(lambda: self._on_faded(text))
        anim_out.start(QPropertyAnimation.DeleteWhenStopped)

    def _on_faded(self, text):
        self.label.setText(text)
        anim_in = QPropertyAnimation(self._opacity, b"opacity", self)
        anim_in.setDuration(self._fade_ms)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.finished.connect(lambda: self._timer.start(self._hold_ms))
        anim_in.start(QPropertyAnimation.DeleteWhenStopped)


class FloatingToast(QLabel):
    """Bottom-up floating text (Meet/stream-style) that animates in and out on demand."""
    def __init__(self, parent=None, bg="#1f1f1f", fg="#a3a3a3", font_size=25, border="#303030"):
        super().__init__(parent)
        self._bg = bg
        self._fg = fg
        self._font_size = font_size
        self._border = border
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setVisible(False)
        self._apply_style()

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._current_anim = None

    def _apply_style(self):
        self.setStyleSheet(f"""
            QLabel {{
                background: {self._bg};
                color: {self._fg};
                padding: 10px 14px;
                border-radius: 12px;
                border: 1px solid {self._border};
                font-weight: 600;
                letter-spacing: 0.3px;
                font-size: {self._font_size}px;
            }}
        """)

    def set_font_size(self, size_px: int):
        """Adjust toast text size."""
        self._font_size = size_px
        self._apply_style()

    def set_border_color(self, color: str):
        """Adjust toast border color."""
        self._border = color
        self._apply_style()

    def show_message(self, text, duration_ms=2200, bottom_band_ratio=0.3, top_band_ratio=0.25):
        parent = self.parentWidget()
        if parent is None:
            return

        # Reset any running animation.
        if self._current_anim:
            self._current_anim.stop()

        self.setText(text)
        self.adjustSize()

        usable_width = max(1, parent.width() - self.width() - 20)
        start_x = random.randint(10, usable_width)
        end_x = start_x  # keep vertical drift; adjust if lateral drift desired

        bottom_band_start = int(parent.height() * (1 - bottom_band_ratio))
        bottom_band_end = parent.height() - self.height() - 10
        bottom_band_end = max(bottom_band_start, bottom_band_end)
        start_y = random.randint(bottom_band_start, bottom_band_end) if bottom_band_end >= bottom_band_start else bottom_band_end

        top_band_end = int(parent.height() * top_band_ratio)
        top_band_end = max(10, top_band_end)
        end_y = random.randint(10, top_band_end)

        self.move(start_x, start_y)
        self._opacity.setOpacity(0.0)
        self.show()
        self.raise_()

        pos_anim = QPropertyAnimation(self, b"pos", self)
        pos_anim.setDuration(duration_ms)
        pos_anim.setStartValue(QPoint(start_x, start_y))
        pos_anim.setEndValue(QPoint(end_x, end_y))
        pos_anim.setEasingCurve(QEasingCurve.OutQuad)

        fade_anim = QPropertyAnimation(self._opacity, b"opacity", self)
        fade_anim.setDuration(duration_ms)
        fade_anim.setKeyValueAt(0.0, 0.0)
        fade_anim.setKeyValueAt(0.15, 1.0)
        fade_anim.setKeyValueAt(0.8, 1.0)
        fade_anim.setKeyValueAt(1.0, 0.0)

        group = QParallelAnimationGroup(self)
        group.addAnimation(pos_anim)
        group.addAnimation(fade_anim)
        group.finished.connect(self._on_finished)

        self._current_anim = group
        group.start(QPropertyAnimation.DeleteWhenStopped)

    def _on_finished(self):
        self.hide()
        self._current_anim = None


class PopupTitleBar(QWidget):
    def __init__(self, title="Settings", parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self._drag_pos = None

        self.setStyleSheet(""" 
            QLabel {
                color: #f0f0f0;
                font-size: 18px;
                font-family: Inter;
                padding-left: 8px;
                padding-top: 3px;
            }
            QPushButton {
                background: none;
                color: #e0e0e0;
                border: none;
                padding: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #454545;
                border-radius: 4px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        self.label = QLabel(title)
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedWidth(28)

        layout.addWidget(self.label)
        layout.addStretch(1)
        layout.addWidget(self.close_btn)

        self.close_btn.clicked.connect(self._close)

    def _close(self):
        self.window().close()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None:
            delta = e.globalPosition().toPoint() - self._drag_pos
            self.window().move(self.window().pos() + delta)
            self._drag_pos = e.globalPosition().toPoint()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None


class SettingsPopup(QWidget):
    def __init__(self, categories=None, parent=None, margin=100):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

        # unify popup background
        self.setStyleSheet("""
            QWidget#SettingsPopup {
                background: #2b2b2b;
                border: 1px solid #1d1d1d;
                border-radius: 8px;
            }
            QLineEdit {
                background: #2c2c2c;
                border: 1px solid #1e1e1e;
                border-radius: 4px;
                padding: 4px;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                background: #2f2f2f;
            }
        """)
        self.setObjectName("SettingsPopup")

        self.margin = margin
        self.setMinimumSize(520, 330)

        self.categories = categories or {}

        # LEFT SIDEBAR
        self.list = QListWidget()
        self.list.setFixedWidth(160)
        self.list.setSpacing(4)

        self.list.setStyleSheet("""
            QListWidget {
                background: #262626;
                border: none;
                color: #d0d0d0;
                border-bottom-left-radius: 8px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #3a3a3a;
                color: white;
            }
        """)

        # RIGHT CONTENT
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("""
            QStackedWidget {
                background: #2f2f2f;
                border-left: 1px solid #1f1f1f;
                border-bottom-right-radius: 8px;
            }
        """)

        for name, widget in self.categories.items():
            widget.setFocusPolicy(Qt.NoFocus)

            # helps on KDE/Breeze
            widget.setAttribute(Qt.WA_NoSystemBackground, True)
            widget.setAutoFillBackground(False)

            if isinstance(widget, QLabel):
                widget.setFrameStyle(QFrame.NoFrame)
                widget.setStyleSheet("background: none; border: none; color: #e0e0e0;")
            item = QListWidgetItem(name)
            item.setSizeHint(QSize(150, 30))
            self.list.addItem(item)
            self.stack.addWidget(widget)

        self.list.currentRowChanged.connect(self.stack.setCurrentIndex)
        if self.list.count():
            self.list.setCurrentRow(0)

        # LAYOUTS
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        title_bar = PopupTitleBar("Settings", self)
        root_layout.addWidget(title_bar)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(6, 6, 6, 6)
        content_layout.addWidget(self.list)
        content_layout.addWidget(self.stack)

        root_layout.addLayout(content_layout)

    def show_pos_size(self, parent_pos: QPoint, parent_size):
        win = self.parent()
        if win:
            win = win.window()

        if win:
            fg = win.frameGeometry().height()
            g = win.geometry().height()
            titlebar_h = max(0, fg - g)
        else:
            titlebar_h = 0

        x = parent_pos.x() + self.margin
        y = parent_pos.y() + self.margin + titlebar_h

        w = parent_size.width() - (self.margin * 2)
        h = parent_size.height() - (self.margin * 2) - titlebar_h

        self.setGeometry(x, y, w, h)
        self.show()


class TextBoxAI(QTextBrowser):
    def __init__(self):
        super().__init__()

        self.setObjectName("TextBox") 
        # self.setReadOnly(True) # QTextBrowser is read-only by default
        self.setOpenExternalLinks(True)

        # padding + border
        self.setStyleSheet("""
            QTextBrowser#TextBox {
                background-color: #0F0F0F;
                color: #B8B8B8;

                border: 1px solid #2A2D31;
                border-radius: 10px;
                padding: 15px;

                font-size: 15px;
                font-weight: 400;
                font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif;
                line-height: 1.4;

                selection-background-color: #3E6AFF;
            }
            /* Style lists */
            QTextBrowser ul, QTextBrowser ol {
                margin-left: 20px;
                padding-left: 0px;
            }
            /* Style code blocks */
            QTextBrowser pre {
                background-color: #1E1E1E;
                padding: 10px;
                border-radius: 5px;
                font-family: "Consolas", "Monaco", monospace;
            }
            QTextBrowser code {
                background-color: #1E1E1E;
                font-family: "Consolas", "Monaco", monospace;
            }
        """)

    def append_message(self, role: str, text: str):
        """Formats and appends a message with markdown support and role-based styling."""
        
        # Pre-process text to ensure lists have a newline before them (AI often skips this)
        processed_text = text.replace("\n*", "\n\n*").replace("\n-", "\n\n-")
        
        # Use 'extra' for tables/code-blocks and 'sane_lists' for better list handling
        html_content = markdown.markdown(processed_text, extensions=['extra', 'sane_lists'])
        
        if role == "user":
            sender = "You"
            color = "#5EA2FF"  # Soft Blue
        elif role == "model":
            sender = "BlueBird"
            color = "#2ECC71"  # Soft Green
        else:
            sender = "System"
            color = "#95A5A6"  # Gray

        # Construct HTML block
        # Note: QT's HTML subset is limited. Simple inline styles work best.
        html_block = f"""
        <div style="margin-top: 10px; margin-bottom: 5px;">
            <span style="color: {color}; font-weight: bold; font-size: 16px;">{sender}</span>
        </div>
        <div style="color: #E0E0E0; margin-bottom: 10px;">
            {html_content}
        </div>
        <hr style="background-color: #2A2D31; height: 1px; border: none; margin: 10px 0;">
        """
        
        self.append("") # Ensure separation from previous block
        self.insertHtml(html_block)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class FloatingMenu(QWidget):
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("PopupMenu")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        labels = [
            QLabel("💼 Work"),
            QLabel("🎉 Party"),
            QLabel("🎮 Gaming")
        ]

        container = QWidget(self)
        container.setObjectName("PopupInner")

        layout = QVBoxLayout(container)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(container)

        font = QFont("Inter")
        font.setWeight(QFont.Normal)

        for lbl in labels:
            lbl.setFont(font)
            layout.addWidget(lbl)

        self.setStyleSheet("""
            QWidget#PopupInner {
                background-color: rgba(15, 15, 15, 235);      /* darker, cleaner */
                border-radius: 14px;
                padding: 8px;
            }

            QLabel {
                background-color: rgba(40, 40, 40, 200);       /* smoother card look */
                border: 1px solid rgba(255, 255, 255, 25);     /* subtle border */
                border-radius: 10px;
                font-size: 20px;
                padding: 10px 14px;
                color: #F3F3F3;                                /* cleaner white */
            }

            QLabel:hover {
                background-color: rgba(50, 50, 50, 220);       /* brighter on hover */
                border: 1px solid rgba(255, 255, 255, 45);     /* pop highlight */
            }
        """)

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)


class TextBox(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        self.setObjectName("TextBox") 
        self.setReadOnly(True)

        # padding + border
        self.setStyleSheet("""
            QPlainTextEdit#TextBox {
                background-color: #0F0F0F;
                color: #B8B8B8;

                border: 1px solid #2A2D31;
                border-radius: 10px;
                padding: 10px;

                font-size: 15px;
                font-weight: 600;
                font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif;

                selection-background-color: #3E6AFF;
            }
        """)

        self.transcript_index: int = 0
        self.transcript: list[str] = []

        self._read_transcript()
        self._display_transcript()

    def _read_transcript(self):
        pass

    def _display_transcript(self, transcript=None):
        if transcript:
            for line in transcript:
                self.appendPlainText(line)
                self.transcript_index += 1

        # self.appendPlainText("SPEAKER 1: Hello")
        # self.appendPlainText("SPEAKER 2: Hi there.")


class TranscriptWindow(QWidget):
    closed = Signal()

    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle("Transcript")

        layout = QVBoxLayout(self)

        record_button = MainUI.button("assets/record_black.png", (65, 65))
        record_button.clicked.connect(parent.record_transcript)

        search_bar = SearchBar()

        top_box = QHBoxLayout()
        top_box.addWidget(record_button)
        top_box.addWidget(search_bar)

        self.text_box = TextBox()

        layout.addLayout(top_box, 1)
        layout.addWidget(self.text_box, 9)
    
    def add_transcript_segment(self, seg):
        self.text_box.appendPlainText(seg)

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)


class InputBlueBird(QTextEdit):
    message_sent = Signal(str)

    def __init__(self, text_box):
        super().__init__()

        self.style_settings()
        self.text_box: TextBoxAI = text_box

    def keyPressEvent(self, e):
        # Send on Ctrl+Enter
        if (e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter) and (e.modifiers() & Qt.ControlModifier):
            self.send_message()
            return
        # Allow default behavior (newline on Enter)
        super().keyPressEvent(e)

    def send_message(self):
        text = self.toPlainText().strip()
        if not text:
            return
        
        self.clear()
        self.message_sent.emit(text)

    def style_settings(self):
        self.setObjectName("InputChat")

        font = QFont()
        font.setPointSize(13)
        self.setFont(font)

        self.setFixedHeight(70)
        self.setPlaceholderText("Type a message to BlueBird AI (Ctrl+Space to send)")

        # padding + border
        self.setStyleSheet("""
            QTextEdit#InputChat {
                background-color: #161616;
                color: #E6E6E6;

                border: 1px solid #2A2D31;
                border-radius: 10px;
                padding: 10px;

                font-size: 15px;
                font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif;

                selection-background-color: #3E6AFF;
            }
        """)


class SearchBar(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setObjectName("SearchBar")

        self.setFixedHeight(48)
        self.setPlaceholderText("Search transcript...")

        self.setFont(QFont("Inter", 13))

        self.setStyleSheet("""
            QTextEdit#SearchBar {
                background-color: #161616;          
                color: #D0D0D0;

                border: 1px solid #303236;
                border-radius: 8px;
                padding: 10px 14px;

                font-size: 14px;
                font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif;

                selection-background-color: #4A78FF;
                selection-color: black;
            }

            /* Optional subtle inset focus ring */
            QTextEdit#SearchBar:focus {
                border: 2px solid #ff7139;
                background-color: #1A1A1A;
            }
        """)


class LoadingCircle(QWidget):
    """Simple animated loading spinner."""
    def __init__(self, parent=None, size=50):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_angle)
        self.hide()

    def _update_angle(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def start(self):
        self._timer.start(80)
        self.show()
        self.raise_()

    def stop(self):
        self._timer.stop()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        cx, cy = self.width() / 2, self.height() / 2
        radius = min(cx, cy) - 6
        
        painter.translate(cx, cy)
        painter.rotate(self._angle)
        
        pen = painter.pen()
        pen.setWidth(5)
        pen.setCapStyle(Qt.RoundCap)
        
        # Draw 8 lines with progressive opacity
        for i in range(8):
            opacity = int(255 * (i + 1) / 8)
            pen.setColor(QColor(62, 106, 255, opacity)) # Soft blue
            painter.setPen(pen)
            painter.drawLine(0, int(-radius), 0, int(-radius + 10))
            painter.rotate(45)


class ChatWorker(QThread):
    response_received = Signal(dict)

    def __init__(self, chatbot, message):
        super().__init__()
        self.chatbot = chatbot
        self.message = message

    def run(self):
        if self.chatbot:
            response = self.chatbot.send_message(self.message)
            self.response_received.emit(response)
        else:
             self.response_received.emit({"error": "Chatbot not initialized"})


class ChatInitWorker(QThread):
    init_finished = Signal(bool, str)

    def __init__(self, chatbot, transcript):
        super().__init__()
        self.chatbot = chatbot
        self.transcript = transcript

    def run(self):
        try:
            success = self.chatbot.load_context(self.transcript)
            if success:
                self.init_finished.emit(True, "Context loaded.")
            else:
                self.init_finished.emit(False, "Failed to load context. (Make sure you started recording and have 1K+ context or you loaded context from file)")
        except Exception as e:
            self.init_finished.emit(False, str(e))


class ContextUpdateWorker(QThread):
    update_finished = Signal(bool, str)

    def __init__(self, chatbot, file_path):
        super().__init__()
        self.chatbot = chatbot
        self.file_path = file_path

    def run(self):
        try:
            success = self.chatbot.update_context_with_file(self.file_path)
            if success:
                self.update_finished.emit(True, "Context loaded.")
            else:
                self.update_finished.emit(False, "Failed to load context.")
        except Exception as e:
            self.update_finished.emit(False, str(e))


class BlueBirdChat(QWidget):
    closed = Signal()

    def __init__(self, api_key=None, initial_transcript=None):
        super().__init__()
        self.setWindowTitle("BlueBird AI")
        self.api_key = api_key
        self.chatbot = None
        self.initial_transcript = initial_transcript
        
        self.text_box = None
        self.input_field = None
        self.send_btn = None
        self.loader = None
        self.root_layout = self.build_layout()

        if self.api_key:
             self.chatbot = GeminiChatbot(self.api_key)
             
             transcript_to_load = self.initial_transcript if self.initial_transcript else "System: This is the start of the session."
             
             self.text_box.append_message("system", "*Initializing BlueBird AI context...*")
             self.set_input_enabled(False)
             if self.loader:
                 self.loader.start()

             self.init_worker = ChatInitWorker(self.chatbot, transcript_to_load)
             self.init_worker.init_finished.connect(self.on_init_finished)
             self.init_worker.start()
        else:
             self.text_box.append_message("system", "**System:** API Key missing.")

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)

    def set_input_enabled(self, enabled):
        if self.input_field:
            self.input_field.setReadOnly(not enabled)
        if self.send_btn:
            self.send_btn.setEnabled(enabled)

    def on_init_finished(self, success, message):
        if self.loader:
            self.loader.stop()

        if success:
            self.text_box.append_message("system", "*BlueBird AI Ready.*")
        else:
            self.text_box.append_message("system", f"**Error initializing:** {message}")
        
        # Always enable input so the UI is not locked
        self.set_input_enabled(True)

    def on_context_updated(self, success, message):
        if self.loader:
            self.loader.stop()

        if success:
            self.text_box.append_message("system", "*Context updated successfully.*")
        else:
            self.text_box.append_message("system", f"**Error updating context:** {message}")

    def handle_message(self, text: str):
        """Receive text from input widget and append to the chat box."""
        # Display user message
        self.text_box.append_message("user", text)
        
        # Send to AI
        if self.chatbot:
             if self.loader:
                 self.loader.start()
             self.worker = ChatWorker(self.chatbot, text)
             self.worker.response_received.connect(self.handle_ai_response)
             self.worker.start()
        else:
             self.text_box.append_message("system", "**System:** API Key missing or Chatbot not initialized.")

    def handle_ai_response(self, response):
        if self.loader:
            self.loader.stop()

        if "error" in response:
             self.text_box.append_message("system", f"**Error:** {response['error']}")
        else:
             self.text_box.append_message("model", response['text'])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'load_transcript') and self.load_transcript:
            # Position at top right with 10px margin
            self.load_transcript.move(self.width() - self.load_transcript.width() - 22, 22)
            self.load_transcript.raise_()
        
        if hasattr(self, 'loader') and self.loader:
            # Center in text box area
            tb_geom = self.text_box.geometry()
            lx = tb_geom.x() + (tb_geom.width() - self.loader.width()) // 2
            ly = tb_geom.y() + (tb_geom.height() - self.loader.height()) // 2
            self.loader.move(lx, ly)
            self.loader.raise_()

    def open_file_picker(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Transcript", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            if self.chatbot:
                self.text_box.append_message("system", f"*Loading context from: {os.path.basename(file_name)}...*")
                if self.loader:
                    self.loader.start()
                
                self.reinit_worker = ContextUpdateWorker(self.chatbot, file_name)
                self.reinit_worker.update_finished.connect(self.on_context_updated)
                self.reinit_worker.start()
            else:
                 self.text_box.append_message("system", "**System:** Chatbot not initialized.")

    def build_layout(self):
        layout = QVBoxLayout(self)

        self.text_box = TextBoxAI()

        user_input_layout = QHBoxLayout()

        self.input_field = InputBlueBird(self.text_box)
        self.input_field.message_sent.connect(self.handle_message)

        self.send_btn = MainUI.button("assets/send_black.png", size=(63, 63))
        self.send_btn.clicked.connect(self.input_field.send_message)

        user_input_layout.addWidget(self.input_field)
        user_input_layout.addWidget(self.send_btn)

        layout.addWidget(self.text_box, 9)
        layout.addLayout(user_input_layout, 1)

        # Floating button
        self.load_transcript = MainUI.button("assets/load_transcript.png", size=(40, 40))
        self.load_transcript.clicked.connect(self.open_file_picker)
        self.load_transcript.setParent(self)

        # Loading Spinner (Floating)
        self.loader = LoadingCircle(self)


class VolumeButton(ImageButton):
    interaction_start = Signal()
    interaction_move = Signal(QPoint)
    interaction_end = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.interaction_start.emit()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # We want to track movement even if it didn't start as a "hover"
        if event.buttons() & Qt.LeftButton:
            self.interaction_move.emit(event.globalPosition().toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.interaction_end.emit()
        super().mouseReleaseEvent(event)


class VolumePopup(QWidget):
    volume_changed = Signal(float)
    closed = Signal()

    def __init__(self, parent=None, current_volume=1.0):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(60, 200)

        self.slider = QSlider(Qt.Vertical, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(int(current_volume * 100))
        self.slider.valueChanged.connect(self._on_value_changed)

        self.slider.setStyleSheet("""
            QSlider::groove:vertical {
                background: #2A2A2A;
                width: 8px;
                border-radius: 4px;
                margin: 0px 10px;
            }
            QSlider::handle:vertical {
                background: #6A1B9A;
                height: 18px;
                margin: 0 -5px;
                border-radius: 9px;
            }
            QSlider::add-page:vertical {
                background: #6A1B9A;
                border-radius: 4px;
                margin: 0px 10px;
            }
            QSlider::sub-page:vertical {
                background: #2A2A2A;
                border-radius: 4px;
                margin: 0px 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.addWidget(self.slider)

        self.setStyleSheet("""
            VolumePopup {
                background-color: #1E1E1E;
                border: 1px solid #3A3A3A;
                border-radius: 10px;
            }
        """)

    def _on_value_changed(self, value):
        self.volume_changed.emit(value / 100.0)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class MainUI(QWidget):
    transcript_ready = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Testing Site")
        self.move(2500, 70)
        self.resize(721, 487)

        # button references
        self._play_btn = None

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)

        ui = self.build_main_layout()
        self.root.addWidget(ui)

        # managed mem
        self.man_mem = ManagedMem()

        # music player
        self._player = None
        self._paused = False
        self._currently_playing = "deep_purple_smoke_on_the_water.wav"
        self._current_volume = 0.8  # Default volume 80%

        # Transcription Manager
        self.transcription_manager = None
        self.transcript_line = 0
        
        # mood selection
        self.mood_map = None
        mood_data_path = resource_path("mood_readers/data/mood_playlists_organized.json")
        with open(mood_data_path, 'r', encoding='utf-8') as f:
            self.mood_map = json.load(f)

        # childrens windows/menus
        # transcript window
        self._transcript_win = TranscriptWindow(parent=self)
        # Fix: Don't destroy the window reference on close, just update state
        self._transcript_win.closed.connect(lambda: setattr(self, "_show_transcript_window", False))
        self._show_transcript_window = False

        # transcript segments
        self._current_session_segments = []
        self._current_session = f"SESSION [{self.man_mem.timestamp_helper()}]"

        # Route transcript data to MainUI handler
        self.transcript_ready.connect(self.handle_transcript_data)

        self._bluebird_chat = None
        self._settings_menu = None
        self._meet_type = None
        self._volume_popup = None

        # API Utils / Transcription
        api_key = self.load_api_key()
        if not api_key:
            print("Missing API Key, TranscriptionManager not initialized")
        else:
            self.transcription_manager = TranscriptionManager(api_key, chunk_seconds=T_CHUNK)
            self.transcription_manager.set_callback(self.transcript_ready.emit)

    def basic_music_play(self, music_path):
        # Resolve path relative to project root if needed
        clean_path = music_path
        if clean_path.startswith("./"):
             clean_path = clean_path[2:]
        
        # Try resolving using resource_path (handles frozen and dev)
        real_path = Path(resource_path(clean_path))
        if not real_path.exists():
             # Try assuming it is in ui_ux_team/prototype_r
             real_path = Path(resource_path(os.path.join("ui_ux_team/prototype_r", clean_path)))

        if not real_path.exists():
             print(f"Music file not found: {real_path}")
             return

        # If already playing this track, ensure it is playing
        if self._player and self._currently_playing == music_path and self._player.is_playing():
             return

        if self._player:
            self._player.stop()
        
        self._currently_playing = music_path
        self._play_btn.set_image("assets/pause.png")
        self._player = MiniaudioPlayer(str(real_path))
        self._player.set_volume(self._current_volume)  # Apply current volume
        self._player.start()

        print(f"Playing Music: {self._currently_playing}")

    def handle_transcript_data(self, data: dict):
        """
        Slot to handle the raw transcription data dictionary.
        Distributes data to various UI components.
        """
        # 1. Update Transcript Window
        text = TranscriptionManager.format_transcript_text(data)
        if text:
            # We must ensure the window exists/is receiving updates
            self._transcript_win.add_transcript_segment(text)
            self._save_translation_progressive(data)
            self._save_transcript_progressive(data)

        mood_mapper_key = {
            "positive": "😊 positive", 
            "neutral": "😐 neutral", 
            "tense": "😠 tense",
            "unfocused":"😴 unfocused", 
            "collaborative": "🤝 collaborative", 
            "creative": "💡 creative", 
            "unproductive": "📉 unproductive",
            "melancholic": "😢 melancholic",
            "nostalgic": "😢 nostalgic",
            "sad": "😢 sad",
        }

        mood_mapper_display = {
            "positive": "😊 Positive", 
            "neutral": "😐 Neutral", 
            "tense": "😠 Tense",
            "unfocused":"😴 Unfocused", 
            "collaborative": "🤝 Collaborative", 
            "creative": "💡 Creative", 
            "unproductive": "📉 Unproductive",
            "melancholic": "😢 Melancholic",
            "nostalgic": "😢 Nostalgic",
            "sad": "😢 Sad",
        }

        # 2. Update Mood Marque
        mood = data.get("emotion")
        if mood:
            print(f"Received mood update: {mood}")
            if mood in mood_mapper_display:
                self.mood_tag.hold_ms = 100_000
                self.mood_tag.set_queue([mood_mapper_display[mood]])
                self.float_mood(mood_mapper_display[mood])

            # 3. Play Music based on current Mood (Simple)
            # Check last mood to prevent skipping on every segment
            last_mood = getattr(self, "_last_mood", None)

            if mood != last_mood:
                self._last_mood = mood
                music_path = None

                if mood in mood_mapper_key:
                    music_data = self.mood_map[mood_mapper_key[mood]]
                    if music_data:
                        music_path = random.choice(music_data)

                # If no specific mood music found, or mood not in key, fallback if nothing playing
                if not music_path and (self._player is None or not self._player.is_playing()):
                     music_path = "ui_ux_team/prototype_r/deep_purple_smoke_on_the_water.wav"

                if music_path:
                    self.basic_music_play(music_path)

    def _save_transcript_progressive(self, data: dict):
        """Temporary method to save transcript text progressively to a file."""
        transcript_text = data.get("text")
        if not transcript_text:
            return
        if not self.transcript_line:
            self.transcript_line = 0

        try:
            # Create transcripts subfolder
            save_dir = Path(__file__).parent / "transcripts"
            save_dir.mkdir(exist_ok=True)

            # Use session name for filename (sanitize if needed, but SESSION [...] is mostly okay for simple use)
            filename = f"{self._current_session.replace(' ', '_').replace('[', '').replace(']', '').replace(':', '-').replace('+', '')}.txt"
            file_path = save_dir / filename

            start_sec = self.transcript_line * T_CHUNK
            end_sec = start_sec + T_CHUNK
            time_chunk = f"{self.seconds_to_hms(start_sec)} - {self.seconds_to_hms(end_sec)}"
            self.transcript_line += 1

            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"[{time_chunk}]\n{transcript_text}\n\n")

        except Exception as e:
            print(f"Failed to save progressive transcript: {e}")

    def _save_translation_progressive(self, data: dict):
        """Temporary method to save translated transcript text progressively to a file."""
        translation_text = data.get("translation")
        if not translation_text:
            return

        try:
            # Create transcripts_translated subfolder
            save_dir = Path(__file__).parent / "transcripts_translated"
            save_dir.mkdir(exist_ok=True)

            # Use session name for filename
            filename = f"{self._current_session.replace(' ', '_').replace('[', '').replace(']', '').replace(':', '-').replace('+', '')}_translated.txt"
            file_path = save_dir / filename

            start_sec = self.transcript_line * T_CHUNK
            end_sec = start_sec + T_CHUNK
            time_chunk = f"{self.seconds_to_hms(start_sec)} - {self.seconds_to_hms(end_sec)}"

            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"[{time_chunk}]\n{translation_text}\n\n")

        except Exception as e:
            print(f"Failed to save progressive translation: {e}")

    @staticmethod
    def seconds_to_hms(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @staticmethod
    def load_api_key():
        # settings runs hybrid keyring then .env loadenv flow
        import settings
        # load_dotenv()
        # os.environ["AI_STUDIO_API_KEY"] = os.getenv("AI_STUDIO_API_KEY", "")
        api_key = os.getenv("AI_STUDIO_API_KEY")

        return api_key

    def _update_transcript_mem(self, new_seg=None):
        transcript_key = 'transcript_sessions'
        # TODO: ManagedMem.gettr triggers log + auto-flush, causing file writes even on read
        mem_segments = self.man_mem.gettr(transcript_key) or dict()
        if not isinstance(mem_segments, dict):
            mem_segments = dict()

        if new_seg:
            self._current_session_segments.append(new_seg)

        session = self._current_session
        segs = self._current_session_segments

        mem_segments.setdefault(session, [])
        mem_segments[session].append(segs)

        self.man_mem.settr(transcript_key, mem_segments)

    def open_transcript(self):
        if self._show_transcript_window is False:
            self._show_transcript_window = True

            x = self.x() + self.width()
            y = self.y()
            self._transcript_win.move(x + 10, y)
            self._transcript_win.resize(400, self.height())

            self._transcript_win.show()
            return

        self._transcript_win.hide()
        self._show_transcript_window = False

    def record_transcript(self):
        if not self.transcription_manager:
            print("TranscriptionManager not available (check API key)")
            return

        if not self.transcription_manager.is_recording():
            self.transcription_manager.start_recording()
            print('recording...')
        else:
            self.transcription_manager.stop_recording()
            print('recording stopped')

    def meet_type_menu(self, parent):
        if self._meet_type is None:
            self._meet_type = FloatingMenu(parent)

            global_pos = parent.mapToGlobal(parent.rect().bottomLeft())
            self._meet_type.move(global_pos.x(), global_pos.y())
            self._meet_type.show()

            # connect close event
            self._meet_type.closed.connect(
                lambda: setattr(self, "_meet_type", None)
            )

            # close handler
            self._meet_type.destroyed.connect(lambda: setattr(self, "_meet_type", None))
            return

        self._meet_type.close()
        self._meet_type = None

    def settings_menu(self):
        recording_tabs = QListWidget()
        recording_tabs.addItems([f"{x} | {(y[:30].rstrip() + '...') if len(y) > 30 else y}" 
                                 for x, y in get_display_names()])

        test_tab = QListWidget()
        test_tab.addItems(["test1", 'test2'])

        self._settings_menu = SettingsPopup({
            "Recording Sources": recording_tabs,
            "Test Tab": test_tab,
        }, parent=self)
        self._settings_menu.show_pos_size(self.pos(), self.size())

    def info_clicked(self, text="Test"):
        mood_items = [
            "😊 Positive",
            "😐 Neutral",
            "😠 Tense",
            "😴 Unfocused",
            "🤝 Collaborative",
            "💡 Creative",
            "📉 Unproductive",
        ]

        FloatingToast(self).show_message(random.choice(mood_items))

    def float_mood(self, mood: str):
        FloatingToast(self).show_message(mood)

    def build_sidebar(self):
        # depth 1
        # vertical sidebar right side
        sidebar = self.color_box(COLOR_SIDEBAR)

        layout = QVBoxLayout()
        layout.setContentsMargins(2.5, 7, 2.5, 7)
        layout.setSpacing(10)

        #sidebar buttons depth 2

        # transcript button
        transcript_button = self.button("assets/transcript_black.png", size=(60, 60))
        transcript_button.clicked.connect(self.open_transcript)
        layout.addWidget(transcript_button, alignment=Qt.AlignHCenter)

        # api connector
        api_button = self.button("assets/api_black.png", size=(50, 50))
        layout.addWidget(api_button, alignment=Qt.AlignHCenter)

        # info/dark/light theme
        info_button = self.button("assets/info.png", size=(50, 50))
        info_button.clicked.connect(self.info_clicked)
        layout.addWidget(info_button, alignment=Qt.AlignHCenter)

        meet_type = self.button("assets/meet_type_black.png", size=(50, 50))
        meet_type.clicked.connect(lambda :self.meet_type_menu(meet_type))
        layout.addWidget(meet_type, alignment=Qt.AlignHCenter)

        layout.addStretch(1)    # middle stretch

        # user
        user_button = self.button("assets/user_black.png", size=(60, 60))
        layout.addWidget(user_button, alignment=Qt.AlignHCenter)

        # settings
        settings_button = self.button("assets/settings_black.png", size=(50, 50))
        settings_button.clicked.connect(self.settings_menu)
        layout.addWidget(settings_button, alignment=Qt.AlignHCenter)

        # bottom_boxes = [self.image_box("") for _ in range(1)]
        # for b in bottom_boxes:
        #     b.setMinimumSize(50, 50)
        #     b.setMaximumSize(50, 50)
        #     layout.addWidget(b, alignment=Qt.AlignHCenter)

        sidebar.setMinimumWidth(70)
        sidebar.setMaximumWidth(70)
        sidebar.setLayout(layout)
        return sidebar
    
    def build_cover_images(self):
        # depth 2
        covers = self.color_box(COLOR_COVERS_BG)
        covers.setContentsMargins(0, 0, 0, 0)
        covers.setMinimumSize(500, 200)

        covers_layout = QHBoxLayout()
        covers_images = [self.image_box("") for _ in range(3)]
        for i, b in enumerate(covers_images):
            b.setMinimumSize(50, 50)
            if i in [0, 2]:
                b.setMaximumSize(120, 120)
            if i == 1:
                b.setMaximumSize(180, 180)

            covers_layout.addWidget(b)
        covers.setLayout(covers_layout)

        return covers

    def build_main_timeline(self):
        timeline_box = self.color_box(COLOR_TIMELINE_BG)
        timeline_box.setFixedHeight(15)

        return timeline_box

    def stop_click(self):
        self._player.stop()
        self._player.close()

        self._player = None
        print("Stopping")

    def play_click(self, file_path=None):
        if file_path is None:
            file_path = self._currently_playing

        if self._player is None:
            self._play_btn.set_image("assets/pause.png")
            
            clean_path = file_path
            if clean_path.startswith("./"): clean_path = clean_path[2:]
            
            # Try resolving using resource_path
            real_path = Path(resource_path(clean_path))
            if not real_path.exists():
                 # Try assuming it is in ui_ux_team/prototype_r
                 real_path = Path(resource_path(os.path.join("ui_ux_team/prototype_r", clean_path)))

            self._player = MiniaudioPlayer(str(real_path))
            self._player.set_volume(self._current_volume)  # Apply current volume
            self._player.start()

            print("Playing Music...")
        else:
            if self._player.paused:
                self._player.start()
                self._play_btn.set_image("assets/pause.png")

                print("Resuming Music...")
            else:
                self._player.pause()
                self._play_btn.set_image("assets/play.png")

                print("Pausing Music...")
    
    def build_main_controls(self):
        # depth 3
        control_layer = QHBoxLayout()
        control_layer.setContentsMargins(10, 10, 10, 10)
        # control_layer.setSpacing(5)
        controls = self.color_box(COLOR_CONTROLS_BG)
        controls.setMaximumHeight(100)
        controls.setLayout(control_layer)

        prev = self.button("assets/prev.png", size=(35, 35))
        self._play_btn = self.button("assets/play.png", size=(80, 80))
        self._play_btn.clicked.connect(self.play_click)
        next = self.button("assets/next.png", size=(35, 35))

        control_layer.addWidget(prev)
        # control_layer.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        control_layer.addWidget(self._play_btn)
        # control_layer.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        control_layer.addWidget(next)

        return controls
    
    def open_bluebird_chat(self):
        if self._bluebird_chat is None:
            # Get current transcript text
            transcript_text = self._transcript_win.text_box.toPlainText()
            api_key = self.load_api_key()

            self._bluebird_chat = BlueBirdChat(api_key=api_key, initial_transcript=transcript_text)

            self._bluebird_chat.closed.connect(
                lambda: setattr(self, "_bluebird_chat", None))

            x = self.x() - 400
            y = self.y()
            self._bluebird_chat.move(x - 10, y)
            self._bluebird_chat.resize(400, self.height())

            self._bluebird_chat.show()
            return

        self._bluebird_chat.close()
        self._bluebird_chat = None

    def build_blue_bird(self):
        # depth 3
        blue_bird = self.button("assets/blue_bird.png", size=(70, 70))
        blue_bird.clicked.connect(self.open_bluebird_chat)
        # blue_bird.setFixedSize(70, 70)

        right_spacer = QWidget()
        right_spacer.setFixedSize(70, 70)

        return blue_bird, right_spacer

    def on_volume_start(self):
        button = self.sender()
        if not button:
            return

        current_vol = 1.0
        if self._player:
            current_vol = self._player._volume

        if not self._volume_popup:
            # Parent to button for easier lifecycle management and relative positioning
            self._volume_popup = VolumePopup(parent=button, current_volume=current_vol)
            self._volume_popup.volume_changed.connect(self.set_volume)
            self._volume_popup.closed.connect(lambda: setattr(self, "_volume_popup", None))
        
        # Auto position logic: Center above the button
        self._volume_popup.show()
        
        popup_w = self._volume_popup.width()
        popup_h = self._volume_popup.height()
        
        # Offset calculation (relative to button's top-left)
        local_offset = QPoint((button.width() - popup_w) // 2 + button.width() // 2, -popup_h - 10)
        
        # Move the popup window to the global position corresponding to the local offset
        self._volume_popup.move(button.mapToGlobal(local_offset))

    def on_volume_move(self, global_pos):
        if self._volume_popup and self._volume_popup.isVisible():
            slider = self._volume_popup.slider
            # Map global mouse pos to slider's coordinate system
            local_pos = slider.mapFromGlobal(global_pos)
            
            # Vertical slider: 0 is top, height is bottom visually in widget coords
            # But we want 100% volume at top, 0% at bottom.
            h = slider.height()
            y = local_pos.y()
            
            # Clamp y
            y = max(0, min(h, y))
            
            # Calculate value ratio (top=1.0, bottom=0.0)
            if h > 0:
                ratio = 1.0 - (y / h)
            else:
                ratio = 0.0
            
            val = int(ratio * slider.maximum())
            slider.setValue(val)

    def on_volume_end(self):
        if self._volume_popup:
            self._volume_popup.close()
            self._volume_popup = None

    def set_volume(self, volume):
        if self._player:
            self._player.set_volume(volume)
        else:
            # TODO: Store volume for when player starts
            pass

    def build_main_bottom_panel(self):
        # depth 2
        bottom_con = self.color_box(COLOR_BOTTOM_BG)
        bottom_con_layout = QHBoxLayout()
        bottom_con.setLayout(bottom_con_layout)

        blue_bird, _ = self.build_blue_bird()

        # Volume Control Button
        volume_control = VolumeButton(
            path=MainUI.build_path("assets/volume_button.png"), 
            size=(42, 42), 
            fallback=IMAGE_NOT_FOUND
        )
        volume_control.interaction_start.connect(self.on_volume_start)
        volume_control.interaction_move.connect(self.on_volume_move)
        volume_control.interaction_end.connect(self.on_volume_end)

        right_spacer = QWidget()
        right_spacer.setFixedSize(70, 70)
        right_spacer_layout = QHBoxLayout(right_spacer)
        right_spacer_layout.setContentsMargins(5, 5, 5, 5)

        right_spacer_layout.addWidget(volume_control, alignment=Qt.AlignTop | Qt.AlignRight)

        controls = self.build_main_controls()

        bottom_con_layout.addWidget(blue_bird, alignment=Qt.AlignBottom)
        bottom_con_layout.addWidget(controls, alignment=Qt.AlignHCenter | Qt.AlignTop)
        bottom_con_layout.addWidget(right_spacer, alignment=Qt.AlignTop)


        return bottom_con

    def build_main_panel(self):
        # depth 1
        l_main = QVBoxLayout()
        l_main.setContentsMargins(0, 0, 0, 0)
        l_main.setSpacing(10)

        mood_items = [
            "😊 Positive",
            "😐 Neutral",
            "😠 Tense",
            "😴 Unfocused",
            "🤝 Collaborative",
            "💡 Creative",
            "📉 Unproductive",
        ]

        self.mood_tag = QueuedMarqueeLabel(
            mood_items,
            hold_ms=3200,
            fade_ms=220,
            step=1,
            interval_ms=25,
            gap=60,
        )
        font = QFont()
        font.setPointSize(20)
        self.mood_tag.label.setFont(font)
        self.mood_tag.setMaximumHeight(30)

        covers = self.build_cover_images()
        timeline_box = self.build_main_timeline()
        bottom_panel = self.build_main_bottom_panel()

        l_main.addWidget(self.mood_tag)
        l_main.addWidget(covers, alignment=Qt.AlignCenter | Qt.AlignBottom)
        l_main.addWidget(timeline_box)
        l_main.addWidget(bottom_panel)

        orange = self.color_box(COLOR_BG_MAIN)
        orange.setLayout(l_main)

        return orange
    
    @staticmethod
    def color_box(color):
        box = QFrame()
        box.setAutoFillBackground(True)
        pal = box.palette()
        pal.setColor(QPalette.Window, QColor(color))
        box.setPalette(pal)
        return box
    
    @staticmethod
    def build_path(file_path):
        # Use global BASE which is resource_path aware
        return os.path.join(BASE, file_path)
    
    @staticmethod
    def button(file_path="", size=(40, 40)):
        button = ImageButton(
            path=MainUI.build_path(file_path), 
            size=size, 
            fallback=IMAGE_NOT_FOUND
            )

        return button
    
    @staticmethod
    def image_box(file_path):
        label = QLabel()
        label.setScaledContents(True)
        label.setMinimumSize(50, 50)

        pix = QPixmap(MainUI.build_path(file_path))

        if pix.isNull():
            label.setPixmap(QPixmap(IMAGE_NOT_FOUND))
        else:
            label.setPixmap(pix)
        
        return label

    def build_main_layout(self):
        # depth 0
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        main_panel = self.build_main_panel()
        sidebar = self.build_sidebar()

        h.addWidget(main_panel, 4)
        h.addWidget(sidebar, 1)

        h_widget = QWidget()
        h_widget.setLayout(h)
        return h_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainUI()

    # makes it not steal focus
    # window.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)

    window.show()

    sys.exit(app.exec())
