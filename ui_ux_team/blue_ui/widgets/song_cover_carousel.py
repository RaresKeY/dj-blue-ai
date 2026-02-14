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
from ui_ux_team.blue_ui.theme import tokens as theme_tokens
from ui_ux_team.blue_ui.widgets.cover_song_titles import HoverMarqueeTitle
from ui_ux_team.blue_ui.widgets.image_button import IMAGE_NOT_FOUND, ImageButton


class SongCoverCarousel(QWidget):
    prev_requested = Signal()
    next_requested = Signal()
    current_requested = Signal()
    current_changed = Signal(str)
    current_song_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._covers = self._load_covers()
        self._song_paths: list[str] = []
        self._song_titles: list[str] = []
        self._index = 0
        self._ratio_side_to_center = 2.0 / 3.0
        self._preferred_center = 230
        self._min_center = 96
        self._title_row_height = 34

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

        self._prev_slot, self._prev_slot_layout = self._make_cover_slot(self._prev)
        self._current_slot, self._current_slot_layout = self._make_cover_slot(self._current)
        self._next_slot, self._next_slot_layout = self._make_cover_slot(self._next)

        self._prev_title = HoverMarqueeTitle("")
        self._prev_title.setObjectName("CoverSongTitlePrev")
        self._current_title = HoverMarqueeTitle("")
        self._current_title.setObjectName("CoverSongTitleCurrent")
        self._next_title = HoverMarqueeTitle("")
        self._next_title.setObjectName("CoverSongTitleNext")

        self._prev_col = self._make_cover_column(self._prev_slot, self._prev_title)
        self._current_col = self._make_cover_column(self._current_slot, self._current_title)
        self._next_col = self._make_cover_column(self._next_slot, self._next_title)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)
        top_row.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self._row = top_row
        top_row.addWidget(self._prev_col, 0, Qt.AlignTop)
        top_row.addWidget(self._current_col, 0, Qt.AlignTop)
        top_row.addWidget(self._next_col, 0, Qt.AlignTop)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        root.addLayout(top_row)

        self._prev.clicked.connect(self._on_prev_clicked)
        self._current.clicked.connect(self._on_current_clicked)
        self._next.clicked.connect(self._on_next_clicked)

        self._set_fallback_song_items()
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.setMinimumHeight(152)
        self.refresh_theme()
        self._refresh()
        self._update_cover_sizes()

    def sizeHint(self) -> QSize:
        side = int(round(self._preferred_center * self._ratio_side_to_center))
        width = self._preferred_center + (2 * side) + (2 * self._row.spacing())
        height = self._preferred_center + self._title_row_height
        return QSize(width, height)

    def minimumSizeHint(self) -> QSize:
        side = int(round(self._min_center * self._ratio_side_to_center))
        width = self._min_center + (2 * side) + (2 * self._row.spacing())
        height = self._min_center + self._title_row_height
        return QSize(width, height)

    @staticmethod
    def _load_covers() -> list[str]:
        covers_dir = Path(resource_path("ui_ux_team/assets/song_covers_temp"))
        if not covers_dir.exists():
            return []
        covers = sorted(str(p) for p in covers_dir.glob("*.png"))
        random.shuffle(covers)
        return covers

    @staticmethod
    def _make_cover_slot(button: QWidget) -> tuple[QWidget, QVBoxLayout]:
        slot = QWidget()
        slot.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout = QVBoxLayout(slot)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(button, 0, Qt.AlignHCenter | Qt.AlignTop)
        return slot, layout

    @staticmethod
    def _make_cover_column(cover_slot: QWidget, title_widget: QLabel) -> QWidget:
        column = QWidget()
        column.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.addWidget(cover_slot, 0, Qt.AlignTop | Qt.AlignHCenter)
        layout.addWidget(title_widget, 0, Qt.AlignTop | Qt.AlignHCenter)
        return column

    def cover_paths(self) -> list[str]:
        return list(self._covers)

    def song_paths(self) -> list[str]:
        return list(self._song_paths)

    def set_song_items(self, song_items: list[str | Path]):
        paths: list[str] = []
        titles: list[str] = []
        for item in song_items or []:
            raw = str(item or "").strip()
            if not raw:
                continue
            paths.append(str(Path(raw).expanduser()))
            titles.append(self._song_title_from_path(raw))

        self._song_paths = paths
        self._song_titles = titles
        if not self._song_titles:
            self._set_fallback_song_items()
        self._index = self._index % self._item_count()
        self._refresh()

    @staticmethod
    def _song_title_from_path(song_path: str) -> str:
        stem = Path(song_path).stem or Path(song_path).name
        if not stem:
            return "Untitled"
        normalized = stem.replace("_", " ").replace("-", " ").strip()
        return " ".join(normalized.split()) or stem

    def _set_fallback_song_items(self):
        if self._covers:
            self._song_titles = [self._song_title_from_path(p) for p in self._covers]
        else:
            self._song_titles = ["No songs found"]
        self._song_paths = []

    def _item_count(self) -> int:
        return max(len(self._covers), len(self._song_titles), 1)

    def _cycle_index(self, offset: int) -> int:
        return (self._index + offset) % self._item_count()

    def _cycle_cover(self, offset: int) -> str:
        if not self._covers:
            return IMAGE_NOT_FOUND
        idx = self._cycle_index(offset) % len(self._covers)
        return self._covers[idx]

    def _cycle_title(self, offset: int) -> str:
        if not self._song_titles:
            return "No songs found"
        idx = self._cycle_index(offset) % len(self._song_titles)
        return self._song_titles[idx]

    def _cycle_song_path(self, offset: int) -> str:
        if not self._song_paths:
            return ""
        idx = self._cycle_index(offset) % len(self._song_paths)
        return self._song_paths[idx]

    def current_song_path(self) -> str:
        return self._cycle_song_path(0)

    def current_song_title(self) -> str:
        return self._cycle_title(0)

    def _refresh(self):
        self._prev.set_image(self._cycle_cover(-1))
        self._current.set_image(self._cycle_cover(0))
        self._next.set_image(self._cycle_cover(1))
        self._prev_title.setText(self._cycle_title(-1))
        self._current_title.setText(self._cycle_title(0))
        self._next_title.setText(self._cycle_title(1))
        self._animate_side_fade(self._prev_effect)
        self._animate_side_fade(self._next_effect)
        self.current_changed.emit(self._cycle_cover(0))
        self.current_song_changed.emit(self._cycle_song_path(0))

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
        if self._item_count() <= 1:
            self._refresh()
            return
        self._index = self._cycle_index(-1)
        self._refresh()

    def step_next(self):
        if self._item_count() <= 1:
            self._refresh()
            return
        self._index = self._cycle_index(1)
        self._refresh()

    def refresh_theme(self):
        self.setStyleSheet(
            f"""
            QLabel#CoverSongTitlePrev {{
                color: {theme_tokens.TEXT_MUTED};
                font-size: 12px;
                font-weight: 500;
                background: transparent;
            }}
            QLabel#CoverSongTitleCurrent {{
                color: {theme_tokens.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 700;
                background: transparent;
            }}
            QLabel#CoverSongTitleNext {{
                color: {theme_tokens.TEXT_MUTED};
                font-size: 12px;
                font-weight: 500;
                background: transparent;
            }}
            """
        )

    def _update_cover_sizes(self):
        spacing = self._row.spacing()
        usable_w = max(1, self.width() - (spacing * 2))
        title_h = self._title_row_height
        usable_h = max(1, self.height() - title_h)

        ratio = self._ratio_side_to_center
        max_center_by_w = int(usable_w / (1.0 + (2.0 * ratio)))
        max_center_by_h = usable_h

        center = min(self._preferred_center, max_center_by_w, max_center_by_h)
        center = max(56, center)
        side = max(36, int(round(center * ratio)))

        self._current.setFixedSize(center, center)
        self._prev.setFixedSize(side, side)
        self._next.setFixedSize(side, side)
        side_top_pad = max(0, (center - side) // 2)
        side_slot_h = side_top_pad + side
        self._prev_slot.setFixedSize(side, side_slot_h)
        self._current_slot.setFixedSize(center, center)
        self._next_slot.setFixedSize(side, side_slot_h)
        self._prev_col.setFixedSize(side, side_slot_h + title_h)
        self._current_col.setFixedSize(center, center + title_h)
        self._next_col.setFixedSize(side, side_slot_h + title_h)
        self._prev_slot_layout.setContentsMargins(0, side_top_pad, 0, 0)
        self._current_slot_layout.setContentsMargins(0, 0, 0, 0)
        self._next_slot_layout.setContentsMargins(0, side_top_pad, 0, 0)
        self._prev_title.setFixedSize(side, title_h)
        self._current_title.setFixedSize(center, title_h)
        self._next_title.setFixedSize(side, title_h)

        # Keep enough internal breathing room so 1.06 hover scale does not look clipped.
        center_pad = max(4, int(center * 0.06))
        side_pad = max(3, int(side * 0.06))
        self._current.setContentsMargins(center_pad, center_pad, center_pad, 1)
        self._prev.setContentsMargins(side_pad, side_pad, side_pad, 1)
        self._next.setContentsMargins(side_pad, side_pad, side_pad, 1)

        self._current.set_corner_radius(max(14, int(center * 0.10)))
        side_radius = max(10, int(side * 0.10))
        self._prev.set_corner_radius(side_radius)
        self._next.set_corner_radius(side_radius)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_cover_sizes()
