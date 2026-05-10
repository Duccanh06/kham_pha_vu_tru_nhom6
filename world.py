"""World generation and space background renderer"""
import pygame
import math
import random
from constants import *
from entities import Asteroid, Enemy, AbandonedBase, ResourcePickup


class StarField:
    """Multi-layer parallax star field."""
    def __init__(self, seed=42):
        rng = random.Random(seed)
        self.layers = []
        # Layer: (stars_list, parallax_factor)
        # Each star: (x, y, radius, brightness, twinkle_offset)
        for factor, count, max_r in [(0.1, 300, 1), (0.3, 200, 1.5), (0.6, 100, 2)]:
            stars = []
            for _ in range(count):
                x = rng.uniform(0, SCREEN_W * 3)
                y = rng.uniform(0, SCREEN_H * 3)
                r = rng.uniform(0.5, max_r)
                b = rng.uniform(120, 255)
                twinkle = rng.uniform(0, math.tau)
                tint = rng.choice([(255,255,255),(200,220,255),(255,200,180),(180,255,200)])
                stars.append((x, y, r, b, twinkle, tint))
            self.layers.append((stars, factor))
        self._frame = 0

        # Nebula clouds
        self._nebula = []
        for _ in range(6):
            nx = rng.uniform(0, WORLD_W)
            ny = rng.uniform(0, WORLD_H)
            nr = rng.randint(300, 800)
            nc = rng.choice([
                (20, 10, 60), (10, 30, 60), (40, 10, 50),
                (10, 40, 50), (30, 60, 20), (60, 20, 40)
            ])
            self._nebula.append((nx, ny, nr, nc))

    def draw(self, surf, cam_x, cam_y):
        self._frame += 1
        surf.fill(DEEP_SPACE)

        # Nebulas (very slow parallax)
        for nx, ny, nr, nc in self._nebula:
            px = (nx - cam_x * 0.05) % (SCREEN_W * 1.5) - SCREEN_W * 0.25
            py = (ny - cam_y * 0.05) % (SCREEN_H * 1.5) - SCREEN_H * 0.25
            if -nr < px < SCREEN_W+nr and -nr < py < SCREEN_H+nr:
                ns = pygame.Surface((nr*2, nr*2), pygame.SRCALPHA)
                r, g, b = nc
                for rr in range(nr, 0, -nr//8):
                    alpha = int(20 * (1 - rr/nr))
                    pygame.draw.circle(ns, (r, g, b, alpha), (nr, nr), rr)
                surf.blit(ns, (int(px)-nr, int(py)-nr))

        # Stars
        for stars, factor in self.layers:
            for sx, sy, r, b, twinkle, tint in stars:
                px = (sx - cam_x * factor) % SCREEN_W
                py = (sy - cam_y * factor) % SCREEN_H
                # Twinkle
                bright = b + 30 * math.sin(self._frame * 0.05 + twinkle)
                bright = max(0, min(255, int(bright)))
                tr, tg, tb = tint
                col = (int(tr*bright/255), int(tg*bright/255), int(tb*bright/255))
                if r <= 1:
                    surf.set_at((int(px), int(py)), col)
                else:
                    pygame.draw.circle(surf, col, (int(px), int(py)), int(r))


class WorldGenerator:
    def __init__(self, seed=None):
        self.seed = seed or random.randint(0, 99999)
        self.rng  = random.Random(self.seed)
        print(f"[World] Seed: {self.seed}")

    def generate(self):
        """Returns (asteroids, bases, enemies, pickups)"""
        rng = self.rng

        asteroids = []
        for _ in range(ASTEROID_COUNT):
            x = rng.uniform(200, WORLD_W - 200)
            y = rng.uniform(200, WORLD_H - 200)
            size = rng.choices(['large','medium','small'], weights=[2,3,5])[0]
            asteroids.append(Asteroid(x, y, size))

        bases = []
        for _ in range(ABANDONED_BASE_COUNT):
            x = rng.uniform(500, WORLD_W - 500)
            y = rng.uniform(500, WORLD_H - 500)
            bases.append(AbandonedBase(x, y))

        enemies = []
        for _ in range(ENEMY_COUNT):
            x = rng.uniform(300, WORLD_W - 300)
            y = rng.uniform(300, WORLD_H - 300)
            enemies.append(Enemy(x, y))

        pickups = []
        kinds = ['ore','ore','ore','crystal','tech']
        for _ in range(RESOURCE_COUNT):
            x = rng.uniform(100, WORLD_W - 100)
            y = rng.uniform(100, WORLD_H - 100)
            kind = rng.choice(kinds)
            amt  = rng.randint(3, 12)
            pickups.append(ResourcePickup(x, y, kind, amt))

        return asteroids, bases, enemies, pickups

    def make_pathfinding_grid(self, asteroids, bases, rows=MAP_ROWS, cols=MAP_COLS):
        """Build a grid for pathfinding demos."""
        grid = [[0]*cols for _ in range(rows)]
        cell_x = WORLD_W / cols
        cell_y = WORLD_H / rows

        # Place walls from asteroid positions
        for ast in asteroids:
            c = int(ast.x / cell_x)
            r = int(ast.y / cell_y)
            if 0 <= r < rows and 0 <= c < cols:
                if ast.size == 'large':
                    grid[r][c] = 1
                    # Neighbors as high-cost
                    for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                            grid[nr][nc] = 2
                elif ast.size == 'medium':
                    if grid[r][c] != 1:
                        grid[r][c] = 3
                else:
                    pass  # small = passable but expensive

        # Place walls from bases
        for base in bases:
            c = int(base.x / cell_x)
            r = int(base.y / cell_y)
            if 0 <= r < rows and 0 <= c < cols:
                grid[r][c] = 0  # bases are passable (interesting to visit)

        return grid
