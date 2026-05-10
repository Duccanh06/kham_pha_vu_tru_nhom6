"""Cinematic intro trailer screen for STELLAR VOID"""
import pygame
import math
import random
from constants import *


class TrailerScreen:
    """Full animated intro/trailer before the game starts."""
    SCENES = [
        {
            'duration': 180,
            'title': '',
            'subtitle': '',
            'bg_color': BLACK,
            'text_lines': [],
        },
        {
            'duration': 220,
            'title': 'STELLAR VOID',
            'subtitle': 'Vũ trụ... rộng lớn và hoang vắng',
            'text_lines': [],
        },
        {
            'duration': 200,
            'title': 'KHÁM PHÁ',
            'subtitle': 'Hàng trăm thiên thạch bí ẩn\nvà cơ sở bỏ hoang chứa đựng kho báu',
            'text_lines': [],
        },
        {
            'duration': 200,
            'title': 'SINH TỒN',
            'subtitle': 'Đối mặt với kẻ thù không gian\nQuản lý tài nguyên để tồn tại',
            'text_lines': [],
        },
        {
            'duration': 200,
            'title': 'TRÍ TUỆ NHÂN TẠO',
            'subtitle': 'Điều khiển bằng cử chỉ tay qua camera\nAI MediaPipe nhận diện chuyển động thực',
            'text_lines': [],
        },
        {
            'duration': 200,
            'title': 'THUẬT TOÁN',
            'subtitle': 'BFS  •  DFS  •  A*  •  Dijkstra\nKẻ thù sử dụng AI tìm đường thông minh',
            'text_lines': [],
        },
        {
            'duration': 240,
            'title': 'STELLAR VOID',
            'subtitle': 'Nhấn ENTER để bắt đầu hành trình\nNhấn SPACE để bỏ qua',
            'text_lines': [],
        },
    ]

    def __init__(self, screen):
        self.screen = screen
        self.scene_idx = 0
        self.scene_timer = 0
        self.done = False
        self.skip = False
        self.stars = []
        self._gen_stars()
        self._particles = []
        self._ship_x = SCREEN_W + 200
        self._ship_y = SCREEN_H // 2
        self._ship_angle = math.pi
        self._global_timer = 0
        self._logo_scale = 0.0

        self.font_xl  = pygame.font.SysFont("consolas", 72, bold=True)
        self.font_lg  = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_md  = pygame.font.SysFont("consolas", 20)
        self.font_sm  = pygame.font.SysFont("consolas", 15)

        # Pre-render title glow
        self._title_cache = {}

    def _gen_stars(self):
        for _ in range(400):
            self.stars.append({
                'x': random.uniform(0, SCREEN_W),
                'y': random.uniform(0, SCREEN_H),
                'spd': random.uniform(0.3, 3.5),
                'r': random.uniform(0.5, 2.5),
                'col': random.choice([WHITE,(200,220,255),(255,200,180),(180,200,255)]),
            })

    def _update_stars(self):
        for st in self.stars:
            st['x'] -= st['spd']
            if st['x'] < 0:
                st['x'] = SCREEN_W
                st['y'] = random.uniform(0, SCREEN_H)

    def _draw_stars(self):
        self.screen.fill(DEEP_SPACE)
        for st in self.stars:
            c = st['col']
            r = st['r']
            x, y = int(st['x']), int(st['y'])
            if r <= 1:
                self.screen.set_at((x, y), c)
            else:
                pygame.draw.circle(self.screen, c, (x,y), int(r))

    def _draw_title_glow(self, text, cx, cy, size=72, color=CYAN):
        """Draw text with glow effect."""
        font = pygame.font.SysFont("consolas", size, bold=True)
        # Glow layers
        for glow_r in [4, 2]:
            glow_font = pygame.font.SysFont("consolas", size + glow_r*2, bold=True)
            g_surf = glow_font.render(text, True, (color[0]//3, color[1]//3, color[2]//3))
            g_surf.set_alpha(80)
            gx = cx - g_surf.get_width()//2
            gy = cy - g_surf.get_height()//2
            self.screen.blit(g_surf, (gx, gy))
        # Main text
        t = font.render(text, True, color)
        self.screen.blit(t, (cx - t.get_width()//2, cy - t.get_height()//2))

    def _draw_scene(self, scene):
        t = self.scene_timer
        dur = scene['duration']
        fade_in  = min(1.0, t / 40)
        fade_out = min(1.0, (dur - t) / 40) if t > dur - 40 else 1.0
        alpha = int(255 * fade_in * fade_out)

        title    = scene.get('title', '')
        subtitle = scene.get('subtitle', '')

        if title:
            # Determine color by scene
            colors = [CYAN, GOLD, CYAN, RED_BRIGHT, PURPLE, ASTAR_COLOR, CYAN]
            col = colors[min(self.scene_idx, len(colors)-1)]
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

            # Title
            tf = pygame.font.SysFont("consolas", 68, bold=True)
            ts = tf.render(title, True, col)
            ts.set_alpha(alpha)
            tx = SCREEN_W//2 - ts.get_width()//2
            ty = SCREEN_H//2 - 80
            overlay.blit(ts, (tx, ty))
            self.screen.blit(ts, (tx, ty))

            # Decorative line
            if alpha > 50:
                lw = int(ts.get_width() * 0.8 * fade_in)
                lx = SCREEN_W//2 - lw//2
                ly = ty + ts.get_height() + 5
                pygame.draw.line(self.screen, (*col, alpha), (lx, ly), (lx+lw, ly), 2)

            # Subtitle (multiline)
            if subtitle:
                sf = pygame.font.SysFont("consolas", 22)
                for i, line in enumerate(subtitle.split('\n')):
                    ss = sf.render(line, True, WHITE)
                    ss.set_alpha(alpha)
                    sx = SCREEN_W//2 - ss.get_width()//2
                    sy = ty + ts.get_height() + 25 + i * 30
                    self.screen.blit(ss, (sx, sy))

        # Scene 0: just black fade
        if self.scene_idx == 0:
            fade_surf = pygame.Surface((SCREEN_W, SCREEN_H))
            fade_surf.fill(BLACK)
            fade_surf.set_alpha(max(0, 255 - alpha))
            self.screen.blit(fade_surf, (0,0))

    def _draw_ship_flyby(self):
        """Animated spaceship flying across the screen."""
        sx, sy = int(self._ship_x), int(self._ship_y)
        a = self._ship_angle

        if not (0 < sx < SCREEN_W + 100):
            return

        c, s = math.cos(a), math.sin(a)
        L = 32

        def rot(dx, dy):
            return (sx + c*dx - s*dy, sy + s*dx + c*dy)

        hull  = [rot(L,0), rot(-L*.5,L*.5), rot(-L*.7,0), rot(-L*.5,-L*.5)]
        lwing = [rot(-.1*L,.3*L), rot(-.5*L,1.6*L), rot(-.7*L,.9*L)]
        rwing = [rot(-.1*L,-.3*L), rot(-.5*L,-1.6*L), rot(-.7*L,-.9*L)]

        pygame.draw.polygon(self.screen, SHIP_BODY, [(int(x),int(y)) for x,y in hull])
        pygame.draw.polygon(self.screen, SHIP_ACCENT, [(int(x),int(y)) for x,y in hull], 2)
        for wing in [lwing, rwing]:
            pygame.draw.polygon(self.screen, (40,100,180), [(int(x),int(y)) for x,y in wing])

        # Engine glow
        eng = rot(-L*.72, 0)
        for r, al in [(14,30),(9,70),(5,140),(3,220)]:
            gs = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*SHIP_ENGINE, al), (r,r), r)
            self.screen.blit(gs, (int(eng[0])-r, int(eng[1])-r))

        # Trail
        for i in range(20):
            tx = sx + c*(L*.72 + i*8) + random.uniform(-2,2)
            ty = sy + s*(L*.72 + i*8) + random.uniform(-2,2)
            al = int(180 * (1 - i/20))
            ts = pygame.Surface((6,6), pygame.SRCALPHA)
            orange_dim = (255, 140-i*5, 0)
            pygame.draw.circle(ts, (*orange_dim, al), (3,3), 3)
            self.screen.blit(ts, (int(tx)-3, int(ty)-3))

    def _draw_corner_decoration(self):
        """Sci-fi corner brackets."""
        cols = [HUD_BORDER, CYAN_DIM]
        blen = 40
        bthick = 2
        positions = [(0,0,1,1),(SCREEN_W,0,-1,1),(0,SCREEN_H,1,-1),(SCREEN_W,SCREEN_H,-1,-1)]
        for cx, cy, xd, yd in positions:
            for i, c in enumerate(cols):
                offset = i * 8
                pygame.draw.line(self.screen, c,
                    (cx+xd*offset, cy+yd*offset),
                    (cx+xd*(offset+blen), cy+yd*offset), bthick)
                pygame.draw.line(self.screen, c,
                    (cx+xd*offset, cy+yd*offset),
                    (cx+xd*offset, cy+yd*(offset+blen)), bthick)

    def _draw_progress_bar(self):
        """Total scenes progress at bottom."""
        total = sum(s['duration'] for s in self.SCENES)
        elapsed = sum(self.SCENES[i]['duration'] for i in range(self.scene_idx)) + self.scene_timer
        progress = elapsed / total
        bw = SCREEN_W - 100
        bx = 50
        by = SCREEN_H - 18
        pygame.draw.rect(self.screen, (20,30,50), (bx, by, bw, 6))
        pygame.draw.rect(self.screen, CYAN, (bx, by, int(bw*progress), 6))
        pygame.draw.rect(self.screen, CYAN_DIM, (bx, by, bw, 6), 1)
        skip_txt = self.font_sm.render("SPACE = Bỏ qua  |  ENTER = Bắt đầu ngay", True, (80,80,100))
        self.screen.blit(skip_txt, (SCREEN_W//2 - skip_txt.get_width()//2, SCREEN_H-38))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.done = True
            if event.key == pygame.K_RETURN:
                self.done = True

    def update(self):
        if self.done:
            return
        self._global_timer += 1
        self.scene_timer += 1
        self._update_stars()

        # Advance ship
        if 2 <= self.scene_idx <= 4:
            self._ship_x -= 2.5
            self._ship_y = SCREEN_H//2 + math.sin(self._global_timer * 0.02) * 40
            if self._ship_x < -200:
                self._ship_x = SCREEN_W + 200

        # Next scene
        cur = self.SCENES[self.scene_idx]
        if self.scene_timer >= cur['duration']:
            self.scene_timer = 0
            self.scene_idx += 1
            if self.scene_idx >= len(self.SCENES):
                self.done = True

    def draw(self):
        self._draw_stars()
        self._draw_scene(self.SCENES[self.scene_idx])
        if 1 <= self.scene_idx <= 5:
            self._draw_ship_flyby()
        self._draw_corner_decoration()
        self._draw_progress_bar()


class GameOverScreen:
    def __init__(self, screen, score, resources, cause='destroyed'):
        self.screen = screen
        self.score = score
        self.resources = resources
        self.cause = cause
        self.done = False
        self._timer = 0
        self.font_xl = pygame.font.SysFont("consolas", 64, bold=True)
        self.font_lg = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_md = pygame.font.SysFont("consolas", 20)
        self._particles = [
            {'x': random.uniform(0, SCREEN_W), 'y': random.uniform(0, SCREEN_H),
             'vx': random.uniform(-1,1), 'vy': random.uniform(-1,1),
             'col': random.choice([RED, ORANGE, YELLOW]),
             'r': random.randint(1,3)}
            for _ in range(80)
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                self.done = True

    def update(self):
        self._timer += 1
        for p in self._particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.02
            if p['y'] > SCREEN_H:
                p['y'] = 0
                p['x'] = random.uniform(0, SCREEN_W)

    def draw(self):
        self.screen.fill((8, 2, 2))
        for p in self._particles:
            pygame.draw.circle(self.screen, p['col'], (int(p['x']),int(p['y'])), p['r'])

        a = min(1.0, self._timer / 60)
        alpha = int(a * 255)

        # Title
        title = "GAME OVER" if self.cause == 'destroyed' else "MISSION COMPLETE"
        col   = RED_BRIGHT if self.cause == 'destroyed' else GOLD
        t = self.font_xl.render(title, True, col)
        t.set_alpha(alpha)
        self.screen.blit(t, (SCREEN_W//2 - t.get_width()//2, 160))

        # Cause
        causes = {
            'destroyed': 'Tàu của bạn đã bị phá hủy!',
            'win': 'Bạn đã khám phá toàn bộ vũ trụ!',
        }
        c2 = self.font_lg.render(causes.get(self.cause, ''), True, WHITE)
        c2.set_alpha(alpha)
        self.screen.blit(c2, (SCREEN_W//2 - c2.get_width()//2, 260))

        # Stats
        y = 330
        for line in [
            f"Điểm số cuối: {self.score:,}",
            f"Quặng: {self.resources.get('ore', 0)}   Tinh thể: {self.resources.get('crystal', 0)}   Công nghệ: {self.resources.get('tech', 0)}",
        ]:
            s = self.font_md.render(line, True, HUD_TEXT)
            s.set_alpha(alpha)
            self.screen.blit(s, (SCREEN_W//2 - s.get_width()//2, y))
            y += 35

        # Prompt
        if self._timer > 90:
            blink = (self._timer // 30) % 2 == 0
            if blink:
                p = self.font_md.render("Nhấn ENTER hoặc R để chơi lại", True, CYAN)
                self.screen.blit(p, (SCREEN_W//2 - p.get_width()//2, SCREEN_H - 100))


class PauseScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font_xl = pygame.font.SysFont("consolas", 52, bold=True)
        self.font_md = pygame.font.SysFont("consolas", 22)
        self._timer  = 0

    def update(self):
        self._timer += 1

    def draw(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((5, 10, 20, 180))
        self.screen.blit(overlay, (0,0))

        t = self.font_xl.render("⏸  TẠM DỪNG", True, CYAN)
        self.screen.blit(t, (SCREEN_W//2 - t.get_width()//2, SCREEN_H//2 - 60))

        lines = [
            "P — Tiếp tục chơi",
            "M — Hiển thị Pathfinding Map",
            "TAB — Đổi thuật toán tìm đường",
            "ESC — Thoát game",
        ]
        y = SCREEN_H//2 + 20
        for line in lines:
            s = self.font_md.render(line, True, HUD_TEXT)
            self.screen.blit(s, (SCREEN_W//2 - s.get_width()//2, y))
            y += 32
