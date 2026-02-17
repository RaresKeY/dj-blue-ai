from PySide6.QtWidgets import QVBoxLayout, QWidget

from ui_ux_team.blue_ui.views.api_settings_window import APISettingsWindowView


class ApiSettingsKeyringSetupTestComponent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ApiSettingsKeyringSetupTestComponent")
        self.setMinimumSize(760, 380)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(0)

        self._api_settings = APISettingsWindowView(self)
        root.addWidget(self._api_settings, 1)
