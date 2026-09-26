"""pygame-Loop, Kamera und 2.5D-Rendering (T-004, Deliverable 3).

Fixed-Timestep-Update (60 Hz), Rendering mit Parallax-Layern pro Biome-Palette
aus assets/ (Falls Asset fehlt: deterministischer Platzhalter aus der Palette —
keine Blockade durch T-005). Side-Scrolling-Kamera mit Lookahead.
"""
from __future__ import annotations

import os

import pygame

from .constants import (
    CAMERA_LOOKAHEAD,
    FIXED_DT,
    FPS,
    GRAVITY,
    IFRAME_TICKS,
    JUMP_VELOCITY,
    MAX_FALL_SPEED,
    MOVE_SPEED,
    NODE_WORLD_H,
    NODE_WORLD_W,
    WINDOW_H,
    WINDOW_W,
)
from .data import GameData
from .player import Player
from .rooms import WorldLayout


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


class ParallaxLayer:
    """Eine Parallax-Ebene; lädt assets/<biome>/parallax_<layer>.png, sonst Platzhalter."""

    def __init__(self, data: GameData, biome_id: str, layer_name: str, factor: float):
        self.factor = factor
        palette = data.biomes[biome_id].get("palette_hint", ["#000000"] * 4)
        self.color = _hex_to_rgb(palette[min(1, len(palette) - 1)])
        path = os.path.join(str(data.root), "assets", biome_id, f"parallax_{layer_name}.png")
        if os.path.isfile(path):
            try:
                surface = pygame.image.load(path).convert_alpha()
                self.surface = pygame.transform.scale(surface, (NODE_WORLD_W, NODE_WORLD_H))
            except pygame.error:
                self.surface = None
        else:
            self.surface = None


class Game:
    """Display-Modus: Engine-Loop gegen echte Daten + Assets."""

    def __init__(self, data: GameData, player: Player, seed: int = 1):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Lumenfall")
        self.clock = pygame.time.Clock()
        self.data = data
        self.player = player
        self.layout = WorldLayout(data, seed)

        # Spieler-Physik-Zustand (Node-Lokal)
        self.node_id = data.start_node
        self.px = 100.0
        self.py = float(NODE_WORLD_H - 48.0 - 48.0)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.on_ground = True
        self.iframes = 0

        # Parallax-Layer pro Biome (far/mid/near), lazy gecacht
        self._parallax: dict[str, list[ParallaxLayer]] = {}
        self.running = True

    def _layers_for(self, biome_id: str) -> list[ParallaxLayer]:
        if biome_id not in self._parallax:
            factors = {"far": 0.25, "mid": 0.5, "near": 0.75}
            self._parallax[biome_id] = [
                ParallaxLayer(self.data, biome_id, name, factor) for name, factor in factors.items()
            ]
        return self._parallax[biome_id]

    # --- Update (Fixed Timestep) -------------------------------------------------
    def update(self, dt: float) -> None:
        if self.iframes > 0:
            self.iframes -= 1

        keys = pygame.key.get_pressed()
        target_vx = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            target_vx = -MOVE_SPEED * (self.player.speed_pct / 100.0)
            self.facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            target_vx = MOVE_SPEED * (self.player.speed_pct / 100.0)
            self.facing = 1

        self.vx += (target_vx - self.vx) * min(1.0, dt * 12.0)
        if not keys[pygame.K_SPACE] and not keys[pygame.K_UP] and not keys[pygame.K_w]:
            pass
        else:
            if self.on_ground:
                self.vy = JUMP_VELOCITY
                self.on_ground = False

        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL_SPEED)
        self.px += self.vx * dt
        self.py += self.vy * dt

        # Kollision gegen Plattformen des aktuellen Nodes
        ground_y = NODE_WORLD_H - 48.0
        if self.py >= ground_y:
            self.py = ground_y
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False
            for x, y, width in self.layout.platforms[self.node_id]:
                if x <= self.px + 16.0 <= x + width and abs((self.py + 48.0) - y) < 24.0 and self.vy >= 0:
                    self.py = y - 48.0
                    self.vy = 0.0
                    self.on_ground = True

        # Node-Grenzen → Raumwechsel über Kanten (Gating-Check)
        if self.px < 0:
            self._try_move(-1)
        elif self.px > NODE_WORLD_W - 32.0:
            self._try_move(1)

    def _try_move(self, direction: int) -> None:
        from .navigation import neighbors

        options = neighbors(self.data, self.node_id, self.player.abilities,
                            self.player.bosses_defeated)
        if not options:
            return  # Gating/Siegel blockiert den Raumwechsel
        target, _edge = options[0]
        self.node_id = target
        self.px = 16.0 if direction > 0 else NODE_WORLD_W - 48.0

    # --- Rendering -----------------------------------------------------------------
    def render(self) -> None:
        biome_id = self.data.biome_of(self.node_id)
        palette = [ _hex_to_rgb(c) for c in self.data.biomes[biome_id].get("palette_hint", ["#202020"] * 4)]

        # Kamera mit Lookahead
        cam_x = max(0.0, min(self.px + CAMERA_LOOKAHEAD - WINDOW_W / 2.0, NODE_WORLD_W - WINDOW_W))
        cam_y = 0.0

        self.screen.fill(palette[3])
        for layer in self._layers_for(biome_id):
            if layer.surface is not None:
                offset_x = int(-cam_x * layer.factor) % NODE_WORLD_W
                self.screen.blit(layer.surface, (offset_x - NODE_WORLD_W + WINDOW_W // 2, 0))

        # Plattformen
        for x, y, width in self.layout.platforms[self.node_id]:
            rect = pygame.Rect(int(x - cam_x), int(y - cam_y), int(width), 16)
            if rect.right > 0 and rect.left < WINDOW_W:
                pygame.draw.rect(self.screen, palette[2], rect)

        # Spieler (Platzhalter-Rect bis T-005-Sprites; i-Frames blinken)
        if self.iframes == 0 or (self.iframes // 4) % 2 == 0:
            player_rect = pygame.Rect(int(self.px - cam_x), int(self.py - cam_y), 32, 48)
            pygame.draw.rect(self.screen, palette[0], player_rect)

        # HUD: Level / HP / Lumen (nur Stats aus balance/)
        font = pygame.font.SysFont(None, 24)
        hp_text = font.render(f"LV {self.player.level}   Lumen {int(self.player.lumen)}", True, palette[0])
        self.screen.blit(hp_text, (16, 12))

        pygame.display.flip()

    # --- Loop ------------------------------------------------------------------------
    def run(self) -> None:
        accumulator = 0.0
        while self.running:
            frame_dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            accumulator += min(frame_dt, 0.25)
            while accumulator >= FIXED_DT:
                self.update(FIXED_DT)
                accumulator -= FIXED_DT
            self.render()
        pygame.quit()
