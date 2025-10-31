# app/utils/icon_tint.py
from __future__ import annotations

from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor
from PySide6.QtCore import QByteArray, QSize, QFile, Qt
from functools import lru_cache

@lru_cache(maxsize=256)
def svg_icon(resource_path: str,
             color: str = "#FFFFFF",
             size: QSize = QSize(22, 22)) -> QIcon:
    """
    Load an SVG from Qt resource and render to a monochrome QIcon tinted with `color`.
    Works for both stroke-based and fill-based SVGs without editing the SVG text.
    """
    f = QFile(resource_path)
    if not f.open(QFile.ReadOnly):
        return QIcon()

    data = f.readAll()
    renderer = QSvgRenderer(QByteArray(data))

    pm = QPixmap(size)
    pm.fill(Qt.transparent)

    # First render as-is to transparent background
    p = QPainter(pm)
    renderer.render(p)
    # Then use SourceIn to uniformly tint all valid pixels
    p.setCompositionMode(QPainter.CompositionMode_SourceIn)
    p.fillRect(pm.rect(), QColor(color))
    p.end()

    return QIcon(pm)
