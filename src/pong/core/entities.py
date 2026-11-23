from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Side(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class MatchStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


@dataclass(frozen=True, slots=True)
class GameSnapshot:
    ball_x: float
    ball_y: float
    left_paddle_y: float
    right_paddle_y: float
    left_score: int
    right_score: int
    status: MatchStatus
    winner: Side | None


@dataclass(frozen=True, slots=True)
class PointEvent:
    scorer: Side
    left_score: int
    right_score: int
    match_finished: bool


class Ball:
    def __init__(self, width: float, height: float, radius: float = 11.0) -> None:
        self.width = width
        self.height = height
        self.radius = radius
        self._x = width / 2
        self._y = height / 2
        self._vx = 0.0
        self._vy = 0.0

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def vx(self) -> float:
        return self._vx

    @property
    def vy(self) -> float:
        return self._vy

    def reset(self, horizontal_direction: int) -> None:
        self._x = self.width / 2
        self._y = self.height / 2
        self._vx = 360.0 * horizontal_direction
        self._vy = 150.0 if horizontal_direction > 0 else -150.0

    def move(self, elapsed: float) -> None:
        self._x += self._vx * elapsed
        self._y += self._vy * elapsed

    def bounce_vertical(self, top: float, bottom: float) -> None:
        if self._y - self.radius <= top:
            self._y = top + self.radius
            self._vy = abs(self._vy)
        elif self._y + self.radius >= bottom:
            self._y = bottom - self.radius
            self._vy = -abs(self._vy)
    def bounce_horizontal(self, direction: int, paddle_x: float) -> None:
        self._vx = abs(self._vx) * direction
        self._x = paddle_x

    def adjust_vertical(self, amount: float) -> None:
        self._vy = max(-430.0, min(430.0, self._vy + amount))


class Paddle:
    def __init__(self, x: float, height: float, field_height: float, width: float = 18.0) -> None:
        self.x = x
        self.width = width
        self.height = height
        self.field_height = field_height
        self._y = (field_height - height) / 2

    @property
    def y(self) -> float:
        return self._y

    @property
    def center(self) -> float:
        return self._y + self.height / 2

    def move(self, direction: int, elapsed: float) -> None:
        self._y += direction * 430.0 * elapsed
        self._y = max(0.0, min(self.field_height - self.height, self._y))

    def overlaps(self, ball: Ball) -> bool:
        return (
            ball.x + ball.radius >= self.x
            and ball.x - ball.radius <= self.x + self.width
            and ball.y + ball.radius >= self._y
            and ball.y - ball.radius <= self._y + self.height
        )


class Player:
    def __init__(self, name: str, side: Side) -> None:
        self.name = name
        self.side = side
        self._score = 0

    @property
    def score(self) -> int:
        return self._score

    def add_point(self) -> None:
        self._score += 1

    def reset_score(self) -> None:
        self._score = 0


class PongGame:
    def __init__(self, width: float = 900.0, height: float = 500.0, target_score: int = 5) -> None:
        self.width = width
        self.height = height
        self.target_score = target_score
        self.ball = Ball(width, height)
        self.left_paddle = Paddle(26.0, 108.0, height)
        self.right_paddle = Paddle(width - 44.0, 108.0, height)
        self.left_player = Player("Jogador 1", Side.LEFT)
        self.right_player = Player("Jogador 2", Side.RIGHT)
        self._status = MatchStatus.READY
        self._winner: Side | None = None
        self._left_input = 0
        self._right_input = 0
        self._next_direction = 1
        self.reset()

    @property
    def status(self) -> MatchStatus:
        return self._status

    @property
    def winner(self) -> Side | None:
        return self._winner

    def reset(self) -> None:
        self.left_player.reset_score()
        self.right_player.reset_score()
        self.left_paddle = Paddle(26.0, 108.0, self.height)
        self.right_paddle = Paddle(self.width - 44.0, 108.0, self.height)
        self._status = MatchStatus.READY
        self._winner = None
        self._left_input = 0
        self._right_input = 0
        self._next_direction = 1
        self.ball.reset(self._next_direction)

    def start(self) -> None:
        if self._status in (MatchStatus.READY, MatchStatus.PAUSED):
            self._status = MatchStatus.RUNNING

    def pause(self) -> None:
        if self._status is MatchStatus.RUNNING:
            self._status = MatchStatus.PAUSED

    def set_input(self, side: Side, direction: int) -> None:
        if side is Side.LEFT:
            self._left_input = direction
        else:
            self._right_input = direction

    def snapshot(self) -> GameSnapshot:
        return GameSnapshot(
            ball_x=self.ball.x,
            ball_y=self.ball.y,
            left_paddle_y=self.left_paddle.y,
            right_paddle_y=self.right_paddle.y,
            left_score=self.left_player.score,
            right_score=self.right_player.score,
            status=self._status,
            winner=self._winner,
        )

    def tick(self, elapsed: float) -> PointEvent | None:
        if self._status is not MatchStatus.RUNNING:
            return None

        elapsed = min(elapsed, 0.04)
        self.left_paddle.move(self._left_input, elapsed)
        self.right_paddle.move(self._right_input, elapsed)
        self.ball.move(elapsed)
        self.ball.bounce_vertical(0.0, self.height)
        self._check_paddle_collision()

        if self.ball.x + self.ball.radius < 0:
            return self._score(Side.RIGHT)
        if self.ball.x - self.ball.radius > self.width:
            return self._score(Side.LEFT)
        return None

    def _check_paddle_collision(self) -> None:
        if self.ball.vx < 0 and self.left_paddle.overlaps(self.ball):
            self.ball.bounce_horizontal(1, self.left_paddle.x + self.left_paddle.width + self.ball.radius)
            self._apply_spin(self.left_paddle)
        elif self.ball.vx > 0 and self.right_paddle.overlaps(self.ball):
            self.ball.bounce_horizontal(-1, self.right_paddle.x - self.ball.radius)
            self._apply_spin(self.right_paddle)

    def _apply_spin(self, paddle: Paddle) -> None:
        offset = (self.ball.y - paddle.center) / (paddle.height / 2)
        self.ball.adjust_vertical(offset * 170.0)

    def _score(self, scorer: Side) -> PointEvent:
        player = self.left_player if scorer is Side.LEFT else self.right_player
        player.add_point()
        self._next_direction *= -1
        finished = player.score >= self.target_score
        self._winner = scorer if finished else None
        self._status = MatchStatus.FINISHED if finished else MatchStatus.PAUSED
        self.ball.reset(self._next_direction)
        return PointEvent(scorer, self.left_player.score, self.right_player.score, finished)
