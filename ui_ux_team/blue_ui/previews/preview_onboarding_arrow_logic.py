import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.theme import ensure_default_theme
from ui_ux_team.blue_ui.theme import tokens
from ui_ux_team.blue_ui.widgets.onboarding_arrow_guide import OnboardingArrowGuide


class MockAPISetupWindow(QWidget):
    api_key_set = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mock API Settings")
        self.setMinimumSize(360, 170)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        hint = QLabel("Preview flow: click the button below to simulate a valid API key save.")
        hint.setWordWrap(True)
        btn_set = QPushButton("Set API Key")
        btn_set.clicked.connect(self._emit_set)

        root.addWidget(hint)
        root.addWidget(btn_set, alignment=Qt.AlignLeft)
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {tokens.COLOR_BG_MAIN};
                color: {tokens.TEXT_PRIMARY};
            }}
            QPushButton {{
                background: rgba(255, 138, 61, 0.14);
                color: {tokens.ACCENT};
                border: 1px solid rgba(255, 138, 61, 0.62);
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(255, 138, 61, 0.24);
            }}
            """
        )

    def _emit_set(self):
        self.api_key_set.emit()
        self.close()


class OnboardingArrowLogicPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OnboardingArrowLogicPreview")
        self.resize(920, 560)

        self._api_ready = False
        self._api_window = None

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(10)

        self._status = QLabel("Stage: API required (arrow points API).")
        self._status.setObjectName("status")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        canvas = QWidget()
        canvas_layout = QHBoxLayout(canvas)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addStretch(1)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(10, 14, 10, 14)
        side_layout.setSpacing(10)

        self.btn_transcript = QPushButton("Transcript")
        self.btn_transcript.clicked.connect(self._on_transcript_clicked)
        self.btn_api = QPushButton("API")
        self.btn_api.clicked.connect(self._open_api_mock)
        side_layout.addWidget(self.btn_transcript)
        side_layout.addWidget(self.btn_api)
        side_layout.addStretch(1)

        canvas_layout.addWidget(sidebar, 0)
        root.addWidget(canvas, 1)

        self.setStyleSheet(
            f"""
            QWidget {{
                background: {tokens.COLOR_BG_MAIN};
                color: {tokens.TEXT_PRIMARY};
            }}
            QWidget#sidebar {{
                background: {tokens.COLOR_SIDEBAR};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 10px;
                min-width: 140px;
                max-width: 140px;
            }}
            QPushButton {{
                background: rgba(255, 138, 61, 0.14);
                color: {tokens.ACCENT};
                border: 1px solid rgba(255, 138, 61, 0.62);
                border-radius: 8px;
                padding: 10px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(255, 138, 61, 0.24);
            }}
            QLabel#status {{
                font-size: 13px;
                font-weight: 700;
            }}
            """
        )

        self._guide = OnboardingArrowGuide(self)
        self._guide.set_targets(self.btn_api, self.btn_transcript)
        self._guide.stage_changed.connect(self._on_stage_changed)
        self._guide.set_api_ready(False)
        self._guide.show_if_needed()

    def _open_api_mock(self):
        if self._api_window is not None:
            self._api_window.raise_()
            self._api_window.activateWindow()
            return
        self._api_window = MockAPISetupWindow()
        self._api_window.api_key_set.connect(self._on_api_key_set)
        self._api_window.destroyed.connect(lambda: setattr(self, "_api_window", None))
        self._api_window.move(self.x() + 120, self.y() + 120)
        self._api_window.show()

    def _on_api_key_set(self):
        self._api_ready = True
        self._guide.set_api_ready(True)
        self._status.setText("Stage: API set, arrow now points Transcript. Click Transcript to finish.")

    def _on_transcript_clicked(self):
        self._guide.handle_transcript_clicked()
        if self._guide.stage == OnboardingArrowGuide.STAGE_DONE:
            self._status.setText("Stage: done. Arrow removed after transcript click.")
        elif not self._api_ready:
            self._status.setText("Stage: API required first. Click API and set key in mock window.")

    def _on_stage_changed(self, stage: str):
        if stage == OnboardingArrowGuide.STAGE_API:
            self._status.setText("Stage: API required (arrow points API).")
        elif stage == OnboardingArrowGuide.STAGE_TRANSCRIPT:
            self._status.setText("Stage: API set, arrow points Transcript.")
        elif stage == OnboardingArrowGuide.STAGE_DONE:
            self._status.setText("Stage: done. Arrow removed.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._guide.reposition()

    def showEvent(self, event):
        super().showEvent(event)
        self._guide.show_if_needed()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ensure_default_theme()
    window = OnboardingArrowLogicPreview()
    window.show()
    raise SystemExit(app.exec())
