import re

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
from ui_ux_team.blue_ui.theme import tokens

ORANGE_SELECTION = "#FF8A3D"


def _with_alpha(color: str, alpha: float) -> str:
    a = max(0.0, min(1.0, float(alpha)))
    c = (color or "").strip()
    if c.startswith("#") and len(c) in (4, 7):
        if len(c) == 4:
            r = int(c[1] * 2, 16)
            g = int(c[2] * 2, 16)
            b = int(c[3] * 2, 16)
        else:
            r = int(c[1:3], 16)
            g = int(c[3:5], 16)
            b = int(c[5:7], 16)
        return f"rgba({r}, {g}, {b}, {a:.3f})"

    match = re.match(r"rgba?\(([^)]+)\)", c)
    if match:
        parts = [p.strip() for p in match.group(1).split(",")]
        if len(parts) >= 3:
            return f"rgba({parts[0]}, {parts[1]}, {parts[2]}, {a:.3f})"
    return c


class PopupTitleBar(QWidget):
    def __init__(self, title="Settings", parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self._drag_pos = None
        self._title_text = title

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        self.label = QLabel(self._title_text)
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedWidth(28)

        layout.addWidget(self.label)
        layout.addStretch(1)
        layout.addWidget(self.close_btn)

        self.close_btn.clicked.connect(lambda: self.window().close())
        self.refresh_theme()

    def refresh_theme(self):
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {tokens.TEXT_PRIMARY};
                font-size: 17px;
                font-weight: 600;
                font-family: Inter;
                padding-left: 6px;
                padding-top: 2px;
            }}
            QPushButton {{
                background: {_with_alpha(tokens.BG_INPUT, 0.85)};
                color: {tokens.TEXT_PRIMARY};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 7px;
                padding: 4px 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: rgba(255, 138, 61, 0.16);
                color: {ORANGE_SELECTION};
                border: 1px solid rgba(255, 138, 61, 0.50);
            }}
            """
        )

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
        self.setMinimumSize(560, 350)
        self.categories = categories or {}

        self.list = QListWidget()
        self.list.setFixedWidth(190)
        self.list.setSpacing(6)
        self.stack = QStackedWidget()

        for name, widget in self.categories.items():
            widget.setFocusPolicy(Qt.NoFocus)
            widget.setAttribute(Qt.WA_NoSystemBackground, True)
            widget.setAutoFillBackground(False)

            if isinstance(widget, QLabel):
                widget.setFrameStyle(QFrame.NoFrame)
                widget.setStyleSheet(f"background: none; border: none; color: {tokens.TEXT_PRIMARY};")

            item = QListWidgetItem(name)
            item.setSizeHint(QSize(172, 40))
            self.list.addItem(item)
            self.stack.addWidget(widget)

        self.list.currentRowChanged.connect(self.stack.setCurrentIndex)
        if self.list.count():
            self.list.setCurrentRow(0)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)
        self.title_bar = PopupTitleBar("Settings", self)
        root_layout.addWidget(self.title_bar)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        content_layout.addWidget(self.list)
        content_layout.addWidget(self.stack)
        root_layout.addLayout(content_layout)

        self.refresh_theme()

    def refresh_theme(self):
        panel_bg = _with_alpha(tokens.COLOR_BG_MAIN, 0.97)
        panel_border = _with_alpha(tokens.BORDER_SUBTLE, 0.78)
        input_bg = _with_alpha(tokens.BG_INPUT, 0.95)
        input_focus_bg = _with_alpha(tokens.BG_INPUT, 1.0)
        nav_bg = _with_alpha(tokens.BG_INPUT, 0.78)
        stack_bg = _with_alpha(tokens.BG_INPUT, 0.62)

        self.setStyleSheet(
            f"""
            QWidget#SettingsPopup {{
                background: {panel_bg};
                border: 1px solid {panel_border};
                border-radius: 14px;
            }}
            QLineEdit {{
                background: {input_bg};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 6px 8px;
                color: {tokens.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                background: {input_focus_bg};
                border: 1px solid {ORANGE_SELECTION};
            }}
            """
        )
        self.list.setStyleSheet(
            f"""
            QListWidget {{
                background: {nav_bg};
                border: none;
                color: {tokens.TEXT_MUTED};
                border-radius: 10px;
                padding: 6px;
                outline: 0;
            }}
            QListWidget::item {{
                background: transparent;
                padding: 10px 12px;
                border-radius: 8px;
                border: 1px solid transparent;
            }}
            QListWidget::item:hover {{
                background: rgba(255, 138, 61, 0.10);
                border: 1px solid rgba(255, 138, 61, 0.35);
                color: {tokens.TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background: rgba(255, 138, 61, 0.18);
                border: 1px solid rgba(255, 138, 61, 0.62);
                color: {ORANGE_SELECTION};
                font-weight: 600;
            }}
            QListWidget::item:selected:active {{
                background: rgba(255, 138, 61, 0.18);
                border: 1px solid rgba(255, 138, 61, 0.62);
                color: {ORANGE_SELECTION};
            }}
            QListWidget::item:selected:!active {{
                background: rgba(255, 138, 61, 0.18);
                border: 1px solid rgba(255, 138, 61, 0.62);
                color: {ORANGE_SELECTION};
            }}
            """
        )
        self.stack.setStyleSheet(
            f"""
            QStackedWidget {{
                background: {stack_bg};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 10px;
                padding: 8px;
            }}
            """
        )
        self.title_bar.refresh_theme()
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if isinstance(w, QListWidget):
                w.setStyleSheet(self._content_list_style())
            refresh = getattr(w, "refresh_theme", None)
            if callable(refresh):
                refresh()

    def _content_list_style(self) -> str:
        return f"""
        QListWidget {{
            background: {_with_alpha(tokens.BG_INPUT, 0.88)};
            color: {tokens.TEXT_PRIMARY};
            border: 1px solid {tokens.BORDER_SUBTLE};
            border-radius: 8px;
            padding: 4px;
        }}
        QListWidget::item {{
            padding: 8px 10px;
            border-radius: 6px;
        }}
        QListWidget::item:selected {{
            background: rgba(255, 138, 61, 0.16);
            color: {ORANGE_SELECTION};
        }}
        """

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

        self.refresh_theme()

    def refresh_theme(self):
        self.setStyleSheet(
            f"""
            QWidget#PopupInner {{
                background-color: {_with_alpha(tokens.COLOR_BG_MAIN, 0.95)};
                border-radius: 14px;
                padding: 8px;
                border: 1px solid {tokens.BORDER_SUBTLE};
            }}

            QLabel {{
                background-color: {_with_alpha(tokens.BG_INPUT, 0.82)};
                border: 1px solid {_with_alpha(tokens.PRIMARY, 0.34)};
                border-radius: 10px;
                font-size: 20px;
                padding: 10px 14px;
                color: {tokens.TEXT_PRIMARY};
            }}

            QLabel:hover {{
                background-color: {_with_alpha(tokens.BG_INPUT, 0.96)};
                border: 1px solid {_with_alpha(tokens.ACCENT, 0.52)};
            }}
            """
        )

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)
