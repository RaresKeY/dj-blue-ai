from PySide6.QtCore import Qt, QSize, QPoint, Signal
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QStackedWidget, QFrame
from PySide6.QtGui import QFont


class PopupTitleBar(QWidget):
    def __init__(self, title="Settings", parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        self.label = QLabel(title)
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedWidth(28)
        layout.addWidget(self.label)
        layout.addStretch(1)
        layout.addWidget(self.close_btn)
        self.close_btn.clicked.connect(lambda: self.window().close())

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
        self.setObjectName("SettingsPopup")
        self.margin = margin
        self.setMinimumSize(520, 330)
        self.categories = categories or {}

        self.list = QListWidget()
        self.list.setFixedWidth(160)
        self.stack = QStackedWidget()

        for name, widget in self.categories.items():
            if isinstance(widget, QLabel):
                widget.setFrameStyle(QFrame.NoFrame)
                widget.setStyleSheet("background: none; border: none; color: #e0e0e0;")
            self.list.addItem(QListWidgetItem(name))
            self.stack.addWidget(widget)

        self.list.currentRowChanged.connect(self.stack.setCurrentIndex)
        if self.list.count():
            self.list.setCurrentRow(0)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(PopupTitleBar("Settings", self))

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(6, 6, 6, 6)
        content_layout.addWidget(self.list)
        content_layout.addWidget(self.stack)
        root_layout.addLayout(content_layout)

    def show_pos_size(self, parent_pos: QPoint, parent_size):
        x = parent_pos.x() + self.margin
        y = parent_pos.y() + self.margin
        w = parent_size.width() - (self.margin * 2)
        h = parent_size.height() - (self.margin * 2)
        self.setGeometry(x, y, w, h)
        self.show()


class FloatingMenu(QWidget):
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PopupMenu")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        labels = [QLabel("Work"), QLabel("Party"), QLabel("Gaming")]
        container = QWidget(self)
        container.setObjectName("PopupInner")
        layout = QVBoxLayout(container)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(container)

        font = QFont("Inter")
        for lbl in labels:
            lbl.setFont(font)
            layout.addWidget(lbl)

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)
