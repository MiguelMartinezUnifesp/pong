from __future__ import annotations

from PyQt6.QtCore import QEvent, QThread, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ..core import GameSnapshot, GameWorker, MatchStatus, Side
from .board import PongBoard


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PONG — Dupla")
        self.setMinimumSize(1020, 720)
        self.resize(1120, 780)
        self._last_snapshot: GameSnapshot | None = None
        self._thread = QThread(self)
        self._worker = GameWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run_loop)
        self._worker.snapshot_changed.connect(self._update_view)
        self._worker.point_scored.connect(self._show_point)
        self._build_ui()
        self._apply_style()
        self.installEventFilter(self)
        self._thread.start()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(26, 22, 26, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("PONG")
        title.setObjectName("title")
        subtitle = QLabel("DUELO DE RAQUETES")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        self.left_score = QLabel("00")
        self.left_score.setObjectName("leftScore")
        self.right_score = QLabel("00")
        self.right_score.setObjectName("rightScore")
        header.addWidget(self._score_box("JOGADOR 1", self.left_score, "left"))
        header.addWidget(self._score_box("JOGADOR 2", self.right_score, "right"))
        root.addLayout(header)

        self.board = PongBoard()
        self.board.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self.board, 1)

        self.status_label = QLabel("Pronto. Inicie a partida para soltar a bola.")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status_label)

        controls = QHBoxLayout()
        controls.setSpacing(10)
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

        hints = QLabel("JOGADOR 1  W / S    •    JOGADOR 2  ↑ / ↓    •    PRIMEIRO A 5 PONTOS VENCE")
        hints.setObjectName("hints")
        hints.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(hints)

    def _score_box(self, label_text: str, score: QLabel, side: str) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(14, 0, 14, 0)
        label = QLabel(label_text)
        label.setObjectName(f"{side}Label")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addWidget(score)
        return box

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QWidget#central { background: #06101d; color: #f7f4ea; }
            QLabel#title { color: #f7f4ea; font-family: Arial; font-size: 38px; font-weight: 900; letter-spacing: 3px; }
            QLabel#subtitle { color: #6f8ba1; font-family: Arial; font-size: 11px; font-weight: 700; letter-spacing: 3px; }
            QLabel#leftLabel, QLabel#rightLabel { color: #8da8bb; font-family: Arial; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
            QLabel#leftScore, QLabel#rightScore { font-family: Arial; font-size: 38px; font-weight: 900; }
            QLabel#leftScore { color: #f4d35e; }
            QLabel#rightScore { color: #ef6f6c; }
            QLabel#status { color: #f7f4ea; background: #0d1b2a; border: 2px solid #26435b; padding: 10px; font-family: Arial; font-size: 13px; font-weight: 700; }
            QLabel#hints { color: #6f8ba1; font-family: Arial; font-size: 11px; font-weight: 700; }
            QPushButton { min-height: 46px; color: #f7f4ea; background: #11283c; border: 2px solid #31536d; padding: 10px 18px; font-family: Arial; font-size: 12px; font-weight: 900; }
            QPushButton:hover { background: #1a3b55; }
            QPushButton:disabled { color: #587286; background: #0a1725; border-color: #1c3142; }
            QPushButton#startButton { color: #06101d; background: #f4d35e; border-color: #f4d35e; }
            QPushButton#startButton:hover { background: #ffe98f; }
            QPushButton#restartButton { color: #06101d; background: #ef6f6c; border-color: #ef6f6c; }
            QPushButton#restartButton:hover { background: #ff8b87; }
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
        self.left_score.setText(f"{snapshot.left_score:02d}")
        self.right_score.setText(f"{snapshot.right_score:02d}")
        self.pause_button.setEnabled(snapshot.status in (MatchStatus.RUNNING, MatchStatus.PAUSED))
        if snapshot.status is MatchStatus.READY:
            self.status_label.setText("Pronto. Inicie a partida para soltar a bola.")
            self.start_button.setText("INICIAR JOGO")
        elif snapshot.status is MatchStatus.RUNNING:
            self.status_label.setText("Partida em andamento. Rebate a bola e proteja seu lado.")
            self.start_button.setText("JOGO ATIVO")
        elif snapshot.status is MatchStatus.PAUSED:
            self.status_label.setText("Ponto marcado ou partida pausada. Clique em continuar.")
            self.start_button.setText("CONTINUAR")
        else:
            winner = "JOGADOR 1" if snapshot.winner is Side.LEFT else "JOGADOR 2"
            self.status_label.setText(f"{winner} venceu! Reinicie para uma nova partida.")
            self.start_button.setText("JOGO ENCERRADO")
        self.start_button.setEnabled(snapshot.status in (MatchStatus.READY, MatchStatus.PAUSED))

    def _show_point(self, event) -> None:
        scorer = "Jogador 1" if event.scorer is Side.LEFT else "Jogador 2"
        if event.match_finished:
            self.status_label.setText(f"{scorer} alcançou 5 pontos e venceu a partida.")
        else:
            self.status_label.setText(f"Ponto para {scorer}. Clique em continuar para sacar.")

    def eventFilter(self, watched, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            key_event = event
            if isinstance(key_event, QKeyEvent):
                direction = 0 if event.type() is QEvent.Type.KeyRelease else 1
                if key_event.key() == Qt.Key.Key_W:
                    self._worker.set_input(Side.LEFT, -direction)
                    return True
                if key_event.key() == Qt.Key.Key_S:
                    self._worker.set_input(Side.LEFT, direction)
                    return True
                if key_event.key() == Qt.Key.Key_Up:
                    self._worker.set_input(Side.RIGHT, -direction)
                    return True
                if key_event.key() == Qt.Key.Key_Down:
                    self._worker.set_input(Side.RIGHT, direction)
                    return True
        return super().eventFilter(watched, event)

    def closeEvent(self, event) -> None:
        self._worker.stop()
        self._thread.quit()
        self._thread.wait(2000)
        event.accept()
