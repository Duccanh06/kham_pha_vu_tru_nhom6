"""Constants and game configuration"""
import math

# ─── WINDOW ───────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
TITLE = "STELLAR VOID — Space Survival"

# ─── COLORS ───────────────────────────────────────────────────────────────────
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
DEEP_SPACE  = (4, 6, 18)
NEBULA_BLUE = (10, 20, 60)

CYAN        = (0, 220, 255)
CYAN_DIM    = (0, 100, 140)
ORANGE      = (255, 140, 0)
ORANGE_DIM  = (180, 80, 0)
RED         = (220, 50, 50)
RED_BRIGHT  = (255, 80, 80)
GREEN       = (50, 220, 100)
GREEN_DIM   = (30, 120, 60)
YELLOW      = (255, 220, 50)
PURPLE      = (180, 60, 220)
PURPLE_DIM  = (80, 20, 100)
GOLD        = (255, 200, 50)
SILVER      = (180, 190, 200)
TEAL        = (0, 200, 180)

SHIP_BODY   = (60, 160, 220)
SHIP_ACCENT = (0, 240, 255)
SHIP_ENGINE = (255, 160, 40)
SHIP_GLOW   = (0, 180, 255)

ASTEROID_COLOR  = (120, 100, 80)
ASTEROID_CRACK  = (80, 65, 50)
BASE_WALL       = (60, 55, 70)
BASE_LIGHT      = (100, 180, 200)

HUD_BG      = (8, 15, 30, 180)
HUD_BORDER  = (0, 180, 255)
HUD_TEXT    = (180, 230, 255)

PATH_COLOR  = (255, 200, 0)
BFS_COLOR   = (50, 255, 100)
DFS_COLOR   = (255, 100, 50)
ASTAR_COLOR = (100, 200, 255)
DIJ_COLOR   = (255, 50, 200)

PARTICLE_COLORS = [(255,200,100),(255,150,50),(255,100,50),(200,80,30),(255,220,150)]

# ─── GAMEPLAY ─────────────────────────────────────────────────────────────────
WORLD_W, WORLD_H = 5000, 5000
TILE_SIZE = 64
CHUNK_SIZE = 16  # tiles per chunk

PLAYER_SPEED = 4.5
PLAYER_MAX_HP = 100
PLAYER_SHIELD = 50
BULLET_SPEED = 12
BULLET_DAMAGE = 15
BULLET_LIFETIME = 60

ASTEROID_COUNT = 80
ABANDONED_BASE_COUNT = 6
ENEMY_COUNT = 25
RESOURCE_COUNT = 120

# ─── MAP GRID (for pathfinding demo) ──────────────────────────────────────────
MAP_ROWS = 30
MAP_COLS = 40
CELL_W = SCREEN_W // MAP_COLS
CELL_H = (SCREEN_H - 120) // MAP_ROWS
