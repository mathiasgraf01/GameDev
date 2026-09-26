"""Feind- und Boss-Archetypen (T-004, Deliverable 4).

Die 8 Feindtypen aus dem GDD-Scope (§4) als Archetyp-Tabelle. Basis-HP/-Damage
sind Engine-Mechanik; das Run-Scaling kommt ausschließlich aus
`balance/difficulty.json` (Run-Tiefe), die XP-Belohnung aus `stat_curves.json`.

Hinweis: Die Feind-IDs sind PROVISIONAL, bis @worldbuilder sie in lore.md
finalisiert (Artist braucht sie für T-005 Deliverable 4). Umbenennung = Daten-
änderung an dieser Tabelle, kein Logik-Change.
"""
from __future__ import annotations

import random

from .data import GameData

# Archetyp-Tabelle: id → (Biome, Basis-HP, Basis-Damage, XP-Belohnung)
ENEMY_ARCHETYPES: dict[str, dict] = {
    "enemy_spore_wisp":      {"biome": "aschen_wald",   "hp": 26,  "damage": 5,  "xp": 14},
    "enemy_ashen_stag":      {"biome": "aschen_wald",   "hp": 40,  "damage": 8,  "xp": 20},
    "enemy_cinder_imp":      {"biome": "glut_hoehlen",  "hp": 52,  "damage": 11, "xp": 26},
    "enemy_magma_golem":     {"biome": "glut_hoehlen",  "hp": 70,  "damage": 14, "xp": 34},
    "enemy_frost_sentinel":  {"biome": "frost_hallen",  "hp": 62,  "damage": 13, "xp": 30},
    "enemy_ice_wraith":      {"biome": "frost_hallen",  "hp": 48,  "damage": 16, "xp": 32},
    "enemy_core_shade":      {"biome": "hohle_tiefen",  "hp": 78,  "damage": 17, "xp": 40},
    "enemy_lumen_drake":     {"biome": "lumen_well",    "hp": 34,  "damage": 9,  "xp": 18},
}

# Boss-Basiswerte (Mechanik; Scaling über difficulty.json wie Feinde)
BOSS_BASE = {
    "boss_aschen_waechter": {"hp": 260, "damage": 14, "xp": 90},
    "boss_frost_koenigin":  {"hp": 320, "damage": 17, "xp": 120},
}


def enemies_for_biome(biome_id: str) -> list[str]:
    """Feind-IDs, die in einem Biome spawnen (leer = Hub ohne Wildfeinde)."""
    return [eid for eid, spec in ENEMY_ARCHETYPES.items() if spec["biome"] == biome_id]


def make_enemy(rng: random.Random, data: GameData, enemy_id: str, depth: float) -> dict:
    """Feind-Instanz mit Run-Tiefe-Scaling (difficulty.json)."""
    spec = ENEMY_ARCHETYPES[enemy_id]
    mult = data.depth_row(depth)
    return {
        "id": enemy_id,
        "hp": int(spec["hp"] * mult["hp_multiplier"]),
        "max_hp": int(spec["hp"] * mult["hp_multiplier"]),
        "damage": max(1, int(spec["damage"] * mult["damage_multiplier"])),
        "xp_reward": spec["xp"],  # XP-Scaling wird in headless.py über xp_reward_multiplier angewendet
    }


def make_boss(rng: random.Random, data: GameData, boss_id: str, depth: float) -> dict:
    """Boss-Instanz mit Run-Tiefe-Scaling (difficulty.json)."""
    spec = BOSS_BASE[boss_id]
    mult = data.depth_row(depth)
    return {
        "id": boss_id,
        "hp": int(spec["hp"] * mult["hp_multiplier"]),
        "max_hp": int(spec["hp"] * mult["hp_multiplier"]),
        "damage": max(1, int(spec["damage"] * mult["damage_multiplier"])),
        "xp_reward": spec["xp"],
    }
