"""T-003 — Referenzintegrität der Balance-Daten (systems/qa).

Prinzip: Zahlen sind Daten, nie Code. Jede Kreuzreferenz zwischen den
Balance-Dateien und world/map_graph.json muss auflösbar sein:
  - jedes Item-Affix existiert in affixes.json
  - jede Drop-Eintrags item_id existiert in items.json
  - jede Drop-Tabelle referenziert ein existierendes Biome oder Boss (map_graph)
  - jedes Item.source ist 'any' oder ein existierendes Biome/Boss
  - alle 40 Items sind über mindestens eine Drop-Tabelle erreichbar

Laufzeit: pytest tests/test_balance_refs.py -q   (headless, ohne Display)
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load(rel: str):
    with open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def world():
    return load("world/map_graph.json")


@pytest.fixture(scope="module")
def items():
    return load("balance/items.json")["items"]


@pytest.fixture(scope="module")
def affixes():
    return {a["id"]: a for a in load("balance/affixes.json")["affixes"]}


@pytest.fixture(scope="module")
def drops():
    return load("balance/drops.json")["tables"]


def test_item_affixes_exist(items, affixes):
    """Jedes Item referenziert nur existierende Affixe."""
    for item in items:
        missing = [a for a in item.get("affixes", []) if a not in affixes]
        assert not missing, f"{item['id']}: unbekannte Affixe {missing}"


def test_drop_entries_reference_existing_items(drops, items):
    """Jeder Drop-Eintrag referenziert ein existierendes Item."""
    item_ids = {i["id"] for i in items}
    for table in drops:
        missing = [e["item_id"] for e in table["entries"] if e["item_id"] not in item_ids]
        assert not missing, f"{table['source_id']}: unbekannte Items {missing}"


def test_drop_tables_reference_existing_sources(drops, world):
    """Jede Drop-Tabelle referenziert ein existierendes Biome oder Boss."""
    known = {b["id"] for b in world["biomes"]} | {b["id"] for b in world["bosses"]}
    unknown = [t["source_id"] for t in drops if t["source_id"] not in known]
    assert not unknown, f"Drop-Tabellen mit unbekannter Quelle: {unknown}"


def test_item_sources_reference_existing_biomes_or_bosses(items, world):
    """Jedes Item.source ist 'any' oder ein existierendes Biome/Boss."""
    known = {"any"} | {b["id"] for b in world["biomes"]} | {b["id"] for b in world["bosses"]}
    unknown = [i["id"] for i in items if i["source"] not in known]
    assert not unknown, f"Items mit unbekanntem source: {unknown}"


def test_all_items_are_droppable(drops, items):
    """Jedes Item ist über mindestens eine Drop-Tabelle erreichbar (kein totes Gear)."""
    droppable = {e["item_id"] for t in drops for e in t["entries"]}
    missing = [i["id"] for i in items if i["id"] not in droppable]
    assert not missing, f"Items ohne Drop-Tabelle: {missing}"
