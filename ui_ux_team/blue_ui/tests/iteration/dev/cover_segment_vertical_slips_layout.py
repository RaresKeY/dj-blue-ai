from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget


def _color_frame(object_name: str, bg: str, border: str, radius: int = 8) -> QFrame:
    frame = QFrame()
    frame.setObjectName(object_name)
    frame.setStyleSheet(
        f"""
        QFrame#{object_name} {{
            background: {bg};
            border: 2px solid {border};
            border-radius: {max(0, int(radius))}px;
        }}
        """
    )
    return frame


class CoverSegmentVerticalSlipsLayoutTestComponent(QWidget):
    """Color-only scaffold for 3 vertical strips (prev/current/next)."""

    _SIDE_COVER = 150
    _CENTER_COVER = 220
    _SIDE_STRIP_W = 170
    _CENTER_STRIP_W = 240
    _TITLE_H = 34
    _COVER_TRACK_H = _CENTER_COVER

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CoverSegmentVerticalSlipsLayoutTestComponent")
        self.setMinimumSize(900, 460)

        page = QVBoxLayout(self)
        page.setContentsMargins(18, 18, 18, 18)
        page.setSpacing(0)

        root = _color_frame("COVER_SEGMENT_ROOT", "#1A2238", "#9CB2D7", 10)
        page.addWidget(root, 1)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(10)
        root_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        prev_strip = self._build_strip(
            strip_name="PREV_COLUMN_STRIP",
            cover_name="PREV_COVER_SLOT",
            title_name="PREV_TITLE_SLOT",
            strip_w=self._SIDE_STRIP_W,
            cover_size=self._SIDE_COVER,
            strip_bg="#25415E",
            strip_border="#8FC8FF",
            cover_bg="#3C638C",
            cover_border="#A6DBFF",
            title_bg="#3B6A42",
            title_border="#A6E5AF",
        )
        current_strip = self._build_strip(
            strip_name="CURRENT_COLUMN_STRIP",
            cover_name="CURRENT_COVER_SLOT",
            title_name="CURRENT_TITLE_SLOT",
            strip_w=self._CENTER_STRIP_W,
            cover_size=self._CENTER_COVER,
            strip_bg="#4A337A",
            strip_border="#D7BEFF",
            cover_bg="#6C4AAE",
            cover_border="#E0CCFF",
            title_bg="#2F7B66",
            title_border="#9EEFD8",
        )
        next_strip = self._build_strip(
            strip_name="NEXT_COLUMN_STRIP",
            cover_name="NEXT_COVER_SLOT",
            title_name="NEXT_TITLE_SLOT",
            strip_w=self._SIDE_STRIP_W,
            cover_size=self._SIDE_COVER,
            strip_bg="#5D3B2A",
            strip_border="#FFC6A1",
            cover_bg="#8A563A",
            cover_border="#FFD7BC",
            title_bg="#2D6A7F",
            title_border="#AEE9FF",
        )

        root_layout.addWidget(prev_strip, 0, Qt.AlignTop)
        root_layout.addWidget(current_strip, 0, Qt.AlignTop)
        root_layout.addWidget(next_strip, 0, Qt.AlignTop)

    def _build_strip(
        self,
        *,
        strip_name: str,
        cover_name: str,
        title_name: str,
        strip_w: int,
        cover_size: int,
        strip_bg: str,
        strip_border: str,
        cover_bg: str,
        cover_border: str,
        title_bg: str,
        title_border: str,
    ) -> QFrame:
        strip_h = self._COVER_TRACK_H + self._TITLE_H

        strip = _color_frame(strip_name, strip_bg, strip_border, 8)
        strip.setFixedSize(int(strip_w), int(strip_h))

        strip_layout = QVBoxLayout(strip)
        strip_layout.setContentsMargins(8, 8, 8, 0)
        strip_layout.setSpacing(0)
        strip_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        cover_track = _color_frame(f"{strip_name}_COVER_TRACK", "#1D2B44", "#5D78A8", 6)
        cover_track.setFixedHeight(self._COVER_TRACK_H)
        track_layout = QVBoxLayout(cover_track)
        track_layout.setContentsMargins(0, 0, 0, 0)
        track_layout.setSpacing(0)
        track_layout.addStretch(1)

        cover = _color_frame(cover_name, cover_bg, cover_border, 12)
        cover.setFixedSize(int(cover_size), int(cover_size))
        track_layout.addWidget(cover, 0, Qt.AlignHCenter | Qt.AlignVCenter)
        track_layout.addStretch(1)

        title = _color_frame(title_name, title_bg, title_border, 7)
        title.setFixedSize(int(cover_size), int(self._TITLE_H))

        strip_layout.addWidget(cover_track, 0, Qt.AlignTop)
        strip_layout.addWidget(title, 0, Qt.AlignHCenter | Qt.AlignTop)
        return strip

