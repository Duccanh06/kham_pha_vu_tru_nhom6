"""
STELLAR VOID — Main Game Engine
Coordinates all subsystems: world, entities, rendering, input, AI, pathfinding.
"""
import pygame
import math
import random
import sys
import os

from constants import *
from sound_manager import SoundManager
from hand_controller import HandController
from entities import (Player, Asteroid, Enemy, AbandonedBase,
                      ResourcePickup, Particle, spawn_explosion)
from world import StarField, WorldGenerator
from hud import HUD, PathfindingOverlay
from screens import TrailerScreen, GameOverScreen, PauseScreen
from pathfinding import find_path, ALGORITHMS


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self._tx = 0.0
        self._ty = 0.0

    def follow(self, target_x, target_y):
        self._tx = target_x - SCREEN_W / 2
        self._ty = target_y - SCREEN_H / 2
        self._tx = max(0, min(WORLD_W - SCREEN_W, self._tx))
        self._ty = max(0, min(WORLD_H - SCREEN_H, self._ty))
        # Smooth follow
        self.x += (self._tx - self.x) * 0.1
        self.y += (self._ty - self.y) * 0.1


class GameEngine:
    STATE_TRAILER   = 'trailer'
    STATE_PLAYING   = 'playing'
    STATE_PAUSED    = 'paused'
    STATE_GAMEOVER  = 'gameover'

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # Systems
        self.sound   = SoundManager()
        self.hand    = HandController()
        self.camera  = Camera()

        # State
        self.state = self.STATE_TRAILER
        self.paused = False

        # Screens
        self.trailer_screen = TrailerScreen(self.screen)
        self.pause_screen   = PauseScreen(self.screen)
        self.gameover_screen = None

        # Game objects (populated in _new_game)
        self.player    = None
        self.asteroids = []
        self.bases     = []
        self.enemies   = []
        self.pickups   = []
        self.bullets   = []
        self.particles = []

        # HUD & overlay
        self.hud     = HUD()
        self.pf_overlay = PathfindingOverlay()
        self.show_map   = False

        # Pathfinding
        self.algo_names = list(ALGORITHMS.keys())
        self.algo_idx   = 2  # default A*
        self.pf_grid    = None

        # Camera feedback
        self.screen_shake = 0

        # FPS tracking
        self._fps_smooth = 60.0

    # ─── Public ───────────────────────────────────────────────────────────────
    def run(self):
        """Main game loop."""
        self.hand.start()
        while True:
            dt = self.clock.tick(FPS)
            self._fps_smooth = 0.95 * self._fps_smooth + 0.05 * self.clock.get_fps()

            for event in pygame.event.get():
                self._handle_event(event)

            self._update()
            self._draw()
            pygame.display.flip()

    # ─── Setup ────────────────────────────────────────────────────────────────
    def _new_game(self):
        gen = WorldGenerator()
        self.asteroids, self.bases, self.enemies, self.pickups = gen.generate()
        self.pf_grid = gen.make_pathfinding_grid(self.asteroids, self.bases)

        # Player starts at world center
        self.player = Player(WORLD_W // 2, WORLD_H // 2)
        self.bullets = []
        self.particles = []
        self.camera.x = self.player.x - SCREEN_W / 2
        self.camera.y = self.player.y - SCREEN_H / 2
        self.show_map = False
        self.pf_overlay.active = False
        self.hud.add_flash("STELLAR VOID — Bắt đầu hành trình!", CYAN, 150)
        self.hud.add_flash("E = Khám phá cơ sở  |  TAB = Đổi thuật toán", HUD_TEXT, 200)

    # ─── Events ───────────────────────────────────────────────────────────────
    def _handle_event(self, event):
        if event.type == pygame.QUIT:
            self._quit()

        if self.state == self.STATE_TRAILER:
            self.trailer_screen.handle_event(event)

        elif self.state == self.STATE_GAMEOVER:
            if self.gameover_screen:
                self.gameover_screen.handle_event(event)

        elif self.state in (self.STATE_PLAYING, self.STATE_PAUSED):
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_keydown(self, key):
        if key == pygame.K_ESCAPE:
            self._quit()
        if key == pygame.K_p:
            self.state = (self.STATE_PAUSED
                          if self.state == self.STATE_PLAYING
                          else self.STATE_PLAYING)
        if key == pygame.K_m and self.state == self.STATE_PLAYING:
            self.show_map = not self.show_map
            if self.show_map:
                self._run_pathfinding()
        if key == pygame.K_TAB:
            self.algo_idx = (self.algo_idx + 1) % len(self.algo_names)
            algo = self.algo_names[self.algo_idx]
            self.hud.add_flash(f"Thuật toán: {algo}", PATH_COLOR, 90)
            if self.show_map:
                self._run_pathfinding()
        if key == pygame.K_e and self.state == self.STATE_PLAYING:
            self._interact()

    # ─── Pathfinding ──────────────────────────────────────────────────────────
    def _run_pathfinding(self):
        if not self.pf_grid or not self.player:
            return
        rows = len(self.pf_grid)
        cols = len(self.pf_grid[0])
        cell_x = WORLD_W / cols
        cell_y = WORLD_H / rows

        # Start = player
        sc = int(self.player.x / cell_x)
        sr = int(self.player.y / cell_y)
        sc = max(0, min(cols-1, sc))
        sr = max(0, min(rows-1, sr))
        start = (sr, sc)

        # Goal = nearest base or random reachable cell
        goal = None
        min_dist = float('inf')
        for base in self.bases:
            bc = int(base.x / cell_x)
            br = int(base.y / cell_y)
            if 0 <= br < rows and 0 <= bc < cols and self.pf_grid[br][bc] != 1:
                d = math.hypot(br - sr, bc - sc)
                if d < min_dist:
                    min_dist = d
                    goal = (br, bc)

        if goal is None:
            # Random passable goal
            for _ in range(100):
                gr = random.randint(0, rows-1)
                gc = random.randint(0, cols-1)
                if self.pf_grid[gr][gc] != 1:
                    goal = (gr, gc)
                    break

        if goal is None or start == goal:
            return

        algo = self.algo_names[self.algo_idx]
        path, visited = find_path(self.pf_grid, start, goal, algo)
        self.pf_overlay.show(self.pf_grid, path, visited, start, goal, algo)
        self.hud.add_flash(
            f"{algo}: {len(path)} bước, khám phá {len(visited)} ô",
            PATH_COLOR, 120)

    # ─── Update ───────────────────────────────────────────────────────────────
    def _update(self):
        if self.state == self.STATE_TRAILER:
            self.trailer_screen.update()
            if self.trailer_screen.done:
                self._new_game()
                self.state = self.STATE_PLAYING
            return

        if self.state == self.STATE_GAMEOVER:
            if self.gameover_screen:
                self.gameover_screen.update()
                if self.gameover_screen.done:
                    self.state = self.STATE_TRAILER
                    self.trailer_screen = TrailerScreen(self.screen)
            return

        if self.state == self.STATE_PAUSED:
            self.pause_screen.update()
            return

        # ── PLAYING ──
        self._update_input()
        self._update_player()
        self._update_bullets()
        self._update_asteroids()
        self._update_enemies()
        self._update_bases()
        self._update_pickups()
        self._update_particles()
        self._update_collisions()
        self.camera.follow(self.player.x, self.player.y)
        if self.screen_shake > 0:
            self.screen_shake -= 1
        self.pf_overlay.update()

        if not self.player.alive:
            self._game_over('destroyed')

    def _update_input(self):
        """Keyboard + Hand Controller input."""
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        boost = False

        # Keyboard
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_LSHIFT]: boost = True

        shoot_kb = keys[pygame.K_SPACE]

        # Hand Controller override
        if self.hand.available:
            gesture = self.hand.gesture
            hdx, hdy = self.hand.direction
            if gesture == 'open':
                dx = hdx * 1.5
                dy = hdy * 1.5
            elif gesture == 'thumbs_up':
                boost = True
                dx = hdx
                dy = hdy
            elif gesture == 'fist':
                dx = hdx * 0.5
                dy = hdy * 0.5

            if self.hand.should_shoot:
                if self.player.can_shoot():
                    bullet = self.player.shoot()
                    self.bullets.append(bullet)
                    self.sound.play('laser', 0.4)

        # Apply movement
        if dx != 0 or dy != 0:
            self.player.move(dx, dy, boost)

        # Keyboard shoot
        if shoot_kb:
            if self.player.can_shoot():
                bullet = self.player.shoot()
                self.bullets.append(bullet)
                self.sound.play('laser', 0.4)

    def _update_player(self):
        self.player.update()

    def _update_bullets(self):
        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.alive]

    def _update_asteroids(self):
        new_children = []
        for ast in self.asteroids:
            ast.update()
        # Remove dead ones, spawn children
        dead = [a for a in self.asteroids if not a.alive]
        for a in dead:
            children = a.get_children()
            new_children.extend(children)
            spawn_explosion(self.particles, a.x, a.y, big=(a.size=='large'))
            self.sound.play('explosion' if a.size=='large' else 'hit', 0.5)
            if a.resource != 'none':
                self.pickups.append(ResourcePickup(a.x, a.y, a.resource,
                                                    random.randint(4,12)))
            self.player.score += {'large':50,'medium':25,'small':10}[a.size]
        self.asteroids = [a for a in self.asteroids if a.alive] + new_children

    def _update_enemies(self):
        new_bullets = []
        for en in self.enemies:
            en.update(self.player.x, self.player.y)
            if en.can_shoot(self.player.x, self.player.y):
                new_bullets.append(en.shoot())
                self.sound.play('hit', 0.2)
        self.bullets.extend(new_bullets)
        self.enemies = [e for e in self.enemies if e.alive]

    def _update_bases(self):
        for base in self.bases:
            base.update()
        self.bases = [b for b in self.bases if b.alive]

    def _update_pickups(self):
        for pk in self.pickups:
            pk.update()
        self.pickups = [p for p in self.pickups if p.alive]

    def _update_particles(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def _update_collisions(self):
        cx, cy = self.camera.x, self.camera.y

        # Bullets vs asteroids
        for b in self.bullets[:]:
            if not b.friendly:
                continue
            for ast in self.asteroids:
                if math.hypot(b.x - ast.x, b.y - ast.y) < ast.radius:
                    ast.take_damage(b.damage)
                    b.alive = False
                    spawn_explosion(self.particles, b.x, b.y)
                    break

        # Bullets vs enemies
        for b in self.bullets[:]:
            if not b.friendly:
                continue
            for en in self.enemies:
                if math.hypot(b.x - en.x, b.y - en.y) < 18:
                    en.take_damage(b.damage)
                    b.alive = False
                    spawn_explosion(self.particles, b.x, b.y)
                    if not en.alive:
                        self.player.score += 100
                        spawn_explosion(self.particles, en.x, en.y, big=True)
                        self.sound.play('big_exp', 0.6)
                        self.hud.add_flash("+100 Tiêu diệt kẻ thù!", RED_BRIGHT, 80)
                    break

        # Enemy bullets vs player
        for b in self.bullets[:]:
            if b.friendly:
                continue
            if math.hypot(b.x - self.player.x, b.y - self.player.y) < 22:
                self.player.take_damage(b.damage)
                b.alive = False
                self.sound.play('shield' if self.player.shield > 0 else 'hit', 0.5)
                self.screen_shake = 8
                if self.player.shield <= 0:
                    self.hud.add_flash("⚠ HULL DAMAGE!", RED_BRIGHT, 60)

        # Asteroids vs player
        for ast in self.asteroids:
            if math.hypot(ast.x - self.player.x, ast.y - self.player.y) < ast.radius + 20:
                self.player.take_damage(8)
                ast.take_damage(20)
                self.screen_shake = 10
                self.sound.play('hit', 0.4)

        # Pickups vs player
        for pk in self.pickups[:]:
            if math.hypot(pk.x - self.player.x, pk.y - self.player.y) < 35:
                if pk.kind in self.player.resources:
                    self.player.resources[pk.kind] += pk.amount
                    self.player.score += pk.amount * 5
                    pk.alive = False
                    self.sound.play('pickup', 0.5)
                    self.hud.add_flash(f"+{pk.amount} {pk.kind.upper()}", GOLD, 60)

    def _interact(self):
        """Player interacts with nearest base."""
        nearest_base = None
        min_d = float('inf')
        for base in self.bases:
            d = math.hypot(base.x - self.player.x, base.y - self.player.y)
            if d < 120 and d < min_d:
                min_d = d
                nearest_base = base
        if nearest_base:
            rewards = nearest_base.interact(self.player)
            if rewards:
                self.sound.play('pickup', 0.7)
                parts = [f"+{v} {k.upper()}" for k,v in rewards.items()]
                self.hud.add_flash(f"KHÁM PHÁ: {', '.join(parts)}", GREEN, 150)
                self.hud.add_flash(f"+200 XP — {nearest_base.name} [{nearest_base.room_type}]", GOLD, 120)
                self.player.score += 200
                spawn_explosion(self.particles, nearest_base.x, nearest_base.y)
            else:
                self.hud.add_flash("Đã khám phá rồi!", HUD_TEXT, 60)
        else:
            self.hud.add_flash("Không có gì gần đây để tương tác", HUD_TEXT, 60)

    def _game_over(self, cause):
        self.state = self.STATE_GAMEOVER
        self.gameover_screen = GameOverScreen(
            self.screen, self.player.score, self.player.resources, cause)
        self.sound.play('big_exp', 0.8)

    # ─── Draw ─────────────────────────────────────────────────────────────────
    def _draw(self):
        if self.state == self.STATE_TRAILER:
            self.trailer_screen.draw()
            return

        if self.state == self.STATE_GAMEOVER:
            if self.gameover_screen:
                self.gameover_screen.draw()
            return

        # Shake offset
        shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake else 0
        shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake else 0
        cx = self.camera.x + shake_x
        cy = self.camera.y + shake_y

        # Background starfield
        if not hasattr(self, '_starfield'):
            self._starfield = StarField()
        self._starfield.draw(self.screen, cx, cy)

        # World objects
        for pk in self.pickups:
            pk.draw(self.screen, cx, cy)
        for base in self.bases:
            base.draw(self.screen, cx, cy)
        for ast in self.asteroids:
            ast.draw(self.screen, cx, cy)
        for en in self.enemies:
            en.draw(self.screen, cx, cy)
        for p in self.particles:
            p.draw(self.screen, cx, cy)
        for b in self.bullets:
            b.draw(self.screen, cx, cy)
        self.player.draw(self.screen, cx, cy)

        # HUD
        algo_name = self.algo_names[self.algo_idx]
        self.hud.draw(self.screen, self.player, cx, cy,
                      self._fps_smooth, algo_name,
                      self.hand if self.hand.available else None)

        # Pathfinding overlay
        if self.show_map:
            self.pf_overlay.draw(self.screen)

        # Camera frame from hand controller
        if self.hand.available and self.hand.frame is not None:
            try:
                import cv2
                import numpy as np
                frame = self.hand.frame
                small = cv2.resize(frame, (240, 135))
                small_rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                cam_surf = pygame.surfarray.make_surface(
                    np.transpose(small_rgb, (1, 0, 2)))
                # Border
                pygame.draw.rect(cam_surf, PURPLE, (0,0,240,135), 2)
                self.screen.blit(cam_surf, (SCREEN_W - 250, SCREEN_H - 175))
                lbl = self.hud.font_sm.render("📷 AI Camera", True, PURPLE)
                self.screen.blit(lbl, (SCREEN_W - 250, SCREEN_H - 188))
            except Exception:
                pass

        # Pause overlay
        if self.state == self.STATE_PAUSED:
            self.pause_screen.draw()

    def _quit(self):
        self.hand.stop()
        pygame.quit()
        sys.exit()
