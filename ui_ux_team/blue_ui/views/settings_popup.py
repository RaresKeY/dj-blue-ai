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
    QSizeGrip,
    QScrollArea,
)
from PySide6.QtGui import QFont
from ui_ux_team.blue_ui.theme import tokens
from ui_ux_team.blue_ui.theme.native_window import apply_native_titlebar_for_theme

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


def _is_light(color: str) -> bool:
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
        lum = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
        return lum >= 170
    return False


class PopupTitleBar(QWidget):
    def __init__(self, title="Settings", parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
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
        selection_color = getattr(tokens, "ACCENT", ORANGE_SELECTION)
        hover_bg = _with_alpha(selection_color, 0.16 if _is_light(tokens.COLOR_BG_MAIN) else 0.14)
        hover_border = _with_alpha(selection_color, 0.50 if _is_light(tokens.COLOR_BG_MAIN) else 0.42)
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {tokens.TEXT_PRIMARY};
                font-size: 18px;
                font-weight: 700;
                font-family: Inter;
                padding-left: 6px;
                padding-top: 0px;
            }}
            QPushButton {{
                background: {_with_alpha(tokens.BG_INPUT, 1.0)};
                color: {tokens.TEXT_PRIMARY};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                color: {selection_color};
                border: 1px solid {hover_border};
            }}
            """
        )

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            win = self.window()
            # Notify window that drag started to prevent auto-repositioning
            begin_drag = getattr(win, "_begin_user_drag", None)
            if callable(begin_drag):
                begin_drag()

            handle = win.windowHandle()
            if handle is not None:
                try:
                    # Prefer native system move if available
                    if hasattr(handle, "startSystemMove"):
                        if handle.startSystemMove():
                            e.accept()
                            return
                except Exception:
                    pass

            # Fallback to manual move
            self._drag_pos = e.globalPosition().toPoint()
            e.accept()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton and self._drag_pos is not None:
            # Calculate delta using global position to avoid jitter
            current_pos = e.globalPosition().toPoint()
            delta = current_pos - self._drag_pos
            self.window().move(self.window().pos() + delta)
            self._drag_pos = current_pos
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        win = self.window()
        # Notify window that drag ended
        end_drag = getattr(win, "_end_user_drag", None)
        if callable(end_drag):
            end_drag()
        e.accept()


class SettingsPopup(QWidget):
    closed = Signal()

    def __init__(self, categories=None, parent=None, margin=100):
        # Pass None to super() to ensure it is a top-level window
        super().__init__(None)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setObjectName("SettingsPopup")
        self.setWindowTitle("Settings")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(False)

        self.margin = margin
        self._user_dragging = False
        self.setMinimumSize(560, 350)
        self.categories = categories or {}

        self.list = QListWidget()
        self.list.setFixedWidth(190)
        self.list.setSpacing(6)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setTextElideMode(Qt.ElideRight)
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

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setWidget(widget)
            self.stack.addWidget(scroll)

        self.list.currentRowChanged.connect(self.stack.setCurrentIndex)
        if self.list.count():
            self.list.setCurrentRow(0)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(0)

        self._plate = QFrame(self)
        self._plate.setObjectName("SettingsPlate")
        root_layout.addWidget(self._plate, 1)

        plate_layout = QVBoxLayout(self._plate)
        plate_layout.setContentsMargins(12, 10, 12, 10)
        plate_layout.setSpacing(10)
        self.title_bar = PopupTitleBar("Settings", self._plate)
        plate_layout.addWidget(self.title_bar)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        content_layout.addWidget(self.list)
        content_layout.addWidget(self.stack)
        plate_layout.addLayout(content_layout)

        self._size_grip = QSizeGrip(self._plate)
        self._size_grip.setFixedSize(14, 14)
        self._size_grip.setToolTip("Resize")

        self.refresh_theme()
        self._position_size_grip()

    def set_active_tab(self, index_or_name: int | str):
        if isinstance(index_or_name, int):
            if 0 <= index_or_name < self.list.count():
                self.list.setCurrentRow(index_or_name)
        elif isinstance(index_or_name, str):
            for i in range(self.list.count()):
                if self.list.item(i).text() == index_or_name:
                    self.list.setCurrentRow(i)
                    break

    def refresh_theme(self):
        selection_color = getattr(tokens, "ACCENT", ORANGE_SELECTION)
        panel_bg = getattr(tokens, "COLOR_SETTINGS_BG", tokens.COLOR_BG_MAIN)
        panel_border = _with_alpha(tokens.BORDER_SUBTLE, 1.0)
        panel_outer = _with_alpha(tokens.BORDER_SUBTLE, 0.95)
        input_bg = tokens.BG_INPUT
        input_focus_bg = tokens.BG_INPUT
        nav_bg = tokens.BG_INPUT
        stack_bg = tokens.BG_INPUT
        item_hover_bg = _with_alpha(selection_color, 0.10 if _is_light(panel_bg) else 0.12)
        item_hover_border = _with_alpha(selection_color, 0.35 if _is_light(panel_bg) else 0.42)
        item_selected_bg = _with_alpha(selection_color, 0.18 if _is_light(panel_bg) else 0.22)
        item_selected_border = _with_alpha(selection_color, 0.62 if _is_light(panel_bg) else 0.68)

        self.setStyleSheet(
            f"""
            QWidget#SettingsPopup {{
                background: transparent;
                border: none;
            }}
            QFrame#SettingsPlate {{
                background-color: {panel_bg};
                border: 1px solid {panel_outer};
                border-radius: 14px;
            }}
            QLineEdit {{
                background: {input_bg};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 10px;
                padding: 8px 10px;
                color: {tokens.TEXT_PRIMARY};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                background: {input_focus_bg};
                border: 1px solid {selection_color};
            }}
            """
        )
        self.list.setStyleSheet(
            f"""
            QListWidget {{
                background: {nav_bg};
                border: 1px solid {panel_border};
                color: {tokens.TEXT_MUTED};
                border-radius: 12px;
                padding: 8px;
                outline: 0;
            }}
            QListWidget::item {{
                background: transparent;
                padding: 12px 14px;
                border-radius: 10px;
                border: 1px solid transparent;
                font-size: 15px;
            }}
            QListWidget::item:hover {{
                background: {item_hover_bg};
                border: 1px solid {item_hover_border};
                color: {tokens.TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background: {item_selected_bg};
                border: 1px solid {item_selected_border};
                color: {selection_color};
                font-weight: 600;
            }}
            QListWidget::item:selected:active {{
                background: {item_selected_bg};
                border: 1px solid {item_selected_border};
                color: {selection_color};
            }}
            QListWidget::item:selected:!active {{
                background: {item_selected_bg};
                border: 1px solid {item_selected_border};
                color: {selection_color};
            }}
            """
        )
        self.stack.setStyleSheet(
            f"""
            QStackedWidget {{
                background: {stack_bg};
                border: 1px solid {panel_border};
                border-radius: 12px;
                padding: 10px;
            }}
            """
        )
        self._size_grip.setStyleSheet(
            f"""
            QSizeGrip {{
                background: transparent;
                width: 14px;
                height: 14px;
            }}
            """
        )
        self.title_bar.refresh_theme()
        apply_native_titlebar_for_theme(self)
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if isinstance(w, QScrollArea):
                w.setStyleSheet(
                    f"""
                    QScrollArea {{
                        border: none;
                        background: transparent;
                    }}
                    QScrollArea > QWidget > QWidget {{
                        background: transparent;
                    }}
                    """
                )
            target = w.widget() if isinstance(w, QScrollArea) else w
            if isinstance(target, QListWidget):
                target.setStyleSheet(self._content_list_style())
            refresh = getattr(target, "refresh_theme", None)
            if callable(refresh):
                refresh()

    def _content_list_style(self) -> str:
        selection_color = getattr(tokens, "ACCENT", ORANGE_SELECTION)
        selected_bg = _with_alpha(selection_color, 0.16 if _is_light(tokens.COLOR_BG_MAIN) else 0.18)
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
            background: {selected_bg};
            color: {selection_color};
        }}
        """

    def _position_size_grip(self) -> None:
        if self._size_grip is None or self._plate is None:
            return
        inset = 6
        x = max(0, self._plate.width() - self._size_grip.width() - inset)
        y = max(0, self._plate.height() - self._size_grip.height() - inset)
        self._size_grip.move(x, y)
        self._size_grip.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_size_grip()

    def _begin_user_drag(self) -> None:
        self._user_dragging = True

    def _end_user_drag(self) -> None:
        self._user_dragging = False

    def is_user_dragging(self) -> bool:
        return self._user_dragging

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)


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
