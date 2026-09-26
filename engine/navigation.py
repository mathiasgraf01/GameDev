"""Raum-Navigation über den Graphen (T-004, Deliverable 5).

Kanten sind bidirektional begehbar; `requires` = Fähigkeit-/Schlüssel-ID, die
der Spieler besitzen muss, um die Kante in beiden Richtungen zu passieren
(meta.edge_semantics aus map_graph.json). Startknoten und Zielknoten kommen
aus meta — nichts wird hartkodet.
"""
from __future__ import annotations

from .data import GameData


class NavigationError(RuntimeError):
    """Navigation über den Graphen fehlgeschlagen."""


def can_traverse(data: GameData, player_abilities: set[str], edge: dict) -> bool:
    """Gating-Check für eine Kante (bidirektional)."""
    requires = edge.get("requires")
    if requires is None:
        return True
    return requires in player_abilities


def _boss_gates(data: GameData, node_id: str, bosses_defeated: set[str]) -> bool:
    """Boss-Räume sind Siegel (lore.md §2): Der Boss hütet den Übergang —

    das Boss-Zimmer selbst ist betretbar (Kampf), aber der Ausgang aus ihm
    erst nach Sieg. Ein unbesiegter Boss blockt also alle Kanten VON seinem
    Node; das Betreten löst den Kampf aus (headless.py / game.py).
    """
    boss_id = data.nodes[node_id].get("boss_id")
    return boss_id is None or boss_id in bosses_defeated


def neighbors(data: GameData, node_id: str, abilities: set[str],
              bosses_defeated: set[str] | None = None) -> list[tuple[str, dict]]:
    """Begehbare Nachbar-Nodes (Gating + Boss-Siegel angewendet)."""
    bosses_defeated = bosses_defeated or set()
    result = []
    for edge in data.adjacency[node_id]:
        if not can_traverse(data, abilities, edge):
            continue
        target = edge["to"] if edge["from"] == node_id else edge["from"]
        # Siegel: kein Ausgang aus einem Boss-Raum mit unbesiegtem Boss.
        if _boss_gates(data, node_id, bosses_defeated):
            result.append((target, edge))
    return result


def find_path(data: GameData, start: str, goal: str, abilities: set[str],
              bosses_defeated: set[str] | None = None) -> list[str]:
    """BFS über begehbare Kanten; liefert Node-Pfad inkl. Start/Ziel oder []."""
    if start not in data.nodes or goal not in data.nodes:
        raise NavigationError(f"Unbekannter Node im Pfad: {start} → {goal}")
    if start == goal:
        return [start]
    from collections import deque

    bosses_defeated = bosses_defeated or set()
    queue = deque([(start, [start])])
    seen = {start}
    while queue:
        node, path = queue.popleft()
        for target, _edge in neighbors(data, node, abilities, bosses_defeated):
            if target == goal:
                return path + [target]
            if target not in seen:
                seen.add(target)
                queue.append((target, path + [target]))
    return []


def reachable_nodes(data: GameData, start: str, abilities: set[str],
                    bosses_defeated: set[str] | None = None) -> set[str]:
    """Alle vom Start aus erreichbaren Nodes (Gating + Boss-Siegel angewendet)."""
    from collections import deque

    bosses_defeated = bosses_defeated or set()
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for target, _edge in neighbors(data, node, abilities, bosses_defeated):
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return seen
