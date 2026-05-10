"""HUD (Heads-Up Display) and all in-game UI elements"""
import pygame
import math
import random
from constants import *


def draw_bar(surf, x, y, w, h, value, max_val, fg_col, bg_col=(30,30,50), border=True):
    pygame.draw.rect(surf, bg_col, (x, y, w, h))
    fill = int(w * max(0, value) / max(1, max_val))
    if fill > 0:
        pygame.draw.rect(surf, fg_col, (x, y, fill, h))
    if border:
        pygame.draw.rect(surf, HUD_BORDER, (x, y, w, h), 1)


class HUD:
    def __init__(self, font_path=None):
        self.font_lg = pygame.font.SysFont("consolas", 22, bold=True)
        self.font_md = pygame.font.SysFont("consolas", 16)
        self.font_sm = pygame.font.SysFont("consolas", 13)
        self.font_xl = pygame.font.SysFont("consolas", 36, bold=True)
        self.flash_messages = []   # (text, ttl, color)
        self.notification_timer = 0

    def add_flash(self, text, color=CYAN, ttl=120):
        self.flash_messages.append([text, ttl, color])

    def draw(self, surf, player, cam_x, cam_y, fps, algo_name, hand_ctrl=None):
        self._draw_panel(surf, player)
        self._draw_minimap(surf, player, cam_x, cam_y)
        self._draw_status(surf, fps, algo_name)
        self._draw_resources(surf, player)
        self._draw_flash(surf)
        if hand_ctrl and hand_ctrl.available:
            self._draw_hand_status(surf, hand_ctrl)

    def _draw_panel(self, surf, player):
        # Left panel bg
        panel = pygame.Surface((230, 140), pygame.SRCALPHA)
        panel.fill((5, 12, 28, 200))
        pygame.draw.rect(panel, HUD_BORDER, (0,0,230,140), 2)
        surf.blit(panel, (10, 10))

        # HP
        surf.blit(self.font_sm.render("HULL", True, (180,100,100)), (18, 16))
        draw_bar(surf, 70, 18, 150, 14, player.hp, player.max_hp, RED_BRIGHT)
        hp_txt = self.font_sm.render(f"{int(player.hp)}/{player.max_hp}", True, WHITE)
        surf.blit(hp_txt, (224 - hp_txt.get_width(), 18))

        # Shield
        surf.blit(self.font_sm.render("SHIELD", True, (100,150,220)), (18, 38))
        draw_bar(surf, 70, 40, 150, 14, player.shield, player.max_shield, CYAN)
        sh_txt = self.font_sm.render(f"{int(player.shield)}/{player.max_shield}", True, WHITE)
        surf.blit(sh_txt, (224 - sh_txt.get_width(), 40))

        # Fuel / score
        surf.blit(self.font_sm.render("FUEL", True, (100,220,150)), (18, 58))
        draw_bar(surf, 70, 60, 150, 14, player.fuel, 100, GREEN)

        # Score
        score_txt = self.font_md.render(f"SCORE: {player.score:,}", True, GOLD)
        surf.blit(score_txt, (18, 80))

        # Coords
        coord_txt = self.font_sm.render(
            f"POS  {int(player.x):5d} , {int(player.y):5d}", True, HUD_TEXT)
        surf.blit(coord_txt, (18, 102))

        # Speed
        spd = math.hypot(player.vx, player.vy)
        spd_txt = self.font_sm.render(f"SPD  {spd*10:.1f} km/s", True, HUD_TEXT)
        surf.blit(spd_txt, (18, 120))

    def _draw_resources(self, surf, player):
        rx, ry = 10, 158
        panel = pygame.Surface((230, 60), pygame.SRCALPHA)
        panel.fill((5,12,28,200))
        pygame.draw.rect(panel, (60,60,100), (0,0,230,60), 1)
        surf.blit(panel, (rx, ry))

        icons = [('ORE', player.resources['ore'], (200,150,80)),
                 ('CRYS', player.resources['crystal'], (100,180,255)),
                 ('TECH', player.resources['tech'], (80,220,150))]
        for i, (label, val, col) in enumerate(icons):
            x = rx + 10 + i * 75
            lbl = self.font_sm.render(label, True, col)
            surf.blit(lbl, (x, ry + 8))
            val_txt = self.font_md.render(str(val), True, WHITE)
            surf.blit(val_txt, (x, ry + 26))

    def _draw_minimap(self, surf, player, cam_x, cam_y):
        mx, my, mw, mh = SCREEN_W - 170, 10, 160, 120
        panel = pygame.Surface((mw, mh), pygame.SRCALPHA)
        panel.fill((5, 10, 25, 210))
        surf.blit(panel, (mx, my))
        pygame.draw.rect(surf, HUD_BORDER, (mx, my, mw, mh), 2)

        sx_label = self.font_sm.render("SECTOR MAP", True, CYAN_DIM)
        surf.blit(sx_label, (mx + 5, my + 4))

        # Player dot
        px = mx + int(player.x / WORLD_W * mw)
        py = my + int(player.y / WORLD_H * mh)
        pygame.draw.circle(surf, CYAN, (px, py), 3)

        # Camera view box
        vx1 = mx + int(cam_x / WORLD_W * mw)
        vy1 = my + int(cam_y / WORLD_H * mh)
        vw  = int(SCREEN_W / WORLD_W * mw)
        vh  = int(SCREEN_H / WORLD_H * mh)
        pygame.draw.rect(surf, (0,100,150), (vx1, vy1, vw, vh), 1)

    def _draw_status(self, surf, fps, algo_name):
        # Bottom bar
        bx, by, bw, bh = 0, SCREEN_H - 36, SCREEN_W, 36
        bar = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bar.fill((3, 8, 20, 220))
        pygame.draw.rect(bar, HUD_BORDER, (0,0,bw,bh), 1)
        surf.blit(bar, (bx, by))

        fps_txt = self.font_md.render(f"FPS: {int(fps):3d}", True, GREEN_DIM)
        surf.blit(fps_txt, (10, by + 9))

        algo_txt = self.font_md.render(f"PATHFIND: {algo_name}", True, ASTAR_COLOR)
        surf.blit(algo_txt, (100, by + 9))

        ctrl_txt = self.font_md.render(
            "WASD:Move  SPACE:Shoot  E:Interact  M:Map  P:Pause  TAB:Algo", True, (100,120,150))
        surf.blit(ctrl_txt, (320, by + 9))

    def _draw_flash(self, surf):
        self.flash_messages = [[t, ttl-1, c] for t, ttl, c in self.flash_messages if ttl > 0]
        cy = SCREEN_H // 2 - 80
        for text, ttl, col in self.flash_messages[-4:]:
            alpha = min(255, int(ttl * 3.5))
            txt_surf = self.font_lg.render(text, True, col)
            txt_surf.set_alpha(alpha)
            rx = SCREEN_W // 2 - txt_surf.get_width() // 2
            surf.blit(txt_surf, (rx, cy))
            cy += 32

    def _draw_hand_status(self, surf, hand_ctrl):
        gst = hand_ctrl.gesture
        dx, dy = hand_ctrl.direction
        # Small panel top center
        px, py, pw, ph = SCREEN_W//2 - 120, 10, 240, 52
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((5, 15, 35, 200))
        pygame.draw.rect(panel, PURPLE, (0,0,pw,ph), 2)
        surf.blit(panel, (px, py))

        icons = {
            'none': '✋ IDLE', 'open': f'✋ MOVE ({dx:+.2f},{dy:+.2f})',
            'fist': '👊 SHOOT', 'peace': '✌️ INTERACT',
            'thumbs_up': '👍 BOOST', 'pinch': '🤏 PAUSE',
        }
        label = icons.get(gst, gst.upper())
        col = GREEN if gst != 'none' else (100,80,120)
        txt = self.font_md.render(f"🤖 AI CTRL: {label}", True, col)
        surf.blit(txt, (px + 8, py + 8))
        cam_txt = self.font_sm.render("Camera Active — Hand Gestures Control Ship", True, PURPLE_DIM)
        surf.blit(cam_txt, (px + 8, py + 30))


class PathfindingOverlay:
    """Visualizes BFS/DFS/A*/Dijkstra on a mini grid panel."""
    def __init__(self):
        self.font = pygame.font.SysFont("consolas", 12)
        self.active = False
        self.grid   = None
        self.path   = []
        self.visited= []
        self.start  = None
        self.goal   = None
        self.algo   = 'A*'
        self._anim_frame = 0
        self._show_visited = True

    def show(self, grid, path, visited, start, goal, algo):
        self.grid = grid
        self.path = path
        self.visited = visited
        self.start = start
        self.goal  = goal
        self.algo  = algo
        self.active = True
        self._anim_frame = 0

    def update(self):
        if self.active:
            self._anim_frame = min(self._anim_frame + 3, len(self.visited))

    def draw(self, surf):
        if not self.active or self.grid is None:
            return

        rows = len(self.grid)
        cols = len(self.grid[0])
        panel_x = SCREEN_W//2 - 380
        panel_y = SCREEN_H//2 - 220
        pw = 760
        ph = 440
        cw = pw // cols
        ch = ph // rows

        # Background
        bg = pygame.Surface((pw + 20, ph + 60), pygame.SRCALPHA)
        bg.fill((5, 10, 25, 230))
        pygame.draw.rect(bg, HUD_BORDER, (0,0,pw+20,ph+60), 2)
        surf.blit(bg, (panel_x-10, panel_y-40))

        title_font = pygame.font.SysFont("consolas", 18, bold=True)
        colors = {'BFS':BFS_COLOR,'DFS':DFS_COLOR,'A*':ASTAR_COLOR,'Dijkstra':DIJ_COLOR}
        col = colors.get(self.algo, WHITE)
        title = title_font.render(
            f"PATHFINDING: {self.algo}  |  Visited:{len(self.visited)}  Path:{len(self.path)}  [M to close]",
            True, col)
        surf.blit(title, (panel_x, panel_y - 30))

        # Draw grid
        for r in range(rows):
            for c in range(cols):
                rx = panel_x + c * cw
                ry = panel_y + r * ch
                cell_val = self.grid[r][c]
                if cell_val == 1:
                    color = (60, 50, 80)   # wall
                elif cell_val == 2:
                    color = (80, 60, 30)   # debris
                elif cell_val == 3:
                    color = (100, 70, 30)  # asteroid
                else:
                    color = (10, 18, 35)   # empty

                pygame.draw.rect(surf, color, (rx, ry, cw-1, ch-1))

        # Visited nodes (animated)
        visited_col = colors.get(self.algo, WHITE)
        for i, (r,c) in enumerate(self.visited[:self._anim_frame]):
            if (r,c) == self.start or (r,c) == self.goal:
                continue
            rx = panel_x + c * cw
            ry = panel_y + r * ch
            alpha = int(100 + 80 * (i / max(1, len(self.visited))))
            vs = pygame.Surface((cw-1, ch-1), pygame.SRCALPHA)
            vr, vg, vb = visited_col
            vs.fill((vr, vg, vb, min(alpha, 160)))
            surf.blit(vs, (rx, ry))

        # Path
        for r, c in self.path:
            if (r,c) == self.start or (r,c) == self.goal:
                continue
            rx = panel_x + c * cw
            ry = panel_y + r * ch
            ps = pygame.Surface((cw-1, ch-1), pygame.SRCALPHA)
            ps.fill((*PATH_COLOR, 200))
            surf.blit(ps, (rx, ry))

        # Start / Goal
        if self.start:
            r, c = self.start
            sx = panel_x + c * cw
            sy = panel_y + r * ch
            pygame.draw.rect(surf, GREEN, (sx, sy, cw-1, ch-1))
            surf.blit(self.font.render("S", True, BLACK), (sx+1, sy+1))

        if self.goal:
            r, c = self.goal
            gx = panel_x + c * cw
            gy = panel_y + r * ch
            pygame.draw.rect(surf, GOLD, (gx, gy, cw-1, ch-1))
            surf.blit(self.font.render("G", True, BLACK), (gx+1, gy+1))

        # Legend
        leg_y = panel_y + ph + 5
        items = [("Start", GREEN), ("Goal", GOLD), ("Path", PATH_COLOR),
                 ("Visited", visited_col), ("Wall", (60,50,80))]
        lx = panel_x
        for label, color in items:
            pygame.draw.rect(surf, color, (lx, leg_y, 14, 14))
            surf.blit(self.font.render(label, True, WHITE), (lx+18, leg_y))
            lx += 90
