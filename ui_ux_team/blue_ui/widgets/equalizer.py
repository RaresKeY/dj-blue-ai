from __future__ import annotations

import math

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class EqualizerWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        points: int = 96,
        interval_ms: int = 50,
        thickness: float = 2.2,
        stick_gap_px: int = 8,
        amplitude: float = 0.78,
        edge_fade_power: float = 1.4,
    ) -> None:
        super().__init__(parent)
        self._points = max(32, int(points))
        self._tick = 0
        self._playing = False
        self._thickness = max(1.0, float(thickness))
        self._stick_gap_px = max(2, int(stick_gap_px))
        self._amplitude = max(0.1, min(1.0, float(amplitude)))
        self._edge_fade_power = max(0.1, float(edge_fade_power))
        self._wave_color = QColor("#FFFFFF")
        self._phase = 0.0
        self._samples = [0.0 for _ in range(self._points)]

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.setInterval(max(16, int(interval_ms)))

        self.setMinimumHeight(18)
        self.refresh_theme()

    def is_playing(self) -> bool:
        return bool(self._playing)

    def set_playing(self, playing: bool) -> None:
        playing = bool(playing)
        if playing == self._playing:
            return
        self._playing = playing
        if self._playing:
            self._timer.start()
        else:
            self._timer.stop()
            self._tick = 0
            self._phase = 0.0
            self._samples = [0.0 for _ in range(self._points)]
            self.update()

    def refresh_theme(self) -> None:
        # User requested white waveform.
        self._wave_color = QColor("#FFFFFF")
        self.update()

    def _on_tick(self) -> None:
        self._tick += 1
        self._phase += 0.18

        # Deterministic waveform (no RNG): sum of a few sines with a gentle envelope.
        # Samples are in [-1, 1] and will be scaled in paintEvent.
        samples: list[float] = []
        t = self._phase
        for i in range(self._points):
            x = float(i) / float(self._points - 1)
            # Small at edges, fuller in the middle, like a classic waveform.
            edge = max(0.0, math.sin(math.pi * x))
            edge = edge**self._edge_fade_power
            env = (0.55 + 0.45 * math.sin((x * math.tau) + (t * 0.35))) * (0.25 + 0.75 * edge)
            y = (
                0.60 * math.sin((x * math.tau * 1.25) + (t * 1.00))
                + 0.28 * math.sin((x * math.tau * 2.60) + (t * 1.45) + 1.3)
                + 0.12 * math.sin((x * math.tau * 5.10) + (t * 0.70) + 0.4)
            )
            samples.append(max(-1.0, min(1.0, y * env)))
        self._samples = samples
        self.update()

    def changeEvent(self, event: QEvent) -> None:
        if event.type() in (QEvent.PaletteChange, QEvent.StyleChange):
            self.refresh_theme()
        super().changeEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = max(1, self.width())
        h = max(1, self.height())

        pad_x = 2
        pad_y = 2
        x1 = pad_x
        x2 = w - pad_x
        if x2 <= x1 + 6:
            return

        y_mid = h / 2.0
        amp = max(2.0, (h - 2 * pad_y) * self._amplitude)

        pen = QPen(self._wave_color)
        pen.setWidthF(self._thickness)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        available_w = float(x2 - x1)
        if available_w <= 1.0:
            return
        target_count = max(8, int(available_w // float(self._stick_gap_px)))
        step = max(1, int(round(float(len(self._samples)) / float(target_count))))
        indices = list(range(0, len(self._samples), step))
        if indices[-1] != (len(self._samples) - 1):
            indices.append(len(self._samples) - 1)

        denom = float(len(self._samples) - 1)
        for i in indices:
            s = self._samples[i]
            x = x1 + (x2 - x1) * (float(i) / denom)
            half = abs(float(s)) * amp
            painter.drawLine(float(x), float(y_mid - half), float(x), float(y_mid + half))
