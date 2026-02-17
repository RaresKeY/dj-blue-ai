from PySide6.QtCore import QObject, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QAbstractAnimation, Signal
from PySide6.QtWidgets import QWidget

from ui_ux_team.blue_ui.widgets.transcript_hint_arrow import TranscriptHintArrow


class OnboardingArrowGuide(QObject):
    STAGE_API = "api"
    STAGE_TRANSCRIPT = "transcript"
    STAGE_DONE = "done"

    stage_changed = Signal(str)

    def __init__(self, host: QWidget):
        super().__init__(host)
        self._host = host
        self._api_button = None
        self._transcript_button = None
        self._dismissed = False
        self._stage = self.STAGE_API

        self._arrow = TranscriptHintArrow(host)
        self._arrow.hide()

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

    @property
    def stage(self) -> str:
        return self._stage

    def is_dismissed(self) -> bool:
        return self._dismissed

    def set_targets(self, api_button: QWidget | None, transcript_button: QWidget | None):
        self._api_button = api_button
        self._transcript_button = transcript_button
        self.reposition()

    def set_api_ready(self, is_ready: bool):
        if self._dismissed:
            return
        next_stage = self.STAGE_TRANSCRIPT if is_ready else self.STAGE_API
        if self._stage != next_stage:
            self._stage = next_stage
            self.stage_changed.emit(self._stage)
        self.show_if_needed()

    def handle_transcript_clicked(self):
        if self._dismissed:
            return
        if self._stage == self.STAGE_TRANSCRIPT:
            self.dismiss()

    def show_if_needed(self):
        if self._dismissed or self._stage == self.STAGE_DONE:
            return
        target = self._current_target()
        if target is None or not target.isVisible():
            return
        self.reposition()
        self._arrow.show()
        self._arrow.raise_()
        if self._anim.state() != QAbstractAnimation.Running:
            self._anim.start()

    def hide(self):
        self._anim.stop()
        self._arrow.hide()

    def dismiss(self):
        if self._dismissed:
            return
        self._dismissed = True
        self._stage = self.STAGE_DONE
        self.hide()
        self.stage_changed.emit(self._stage)

    def reposition(self):
        target = self._current_target()
        if target is None:
            return
        center = target.mapTo(self._host, target.rect().center())
        tip_x = int(self._arrow.width() * 0.865)
        tip_y = int(self._arrow.height() * 0.225)
        target_x = center.x() - (target.width() // 2) + 10
        target_y = center.y()
        x = max(8, target_x - tip_x)
        y = target_y - tip_y
        y = max(8, min(self._host.height() - self._arrow.height() - 8, y))
        self._arrow.move(x, y)

    def _current_target(self):
        if self._stage == self.STAGE_API:
            return self._api_button
        if self._stage == self.STAGE_TRANSCRIPT:
            return self._transcript_button
        return None
