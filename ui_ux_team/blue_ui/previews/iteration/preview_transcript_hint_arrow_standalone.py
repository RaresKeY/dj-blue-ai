import sys
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, Qt
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

project_root = Path(__file__).resolve()
while project_root.name != "ui_ux_team" and project_root != project_root.parent:
    project_root = project_root.parent
project_root = project_root.parent if project_root.name == "ui_ux_team" else Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.theme import ensure_default_theme
from ui_ux_team.blue_ui.widgets.transcript_hint_arrow import TranscriptHintArrow


class TranscriptHintArrowStandalonePreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TranscriptHintArrowStandalonePreview")
        self.resize(560, 420)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)

        stage = QLabel()
        stage.setStyleSheet(
            """
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #0f1e3d,
                stop: 0.65 #11224a,
                stop: 1 #2b1d44
            );
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            """
        )
        root.addWidget(stage, 1)

        self._arrow = TranscriptHintArrow(stage)
        self._layout_arrow()

        poke_anim = QPropertyAnimation(self._arrow, b"poke_offset", self)
        poke_anim.setDuration(1400)
        poke_anim.setEasingCurve(QEasingCurve.InOutCubic)
        poke_anim.setKeyValueAt(0.00, 0.0)
        poke_anim.setKeyValueAt(0.40, 5.2)
        poke_anim.setKeyValueAt(0.60, 1.5)
        poke_anim.setKeyValueAt(1.00, 0.0)

        peck_anim = QPropertyAnimation(self._arrow, b"peck_angle", self)
        peck_anim.setDuration(1400)
        peck_anim.setEasingCurve(QEasingCurve.InOutCubic)
        peck_anim.setKeyValueAt(0.00, 0.0)
        peck_anim.setKeyValueAt(0.30, -6.2)
        peck_anim.setKeyValueAt(0.48, 2.4)
        peck_anim.setKeyValueAt(0.64, -1.2)
        peck_anim.setKeyValueAt(1.00, 0.0)

        self._anim = QParallelAnimationGroup(self)
        self._anim.addAnimation(poke_anim)
        self._anim.addAnimation(peck_anim)
        self._anim.setLoopCount(-1)
        self._anim.start()

    def _layout_arrow(self):
        parent = self._arrow.parentWidget()
        if parent is None:
            return
        cx = parent.width() // 2
        cy = parent.height() // 2
        self._arrow.move(cx - self._arrow.width() // 2, cy - self._arrow.height() // 2)
        self._arrow.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_arrow()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ensure_default_theme()
    window = TranscriptHintArrowStandalonePreview()
    window.show()
    raise SystemExit(app.exec())
