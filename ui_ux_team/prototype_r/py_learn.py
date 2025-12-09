import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QLabel
)
from PySide6.QtGui import (
    QPalette, QColor, QPixmap, QCursor, QTransform, 
    QPainter, QFont, QPainterPath, QRegion
)
from PySide6.QtWidgets import (
    QGraphicsColorizeEffect, QSizePolicy, QSpacerItem, 
    QTextBrowser, QPlainTextEdit, QTextEdit
)
from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QEasingCurve, 
    QRect, Property, QRect
)

from pathlib import Path
# Ensure project root is importable when running the script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from architects.helpers.music_player import play_music

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

BASE = os.path.dirname(__file__)
IMAGE_NOT_FOUND = os.path.join(BASE, "assets/image_not_found_white.png")


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


class TextBoxAI(QPlainTextEdit):
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

        self.appendPlainText("SPEAKER 1: Hello")
        self.appendPlainText("SPEAKER 2: Hi there.")


class TranscriptWindow(QWidget):
    closed = Signal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcript")

        layout = QVBoxLayout(self)

        search_bar = SearchBar()
        text_box = TextBox()

        layout.addWidget(search_bar, 1)
        layout.addWidget(text_box, 9)
    
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
        if e.key() == Qt.Key_Return and not e.modifiers():
            self.send_message()
            return
        return super().keyPressEvent(e)

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
        self.setPlaceholderText("Type a message to BlueBird AI")

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


class BlueBirdChat(QWidget):
    closed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BlueBird AI")

        self.text_box = None
        self.root_layout = self.build_layout()

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)

    def handle_message(self, text: str):
        """Receive text from input widget and append to the chat box."""
        print("SENT:", text)
        self.text_box.appendPlainText(text)

    def build_layout(self):
        layout = QVBoxLayout(self)

        self.text_box = TextBoxAI()

        user_input_layout = QHBoxLayout()

        user_input = InputBlueBird(self.text_box)
        user_input.message_sent.connect(self.handle_message)

        send_button = MainUI.button("assets/send_black.png", size=(63, 63))
        send_button.clicked.connect(user_input.send_message)

        user_input_layout.addWidget(user_input)
        user_input_layout.addWidget(send_button)

        layout.addWidget(self.text_box, 9)
        layout.addLayout(user_input_layout, 1)


class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Testing Site")
        self.move(3330, 30)
        self.resize(721, 487)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)

        ui = self.build_main_layout()
        self.root.addWidget(ui)

        # music player
        self._payer = None

        # extra side windows
        self._meet_type = None
        self._transcript_win = None
        self._bluebird_chat = None

    def open_transcript(self):
        if self._transcript_win is None:
            self._transcript_win = TranscriptWindow()

            # connect x to MainUi attr
            self._transcript_win.closed.connect(
                lambda: setattr(self, "_transcript_win", None)
            )

            x = self.x() + self.width()
            y = self.y()
            self._transcript_win.move(x + 10, y)
            self._transcript_win.resize(400, self.height())

            self._transcript_win.show()
            return

        self._transcript_win.close()
        self._transcript_win = None

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

    def build_sidebar(self):
        # depth 1
        # vertical sidebar right side
        sidebar = self.color_box(COLOR_SIDEBAR)

        layout = QVBoxLayout()
        layout.setContentsMargins(2.5, 7, 2.5, 7)
        layout.setSpacing(10)

        #sidebar buttons depth 2

        # user
        user_button = self.button("assets/user_black.png", size=(60, 60))
        layout.addWidget(user_button, alignment=Qt.AlignHCenter)

        # api connector
        api_button = self.button("assets/api_black.png", size=(50, 50))
        layout.addWidget(api_button, alignment=Qt.AlignHCenter)

        # info/dark/light theme
        info_button = self.button("assets/info.png", size=(50, 50))
        layout.addWidget(info_button, alignment=Qt.AlignHCenter)

        meet_type = self.button("assets/meet_type_black.png", size=(50, 50))
        meet_type.clicked.connect(lambda :self.meet_type_menu(meet_type))
        layout.addWidget(meet_type, alignment=Qt.AlignHCenter)

        layout.addStretch(1)    # middle stretch

        # transcript button
        transcript_button = self.button("assets/transcript_black.png", size=(60, 60))
        transcript_button.clicked.connect(self.open_transcript)
        layout.addWidget(transcript_button, alignment=Qt.AlignHCenter)

        # settings
        settings_button = self.button("assets/settings_black.png", size=(50, 50))
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
    
    def play_click(self, file_path="deep_purple_smoke_on_the_water.wav"):
        self._player = play_music(MainUI.build_path(file_path))
        print("Playing Music")
    
    def build_main_controls(self):
        # depth 3
        control_layer = QHBoxLayout()
        control_layer.setContentsMargins(10, 10, 10, 10)
        # control_layer.setSpacing(5)
        controls = self.color_box(COLOR_CONTROLS_BG)
        controls.setMaximumHeight(100)
        controls.setLayout(control_layer)

        prev = self.button("assets/prev.png", size=(35, 35))
        play = self.button("assets/play.png", size=(80, 80))
        play.clicked.connect(self.play_click)
        next = self.button("assets/next.png", size=(35, 35))

        control_layer.addWidget(prev)
        # control_layer.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        control_layer.addWidget(play)
        # control_layer.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        control_layer.addWidget(next)

        return controls
    
    def open_bluebird_chat(self):
        print("Blue Bird")
        if self._bluebird_chat is None:
            self._bluebird_chat = BlueBirdChat()

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
    
    def build_main_bottom_panel(self):
        # depth 2
        bottom_con = self.color_box(COLOR_BOTTOM_BG)
        bottom_con_layout = QHBoxLayout()
        bottom_con.setLayout(bottom_con_layout)

        blue_bird, right_spacer = self.build_blue_bird()

        controls = self.build_main_controls()

        bottom_con_layout.addWidget(blue_bird, alignment=Qt.AlignBottom)
        bottom_con_layout.addWidget(controls, alignment=Qt.AlignHCenter | Qt.AlignTop)
        bottom_con_layout.addWidget(right_spacer)

        return bottom_con
    
    def build_main_panel(self):
        # depth 1
        l_main = QVBoxLayout()
        # l_main.setContentsMargins(0, 0, 0, 0)
        l_main.setSpacing(10)

        covers = self.build_cover_images()
        timeline_box = self.build_main_timeline()
        bottom_panel = self.build_main_bottom_panel()

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
        BASE = os.path.dirname(__file__)
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
    window.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)

    window.show()

    sys.exit(app.exec())
