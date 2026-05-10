#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    STELLAR VOID — SPACE SURVIVAL                        ║
║                          LAUNCHER SCRIPT                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

CÀI ĐẶT (lần đầu):
    pip install pygame opencv-python mediapipe numpy

CHẠY GAME:
    python launch.py
    hoặc: python main.py (trong thư mục space_survival/)

ĐIỀU KHIỂN:
┌────────────────────────────────────────────────────────┐
│  KEYBOARD                                               │
│  W/A/S/D hoặc ↑←↓→  : Di chuyển tàu                  │
│  SPACE               : Bắn đạn                         │
│  E                   : Khám phá cơ sở bỏ hoang         │
│  SHIFT+WASD          : Tăng tốc                        │
│  M                   : Hiện/ẩn bản đồ pathfinding      │
│  TAB                 : Đổi thuật toán (BFS/DFS/A*/Dij) │
│  P                   : Pause                           │
│  ESC                 : Thoát                           │
├────────────────────────────────────────────────────────┤
│  AI HAND CONTROL (cần webcam)                          │
│  ✋ Mở tay       : Di chuyển tàu theo hướng ngón trỏ  │
│  👊 Nắm tay      : Bắn đạn                            │
│  ✌️ Hai ngón     : Tương tác với cơ sở                │
│  👍 Ngón cái     : Tăng tốc boost                     │
│  🤏 Chụm ngón    : Pause/Menu                         │
└────────────────────────────────────────────────────────┘

THUẬT TOÁN PATHFINDING:
  • BFS (Breadth-First Search)  — Tìm đường ngắn nhất không có trọng số
  • DFS (Depth-First Search)    — Khám phá sâu, không tối ưu  
  • A* (A-Star)                 — Tối ưu với heuristic Manhattan/Euclidean
  • Dijkstra                    — Tối ưu với địa hình có trọng số khác nhau
  Nhấn M để xem animation trực tiếp trong game!

MỤC TIÊU GAME:
  ★ Khám phá tất cả cơ sở bỏ hoang để thu thập tài nguyên
  ★ Phá hủy thiên thạch để lấy quặng, tinh thể, công nghệ
  ★ Tiêu diệt kẻ thù để kiếm điểm
  ★ Sinh tồn càng lâu càng tốt!
"""

import os
import sys

# Ensure we can find game modules
game_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'space_survival')
if os.path.exists(game_dir):
    sys.path.insert(0, game_dir)
    os.chdir(game_dir)
else:
    # Already in game dir
    pass

print("=" * 60)
print("  STELLAR VOID — SPACE SURVIVAL GAME")
print("  Phiên bản: 1.0 | Python + Pygame + MediaPipe")
print("=" * 60)
print()
print("Kiểm tra thư viện...")

missing = []
try:
    import pygame
    print(f"  ✓ pygame {pygame.version.ver}")
except ImportError:
    missing.append('pygame')
    print("  ✗ pygame MISSING")

try:
    import cv2
    print(f"  ✓ opencv {cv2.__version__}")
except ImportError:
    print("  ⚠ opencv không có — AI hand control tắt (tùy chọn)")

try:
    import mediapipe as mp
    print(f"  ✓ mediapipe {mp.__version__}")
except ImportError:
    print("  ⚠ mediapipe không có — AI hand control tắt (tùy chọn)")

try:
    import numpy as np
    print(f"  ✓ numpy {np.__version__}")
except ImportError:
    missing.append('numpy')
    print("  ✗ numpy MISSING")

if missing:
    print()
    print(f"Thiếu thư viện bắt buộc: {', '.join(missing)}")
    print(f"Chạy: pip install {' '.join(missing)}")
    sys.exit(1)

print()
print("Khởi động game...")
print("(Nhấn ESC hoặc đóng cửa sổ để thoát)")
print()

from game_engine import GameEngine
engine = GameEngine()
engine.run()
