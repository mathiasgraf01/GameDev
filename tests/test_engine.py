"""Engine-Tests (T-004, Deliverable 8).

Akzeptanzkriterien:
1. Daten-Layer lädt die echten world/ + balance/-Artefakte (inkl. Schema-Validierung).
2. Gating: Kante mit `requires` blockiert ohne Fähigkeit, öffnet exakt mit ihr.
3. Alle 6 Fähigkeiten/Keys werden an ihren granted_at-Nodes vergeben und öffnen ihre Kanten.
4. Save/Load: nach Reload sind Fähigkeiten, Keys, Boss-State identisch.
5. Headless-Smoke-Run: gleicher Seed → byte-identische Reports (T-006-Vertrag).

Lauf: `pytest tests/test_engine.py -q` (headless, kein Display nötig).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine.data import DataLoadError, GameData  # noqa: E402
from engine.headless import report_path, simulate_run  # noqa: E402
from engine.navigation import can_traverse, find_path, neighbors  # noqa: E402
from engine.player import Player  # noqa: E402

DATA = GameData()


# --- 1. Daten-Layer -----------------------------------------------------------

def test_data_layer_loads_real_artifacts():
    assert DATA.meta["game"] == "Lumenfall"
    assert len(DATA.nodes) >= 30, "GDD-Scope: ≥ 30 Map-Nodes"
    assert set(DATA.biomes) == {"lumen_well", "aschen_wald", "glut_hoehlen", "frost_hallen", "hohle_tiefen"}
    assert len(DATA.items) == 40, "T-003: 40 Items"
    assert len(DATA.affixes) == 14, "T-003: 14 Affixe"
    assert len(DATA.drop_tables) == 7, "5 Biome + 2 Boss-Tabellen"
    assert DATA.start_node == "hub_01" and DATA.final_node == "hd_05"


def test_data_layer_validates_against_schemas():
    # Alle Balance-Dateien sind gegen ihre Draft-07-Schemas validiert (GameData-Konstruktor).
    for name in ("stat_curves", "items", "affixes", "drops", "difficulty"):
        assert hasattr(DATA, name), f"Balance-Dokument '{name}' fehlt im Daten-Layer"


def test_data_layer_reports_missing_file(tmp_path):
    with pytest.raises(DataLoadError, match="map_graph.json"):
        GameData(root=tmp_path)


# --- 2. Gating-Logik -----------------------------------------------------------

def test_gated_edge_blocked_without_ability():
    edge = next(e for e in DATA.edges if e["requires"] == "ability_double_jump")
    assert not can_traverse(DATA, set(), edge)
    assert can_traverse(DATA, {"ability_double_jump"}, edge)


def test_open_edge_always_passable():
    open_edges = [e for e in DATA.edges if e["requires"] is None]
    assert open_edges, "Graph braucht offene Kanten"
    for edge in open_edges:
        assert can_traverse(DATA, set(), edge)


def test_neighbors_respects_gating_both_directions():
    # ag_03 → ag_04 nur mit ability_double_jump (bidirektional laut meta.edge_semantics)
    without = {t for t, _e in neighbors(DATA, "ag_03", set())}
    with_ab = {t for t, _e in neighbors(DATA, "ag_03", {"ability_double_jump"})}
    assert "ag_04" not in without and "ag_04" in with_ab
    # Rückrichtung: ag_04 → ag_03 ebenfalls gated
    back_without = {t for t, _e in neighbors(DATA, "ag_04", set())}
    assert "ag_03" not in back_without


# --- 3. Alle 6 Gating-IDs an ihren Nodes ----------------------------------------

def test_all_six_gating_ids_granted_at_their_nodes():
    expected = {
        "ability_double_jump": "ag_03",
        "ability_dash": "ag_05",
        "ability_wall_slide": "ec_02",
        "ability_light_step": "hd_02",
        "key_lumen_shard": "ag_08",
        "key_ember_key": "ec_04",
    }
    for ability_id, node_id in expected.items():
        assert DATA.grants_at(node_id) == [ability_id], f"{ability_id} nicht an {node_id}"

    player = Player(DATA)
    for node_id in expected.values():
        for ability_id in DATA.grants_at(node_id):
            player.grant(ability_id)
    # Mit allen 6 IDs (und gebrochenen Siegeln) ist der Zielknoten hd_05 erreichbar.
    path = find_path(DATA, "hub_01", "hd_05", player.abilities,
                     bosses_defeated={"boss_aschen_waechter", "boss_frost_koenigin"})
    assert path and path[0] == "hub_01" and path[-1] == "hd_05"


def test_goal_unreachable_without_all_gating_ids():
    # hd_05 hat zwei Zugänge (fh_05→hd_01 via key_ember_key, hub_05→hd_03 via
    # ability_light_step) — ohne BEIDE ist das Ziel nicht erreichbar.
    abilities = {a["id"] for a in DATA.abilities} - {"key_ember_key", "ability_light_step"}
    assert not find_path(DATA, "hub_01", "hd_05", abilities), \
        "Ziel ohne key_ember_key UND ability_light_step erreichbar?"


def test_boss_rooms_gate_their_biomes():
    """Boss-Räume sind Siegel (lore.md §2): erst nach Sieg passierbar."""
    without = find_path(DATA, "hub_01", "ec_05", {a["id"] for a in DATA.abilities})
    assert not without, "Gluthöhlen ohne Aschewächter-Sieg erreichbar?"
    with_boss = find_path(DATA, "hub_01", "ec_05", {a["id"] for a in DATA.abilities},
                          bosses_defeated={"boss_aschen_waechter"})
    assert with_boss and with_boss[-1] == "ec_05"


def test_each_gating_id_opens_exactly_its_edges():
    """Jede Fähigkeit/Schlüssel öffnet genau die Kanten, die sie in `requires` nennen."""
    for ability in DATA.abilities:
        gated = [e for e in DATA.edges if e["requires"] == ability["id"]]
        assert gated, f"{ability['id']} gateet keine Kante"
        player = Player(DATA)
        player.grant(ability["id"])
        for edge in gated:
            assert can_traverse(DATA, player.abilities, edge)


# --- 4. Save/Load ----------------------------------------------------------------

def test_save_load_roundtrip_preserves_state(tmp_path):
    from engine import savegame

    original = Player(DATA)
    for ability_id in ("ability_double_jump", "key_lumen_shard"):
        original.grant(ability_id)
    original.bosses_defeated.add("boss_aschen_waechter")
    original.visited_nodes.update(["hub_01", "ag_03"])
    original.level = 5
    original.xp = 12.5

    savegame.SAVE_FILE = tmp_path / "slot1.json"
    try:
        path = savegame.save_game(DATA, original, current_node="ag_04", run_depth=2.3)
        assert path.is_file()

        loaded_player, node, depth = savegame.load_game(DATA)
        assert node == "ag_04" and abs(depth - 2.3) < 1e-9
        # Fähigkeit, Keys und Boss-State identisch nach Reload:
        assert loaded_player.abilities == original.abilities
        assert loaded_player.bosses_defeated == original.bosses_defeated
        assert loaded_player.visited_nodes == original.visited_nodes
        assert loaded_player.level == 5 and abs(loaded_player.xp - 12.5) < 1e-9
    finally:
        savegame.SAVE_FILE = Path(savegame.SAVE_DIR) / "slot1.json"


# --- 5. Headless-Smoke-Run (T-006-Vertrag) ----------------------------------------

REQUIRED_REPORT_FIELDS = {
    "seed", "run_id", "outcome", "duration_s", "death_zone",
    "death_cause", "last_node", "items_picked", "abilities_gained",
}


def test_headless_report_contract_fields():
    report = simulate_run(DATA, seed=42)
    assert REQUIRED_REPORT_FIELDS <= set(report), f"Fehlende Pflichtfelder: {REQUIRED_REPORT_FIELDS - set(report)}"
    assert report["outcome"] in ("clear", "death")
    if report["outcome"] == "death":
        assert report["death_zone"] in DATA.biomes and report["death_cause"] is not None
    else:
        assert report["death_zone"] is None and report["death_cause"] is None
    for item in report["items_picked"]:
        assert set(item) >= {"id", "rarity"}


def test_headless_deterministic_same_seed_byte_identical(tmp_path):
    """Zweiter Lauf mit gleichem Seed → byte-identische Reports (QA-Akzeptanz)."""
    from engine import headless

    old_dir = headless.REPORTS_DIR
    headless.REPORTS_DIR = tmp_path
    try:
        run_ids = (1, 2, 3)
        first_reports = [headless.simulate_run(DATA, seed=42, run_id=i) for i in run_ids]
        for report in first_reports:
            headless.write_report(report)
        bytes_first = {i: headless.report_path(42, i).read_bytes() for i in run_ids}

        # Zweiter Lauf mit gleichem Seed: Simulation identisch, Reports byte-identisch.
        second_reports = [headless.simulate_run(DATA, seed=42, run_id=i) for i in run_ids]
        assert first_reports == second_reports, "Gleicher Seed liefert unterschiedliche Reports"
        for report in second_reports:
            headless.write_report(report)  # überschreibt deterministisch
            assert headless.report_path(42, report["run_id"]).read_bytes() == bytes_first[report["run_id"]]
    finally:
        headless.REPORTS_DIR = old_dir


def test_headless_different_seeds_diverge():
    a = simulate_run(DATA, seed=1)
    b = simulate_run(DATA, seed=2)
    assert (a["last_node"], a["outcome"]) != (b["last_node"], b["outcome"]) or \
           a["items_picked"] != b["items_picked"]


def test_headless_cli_seed_42_runs_3(tmp_path):
    """CLI-Vertrag: `python main.py --headless --seed 42 --runs 3` → 3 Reports."""
    env = {"PYTHONPATH": str(REPO_ROOT), "SDL_VIDEODRIVER": "dummy", **__import__("os").environ}
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--headless", "--seed", "42", "--runs", "3"],
        capture_output=True, text=True, env=env, cwd=str(REPO_ROOT), timeout=120,
    )
    assert result.returncode == 0, f"CLI fehlgeschlagen: {result.stderr}"
    for run_id in (1, 2, 3):
        path = report_path(42, run_id)
        assert path.is_file(), f"Report fehlt: {path}"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert REQUIRED_REPORT_FIELDS <= set(payload)
