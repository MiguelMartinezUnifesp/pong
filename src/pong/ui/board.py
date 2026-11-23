from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from ..core import GameSnapshot


class PongBoard(QWidget):
    input_changed = pyqtSignal(str, int)

    def __init__(self) -> None:
        super().__init__()
        self._snapshot: GameSnapshot | None = None
        self.setMinimumSize(900, 500)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("background: #08111f;")

    def apply_snapshot(self, snapshot: GameSnapshot) -> None:
        self._snapshot = snapshot
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#08111f"))
        margin = 24
        field = self.rect().adjusted(margin, margin, -margin, -margin)
        painter.setBrush(QColor("#0d1b2a"))
        painter.setPen(QPen(QColor("#26435b"), 3))
        painter.drawRoundedRect(field, 8, 8)
        self._draw_center_line(painter, field)
        self._draw_center_circle(painter, field)
        if self._snapshot is None:
            return
        scale_x = field.width() / 900
        scale_y = field.height() / 500
        self._draw_paddle(painter, field, self._snapshot.left_paddle_y, True, scale_x, scale_y)
        self._draw_paddle(painter, field, self._snapshot.right_paddle_y, False, scale_x, scale_y)
        ball_x = field.left() + self._snapshot.ball_x * scale_x
        ball_y = field.top() + self._snapshot.ball_y * scale_y
        radius = 11 * min(scale_x, scale_y)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f7f4ea"))
        painter.drawEllipse(int(ball_x - radius), int(ball_y - radius), int(radius * 2), int(radius * 2))
        self._draw_corner_labels(painter, field)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        self._emit_key(event, True)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        self._emit_key(event, False)

    def _emit_key(self, event: QKeyEvent, pressed: bool) -> None:
        key = event.key()
        direction = 0 if not pressed else 1
        if key == Qt.Key.Key_W:
            self.input_changed.emit("left", -direction)
            event.accept()
        elif key == Qt.Key.Key_S:
            self.input_changed.emit("left", direction)
            event.accept()
        elif key == Qt.Key.Key_Up:
            self.input_changed.emit("right", -direction)
            event.accept()
        elif key == Qt.Key.Key_Down:
            self.input_changed.emit("right", direction)
            event.accept()
        else:
            super().keyPressEvent(event)

    def _draw_center_line(self, painter: QPainter, field) -> None:
        pen = QPen(QColor("#27445b"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(field.center().x(), field.top() + 12, field.center().x(), field.bottom() - 12)

    def _draw_center_circle(self, painter: QPainter, field) -> None:
        painter.setPen(QPen(QColor("#27445b"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        size = min(field.width(), field.height()) * 0.28
        painter.drawEllipse(int(field.center().x() - size / 2), int(field.center().y() - size / 2), int(size), int(size))

    def _draw_paddle(self, painter: QPainter, field, y: float, left: bool, scale_x: float, scale_y: float) -> None:
        x = field.left() + (26 if left else 830) * scale_x
        width = 18 * scale_x
        height = 108 * scale_y
        top = field.top() + y * scale_y
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f4d35e" if left else "#ef6f6c"))
        painter.drawRoundedRect(int(x), int(top), int(width), int(height), 5, 5)

    def _draw_corner_labels(self, painter: QPainter, field) -> None:
        painter.setPen(QColor("#6f8ba1"))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(field.left() + 16, field.top() + 24, "W / S")
        painter.drawText(field.right() - 55, field.top() + 24, "↑ / ↓")
