"""
╔══════════════════════════════════════════════════════════════╗
║          STELLAR VOID - SPACE SURVIVAL GAME v1.0             ║
║     Khám phá thiên thạch & Cơ sở bỏ hoang trong vũ trụ      ║
╚══════════════════════════════════════════════════════════════╝

Controls:
  - WASD / Arrow Keys: Di chuyển tàu
  - SPACE: Bắn đạn
  - E: Tương tác / Khám phá
  - M: Bản đồ
  - P: Pause
  - AI Hand Control (qua camera):
      ✋ Mở tay: Di chuyển (ngón tay trỏ = hướng)
      👊 Nắm tay: Bắn đạn
      ✌️ Hai ngón: Tương tác

Algorithms: BFS, DFS, A*, Dijkstra
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_engine import GameEngine

def main():
    engine = GameEngine()
    engine.run()

if __name__ == "__main__":
    main()
