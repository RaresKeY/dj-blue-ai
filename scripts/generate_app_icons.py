#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QImage, QPainter


SOURCE = Path("ui_ux_team/assets/logo_margins.png")
ROOT = Path("ui_ux_team/assets/app_icons")

LINUX_PNG_SIZES = [16, 24, 32, 48, 64, 128, 256, 512]
TRAY_PNG_SIZES = [16, 20, 22, 24, 32]
WINDOWS_ICO_SIZE = 256
MACOS_ICNS_SIZE = 1024


def _load_square_source(path: Path) -> QImage:
    if not path.exists():
        raise FileNotFoundError(f"Missing source icon: {path}")

    image = QImage(str(path))
    if image.isNull():
        raise RuntimeError(f"Failed to load image: {path}")

    if image.width() == image.height():
        return image.convertToFormat(QImage.Format_ARGB32)

    side = max(image.width(), image.height())
    canvas = QImage(side, side, QImage.Format_ARGB32)
    canvas.fill(QColor(0, 0, 0, 0))
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    x = (side - image.width()) / 2.0
    y = (side - image.height()) / 2.0
    painter.drawImage(QRectF(x, y, image.width(), image.height()), image)
    painter.end()
    return canvas


def _render(master: QImage, size: int) -> QImage:
    return master.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def _save_image(image: QImage, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        raise RuntimeError(f"Failed to write image: {path}")


def generate() -> None:
    master = _load_square_source(SOURCE)
    linux_dir = ROOT / "linux"
    tray_dir = ROOT / "tray"

    for size in LINUX_PNG_SIZES:
        _save_image(_render(master, size), linux_dir / f"{size}.png")

    for size in TRAY_PNG_SIZES:
        _save_image(_render(master, size), tray_dir / f"{size}.png")

    _save_image(_render(master, WINDOWS_ICO_SIZE), ROOT / "windows" / "dj-blue-ai.ico")
    _save_image(_render(master, MACOS_ICNS_SIZE), ROOT / "macos" / "dj-blue-ai.icns")
    print(f"Generated app icons from {SOURCE}")


if __name__ == "__main__":
    generate()
