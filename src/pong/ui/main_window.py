from __future__ import annotations

from PyQt6.QtCore import QEvent, QThread, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ..core import GameSnapshot, GameWorker, MatchStatus, Side
from .board import PixelDigits, PongBoard


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PONG — Dupla")
        self.setMinimumSize(980, 700)
        self.resize(1080, 760)
        self._last_snapshot: GameSnapshot | None = None
        self._pressed_keys: set[int] = set()
        self._thread = QThread(self)
        self._worker = GameWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run_loop)
        self._worker.snapshot_changed.connect(self._update_view)
        self._worker.point_scored.connect(self._show_point)
        self._build_ui()
        self._apply_style()
        QApplication.instance().installEventFilter(self)
        self._thread.start()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(30, 22, 30, 22)
        root.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("PONG")
        title.setObjectName("title")
        subtitle = QLabel("ARCADE DE DOIS JOGADORES")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(self._score_box("JOGADOR 1", "W / S", "left"))
        header.addWidget(self._score_box("JOGADOR 2", "↑ / ↓", "right"))
        root.addLayout(header)

        self.board = PongBoard()
        self.board.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self.board, 1)

        self.status_label = QLabel("PRONTO — CLIQUE EM INICIAR JOGO")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status_label)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.start_button = QPushButton("INICIAR JOGO")
        self.start_button.setObjectName("startButton")
        self.pause_button = QPushButton("PAUSAR JOGO")
        self.pause_button.setObjectName("pauseButton")
        self.restart_button = QPushButton("REINICIAR JOGO")
        self.restart_button.setObjectName("restartButton")
        self.start_button.clicked.connect(self._start_game)
        self.pause_button.clicked.connect(self._pause_or_resume)
        self.restart_button.clicked.connect(self._restart_game)
        controls.addWidget(self.start_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.restart_button)
        root.addLayout(controls)

        footer = QLabel("W / S: JOGADOR 1    •    SETAS: JOGADOR 2    •    PRIMEIRO A 5 PONTOS VENCE")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(footer)

    def _score_box(self, name: str, controls: str, side: str) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(14, 0, 14, 0)
        name_label = QLabel(name)
        name_label.setObjectName(f"{side}Name")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score = PixelDigits("#ffffff")
        score.setObjectName(f"{side}Score")
        controls_label = QLabel(controls)
        controls_label.setObjectName("scoreControls")
        controls_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if side == "left":
            self.left_score = score
        else:
            self.right_score = score
        layout.addWidget(name_label)
        layout.addWidget(score, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(controls_label)
        return box

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QWidget#central { background: #000000; color: #ffffff; }
            QLabel#title { color: #ffffff; font-family: "Courier New"; font-size: 42px; font-weight: 900; letter-spacing: 5px; }
            QLabel#subtitle { color: #8f8f8f; font-family: "Courier New"; font-size: 11px; font-weight: 700; letter-spacing: 2px; }
            QLabel#leftName, QLabel#rightName { color: #ffffff; font-family: "Courier New"; font-size: 11px; font-weight: 900; }
            QLabel#scoreControls { color: #8f8f8f; font-family: "Courier New"; font-size: 10px; font-weight: 700; }
            QLabel#status { color: #ffffff; background: #000000; border: 3px solid #ffffff; padding: 9px; font-family: "Courier New"; font-size: 12px; font-weight: 900; }
            QLabel#footer { color: #8f8f8f; font-family: "Courier New"; font-size: 10px; font-weight: 700; }
            QPushButton { min-height: 44px; color: #ffffff; background: #000000; border: 3px solid #ffffff; padding: 8px 14px; font-family: "Courier New"; font-size: 11px; font-weight: 900; }
            QPushButton:hover { color: #000000; background: #ffffff; }
            QPushButton:disabled { color: #565656; border-color: #565656; background: #000000; }
            QPushButton#startButton { color: #000000; background: #ffffff; }
            QPushButton#startButton:hover { color: #ffffff; background: #000000; }
            QPushButton#restartButton { color: #000000; background: #ffffff; }
            QPushButton#restartButton:hover { color: #ffffff; background: #000000; }
        """)

    def _start_game(self) -> None:
        self._worker.start_game()
        self.board.setFocus()

    def _pause_or_resume(self) -> None:
        if self._last_snapshot is not None and self._last_snapshot.status is MatchStatus.PAUSED:
            self._worker.start_game()
        else:
            self._worker.pause_game()
        self.board.setFocus()

    def _restart_game(self) -> None:
        self._worker.reset_game()
        self.board.setFocus()

    def _update_view(self, snapshot: GameSnapshot) -> None:
        self._last_snapshot = snapshot
        self.board.apply_snapshot(snapshot)
        self.left_score.set_value(snapshot.left_score)
        self.right_score.set_value(snapshot.right_score)
        self.pause_button.setEnabled(snapshot.status in (MatchStatus.RUNNING, MatchStatus.PAUSED))
        if snapshot.status is MatchStatus.READY:
            self.status_label.setText("PRONTO — CLIQUE EM INICIAR JOGO")
            self.start_button.setText("INICIAR JOGO")
        elif snapshot.status is MatchStatus.RUNNING:
            self.status_label.setText("JOGANDO — USE AS TECLAS PARA MOVER AS RAQUETES")
            self.start_button.setText("JOGO ATIVO")
        elif snapshot.status is MatchStatus.PAUSED:
            self.status_label.setText("PAUSADO — CLIQUE EM CONTINUAR PARA SACAR")
            self.start_button.setText("CONTINUAR")
        else:
            winner = "JOGADOR 1" if snapshot.winner is Side.LEFT else "JOGADOR 2"
            self.status_label.setText(f"{winner} VENCEU — REINICIE PARA JOGAR NOVAMENTE")
            self.start_button.setText("JOGO ENCERRADO")
        self.start_button.setEnabled(snapshot.status in (MatchStatus.READY, MatchStatus.PAUSED))

    def _show_point(self, event) -> None:
        scorer = "JOGADOR 1" if event.scorer is Side.LEFT else "JOGADOR 2"
        if event.match_finished:
            self.status_label.setText(f"{scorer} ALCANÇOU 5 PONTOS")
        else:
            self.status_label.setText(f"PONTO PARA {scorer} — CLIQUE EM CONTINUAR")

    def eventFilter(self, watched, event: QEvent) -> bool:
        if event.type() not in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            return super().eventFilter(watched, event)
        if not isinstance(event, QKeyEvent):
            return super().eventFilter(watched, event)
        if event.isAutoRepeat() and event.type() is QEvent.Type.KeyRelease:
            return True
        pressed = event.type() is QEvent.Type.KeyPress
        key = event.key()
        if pressed:
            self._pressed_keys.add(key)
        else:
            self._pressed_keys.discard(key)
        if key in (Qt.Key.Key_W, Qt.Key.Key_S):
            direction = -1 if Qt.Key.Key_W in self._pressed_keys else 1 if Qt.Key.Key_S in self._pressed_keys else 0
            self._worker.set_input(Side.LEFT, direction)
            return True
        if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            direction = -1 if Qt.Key.Key_Up in self._pressed_keys else 1 if Qt.Key.Key_Down in self._pressed_keys else 0
            self._worker.set_input(Side.RIGHT, direction)
            return True
        return super().eventFilter(watched, event)

    def closeEvent(self, event) -> None:
        QApplication.instance().removeEventFilter(self)
        self._worker.stop()
        self._thread.quit()
        self._thread.wait(2000)
        event.accept()
