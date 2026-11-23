# Pong — Dupla

Jogo Pong para dois jogadores desenvolvido em Python 3.13, PyQt6 e Programação Orientada a Objetos.

## Executar

```bash
uv sync
uv run pong
```

## Controles

- Jogador 1: `W` sobe e `S` desce a raquete amarela.
- Jogador 2: `Seta para cima` sobe e `Seta para baixo` desce a raquete vermelha.
- **Iniciar Jogo** começa a partida.
- **Pausar Jogo** interrompe ou continua a partida.
- **Reiniciar Jogo** zera os pontos e reposiciona a bola e as raquetes.

O primeiro jogador a alcançar 5 pontos vence.

## Organização

```text
src/pong/
├── core/
│   ├── entities.py
│   └── worker.py
├── ui/
│   ├── board.py
│   └── main_window.py
├── __init__.py
└── main.py
```

- `Ball` guarda posição, velocidade, direção e movimentação da bola.
- `Paddle` controla posição, limites e colisão das raquetes.
- `Player` encapsula lado, nome e pontuação.
- `PongGame` coordena regras, colisões, pontos e estado da partida.
- `GameWorker` executa o processamento contínuo em uma thread dedicada.
- `PongBoard` desenha a quadra e recebe os controles.
- `MainWindow` organiza os controles, placar e comunicação com a thread.

## Thread e comunicação

A interface gráfica permanece na thread principal do Qt. O `GameWorker` é movido para uma `QThread` e executa um laço de atualização em aproximadamente 60 quadros por segundo. Cada atualização emite um `GameSnapshot` por sinal Qt, e a janela redesenha a quadra somente ao receber esse sinal.

Os comandos de iniciar, pausar, reiniciar e movimentar raquetes usam métodos protegidos por `RLock`. O encerramento sinaliza a thread, libera o laço e aguarda seu término antes de fechar a janela.

## Entregáveis

- [Relatório em PDF](docs/relatorio.pdf)
- [Fonte do relatório](docs/relatorio.html)
- [Vídeo demonstrativo](docs/video-demonstrativo.mp4)
- [Roteiro do vídeo](docs/roteiro-video.md)
