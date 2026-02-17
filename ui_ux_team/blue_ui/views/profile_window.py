from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame

from architects.helpers.resource_path import resource_path
from ui_ux_team.blue_ui.theme import tokens
from ui_ux_team.blue_ui.theme.native_window import apply_native_titlebar_for_theme


class ProfileWindowView(QWidget):
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Profile")
        self.setMinimumSize(360, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(12)

        avatar = QLabel()
        avatar.setObjectName("profileAvatar")
        avatar.setFixedSize(72, 72)
        pixmap = QPixmap(resource_path("ui_ux_team/assets/user.png"))
        if not pixmap.isNull():
            avatar.setPixmap(pixmap.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            avatar.setAlignment(Qt.AlignCenter)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title = QLabel("DJ Blue Profile")
        title.setObjectName("profileTitle")
        subtitle = QLabel("Account and app identity")
        subtitle.setObjectName("profileSubtitle")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        header.addWidget(avatar, alignment=Qt.AlignTop)
        header.addLayout(title_block, 1)
        layout.addLayout(header)

        details_card = QFrame()
        details_card.setObjectName("profileCard")
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(14, 14, 14, 14)
        details_layout.setSpacing(10)

        for label, value in [
            ("Name", "DJ Blue User"),
            ("Role", "Listener"),
            ("Status", "Active"),
            ("Theme", "Current Blue UI theme"),
        ]:
            row = QLabel(f"{label}: {value}")
            row.setObjectName("profileRow")
            details_layout.addWidget(row)

        layout.addWidget(details_card)
        layout.addStretch(1)
        self.refresh_theme()

    def refresh_theme(self):
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {tokens.COLOR_BG_MAIN};
                color: {tokens.TEXT_PRIMARY};
            }}
            QLabel#profileTitle {{
                font-size: 20px;
                font-weight: 700;
                color: {tokens.TEXT_PRIMARY};
            }}
            QLabel#profileSubtitle {{
                font-size: 13px;
                color: {tokens.TEXT_MUTED};
            }}
            QLabel#profileAvatar {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 36px;
            }}
            QFrame#profileCard {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 10px;
            }}
            QLabel#profileRow {{
                font-size: 14px;
                color: {tokens.TEXT_PRIMARY};
            }}
            """
        )
        apply_native_titlebar_for_theme(self)

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)
