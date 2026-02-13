import random
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from architects.helpers.resource_path import resource_path
from ui_ux_team.blue_ui.widgets.image_button import IMAGE_NOT_FOUND, ImageButton


class SongCoverCarousel(QWidget):
    prev_requested = Signal()
    next_requested = Signal()
    current_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._covers = self._load_covers()
        self._index = 0

        self._prev = ImageButton(IMAGE_NOT_FOUND, size=(120, 120), fallback=IMAGE_NOT_FOUND)
        self._current = ImageButton(IMAGE_NOT_FOUND, size=(180, 180), fallback=IMAGE_NOT_FOUND)
        self._next = ImageButton(IMAGE_NOT_FOUND, size=(120, 120), fallback=IMAGE_NOT_FOUND)

        self._prev_effect = QGraphicsOpacityEffect(self._prev)
        self._prev_effect.setOpacity(0.66)
        self._prev.setGraphicsEffect(self._prev_effect)

        self._next_effect = QGraphicsOpacityEffect(self._next)
        self._next_effect.setOpacity(0.66)
        self._next.setGraphicsEffect(self._next_effect)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)
        row.addWidget(self._prev)
        row.addWidget(self._current)
        row.addWidget(self._next)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(row)

        self._prev.clicked.connect(self._on_prev_clicked)
        self._next.clicked.connect(self._on_next_clicked)
        self._refresh()

    @staticmethod
    def _load_covers() -> list[str]:
        covers_dir = Path(resource_path("ui_ux_team/assets/song_covers_temp"))
        if not covers_dir.exists():
            return []
        covers = sorted(str(p) for p in covers_dir.glob("*.png"))
        random.shuffle(covers)
        return covers

    def cover_paths(self) -> list[str]:
        return list(self._covers)

    def _cycle(self, offset: int) -> str:
        if not self._covers:
            return IMAGE_NOT_FOUND
        idx = (self._index + offset) % len(self._covers)
        return self._covers[idx]

    def _refresh(self):
        self._prev.set_image(self._cycle(-1))
        self._current.set_image(self._cycle(0))
        self._next.set_image(self._cycle(1))
        self._animate_side_fade(self._prev_effect)
        self._animate_side_fade(self._next_effect)
        self.current_changed.emit(self._cycle(0))

    @staticmethod
    def _animate_side_fade(effect: QGraphicsOpacityEffect):
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(220)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(0.18)
        anim.setEndValue(0.66)
        # Keep ref so Qt doesn't GC it mid-flight.
        effect._fade_anim = anim  # type: ignore[attr-defined]
        anim.start()

    def _on_prev_clicked(self):
        self.prev_requested.emit()

    def _on_next_clicked(self):
        self.next_requested.emit()

    def step_prev(self):
        if not self._covers:
            return
        self._index = (self._index - 1) % len(self._covers)
        self._refresh()

    def step_next(self):
        if not self._covers:
            return
        self._index = (self._index + 1) % len(self._covers)
        self._refresh()
