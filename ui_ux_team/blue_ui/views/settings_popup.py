from PySide6.QtCore import Qt, QSize, QPoint, Signal
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QFrame,
)
from PySide6.QtGui import QFont


class PopupTitleBar(QWidget):
    def __init__(self, title="Settings", parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self._drag_pos = None

        self.setStyleSheet(
            """
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
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        self.label = QLabel(title)
        self.close_btn = QPushButton("✕")
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

        self.setStyleSheet(
            """
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
            """
        )
        self.setObjectName("SettingsPopup")

        self.margin = margin
        self.setMinimumSize(520, 330)
        self.categories = categories or {}

        self.list = QListWidget()
        self.list.setFixedWidth(160)
        self.list.setSpacing(4)
        self.list.setStyleSheet(
            """
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
            """
        )

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(
            """
            QStackedWidget {
                background: #2f2f2f;
                border-left: 1px solid #1f1f1f;
                border-bottom-right-radius: 8px;
            }
            """
        )

        for name, widget in self.categories.items():
            widget.setFocusPolicy(Qt.NoFocus)
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


class FloatingMenu(QWidget):
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PopupMenu")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        labels = [QLabel("💼 Work"), QLabel("🎉 Party"), QLabel("🎮 Gaming")]

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

        self.setStyleSheet(
            """
            QWidget#PopupInner {
                background-color: rgba(15, 15, 15, 235);
                border-radius: 14px;
                padding: 8px;
            }

            QLabel {
                background-color: rgba(40, 40, 40, 200);
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 10px;
                font-size: 20px;
                padding: 10px 14px;
                color: #F3F3F3;
            }

            QLabel:hover {
                background-color: rgba(50, 50, 50, 220);
                border: 1px solid rgba(255, 255, 255, 45);
            }
            """
        )

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)
