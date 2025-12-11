import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QLabel
)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

def color_box(color):
    box = QFrame()
    box.setAutoFillBackground(True)
    pal = box.palette()
    pal.setColor(QPalette.Window, QColor(color))
    box.setPalette(pal)
    return box


class MainUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Testing Site")
        self.move(2000, 100)
        self.resize(420, 230)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)

        ui = self.build_main_layout()

        self.setLayout(self.root)


    def build_main_layout(self):

        # vetical sidebar depth 1
        purple = color_box("purple")

        sidebar_r = QVBoxLayout()
        sidebar_r.setContentsMargins(2.5, 7, 2.5, 7)
        sidebar_r.setSpacing(10)

        # sidebar box widgets depth 2
        top_boxes = [color_box("gray") for _ in range(3)]
        for b in top_boxes:
            b.setMinimumSize(50, 50)
            b.setMaximumSize(50, 50)
            sidebar_r.addWidget(b, alignment=Qt.AlignHCenter)

        sidebar_r.addStretch(1)        # bottom stretch

        bottom_boxes = [color_box("red") for _ in range(2)]
        for b in bottom_boxes:
            b.setMinimumSize(50, 50)
            b.setMaximumSize(50, 50)
            sidebar_r.addWidget(b, alignment=Qt.AlignHCenter)


        purple.setMinimumWidth(55)
        purple.setMaximumWidth(70)
        purple.setLayout(sidebar_r)

        # main screen depth 1
        l_main = QVBoxLayout()
        # l_main.setContentsMargins(0, 0, 0, 0)
        l_main.setSpacing(50)

        # controls + main center depth 2
        covers = color_box("cyan")
        l_main.addWidget(covers, 100)

        l_main.addStretch(1)

        control_layer = QHBoxLayout()
        controls = color_box("pink")
        controls.setMaximumSize(200, 70)
        controls.setMinimumSize(200, 70)
        controls.setLayout(control_layer)

        # actual control widgets depth 3
        con_widgets = [color_box("purple") for _ in range(3)]
        for b in con_widgets:
            b.setMinimumSize(50, 50)
            b.setMaximumSize(50, 50)
            control_layer.addWidget(b, alignment=Qt.AlignHCenter)

        l_main.addWidget(controls, alignment=Qt.AlignHCenter)

        orange = color_box("orange")
        orange.setLayout(l_main)

        # center piece sidebar depth 2
        c_piece = color_box("cyan")


        # horizontal depth 0
        hbox = QHBoxLayout()
        hbox.addWidget(orange, 4)
        hbox.addWidget(purple, 1)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)


        h_widget = QWidget()
        h_widget.setLayout(hbox)

        self.root.addWidget(h_widget)
        self.root.setContentsMargins(0, 0, 0, 0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainUI()

    # makes it not steal focus
    window.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)

    window.show()
    sys.exit(app.exec())