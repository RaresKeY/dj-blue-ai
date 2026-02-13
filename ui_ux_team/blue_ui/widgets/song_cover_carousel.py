import random
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from architects.helpers.resource_path import resource_path
from ui_ux_team.blue_ui.widgets.image_button import IMAGE_NOT_FOUND, ImageButton


class SongCoverCarousel(QWidget):
    prev_requested = Signal()
    next_requested = Signal()
    current_requested = Signal()
    current_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._covers = self._load_covers()
        self._index = 0
        self._ratio_side_to_center = 2.0 / 3.0
        self._preferred_center = 230
        self._min_center = 96

        self._prev = ImageButton(IMAGE_NOT_FOUND, size=(120, 120), fallback=IMAGE_NOT_FOUND)
        self._current = ImageButton(IMAGE_NOT_FOUND, size=(180, 180), fallback=IMAGE_NOT_FOUND)
        self._next = ImageButton(IMAGE_NOT_FOUND, size=(120, 120), fallback=IMAGE_NOT_FOUND)
        self._prev.set_corner_radius(14)
        self._current.set_corner_radius(20)
        self._next.set_corner_radius(14)
        # Keep hover animation but reduce clipping pressure at small sizes.
        self._prev.HOVER_SCALE = 1.06
        self._current.HOVER_SCALE = 1.06
        self._next.HOVER_SCALE = 1.06

        self._prev_effect = QGraphicsOpacityEffect(self._prev)
        self._prev_effect.setOpacity(0.66)
        self._prev.setGraphicsEffect(self._prev_effect)

        self._next_effect = QGraphicsOpacityEffect(self._next)
        self._next_effect.setOpacity(0.66)
        self._next.setGraphicsEffect(self._next_effect)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self._row = row
        row.addWidget(self._prev)
        row.addWidget(self._current)
        row.addWidget(self._next)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignCenter)
        root.addLayout(row)

        self._prev.clicked.connect(self._on_prev_clicked)
        self._current.clicked.connect(self._on_current_clicked)
        self._next.clicked.connect(self._on_next_clicked)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.setMinimumHeight(120)
        self._refresh()
        self._update_cover_sizes()

    def sizeHint(self) -> QSize:
        side = int(round(self._preferred_center * self._ratio_side_to_center))
        width = self._preferred_center + (2 * side) + (2 * self._row.spacing())
        return QSize(width, self._preferred_center)

    def minimumSizeHint(self) -> QSize:
        side = int(round(self._min_center * self._ratio_side_to_center))
        width = self._min_center + (2 * side) + (2 * self._row.spacing())
        return QSize(width, self._min_center)

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
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(0.25)
        anim.setKeyValueAt(0.35, 0.58)
        anim.setEndValue(0.78)
        # Keep ref so Qt doesn't GC it mid-flight.
        effect._fade_anim = anim  # type: ignore[attr-defined]
        anim.start()

    def _on_prev_clicked(self):
        self.prev_requested.emit()

    def _on_next_clicked(self):
        self.next_requested.emit()

    def _on_current_clicked(self):
        self.current_requested.emit()

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

    def _update_cover_sizes(self):
        spacing = self._row.spacing()
        usable_w = max(1, self.width() - (spacing * 2))
        usable_h = max(1, self.height())

        ratio = self._ratio_side_to_center
        max_center_by_w = int(usable_w / (1.0 + (2.0 * ratio)))
        max_center_by_h = usable_h

        center = min(self._preferred_center, max_center_by_w, max_center_by_h)
        center = max(56, center)
        side = max(36, int(round(center * ratio)))

        self._current.setFixedSize(center, center)
        self._prev.setFixedSize(side, side)
        self._next.setFixedSize(side, side)

        # Keep enough internal breathing room so 1.06 hover scale does not look clipped.
        center_pad = max(4, int(center * 0.06))
        side_pad = max(3, int(side * 0.06))
        self._current.setContentsMargins(center_pad, center_pad, center_pad, center_pad)
        self._prev.setContentsMargins(side_pad, side_pad, side_pad, side_pad)
        self._next.setContentsMargins(side_pad, side_pad, side_pad, side_pad)

        self._current.set_corner_radius(max(14, int(center * 0.10)))
        side_radius = max(10, int(side * 0.10))
        self._prev.set_corner_radius(side_radius)
        self._next.set_corner_radius(side_radius)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_cover_sizes()
