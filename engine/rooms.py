"""Deterministische Raum-Layouts (T-004).

Der Graph trägt keine Koordinaten — die Engine legt sie deterministisch fest:
Node-Reihenfolge per BFS ab Startknoten, Weltkoordinaten aus der Reihenfolge.
Plattformen/Geometrie werden pro Node mit `random.Random(seed ^ node_hash)`
generiert → gleiche Seed + gleicher Graph = identische Welten (Display- und
Headless-Modus teilen sich die Layouts).

Kein Content wird hier erfunden: Biome-Paletten, Namen und Gating kommen aus
world/map_graph.json; nur Geometrie ist Engine-Mechanik.
"""
from __future__ import annotations

import hashlib
import random
from collections import deque

from .constants import NODE_WORLD_H, NODE_WORLD_W
from .data import GameData


def _node_seed(seed: int, node_id: str) -> int:
    digest = hashlib.sha256(f"{seed}:{node_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFF


class WorldLayout:
    """Weltkoordinaten + Plattformen für alle Nodes (deterministisch)."""

    def __init__(self, data: GameData, seed: int):
        self.data = data
        self.seed = seed
        self.node_positions: dict[str, tuple[int, int]] = {}
        self.platforms: dict[str, list[tuple[float, float, float]]] = {}
        self._assign_positions()
        for node_id in self.data.nodes:
            self.platforms[node_id] = self._generate_platforms(node_id)

    def _assign_positions(self) -> None:
        """BFS-Reihenfolge → Gitter-Layout (Spalten pro BFS-Tiefe)."""
        order: list[str] = []
        seen = {self.data.start_node}
        queue = deque([self.data.start_node])
        while queue:
            node = queue.popleft()
            order.append(node)
            for edge in self.data.adjacency[node]:
                target = edge["to"] if edge["from"] == node else edge["from"]
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
        # Isolierte Nodes (falls vorhanden) anhängen, damit alle abgedeckt sind.
        for node_id in self.data.nodes:
            if node_id not in seen:
                order.append(node_id)

        per_column = 2
        for index, node_id in enumerate(order):
            column = index // per_column
            row = index % per_column
            self.node_positions[node_id] = (column * NODE_WORLD_W, row * NODE_WORLD_H)

    def _generate_platforms(self, node_id: str) -> list[tuple[float, float, float]]:
        """Plattformen als (x, y, breite) in Node-Lokalkoordinaten.

        Boden ist immer vorhanden; 2–5 zusätzliche Plattformen deterministisch.
        """
        rng = random.Random(_node_seed(self.seed, node_id))
        platforms: list[tuple[float, float, float]] = [(0.0, NODE_WORLD_H - 48.0, float(NODE_WORLD_W))]
        count = rng.randint(2, 5)
        for _ in range(count):
            x = rng.uniform(120.0, NODE_WORLD_W - 360.0)
            y = rng.uniform(180.0, NODE_WORLD_H - 140.0)
            width = rng.uniform(140.0, 320.0)
            platforms.append((x, y, width))
        return platforms

    def node_world_origin(self, node_id: str) -> tuple[int, int]:
        return self.node_positions[node_id]
