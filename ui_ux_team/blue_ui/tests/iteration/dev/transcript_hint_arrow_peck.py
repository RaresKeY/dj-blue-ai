from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation
from PySide6.QtWidgets import QLabel, QWidget

from architects.helpers.resource_path import resource_path
from ui_ux_team.blue_ui.widgets.image_button import ImageButton
from ui_ux_team.blue_ui.widgets.transcript_hint_arrow import TranscriptHintArrow


class TranscriptHintArrowPeckTestComponent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TranscriptHintArrowPeckTestComponent")
        self.setMinimumSize(900, 520)

        self._bg = QLabel(self)
        self._bg.setStyleSheet(
            """
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #0f1e3d,
                stop: 0.65 #11224a,
                stop: 1 #2b1d44
            );
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 10px;
            """
        )

        self._transcript_btn = ImageButton(resource_path("ui_ux_team/assets/transcript_black.png"), size=(62, 62))
        self._transcript_btn.setParent(self)

        self._arrow = TranscriptHintArrow(self)
        self._arrow.show()

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
        self._layout_preview()

    def _layout_preview(self):
        self._bg.setGeometry(12, 12, self.width() - 24, self.height() - 24)
        btn_x = self.width() - 98
        btn_y = 48
        self._transcript_btn.move(btn_x, btn_y)
        tip_x = int(self._arrow.width() * 0.865)
        tip_y = int(self._arrow.height() * 0.225)
        target_x = btn_x + 10
        target_y = btn_y + (self._transcript_btn.height() // 2)
        arrow_x = target_x - tip_x
        arrow_y = target_y - tip_y
        self._arrow.move(arrow_x, arrow_y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_preview()
