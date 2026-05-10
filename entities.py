"""Game entities — Player, Asteroid, Enemy, AbandonedBase, Bullet, Particle"""
import pygame
import math
import random
from constants import *


# ─── Particle ────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, vx, vy, color, life=30, size=3):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.life  = life
        self.max_life = life
        self.size  = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.vx *= 0.97
        self.life -= 1

    def draw(self, surf, cam_x, cam_y):
        if self.life <= 0:
            return
        alpha = self.life / self.max_life
        r, g, b = self.color
        col = (int(r*alpha), int(g*alpha), int(b*alpha))
        s = max(1, int(self.size * alpha))
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if -50 < sx < SCREEN_W+50 and -50 < sy < SCREEN_H+50:
            pygame.draw.circle(surf, col, (sx, sy), s)


def spawn_explosion(particles, x, y, big=False):
    count = 40 if big else 20
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1, 5 if big else 3)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        col = random.choice(PARTICLE_COLORS)
        life = random.randint(20, 50 if big else 35)
        size = random.randint(2, 5 if big else 4)
        particles.append(Particle(x, y, vx, vy, col, life, size))


# ─── Bullet ──────────────────────────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, angle, damage=BULLET_DAMAGE, friendly=True):
        self.x, self.y = x, y
        self.vx = math.cos(angle) * BULLET_SPEED
        self.vy = math.sin(angle) * BULLET_SPEED
        self.damage = damage
        self.friendly = friendly
        self.life  = BULLET_LIFETIME
        self.alive = True
        self.trail = []

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surf, cx, cy):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i+1) / len(self.trail)
            col = (int(0*alpha), int(200*alpha), int(255*alpha)) if self.friendly \
                  else (int(255*alpha), int(80*alpha), int(30*alpha))
            r = max(1, int(2*alpha))
            pygame.draw.circle(surf, col,
                                (int(tx-cx), int(ty-cy)), r)
        # Head
        hx, hy = int(self.x-cx), int(self.y-cy)
        if -10 < hx < SCREEN_W+10 and -10 < hy < SCREEN_H+10:
            col = CYAN if self.friendly else RED_BRIGHT
            pygame.draw.circle(surf, col, (hx, hy), 4)
            # Glow
            glow_surf = pygame.Surface((16,16), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*col, 60), (8,8), 8)
            surf.blit(glow_surf, (hx-8, hy-8))


# ─── Player ──────────────────────────────────────────────────────────────────
class Player:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.angle = -math.pi / 2  # pointing up
        self.hp    = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.shield = PLAYER_SHIELD
        self.max_shield = PLAYER_SHIELD
        self.shield_regen_timer = 0
        self.fuel   = 100.0
        self.score  = 0
        self.resources = {'ore': 0, 'crystal': 0, 'tech': 0}
        self.alive  = True
        self.invincible = 0  # frames of invincibility after hit
        self.boost_cooldown = 0
        self.engine_trail = []
        self._shoot_cooldown = 0

    def move(self, dx, dy, boost=False):
        speed = PLAYER_SPEED * (1.8 if boost else 1.0)
        if dx != 0 or dy != 0:
            mag = math.hypot(dx, dy)
            self.vx += (dx / mag) * 0.6
            self.vy += (dy / mag) * 0.6
            self.angle = math.atan2(dy, dx)
        # Clamp speed
        spd = math.hypot(self.vx, self.vy)
        max_spd = speed
        if spd > max_spd:
            self.vx = self.vx / spd * max_spd
            self.vy = self.vy / spd * max_spd

    def update(self):
        self.x += self.vx
        self.y += self.vy
        # Friction
        self.vx *= 0.88
        self.vy *= 0.88
        # Clamp world
        self.x = max(50, min(WORLD_W - 50, self.x))
        self.y = max(50, min(WORLD_H - 50, self.y))
        # Shield regen
        if self.shield < self.max_shield:
            self.shield_regen_timer += 1
            if self.shield_regen_timer > 180:
                self.shield = min(self.max_shield, self.shield + 0.3)
        else:
            self.shield_regen_timer = 0
        if self.invincible > 0:
            self.invincible -= 1
        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= 1
        # Engine trail
        ex = self.x - math.cos(self.angle) * 22
        ey = self.y - math.sin(self.angle) * 22
        self.engine_trail.append((ex, ey))
        if len(self.engine_trail) > 18:
            self.engine_trail.pop(0)

    def take_damage(self, dmg):
        if self.invincible > 0:
            return
        if self.shield > 0:
            absorbed = min(self.shield, dmg)
            self.shield -= absorbed
            dmg -= absorbed
        self.hp -= dmg
        self.invincible = 45
        self.shield_regen_timer = 0
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def can_shoot(self):
        return self._shoot_cooldown <= 0

    def shoot(self):
        self._shoot_cooldown = 12
        return Bullet(self.x, self.y, self.angle, BULLET_DAMAGE, friendly=True)

    def draw(self, surf, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy)
        if not (-100 < sx < SCREEN_W+100 and -100 < sy < SCREEN_H+100):
            return

        # Engine trail
        for i, (tx, ty) in enumerate(self.engine_trail):
            alpha = (i + 1) / len(self.engine_trail)
            r = max(1, int(4 * alpha))
            c1 = int(255 * alpha * 0.8)
            c2 = int(160 * alpha * 0.5)
            pygame.draw.circle(surf, (c1, c2, 0),
                                (int(tx-cx), int(ty-cy)), r)

        # Draw ship body (polygon)
        self._draw_ship(surf, sx, sy)

        # Shield visual
        if self.shield > 10:
            alpha_s = int(60 * self.shield / self.max_shield)
            shield_surf = pygame.Surface((80,80), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (0,180,255,alpha_s), (40,40), 34)
            pygame.draw.circle(shield_surf, (0,220,255,alpha_s//2), (40,40), 34, 2)
            surf.blit(shield_surf, (sx-40, sy-40))

    def _draw_ship(self, surf, sx, sy):
        a = self.angle
        # Ship parameters
        L = 26  # length
        W = 14  # half-width

        def rot(dx, dy):
            c, s = math.cos(a), math.sin(a)
            return (sx + c*dx - s*dy, sy + s*dx + c*dy)

        # Main hull
        hull = [rot(L, 0), rot(-L*0.5, W), rot(-L*0.7, 0), rot(-L*0.5, -W)]
        pygame.draw.polygon(surf, SHIP_BODY, [(int(x),int(y)) for x,y in hull])
        pygame.draw.polygon(surf, SHIP_ACCENT, [(int(x),int(y)) for x,y in hull], 2)

        # Cockpit
        ckpt = [rot(L*0.85, 0), rot(L*0.1, W*0.55), rot(L*0.05, 0), rot(L*0.1, -W*0.55)]
        pygame.draw.polygon(surf, CYAN_DIM, [(int(x),int(y)) for x,y in ckpt])
        pygame.draw.polygon(surf, CYAN, [(int(x),int(y)) for x,y in ckpt], 1)

        # Left wing
        lwing = [rot(-L*0.1, W*0.3), rot(-L*0.5, W*1.6), rot(-L*0.7, W*0.9)]
        pygame.draw.polygon(surf, SHIP_BODY, [(int(x),int(y)) for x,y in lwing])
        pygame.draw.polygon(surf, SHIP_ACCENT, [(int(x),int(y)) for x,y in lwing], 1)

        # Right wing
        rwing = [rot(-L*0.1, -W*0.3), rot(-L*0.5, -W*1.6), rot(-L*0.7, -W*0.9)]
        pygame.draw.polygon(surf, SHIP_BODY, [(int(x),int(y)) for x,y in rwing])
        pygame.draw.polygon(surf, SHIP_ACCENT, [(int(x),int(y)) for x,y in rwing], 1)

        # Engine glow
        eng_c = rot(-L*0.72, 0)
        for r, alpha in [(12,40),(8,80),(5,140),(3,220)]:
            gs = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*SHIP_ENGINE, alpha), (r+1,r+1), r)
            surf.blit(gs, (int(eng_c[0])-r-1, int(eng_c[1])-r-1))

        # Weapon pods (small bumps on wings)
        for side in [1, -1]:
            pod = rot(-L*0.25, side*W*1.2)
            pygame.draw.circle(surf, ORANGE, (int(pod[0]), int(pod[1])), 4)
            pygame.draw.circle(surf, YELLOW, (int(pod[0]), int(pod[1])), 2)

        # Direction indicator
        front = rot(L+5, 0)
        pygame.draw.circle(surf, CYAN, (int(front[0]), int(front[1])), 2)

        # Flicker during invincibility
        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            overlay = pygame.Surface((60,60), pygame.SRCALPHA)
            pygame.draw.circle(overlay, (255,255,255,60), (30,30), 28)
            surf.blit(overlay, (sx-30, sy-30))


# ─── Asteroid ─────────────────────────────────────────────────────────────────
class Asteroid:
    def __init__(self, x, y, size='large'):
        self.x, self.y = float(x), float(y)
        sizes = {'large': (45,60), 'medium': (25,40), 'small': (10,20)}
        lo, hi = sizes.get(size, (20,40))
        self.radius = random.randint(lo, hi)
        self.size = size
        speed = {'large':0.4,'medium':0.8,'small':1.4}[size]
        angle = random.uniform(0, math.tau)
        self.vx = math.cos(angle) * random.uniform(0, speed)
        self.vy = math.sin(angle) * random.uniform(0, speed)
        self.rot = 0.0
        self.rot_speed = random.uniform(-0.02, 0.02)
        self.hp = self.radius * 3
        self.max_hp = self.hp
        self.alive = True
        # Shape: random polygon
        nv = random.randint(8, 13)
        self.shape = []
        for i in range(nv):
            a = i * math.tau / nv + random.uniform(-0.2, 0.2)
            r = self.radius * random.uniform(0.7, 1.0)
            self.shape.append((math.cos(a)*r, math.sin(a)*r))
        # Resource drop
        self.resource = random.choice(['ore','ore','ore','crystal','tech','none'])
        self.has_crack = random.random() < 0.4
        self.crack_lines = self._gen_cracks()

    def _gen_cracks(self):
        lines = []
        for _ in range(random.randint(2,4)):
            a = random.uniform(0, math.tau)
            r1 = random.uniform(0.1, 0.4) * self.radius
            r2 = random.uniform(0.5, 0.9) * self.radius
            lines.append((math.cos(a)*r1, math.sin(a)*r1,
                           math.cos(a)*r2, math.sin(a)*r2))
        return lines

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rot += self.rot_speed
        # Wrap world
        self.x = self.x % WORLD_W
        self.y = self.y % WORLD_H

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False

    def get_children(self):
        if self.size == 'large':
            return [Asteroid(self.x + random.randint(-30,30),
                             self.y + random.randint(-30,30), 'medium')
                    for _ in range(2)]
        if self.size == 'medium':
            return [Asteroid(self.x + random.randint(-15,15),
                             self.y + random.randint(-15,15), 'small')
                    for _ in range(2)]
        return []

    def draw(self, surf, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy)
        if not (-100 < sx < SCREEN_W+100 and -100 < sy < SCREEN_H+100):
            return

        # Rotate polygon
        c, s = math.cos(self.rot), math.sin(self.rot)
        pts = [(int(sx + c*px - s*py), int(sy + s*px + c*py))
               for px, py in self.shape]
        pygame.draw.polygon(surf, ASTEROID_COLOR, pts)
        pygame.draw.polygon(surf, ASTEROID_CRACK, pts, 2)

        # Crack lines
        if self.has_crack:
            for x1,y1,x2,y2 in self.crack_lines:
                rx1 = int(sx + c*x1 - s*y1)
                ry1 = int(sy + s*x1 + c*y1)
                rx2 = int(sx + c*x2 - s*y2)
                ry2 = int(sy + s*x2 + c*y2)
                pygame.draw.line(surf, ASTEROID_CRACK, (rx1,ry1), (rx2,ry2), 1)

        # HP bar if damaged
        if self.hp < self.max_hp:
            bw = self.radius * 2
            bx = sx - self.radius
            by = sy - self.radius - 8
            pygame.draw.rect(surf, RED, (bx, by, bw, 4))
            pygame.draw.rect(surf, GREEN, (bx, by, int(bw*self.hp/self.max_hp), 4))

        # Glow if resource-rich
        if self.resource == 'crystal':
            glow = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (100,180,255,25),
                               (self.radius*2, self.radius*2), self.radius*2)
            surf.blit(glow, (sx - self.radius*2, sy - self.radius*2))


# ─── Enemy ───────────────────────────────────────────────────────────────────
class Enemy:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.hp    = 60
        self.max_hp = 60
        self.speed = random.uniform(1.5, 2.8)
        self.angle = 0.0
        self.alive = True
        self.shoot_timer = random.randint(60, 120)
        self.patrol_angle = random.uniform(0, math.tau)
        self.state = 'patrol'   # patrol / chase / attack
        self.path = []
        self._flash = 0

    def update(self, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        self.angle = math.atan2(dy, dx)

        if dist < 600:
            self.state = 'chase'
        elif dist > 800:
            self.state = 'patrol'

        if self.state == 'chase':
            self.x += (dx / max(dist, 1)) * self.speed
            self.y += (dy / max(dist, 1)) * self.speed
        else:
            self.patrol_angle += 0.01
            self.x += math.cos(self.patrol_angle) * 1.0
            self.y += math.sin(self.patrol_angle) * 0.8

        self.x = max(50, min(WORLD_W-50, self.x))
        self.y = max(50, min(WORLD_H-50, self.y))
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self._flash > 0:
            self._flash -= 1

    def can_shoot(self, player_x, player_y):
        if self.shoot_timer > 0:
            return False
        dist = math.hypot(player_x-self.x, player_y-self.y)
        if dist < 450:
            self.shoot_timer = random.randint(80,160)
            return True
        return False

    def shoot(self):
        return Bullet(self.x, self.y, self.angle, 12, friendly=False)

    def take_damage(self, dmg):
        self.hp -= dmg
        self._flash = 8
        if self.hp <= 0:
            self.alive = False

    def draw(self, surf, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy)
        if not (-80 < sx < SCREEN_W+80 and -80 < sy < SCREEN_H+80):
            return

        a = self.angle
        c, s = math.cos(a), math.sin(a)

        def rot(dx, dy):
            return (sx + c*dx - s*dy, sy + s*dx + c*dy)

        # Enemy ship (aggressive look)
        hull = [rot(20,0), rot(-10,12), rot(-14,0), rot(-10,-12)]
        col = RED if self._flash == 0 else WHITE
        pygame.draw.polygon(surf, col, [(int(x),int(y)) for x,y in hull])
        pygame.draw.polygon(surf, RED_BRIGHT, [(int(x),int(y)) for x,y in hull], 2)

        # Wings
        lwing = [rot(0,4), rot(-14,18), rot(-16,8)]
        rwing = [rot(0,-4), rot(-14,-18), rot(-16,-8)]
        for wing in [lwing, rwing]:
            pygame.draw.polygon(surf, (150,30,30), [(int(x),int(y)) for x,y in wing])

        # Core glow
        eng = rot(-14, 0)
        for r, al in [(8,30),(5,70),(3,130)]:
            gs = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (255,60,0,al), (r,r), r)
            surf.blit(gs, (int(eng[0])-r, int(eng[1])-r))

        # HP bar
        bw = 30
        by = sy - 28
        pygame.draw.rect(surf, RED_BRIGHT, (sx-15, by, bw, 3))
        pygame.draw.rect(surf, GREEN, (sx-15, by, int(bw*self.hp/self.max_hp), 3))


# ─── Abandoned Base ──────────────────────────────────────────────────────────
class AbandonedBase:
    ROOMS = ['storage','lab','quarters','reactor','hangar','bridge']

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.name = f"Station-{random.randint(100,999)}"
        self.room_type = random.choice(self.ROOMS)
        self.explored = False
        self.loot = self._gen_loot()
        self.hp = 200
        self.max_hp = 200
        self.alive = True
        # Visual: random layout
        self.modules = self._gen_modules()
        self.lights = self._gen_lights()
        self._pulse = 0

    def _gen_loot(self):
        loot = {}
        if random.random() < 0.9:
            loot['ore'] = random.randint(5, 25)
        if random.random() < 0.6:
            loot['crystal'] = random.randint(3, 15)
        if random.random() < 0.4:
            loot['tech'] = random.randint(1, 5)
        if random.random() < 0.3:
            loot['hp_pack'] = random.randint(20, 50)
        return loot

    def _gen_modules(self):
        """List of (dx, dy, w, h) relative rectangles."""
        mods = [(0, 0, 80, 60)]  # main hull
        if random.random() < 0.7:
            mods.append((-50, -20, 40, 30))   # left wing
        if random.random() < 0.7:
            mods.append((70, -10, 40, 25))    # right bay
        if random.random() < 0.5:
            mods.append((20, 55, 30, 35))     # docking tube
        if random.random() < 0.5:
            mods.append((-20, -50, 25, 30))   # sensor tower
        return mods

    def _gen_lights(self):
        lights = []
        for _ in range(random.randint(3, 7)):
            lights.append({
                'dx': random.randint(-60, 120),
                'dy': random.randint(-60, 80),
                'on': random.random() < 0.6,
                'timer': random.randint(0, 90),
                'rate': random.randint(40, 120),
                'col': random.choice([BASE_LIGHT, ORANGE, RED, GREEN_DIM])
            })
        return lights

    def update(self):
        self._pulse = (self._pulse + 1) % 120
        for light in self.lights:
            light['timer'] = (light['timer'] + 1) % light['rate']
            if light['timer'] == 0:
                light['on'] = not light['on']

    def interact(self, player):
        """Player explores the base, gets loot."""
        if self.explored:
            return None
        self.explored = True
        rewards = {}
        for k, v in self.loot.items():
            if k == 'hp_pack':
                player.hp = min(player.max_hp, player.hp + v)
                rewards['hp'] = v
            elif k in player.resources:
                player.resources[k] += v
                rewards[k] = v
        player.score += 200
        return rewards

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False

    def draw(self, surf, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy)
        if not (-200 < sx < SCREEN_W+200 and -200 < sy < SCREEN_H+200):
            return

        # Draw modules
        for (dx, dy, w, h) in self.modules:
            r = pygame.Rect(sx+dx, sy+dy, w, h)
            pygame.draw.rect(surf, BASE_WALL, r)
            pygame.draw.rect(surf, (90,85,105), r, 2)
            # Panel lines
            for lx in range(sx+dx+10, sx+dx+w-5, 12):
                pygame.draw.line(surf, (50,45,60), (lx, sy+dy+2), (lx, sy+dy+h-2), 1)

        # Lights
        for lt in self.lights:
            lx = sx + lt['dx']
            ly = sy + lt['dy']
            if not (-10 < lx < SCREEN_W+10 and -10 < ly < SCREEN_H+10):
                continue
            if lt['on']:
                col = lt['col']
                gls = pygame.Surface((14,14), pygame.SRCALPHA)
                pygame.draw.circle(gls, (*col, 100), (7,7), 7)
                surf.blit(gls, (lx-7, ly-7))
                pygame.draw.circle(surf, col, (lx, ly), 3)
            else:
                pygame.draw.circle(surf, (40,35,45), (lx, ly), 3)

        # Name tag
        if not self.explored:
            # Pulsing indicator
            pulse_a = int(128 + 127 * math.sin(self._pulse * math.pi / 60))
            ind = pygame.Surface((16,16), pygame.SRCALPHA)
            pygame.draw.circle(ind, (0,200,255,pulse_a), (8,8), 6)
            surf.blit(ind, (sx+30, sy-20))

        # Explored marker
        if self.explored:
            pygame.draw.circle(surf, GREEN_DIM, (sx+30, sy-20), 5)

        # Damage visual
        if self.hp < self.max_hp * 0.5:
            for _ in range(1):
                px = sx + random.randint(0, 80)
                py = sy + random.randint(0, 60)
                ps = pygame.Surface((4,4), pygame.SRCALPHA)
                pygame.draw.circle(ps, (255,150,50,random.randint(100,200)), (2,2), 2)
                surf.blit(ps, (px-2, py-2))


# ─── Resource Pickup ─────────────────────────────────────────────────────────
class ResourcePickup:
    def __init__(self, x, y, kind='ore', amount=5):
        self.x, self.y = float(x), float(y)
        self.kind = kind
        self.amount = amount
        self.alive  = True
        self.bob    = random.uniform(0, math.tau)
        self._colors = {'ore':(200,150,80),'crystal':(100,180,255),'tech':(80,220,150)}

    def update(self):
        self.bob += 0.06
        self.y += math.sin(self.bob) * 0.15

    def draw(self, surf, cx, cy):
        sx = int(self.x - cx)
        sy = int(self.y - cy)
        if not (-20 < sx < SCREEN_W+20 and -20 < sy < SCREEN_H+20):
            return
        col = self._colors.get(self.kind, WHITE)
        # Glow
        gs = pygame.Surface((28,28), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*col, 60), (14,14), 12)
        surf.blit(gs, (sx-14, sy-14))
        # Core shape
        if self.kind == 'ore':
            pts = [(sx,sy-7),(sx+6,sy+4),(sx-6,sy+4)]
            pygame.draw.polygon(surf, col, pts)
        elif self.kind == 'crystal':
            pts = [(sx,sy-8),(sx+5,sy-1),(sx+3,sy+7),(sx-3,sy+7),(sx-5,sy-1)]
            pygame.draw.polygon(surf, col, pts)
        else:
            pygame.draw.rect(surf, col, (sx-5,sy-5,10,10))
            pygame.draw.line(surf, WHITE, (sx-3,sy-3),(sx+3,sy+3),1)
            pygame.draw.line(surf, WHITE, (sx+3,sy-3),(sx-3,sy+3),1)
        pygame.draw.circle(surf, WHITE, (sx,sy), 2)
