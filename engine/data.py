"""Daten-Layer (T-004, Deliverable 2).

Lädt `world/map_graph.json` + alle `balance/*.json`, validiert beim Start gegen
die Draft-07-Schemas aus T-003. Fehler → `DataLoadError` mit klarer Meldung
(Headless-Fehlermeldung statt Crash-Mystery).

Kein Content wird hier interpretiert — nur geladen, validiert und indexiert.
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover
    raise DataLoadError("jsonschema ist nicht installiert (uv pip install jsonschema)") from exc


class DataLoadError(RuntimeError):
    """Daten konnten nicht geladen oder validiert werden."""


REPO_ROOT = Path(__file__).resolve().parent.parent

# balance-Datei → Schema (Verzeichnis aus balance/schema.md)
BALANCE_FILES = {
    "stat_curves": ("balance/stat_curves.json", "balance/schema/stat_curves.schema.json"),
    "items": ("balance/items.json", "balance/schema/items.schema.json"),
    "affixes": ("balance/affixes.json", "balance/schema/affixes.schema.json"),
    "drops": ("balance/drops.json", "balance/schema/drops.schema.json"),
    "difficulty": ("balance/difficulty.json", "balance/schema/difficulty.schema.json"),
}

# Referenz-Schema (kein eigenes JSON, nur Stat-Vokabular)
STATS_SCHEMA = Path("balance/schema/stats.schema.json")


def _load_json(path: Path, what: str) -> dict:
    if not path.is_file():
        raise DataLoadError(f"{what}: Datei fehlt → {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise DataLoadError(f"{what}: ungültiges JSON in {path} (Zeile {exc.lineno}): {exc.msg}") from exc


def _validate(data: dict, schema_path: Path, what: str) -> None:
    schema = _load_json(schema_path, f"Schema für {what}")
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        loc = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        raise DataLoadError(f"{what}: Schema-Validierung fehlgeschlagen bei '{loc}': {exc.message}") from exc


class GameData:
    """Alle Spieldaten eines Lumenfall-Runs, indexiert für die Engine."""

    def __init__(self, root: Path = REPO_ROOT):
        self.root = Path(root)

        # --- World (T-002) ---------------------------------------------------
        graph = _load_json(self.root / "world/map_graph.json", "World")
        for key in ("meta", "abilities", "biomes", "nodes", "edges"):
            if key not in graph:
                raise DataLoadError(f"World: map_graph.json fehlt Abschnitt '{key}'")
        self.meta = graph["meta"]
        self.abilities: list[dict] = graph["abilities"]
        self.biomes: dict[str, dict] = {b["id"]: b for b in graph["biomes"]}
        self.nodes: dict[str, dict] = {n["id"]: n for n in graph["nodes"]}
        self.edges: list[dict] = graph["edges"]
        self.bosses: dict[str, dict] = {b["id"]: b for b in graph.get("bosses", [])}
        self.npcs: dict[str, dict] = {n["id"]: n for n in graph.get("npcs", [])}

        # Indexe
        self.adjacency: dict[str, list[dict]] = {nid: [] for nid in self.nodes}
        for edge in self.edges:
            if edge["from"] not in self.nodes or edge["to"] not in self.nodes:
                raise DataLoadError(f"World: Kante referenziert unbekannten Node ({edge['from']} → {edge['to']})")
            self.adjacency[edge["from"]].append(edge)
            self.adjacency[edge["to"]].append({"from": edge["to"], "to": edge["from"], "requires": edge["requires"]})
        for ab in self.abilities:
            if ab.get("granted_at") not in self.nodes:
                raise DataLoadError(f"World: Fähigkeit {ab['id']} wird an unbekanntem Node vergeben ({ab.get('granted_at')})")

        # --- Balance (T-003) --------------------------------------------------
        for name, (data_rel, schema_rel) in BALANCE_FILES.items():
            data = _load_json(self.root / data_rel, f"Balance/{name}")
            _validate(data, self.root / schema_rel, f"Balance/{name}")
            setattr(self, name, data)

        # Indexe für den Daten-Layer-Verbrauch (drops.py, player.py, enemies.py)
        self.items: dict[str, dict] = {i["id"]: i for i in self._doc("items")["items"]}
        self.affixes: dict[str, dict] = {a["id"]: a for a in self._doc("affixes")["affixes"]}
        self.drop_tables: dict[str, dict] = {t["source_id"]: t for t in self._doc("drops")["tables"]}
        self.levels: list[dict] = self._doc("stat_curves")["levels"]
        self.depths: list[dict] = self._doc("difficulty")["run_depths"]

        # Referenzintegrität (Engine-seitig, zusätzlich zu tests/test_balance_refs.py)
        for item in self.items.values():
            for affix_id in item.get("affixes", []):
                if affix_id not in self.affixes:
                    raise DataLoadError(f"Balance/items: Item {item['id']} referenziert unbekanntes Affix {affix_id}")
        for table in self.drop_tables.values():
            for entry in table["entries"]:
                if entry["item_id"] not in self.items:
                    raise DataLoadError(f"Balance/drops: Tabelle {table['source_id']} referenziert unbekanntes Item {entry['item_id']}")

    # --- Helfer ---------------------------------------------------------------
    def _doc(self, name: str) -> dict:
        return getattr(self, name)

    @property
    def start_node(self) -> str:
        return self.meta["start_node"]

    @property
    def final_node(self) -> str:
        return self.meta["final_node"]

    def biome_of(self, node_id: str) -> str:
        return self.nodes[node_id]["biome"]

    def grants_at(self, node_id: str) -> list[str]:
        """Fähigkeit-/Schlüssel-IDs, die an diesem Node vergeben werden."""
        return list(self.nodes[node_id].get("grants", []))

    def level_row(self, level: int) -> dict:
        if not 1 <= level <= len(self.levels):
            raise DataLoadError(f"stat_curves: Level {level} außerhalb 1..{len(self.levels)}")
        return self.levels[level - 1]

    def depth_row(self, depth: float) -> dict:
        """Run-Tiefe clampen und Multiplikatoren liefern (difficulty.json)."""
        d = max(1.0, min(float(depth), len(self.depths)))
        idx = int(d) - 1
        if d == int(d):
            return self.depths[idx]
        lo, hi = self.depths[idx], self.depths[idx + 1]
        frac = d - int(d)
        out = {"depth": d}
        for key in ("hp_multiplier", "damage_multiplier", "xp_reward_multiplier"):
            out[key] = lo[key] * (1 - frac) + hi[key] * frac
        return out

    def drop_table_for(self, source_id: str) -> dict | None:
        """Drop-Tabelle für Biome-ID oder Boss-ID; None = keine Beutequelle."""
        table = self.drop_tables.get(source_id)
        if table is not None:
            return table
        # Item-Quelle 'any' ist keine Tabelle — nur Biome/Boss sind Quellen.
        return None
