import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QLabel
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QSizePolicy, QSpacerItem
from PySide6.QtCore import Qt

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

def color_box(color):
    box = QFrame()
    box.setAutoFillBackground(True)
    pal = box.palette()
    pal.setColor(QPalette.Window, QColor(color))
    box.setPalette(pal)
    return box

app = QApplication(sys.argv)

root = QVBoxLayout()

# vetical sidebar depth 1
# purple = color_box("purple")
purple = color_box(COLOR_SIDEBAR)

sidebar_r = QVBoxLayout()
sidebar_r.setContentsMargins(2.5, 7, 2.5, 7)
sidebar_r.setSpacing(10)

# sidebar box widgets depth 2
top_boxes = [color_box(COLOR_SIDEBAR_TOP) for _ in range(3)]
for b in top_boxes:
    b.setMinimumSize(50, 50)
    b.setMaximumSize(50, 50)
    sidebar_r.addWidget(b, alignment=Qt.AlignHCenter)

sidebar_r.addStretch(1)        # bottom stretch

bottom_boxes = [color_box(COLOR_SIDEBAR_BOTTOM) for _ in range(2)]
for b in bottom_boxes:
    b.setMinimumSize(50, 50)
    b.setMaximumSize(50, 50)
    sidebar_r.addWidget(b, alignment=Qt.AlignHCenter)


purple.setMinimumWidth(70)
purple.setMaximumWidth(70)
purple.setLayout(sidebar_r)

# main screen depth 1
l_main = QVBoxLayout()
# l_main.setContentsMargins(0, 0, 0, 0)
l_main.setSpacing(10)

# controls + main center depth 2
covers = color_box(COLOR_COVERS_BG)
covers.setContentsMargins(0, 0, 0, 0)
covers.setMinimumSize(500, 200)

covers_layout = QHBoxLayout()
covers_images = [color_box(COLOR_COVER_IMAGE) for _ in range(3)]
for i, b in enumerate(covers_images):
    b.setMinimumSize(50, 50)
    if i in [0, 2]:
        b.setMaximumSize(120, 120)
    if i == 1:
        b.setMaximumSize(180, 180)

    covers_layout.addWidget(b)
covers.setLayout(covers_layout)

l_main.addWidget(covers, alignment=Qt.AlignCenter | Qt.AlignBottom)

control_layer = QHBoxLayout()
control_layer.setContentsMargins(10, 10, 10, 10)
# control_layer.setSpacing(5)
controls = color_box(COLOR_CONTROLS_BG)
controls.setMaximumHeight(75)
controls.setLayout(control_layer)

# actual control widgets depth 3
con_widgets = [color_box(COLOR_CONTROL_BTN) for _ in range(3)]
for i, b in enumerate(con_widgets):
    if i in [0, 2]:
        b.setFixedSize(40, 40)
    if i == 1:
        b.setFixedSize(55, 55)

    control_layer.addWidget(b, alignment=Qt.AlignHCenter)


orange = color_box(COLOR_BG_MAIN)
orange.setLayout(l_main)

bottom_con = color_box(COLOR_BOTTOM_BG)
bottom_con_layout = QHBoxLayout()
bottom_con.setLayout(bottom_con_layout)
blue_bird = color_box(COLOR_BLUE_BIRD)
blue_bird.setFixedSize(70, 70)

right_spacer = QWidget()
right_spacer.setFixedSize(70, 70)

bottom_con_layout.addWidget(blue_bird, alignment=Qt.AlignBottom)
bottom_con_layout.addWidget(controls, alignment=Qt.AlignHCenter | Qt.AlignTop)
bottom_con_layout.addWidget(right_spacer)

timeline_box = color_box(COLOR_TIMELINE_BG)
timeline_box.setFixedHeight(15)

l_main.addWidget(timeline_box)
l_main.addWidget(bottom_con)

# horizontal depth 0
hbox = QHBoxLayout()
hbox.addWidget(orange, 4)
hbox.addWidget(purple, 1)
hbox.setContentsMargins(0, 0, 0, 0)
hbox.setSpacing(0)


h_widget = QWidget()
h_widget.setLayout(hbox)

root.addWidget(h_widget)
root.setContentsMargins(0, 0, 0, 0)

window = QWidget()
window.setWindowTitle("Testing Site")
window.move(1940, 30)
window.resize(721, 487)

window.setLayout(root)

# makes it not steal focus
window.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)

window.show()

sys.exit(app.exec())
