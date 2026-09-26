"""Save-System (T-004, Deliverable 6).

Metroidvania-Persistenz als JSON unter `saves/`: Fähigkeiten, Keys, besiegte
Bosse, erreichte Nodes + Level/XP/Lumen. Load beim Start; ein Save-Slot (GDD §4).
"""
from __future__ import annotations

import json
from pathlib import Path

from .data import GameData
from .player import Player

SAVE_DIR = Path(__file__).resolve().parent.parent / "saves"
SAVE_FILE = SAVE_DIR / "slot1.json"


def save_game(data: GameData, player: Player, current_node: str, run_depth: float) -> Path:
    """Spielstand schreiben; liefert den Pfad des Save-Files."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "current_node": current_node,
        "run_depth": run_depth,
        "player": player.to_save(),
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return SAVE_FILE


def load_game(data: GameData) -> tuple[Player, str, float] | None:
    """Spielstand laden; None wenn kein Save existiert.

    Liefert (player, current_node, run_depth).
    """
    if not SAVE_FILE.is_file():
        return None
    with open(SAVE_FILE, encoding="utf-8") as fh:
        payload = json.load(fh)
    player = Player.from_save(data, payload.get("player", {}))
    current_node = payload.get("current_node", data.start_node)
    if current_node not in data.nodes:
        raise ValueError(f"Save referenziert unbekannten Node: {current_node}")
    return player, current_node, float(payload.get("run_depth", 1.0))


def has_save() -> bool:
    return SAVE_FILE.is_file()
