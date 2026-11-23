from __future__ import annotations

import threading
import time

from PyQt6.QtCore import QObject, pyqtSignal

from .entities import PongGame, Side


class GameWorker(QObject):
    snapshot_changed = pyqtSignal(object)
    point_scored = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self._game = PongGame()
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._running_event = threading.Event()

    def run_loop(self) -> None:
        self._emit_snapshot()
        previous = time.perf_counter()
        while not self._stop_event.is_set():
            if not self._running_event.wait(0.1):
                previous = time.perf_counter()
                continue
            current = time.perf_counter()
            elapsed = current - previous
            previous = current
            with self._lock:
                event = self._game.tick(elapsed)
                snapshot = self._game.snapshot()
            self.snapshot_changed.emit(snapshot)
            if event is not None:
                self.point_scored.emit(event)
            time.sleep(max(0.0, (1 / 60) - (time.perf_counter() - current)))

    def start_game(self) -> None:
        with self._lock:
            self._game.start()
            active = self._game.status.value in {"running", "paused"}
            snapshot = self._game.snapshot()
        if active:
            self._running_event.set()
        self.snapshot_changed.emit(snapshot)

    def pause_game(self) -> None:
        with self._lock:
            self._game.pause()
            snapshot = self._game.snapshot()
        self._running_event.clear()
        self.snapshot_changed.emit(snapshot)

    def reset_game(self) -> None:
        with self._lock:
            self._game.reset()
            snapshot = self._game.snapshot()
        self._running_event.clear()
        self.snapshot_changed.emit(snapshot)

    def set_input(self, side: Side, direction: int) -> None:
        with self._lock:
            self._game.set_input(side, direction)

    def stop(self) -> None:
        self._stop_event.set()
        self._running_event.set()

    def _emit_snapshot(self) -> None:
        with self._lock:
            snapshot = self._game.snapshot()
        self.snapshot_changed.emit(snapshot)
