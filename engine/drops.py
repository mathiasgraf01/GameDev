"""Drop-Wurf + Affix-Roll (T-004).

Umsetzt den Engine-Vertrag aus `balance/schema.md`:
1. Affix-Roll: uniform zwischen min_pct und max_pct des Basiswerts der Stat.
2. Biome-Drop: gewichtet nach Wahrscheinlichkeit; Rest = „kein Item, nur Lumen".
3. Boss-Drop (guaranteed): genau ein Eintrag, renormiert — Bosse belohnen immer.

Alle Zufallsquellen laufen über den einzigen `random.Random(seed)` des Runs
(Headless-Vertrag für T-006) → deterministisch pro Seed.
"""
from __future__ import annotations

import random

from .data import GameData


def roll_affixes(rng: random.Random, data: GameData, item: dict) -> list[dict]:
    """Affixe des Items rollen (IDs aus items.json; Werte uniform in min/max_pct).

    Basiswert der Stat = stat_curves Level-1-Wert + Item-base_stats (Vertrag §1).
    """
    base_hp = data.level_row(1)["base_hp"]
    base_attack = data.level_row(1)["base_attack"]
    base_defense = data.level_row(1)["base_defense"]
    bases = {
        "max_hp": base_hp,
        "attack": base_attack,
        "defense": base_defense,
        # Prozent-Stats (speed/crit_*/lumen_gain): Basiswert = 0 → Roll auf den
        # Item-base-Wert selbst; ohne Basis wird der %-Wert flat interpretiert.
    }

    rolled: list[dict] = []
    for affix_id in item.get("affixes", []):
        affix = data.affixes[affix_id]
        stat_key = affix["stat_key"]
        base = bases.get(stat_key, 0) + float(item["base_stats"].get(stat_key, 0))
        if base <= 0:
            # Prozent-Stat ohne Basiswert: Roll auf den %-Wert selbst (flat).
            value = round(rng.uniform(affix["min_pct"], affix["max_pct"]), 2)
        else:
            lo = base * affix["min_pct"] / 100.0
            hi = base * affix["max_pct"] / 100.0
            value = round(rng.uniform(lo, hi), 2)
        rolled.append({"id": affix_id, "stat_key": stat_key, "value": value})
    return rolled


def roll_drop(rng: random.Random, data: GameData, source_id: str) -> dict | None:
    """Drop-Wurf für eine Quelle (Biome- oder Boss-ID).

    Rückgabe: Item-Dict mit gerollten Affixen + `rarity`, oder None („kein Drop").
    """
    table = data.drop_tables.get(source_id)
    if table is None or not table["entries"]:
        return None

    entries = table["entries"]
    total = sum(e["probability"] for e in entries)
    guaranteed = bool(table.get("guaranteed"))
    # guaranteed: Wahrscheinlichkeiten renormieren (Summe → 1.0), Roll immer trifft.
    # biome: Restwahrscheinlichkeit (Summe < 1.0) = „kein Item, nur Lumen".
    weights = [e["probability"] / total for e in entries] if guaranteed else [e["probability"] for e in entries]
    roll = rng.random()
    chosen = None
    acc = 0.0
    for entry, weight in zip(entries, weights):
        acc += weight
        if roll < acc:
            chosen = entry
            break
    if chosen is None and guaranteed:
        chosen = entries[-1]  # Float-Rest: letzter Eintrag fängt auf (immer belohnt)
    if chosen is None:
        return None  # Biome-Tabelle: Restwahrscheinlichkeit = „kein Item, nur Lumen"

    item = data.items[chosen["item_id"]]
    return {
        "id": item["id"],
        "name_de": item["name_de"],
        "slot": item["slot"],
        "rarity": item["rarity"],
        "base_stats": dict(item["base_stats"]),
        "affixes_rolled": roll_affixes(rng, data, item),
    }
