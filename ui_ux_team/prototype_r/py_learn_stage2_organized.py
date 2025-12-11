import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame
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
        self.root.addWidget(ui)

    # -----------------------------------------------------------
    # BUILD LAYOUT SECTIONS
    # -----------------------------------------------------------

    def build_sidebar(self):
        """Build the right sidebar (purple area with gray/red boxes)."""
        sidebar = color_box("purple")

        layout = QVBoxLayout()
        layout.setContentsMargins(3, 7, 3, 7)
        layout.setSpacing(10)

        # top gray boxes
        for _ in range(3):
            b = self.box(50, 50, "gray")
            layout.addWidget(b, alignment=Qt.AlignHCenter)

        layout.addStretch(1)

        # bottom red boxes
        for _ in range(2):
            b = self.box(50, 50, "red")
            layout.addWidget(b, alignment=Qt.AlignHCenter)

        sidebar.setMinimumWidth(55)
        sidebar.setMaximumWidth(70)
        sidebar.setLayout(layout)
        return sidebar

    def build_main_panel(self):
        """Build the left panel with cyan cover + pink controls."""
        panel = color_box("orange")

        v = QVBoxLayout()
        v.setSpacing(50)

        # main cyan area
        covers = color_box("cyan")
        v.addWidget(covers, 100)

        v.addStretch(1)

        # bottom pink controls area
        controls = color_box("pink")
        controls.setFixedSize(200, 70)

        control_row = QHBoxLayout()
        for _ in range(3):
            control_row.addWidget(self.box(50, 50, "purple"),
                                  alignment=Qt.AlignHCenter)

        controls.setLayout(control_row)
        v.addWidget(controls, alignment=Qt.AlignHCenter)

        panel.setLayout(v)
        return panel

    # -----------------------------------------------------------
    # HELPERS
    # -----------------------------------------------------------

    def box(self, w, h, color):
        """Create a consistently-sized colored box."""
        b = color_box(color)
        b.setFixedSize(w, h)
        return b

    # -----------------------------------------------------------
    # TOP-LEVEL LAYOUT
    # -----------------------------------------------------------

    def build_main_layout(self):
        """Horizontal layout: [orange panel | purple sidebar]."""
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        main_panel = self.build_main_panel()
        sidebar = self.build_sidebar()

        h.addWidget(main_panel, 4)
        h.addWidget(sidebar, 1)

        wrapper = QWidget()
        wrapper.setLayout(h)
        return wrapper


# -----------------------------------------------------------
# RUN
# -----------------------------------------------------------
app = QApplication(sys.argv)
window = MainUI()

# makes it not steal focus
window.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)

window.show()
sys.exit(app.exec())
