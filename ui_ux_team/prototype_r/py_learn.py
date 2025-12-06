import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QLabel
)
from PySide6.QtGui import QPalette, QColor, QPixmap, QCursor, QTransform, QPainter
from PySide6.QtWidgets import QGraphicsColorizeEffect, QSizePolicy, QSpacerItem
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, Property

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

    def __init__(self, path, func=None, size=(40, 40), fallback=None):
        super().__init__()
        self.setFixedSize(*size)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAlignment(Qt.AlignCenter)

        self.action = func

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
        if self.action:
            self.action()
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


class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Testing Site")
        self.move(1940, 30)
        self.resize(721, 487)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)

        ui = self.build_main_layout()
        self.root.addWidget(ui)

        # music player
        self._payer = None

    def build_sidebar(self):
        # depth 1
        # vertical sidebar right side
        sidebar = self.color_box(COLOR_SIDEBAR)

        layout = QVBoxLayout()
        layout.setContentsMargins(2.5, 7, 2.5, 7)
        layout.setSpacing(10)

        # sidebar box widgets depth 2
        top_boxes = [self.color_box(COLOR_SIDEBAR_TOP) for _ in range(3)]
        for b in top_boxes:
            b.setMinimumSize(50, 50)
            b.setMaximumSize(50, 50)
            layout.addWidget(b, alignment=Qt.AlignHCenter)

        layout.addStretch(1)        # middle stretch

        bottom_boxes = [self.image_box("") for _ in range(2)]
        for b in bottom_boxes:
            b.setMinimumSize(50, 50)
            b.setMaximumSize(50, 50)
            layout.addWidget(b, alignment=Qt.AlignHCenter)


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
        self._player = play_music(file_path)
        print("Playing Music")
    
    def build_main_controls(self):
        # depth 3
        control_layer = QHBoxLayout()
        control_layer.setContentsMargins(10, 10, 10, 10)
        # control_layer.setSpacing(5)
        controls = self.color_box(COLOR_CONTROLS_BG)
        controls.setMaximumHeight(75)
        controls.setLayout(control_layer)

        prev = self.button("assets/prev.png", size=(30, 30))
        play = self.button("assets/play.png", size=(55, 55), func=self.play_click)
        next = self.button("assets/next.png", size=(30, 30))

        # prev.setFixedSize(30, 30)
        # play.setFixedSize(55, 55)
        # next.setFixedSize(30, 30)

        control_layer.addWidget(prev)
        # control_layer.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        control_layer.addWidget(play)
        # control_layer.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        control_layer.addWidget(next)

        # # actual control widgets depth 3
        # con_widgets = [self.color_box(COLOR_CONTROL_BTN) for _ in range(3)]
        # for i, b in enumerate(con_widgets):
        #     if i in [0, 2]:
        #         b.setFixedSize(40, 40)
        #     if i == 1:
        #         b.setFixedSize(55, 55)

        #     control_layer.addWidget(b, alignment=Qt.AlignHCenter)

        return controls
    
    def blue_bird_click(self):
        print("Blue Bird")
    
    def build_blue_bird(self):
        # depth 3
        blue_bird = self.button("assets/blue_bird.png", size=(70, 70), func=self.blue_bird_click)
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
    def button(file_path, func=None, size=(40, 40)):
        button = ImageButton(path=MainUI.build_path(file_path), func=func, size=size, fallback=IMAGE_NOT_FOUND)

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
