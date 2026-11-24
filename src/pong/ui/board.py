from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from ..core import GameSnapshot


class PixelDigits(QWidget):
    _patterns = {
        "0": ("111", "101", "101", "101", "111"),
        "1": ("010", "110", "010", "010", "111"),
        "2": ("110", "001", "010", "100", "111"),
        "3": ("110", "001", "010", "001", "110"),
        "4": ("101", "101", "111", "001", "001"),
        "5": ("111", "100", "110", "001", "110"),
    }

    def __init__(self, color: str) -> None:
        super().__init__()
        self._value = 0
        self._color = QColor(color)
        self.setFixedSize(62, 42)

    def set_value(self, value: int) -> None:
        self._value = value
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#000000"))
        text = f"{self._value:02d}"
        pixel = 7
        gap = 8
        total_width = len(text) * (3 * pixel) + gap
        x = (self.width() - total_width) // 2
        y = (self.height() - 5 * pixel) // 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        for digit in text:
            pattern = self._patterns.get(digit, self._patterns["0"])
            for row, line in enumerate(pattern):
                for column, cell in enumerate(line):
                    if cell == "1":
                        painter.drawRect(x + column * pixel, y + row * pixel, pixel, pixel)
            x += 3 * pixel + gap


class PongBoard(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._snapshot: GameSnapshot | None = None
        self.setMinimumSize(900, 500)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("background: #000000;")

    def apply_snapshot(self, snapshot: GameSnapshot) -> None:
        self._snapshot = snapshot
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#000000"))
        field = self.rect().adjusted(10, 10, -10, -10)
        painter.setPen(QPen(QColor("#f4f4f4"), 4))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(field)
        self._draw_center_line(painter, field)
        self._draw_corner_labels(painter, field)
        if self._snapshot is None:
            return
        scale_x = field.width() / 900
        scale_y = field.height() / 500
        self._draw_paddle(painter, field, self._snapshot.left_paddle_y, True, scale_x, scale_y)
        self._draw_paddle(painter, field, self._snapshot.right_paddle_y, False, scale_x, scale_y)
        ball_x = field.left() + self._snapshot.ball_x * scale_x
        ball_y = field.top() + self._snapshot.ball_y * scale_y
        size = max(8, int(12 * min(scale_x, scale_y)))
        for offset, shade in ((12, "#4c4c4c"), (7, "#8a8a8a")):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(shade))
            painter.drawRect(int(ball_x - size / 2 - offset), int(ball_y - size / 2), size, size)
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(int(ball_x - size / 2), int(ball_y - size / 2), size, size)

    def _draw_center_line(self, painter: QPainter, field) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffffff"))
        x = field.center().x() - 3
        for y in range(field.top() + 18, field.bottom() - 8, 22):
            painter.drawRect(x, y, 6, 12)

    def _draw_paddle(self, painter: QPainter, field, y: float, left: bool, scale_x: float, scale_y: float) -> None:
        x = field.left() + (28 if left else 854) * scale_x
        width = max(12, int(18 * scale_x))
        height = max(72, int(112 * scale_y))
        top = field.top() + y * scale_y
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(int(x), int(top), width, height)

    def _draw_corner_labels(self, painter: QPainter, field) -> None:
        painter.setPen(QColor("#8f8f8f"))
        painter.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        painter.drawText(field.left() + 16, field.top() + 25, "W / S")
        painter.drawText(field.right() - 58, field.top() + 25, "↑ / ↓")
