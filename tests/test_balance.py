"""T-003 — Headless-Validierung der Balance-Daten (systems/qa).

Prüft alle Akzeptanzkriterien aus tickets/T-003-systems.md:
  - Alle JSON validieren gegen ihre Schemas (jsonschema)
  - stat_curves: XP/Damage monoton steigend, kein Sprung > 50 % zwischen Leveln
  - items: >= 30 Items; Rarity-Caps 60/25/10/5 %; Affix-Anzahl pro Rarity
  - affixes: Min/Max-Bereiche innerhalb ±100 % (Sanity-Grenze)
  - drops: Wahrscheinlichkeiten <= 1.0; Tabelle für jedes Biome und beide Bosse
  - difficulty: Run-Tiefe 1-5 vollständig, Multiplikatoren monoton nicht-fallend

Laufzeit: pytest tests/test_balance.py -q   (headless, ohne Display)
"""
import json
from collections import Counter
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

BALANCE = Path(__file__).resolve().parent.parent / "balance"
SCHEMA_DIR = BALANCE / "schema"


def load(name: str):
    with open(BALANCE / name, encoding="utf-8") as f:
        return json.load(f)


def schema(name: str):
    with open(SCHEMA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- Schemas

@pytest.mark.parametrize(
    "data_file,schema_file",
    [
        ("stat_curves.json", "stat_curves.schema.json"),
        ("items.json", "items.schema.json"),
        ("affixes.json", "affixes.schema.json"),
        ("drops.json", "drops.schema.json"),
        ("difficulty.json", "difficulty.schema.json"),
    ],
)
def test_data_validates_against_schema(data_file, schema_file):
    """Alle Balance-Dateien validieren gegen ihre JSON-Schemas."""
    errors = sorted(Draft7Validator(schema(schema_file)).iter_errors(load(data_file)), key=str)
    assert not errors, [e.message for e in errors[:5]]


# ----------------------------------------------------------- stat_curves

def test_stat_curves_complete_and_monotonic():
    """Level 1-20 vollständig; XP und Damage monoton steigend; Sprung <= 50 %."""
    levels = load("stat_curves.json")["levels"]
    assert [l["level"] for l in levels] == list(range(1, 21)), "Level 1-20 müssen vollständig sein"
    for prev, cur in zip(levels, levels[1:]):
        assert cur["xp_to_next"] > prev["xp_to_next"], f"XP fällt bei Level {cur['level']}"
        assert cur["base_attack"] > prev["base_attack"], f"Damage fällt bei Level {cur['level']}"
        for key in ("xp_to_next", "base_attack"):
            jump = (cur[key] - prev[key]) / prev[key]
            assert jump <= 0.5, f"{key}: Sprung {jump:.1%} > 50 % bei Level {cur['level']}"


# ----------------------------------------------------------------- items

RARITY_CAPS = {"common": 0.60, "uncommon": 0.25, "rare": 0.10, "epic": 0.05}
AFFIX_COUNT_BY_RARITY = {"common": (0, 1), "uncommon": (1, 2), "rare": (2, 3), "epic": (3, 4)}


def test_items_count_and_rarity_caps():
    """>= 30 Items; Rarity-Verteilung hält die Caps 60/25/10/5 % ein."""
    items = load("items.json")["items"]
    assert len(items) >= 30, f"nur {len(items)} Items (benötigt: >= 30)"
    dist = Counter(i["rarity"] for i in items)
    total = len(items)
    for rarity, cap in RARITY_CAPS.items():
        frac = dist.get(rarity, 0) / total
        assert frac <= cap + 1e-9, f"Rarity {rarity}: {frac:.2%} > Cap {cap:.0%}"


def test_items_affix_count_by_rarity():
    """Affix-Anzahl pro Rarity: common 0-1, uncommon 1-2, rare 2-3, epic 3-4."""
    for item in load("items.json")["items"]:
        lo, hi = AFFIX_COUNT_BY_RARITY[item["rarity"]]
        n = len(item.get("affixes", []))
        assert lo <= n <= hi, f"{item['id']}: {n} Affixe bei Rarity {item['rarity']} (erwartet {lo}-{hi})"


def test_items_stat_keys_match_schema():
    """Jedes Item referenziert nur Stat-Keys aus stats.schema.json."""
    valid_stats = set(schema("stats.schema.json")["properties"].keys())
    for item in load("items.json")["items"]:
        bad = set(item["base_stats"]) - valid_stats
        assert not bad, f"{item['id']}: unbekannte Stat-Keys {bad}"


# ---------------------------------------------------------------- affixes

def test_affix_bounds_within_sanity_limit():
    """Jedes Affix hat Min/Max; kein Wert außerhalb ±100 % des Basiswerts."""
    for affix in load("affixes.json")["affixes"]:
        assert "min_pct" in affix and "max_pct" in affix, f"{affix['id']}: fehlt min/max"
        assert affix["min_pct"] <= affix["max_pct"], f"{affix['id']}: min > max"
        assert -100 <= affix["min_pct"] and affix["max_pct"] <= 100, (
            f"{affix['id']}: Bereich [{affix['min_pct']}, {affix['max_pct']}] außerhalb ±100 %"
        )


def test_affix_stat_keys_match_schema():
    """Jedes Affix referenziert nur Stat-Keys aus stats.schema.json."""
    valid_stats = set(schema("stats.schema.json")["properties"].keys())
    for affix in load("affixes.json")["affixes"]:
        assert affix["stat_key"] in valid_stats, f"{affix['id']}: unbekanntes stat_key {affix['stat_key']}"


# ----------------------------------------------------------------- drops

def test_drop_probabilities_sum_to_at_most_one():
    """Wahrscheinlichkeiten pro Tabelle summieren sich zu <= 1.0."""
    for table in load("drops.json")["tables"]:
        total = sum(e["probability"] for e in table["entries"])
        assert total <= 1.0 + 1e-9, f"{table['source_id']}: Summe {total:.3f} > 1.0"


def test_drop_tables_cover_all_biomes_and_bosses():
    """Jedes Biome und beide Bosse aus map_graph.json haben eine Drop-Tabelle."""
    world = json.loads((Path(__file__).resolve().parent.parent / "world" / "map_graph.json").read_text(encoding="utf-8"))
    tables = {t["source_id"] for t in load("drops.json")["tables"]}
    biomes = {b["id"] for b in world["biomes"]}
    bosses = {b["id"] for b in world["bosses"]}
    missing_biomes = biomes - tables
    missing_bosses = bosses - tables
    assert not missing_biomes, f"Drop-Tabelle fehlt für Biome: {missing_biomes}"
    assert not missing_bosses, f"Drop-Tabelle fehlt für Boss: {missing_bosses}"


def test_drop_tables_are_typed_correctly():
    """source_type passt zur Art der Quelle (biome vs. boss)."""
    world = json.loads((Path(__file__).resolve().parent.parent / "world" / "map_graph.json").read_text(encoding="utf-8"))
    biomes = {b["id"] for b in world["biomes"]}
    bosses = {b["id"] for b in world["bosses"]}
    for table in load("drops.json")["tables"]:
        if table["source_id"] in biomes:
            assert table["source_type"] == "biome", f"{table['source_id']}: falscher source_type"
        elif table["source_id"] in bosses:
            assert table["source_type"] == "boss", f"{table['source_id']}: falscher source_type"


# ------------------------------------------------------------- difficulty

def test_difficulty_depths_complete_and_monotonic():
    """Run-Tiefe 1-5 vollständig; alle Multiplikatoren monoton nicht-fallend."""
    depths = load("difficulty.json")["run_depths"]
    assert [d["depth"] for d in depths] == list(range(1, 6)), "Tiefen 1-5 müssen vollständig sein"
    keys = ("hp_multiplier", "damage_multiplier", "xp_reward_multiplier")
    for prev, cur in zip(depths, depths[1:]):
        for key in keys:
            assert cur[key] >= prev[key], f"{key} fällt bei Tiefe {cur['depth']}"
