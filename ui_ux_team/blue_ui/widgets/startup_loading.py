import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from ui_ux_team.blue_ui.theme import tokens


def _format_eta(seconds: float) -> str:
    s = max(0, int(round(seconds)))
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class StartupLoadingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Starting DJ Blue")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("StartupLoadingScreen")
        self.setFixedSize(560, 230)

        self._start_ts = 0.0
        self._estimated_total_s = 6.0
        self._target_progress = 0.0
        self._display_progress = 0.0

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(10)

        self._title = QLabel("Launching DJ Blue")
        self._title.setObjectName("LoadingTitle")
        self._status = QLabel("Preparing startup...")
        self._status.setObjectName("LoadingStatus")
        self._status.setWordWrap(True)

        self._progress = QProgressBar()
        self._progress.setRange(0, 1000)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)

        self._meta = QLabel("ETA: --:--")
        self._meta.setObjectName("LoadingMeta")

        root.addWidget(self._title)
        root.addWidget(self._status)
        root.addSpacing(6)
        root.addWidget(self._progress)
        root.addWidget(self._meta)
        root.addStretch(1)

        self._tick = QTimer(self)
        self._tick.setInterval(33)
        self._tick.timeout.connect(self._on_tick)

        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#StartupLoadingScreen {{
                background: {tokens.COLOR_BG_MAIN};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 14px;
            }}
            QLabel#LoadingTitle {{
                color: {tokens.TEXT_PRIMARY};
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#LoadingStatus {{
                color: {tokens.TEXT_MUTED};
                font-size: 14px;
                line-height: 1.35;
            }}
            QLabel#LoadingMeta {{
                color: {tokens.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 600;
            }}
            QProgressBar {{
                background: rgba(0, 0, 0, 0.18);
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 8px;
                min-height: 16px;
                max-height: 16px;
            }}
            QProgressBar::chunk {{
                background: {tokens.PRIMARY};
                border-radius: 7px;
            }}
            """
        )

    def start(self, estimated_total_seconds: float, initial_status: str = "Preparing startup...") -> None:
        self._start_ts = time.perf_counter()
        self._estimated_total_s = max(1.0, float(estimated_total_seconds))
        self._target_progress = 0.0
        self._display_progress = 0.0
        self._status.setText(initial_status)
        self._progress.setValue(0)
        self._meta.setText("ETA: --:--")
        self._tick.start()

    def update_stage(self, status_text: str, progress: float) -> None:
        self._status.setText(status_text)
        self._target_progress = max(0.0, min(100.0, float(progress)))

    def complete(self, status_text: str = "Ready") -> None:
        self._status.setText(status_text)
        self._target_progress = 100.0

    def _on_tick(self) -> None:
        delta = self._target_progress - self._display_progress
        if abs(delta) < 0.06:
            self._display_progress = self._target_progress
        else:
            # Ease progress movement so startup updates feel smooth.
            self._display_progress += delta * 0.18

        self._progress.setValue(int(round(self._display_progress * 10)))

        elapsed = max(0.001, time.perf_counter() - self._start_ts)
        if self._display_progress <= 0.1:
            eta_s = max(0.0, self._estimated_total_s - elapsed)
        else:
            by_rate = elapsed * ((100.0 - self._display_progress) / self._display_progress)
            by_plan = max(0.0, self._estimated_total_s - elapsed)
            eta_s = (0.65 * by_plan) + (0.35 * by_rate)

        if self._display_progress >= 99.9:
            self._meta.setText("ETA: 00:00")
            self._tick.stop()
        else:
            self._meta.setText(f"ETA: {_format_eta(eta_s)}")
