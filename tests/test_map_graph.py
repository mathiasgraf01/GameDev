"""T-002 — Headless-Validierung von world/map_graph.json (Lumenfall).

Prüft die Akzeptanzkriterien des Tickets:
  - 1 Hub + 4 Biome, >= 30 Nodes
  - BFS-Erreichbarkeit vom Start-Node; keine Orphan-Nodes
  - Jede gated Kante referenziert eine der 6 GDD-Fähigkeiten; jede Fähigkeit wird
    mindestens einmal als Gate verwendet
  - 2 Boss-Räume, jeder ein Gate zu einem neuen Biome-Cluster
  - Keine Zyklen im Gating (Topologische Sortierung über die Abhängigkeits-DAG)

Lauf: pytest tests/test_map_graph.py   (headless, ohne Display)
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import pytest

MAP_PATH = Path(__file__).resolve().parent.parent / "world" / "map_graph.json"


@pytest.fixture(scope="module")
def graph() -> dict:
    with open(MAP_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def build_adjacency(graph: dict):
    """Bidirektionale Adjazenzliste: node_id -> list[(neighbor_id, requires|None)]."""
    adj: dict[str, list[tuple[str, object]]] = {n["id"]: [] for n in graph["nodes"]}
    for e in graph["edges"]:
        src, dst, req = e["from"], e["to"], e.get("requires")
        assert src in adj and dst in adj, f"Kante referenziert unbekannten Node: {src}-{dst}"
        adj[src].append((dst, req))
        adj[dst].append((src, req))
    return adj


def bfs_reachable(graph: dict, abilities: set[str]) -> set[str]:
    """Alle Nodes, die vom Start-Node aus mit der Fähigkeit-Menge `abilities` erreichbar sind."""
    adj = build_adjacency(graph)
    start = graph["meta"]["start_node"]
    seen = {start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for nxt, req in adj[cur]:
            if nxt not in seen and (req is None or req in abilities):
                seen.add(nxt)
                queue.append(nxt)
    return seen


def ability_grant_node(graph: dict, ability_id: str) -> str:
    """Node-ID, an der die Fähigkeit vergeben wird."""
    for a in graph["abilities"]:
        if a["id"] == ability_id:
            assert a.get("granted_at"), f"Fähigkeit {ability_id} hat kein granted_at"
            return a["granted_at"]
    raise KeyError(ability_id)


def simulate_acquisition(graph: dict):
    """Simuliert den Spieler-Fortschritt: Fähigkeiten werden in der Reihenfolge
    'erhalten', sobald ihr Grant-Node mit den bereits erlangten Fähigkeiten erreichbar ist.

    Gibt die Erwerbsreihenfolge zurück (eine gültige topologische Ordnung).
    Wirft AssertionError bei Deadlock (Gating-Zyklus oder unerreichbare Fähigkeit)."""
    all_abilities = {a["id"] for a in graph["abilities"]}
    owned: set[str] = set()
    order: list[str] = []
    while len(owned) < len(all_abilities):
        reachable = bfs_reachable(graph, owned)
        newly = sorted(a for a in all_abilities - owned if ability_grant_node(graph, a) in reachable)
        assert newly, (
            "Gating-Deadlock: keine weitere Fähigkeit erwerbbar. "
            f"Besitzt={sorted(owned)}, fehlt={sorted(all_abilities - owned)} -> Zyklen oder tote Enden."
        )
        for a in newly:
            owned.add(a)
            order.append(a)
    return order


def build_dependency_dag(graph: dict):
    """Abhängigkeits-DAG der Fähigkeiten: Kante A->B, wenn B's Grant-Node ohne A
    (aber mit allen anderen Fähigkeiten) unerreichbar ist. A muss also vor B kommen."""
    all_abilities = [a["id"] for a in graph["abilities"]]
    full = set(all_abilities)
    dag: dict[str, set[str]] = {a: set() for a in all_abilities}  # A -> {B: B hängt an A}
    for b in all_abilities:
        without_b = full - {b}
        grant_b = ability_grant_node(graph, b)
        if grant_b in bfs_reachable(graph, without_b):
            continue  # B ist ohne jede einzelne Fähigkeit erreichbar -> keine strikte Abhängigkeit
        for a in all_abilities:
            if a == b:
                continue
            rest = full - {a}
            if grant_b not in bfs_reachable(graph, rest):
                dag[a].add(b)  # A ist für B strikt erforderlich
    return dag


def topological_sort(dag: dict[str, set[str]]) -> list[str]:
    """Kahn's Algorithmus. Wirft AssertionError bei Zyklen."""
    indeg = {n: 0 for n in dag}
    for a in dag:
        for b in dag[a]:
            indeg[b] += 1
    queue = deque(sorted(n for n, d in indeg.items() if d == 0))
    order: list[str] = []
    while queue:
        n = queue.popleft()
        order.append(n)
        for m in sorted(dag[n]):
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    assert len(order) == len(dag), (
        f"Topologische Sortierung unvollständig -> Zyklus im Gating. "
        f"Sortiert={order}, verbleibend={sorted(set(dag) - set(order))}"
    )
    return order


# ---------------------------------------------------------------------------
# Struktur: Biome, Nodes, Fähigkeiten
# ---------------------------------------------------------------------------

def test_biome_structure(graph):
    """1 Hub + 4 Biome; alle Nodes referenzieren definierte Biome."""
    biomes = graph["biomes"]
    hubs = [b for b in biomes if b.get("is_hub")]
    non_hubs = [b for b in biomes if not b.get("is_hub")]
    assert len(hubs) == 1, f"Genau 1 Hub erwartet, gefunden: {len(hubs)}"
    assert len(non_hubs) == 4, f"Genau 4 Nicht-Hub-Biome erwartet, gefunden: {len(non_hubs)}"

    biome_ids = {b["id"] for b in biomes}
    for n in graph["nodes"]:
        assert n["biome"] in biome_ids, f"Node {n['id']} referenziert unbekanntes Biome '{n['biome']}'"


def test_node_count(graph):
    """>= 30 Nodes."""
    assert len(graph["nodes"]) >= 30, f"Nur {len(graph['nodes'])} Nodes (erwartet >= 30)"

    ids = [n["id"] for n in graph["nodes"]]
    assert len(ids) == len(set(ids)), "Doppelte Node-IDs gefunden"


def test_six_abilities_defined(graph):
    """Genau die 6 GDD-Fähigkeiten sind definiert."""
    abilities = {a["id"] for a in graph["abilities"]}
    expected = {
        "ability_double_jump",
        "ability_dash",
        "ability_wall_slide",
        "ability_light_step",
        "key_lumen_shard",
        "key_ember_key",
    }
    assert abilities == expected, f"Fähigkeits-Satz weicht ab: {sorted(abilities ^ expected)}"


def test_gated_edges_reference_valid_abilities(graph):
    """Jede gated Kante referenziert eine definierte Fähigkeit; jede der 6 wird >= 1x als Gate genutzt."""
    ability_ids = {a["id"] for a in graph["abilities"]}
    used: set[str] = set()
    for e in graph["edges"]:
        req = e.get("requires")
        if req is not None:
            assert req in ability_ids, f"Kante {e['from']}-{e['to']} nutzt unbekanntes Gate '{req}'"
            used.add(req)
    missing = ability_ids - used
    assert not missing, f"Fähigkeiten nie als Gate verwendet: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Erreichbarkeit & Orphans (BFS über alle Kanten)
# ---------------------------------------------------------------------------

def test_all_nodes_reachable_from_start(graph):
    """Jeder Node ist vom Start-Node aus erreichbar (BFS, alle Fähigkeiten vorhanden)."""
    all_abilities = {a["id"] for a in graph["abilities"]}
    reachable = bfs_reachable(graph, all_abilities)
    all_ids = {n["id"] for n in graph["nodes"]}
    missing = all_ids - reachable
    assert not missing, f"Unerreichbare Nodes: {sorted(missing)}"


def test_no_orphan_nodes(graph):
    """Kein Node ohne Kanten (Orphan-Check)."""
    adj = build_adjacency(graph)
    orphans = [nid for nid, nbrs in adj.items() if not nbrs]
    assert not orphans, f"Orphan-Nodes: {orphans}"


def test_start_and_goal_nodes_exist(graph):
    ids = {n["id"] for n in graph["nodes"]}
    assert graph["meta"]["start_node"] in ids, "Start-Node existiert nicht"
    assert graph["meta"]["final_node"] in ids, "Ziel-Node existiert nicht"


# ---------------------------------------------------------------------------
# Boss-Gates
# ---------------------------------------------------------------------------

def test_two_boss_rooms_gate_new_biomes(graph):
    """Genau 2 Boss-Räume; jeder grenzt an ein anderes Biome (Gate zu neuem Cluster)."""
    boss_nodes = [n for n in graph["nodes"] if n.get("boss_id")]
    assert len(boss_nodes) == 2, f"Genau 2 Boss-Räume erwartet, gefunden: {len(boss_nodes)}"

    node_by_id = {n["id"]: n for n in graph["nodes"]}
    adj = build_adjacency(graph)
    for bn in boss_nodes:
        own_biome = bn["biome"]
        cross_biome_neighbors = [
            nxt for nxt, _req in adj[bn["id"]] if node_by_id[nxt]["biome"] != own_biome
        ]
        assert cross_biome_neighbors, (
            f"Boss-Raum {bn['id']} ({own_biome}) grenzt an kein anderes Biome -> "
            "kein Gate zu einem neuen Cluster."
        )


def test_bosses_declared_consistently(graph):
    """Jede boss_id eines Nodes ist in der Boss-Liste deklariert und umgekehrt."""
    declared = {b["id"]: b for b in graph.get("bosses", [])}
    node_ids = {n["id"] for n in graph["nodes"]}
    for n in graph["nodes"]:
        if n.get("boss_id"):
            assert n["boss_id"] in declared, f"Node {n['id']} nutzt undeklarierten Boss {n['boss_id']}"
            boss = declared[n["boss_id"]]
            assert boss["node"] == n["id"], f"Boss {n['boss_id']} sitzt laut Deklaration nicht in {n['id']}"
    for b in graph.get("bosses", []):
        assert b["node"] in node_ids, f"Boss {b['id']} referenziert unbekannten Node {b['node']}"


# ---------------------------------------------------------------------------
# Gating-Zyklen: Erwerbssimulation + Topologische Sortierung
# ---------------------------------------------------------------------------

def test_all_abilities_acquirable_in_order(graph):
    """Erwerbssimulation: alle 6 Fähigkeiten sind in einer gültigen Reihenfolge erwerbbar."""
    order = simulate_acquisition(graph)
    assert len(order) == len(graph["abilities"]), f"Erwerbsreihenfolge unvollständig: {order}"


def test_no_gating_cycles_topological_sort(graph):
    """Topologische Sortierung der Abhängigkeits-DAG muss erfolgreich sein (keine Zyklen)."""
    dag = build_dependency_dag(graph)
    topo_order = topological_sort(dag)

    # Konsistenz: die Erwerbssimulation liefert eine gültige topologische Ordnung.
    acq = simulate_acquisition(graph)
    pos = {a: i for i, a in enumerate(acq)}
    for a in dag:
        for b in dag[a]:
            assert pos[a] < pos[b], (
                f"Erwerbsreihenfolge widerspricht Abhängigkeit {a} -> {b}: {acq}"
            )


def test_grant_nodes_exist(graph):
    """Jede Fähigkeit wird an einem existierenden Node vergeben."""
    node_ids = {n["id"] for n in graph["nodes"]}
    for a in graph["abilities"]:
        assert a.get("granted_at") in node_ids, (
            f"Fähigkeit {a['id']} wird an unbekanntem Node '{a.get('granted_at')}' vergeben"
        )


def test_npc_and_boss_node_references(graph):
    """Alle NPC-/Boss-Node-Referenzen zeigen auf existierende Nodes."""
    node_ids = {n["id"] for n in graph["nodes"]}
    for npc in graph.get("npcs", []):
        assert npc["node"] in node_ids, f"NPC {npc['id']} steht in unbekanntem Node {npc['node']}"


# ---------------------------------------------------------------------------
# Feindtypen: lore.md §7 ist der kanonische Vertrag für T-005 Deliverable 4
# ---------------------------------------------------------------------------

LORE_PATH = Path(__file__).resolve().parent.parent / "world" / "lore.md"


def _parse_lore_enemy_table() -> dict[str, str]:
    """Liest die Feind-Tabelle aus lore.md §7: enemy_id -> biome-Name (de)."""
    import re

    text = LORE_PATH.read_text(encoding="utf-8")
    section = text.split("## 7. Feindtypen", 1)
    assert len(section) == 2, "lore.md enthält keine Sektion '## 7. Feindtypen'"
    table_rows: dict[str, str] = {}
    for line in section[1].splitlines():
        m = re.match(r"^\|\s*`([a-z0-9_]+)`\s*\|[^|]*\|\s*([^|]+?)\s*\|", line)
        if m and m.group(1).startswith("enemy_"):
            table_rows[m.group(1)] = m.group(2)
    return table_rows


def test_lore_enemy_table_has_eight_types(graph):
    """lore.md §7 definiert exakt 8 Feindtypen (GDD-Scope v1)."""
    rows = _parse_lore_enemy_table()
    assert len(rows) == 8, f"Erwarte 8 Feindtypen in lore.md §7, gefunden: {sorted(rows)}"


def test_lore_enemies_match_engine_archetypes(graph):
    """Die Feind-IDs aus lore.md §7 decken exakt die Engine-Archetypen ab (keine Drift)."""
    from engine.enemies import ENEMY_ARCHETYPES

    rows = _parse_lore_enemy_table()
    assert set(rows) == set(ENEMY_ARCHETYPES), (
        f"lore.md §7 und engine/enemies.py weichen ab: "
        f"nur in lore={sorted(set(rows) - set(ENEMY_ARCHETYPES))}, "
        f"nur in Engine={sorted(set(ENEMY_ARCHETYPES) - set(rows))}"
    )


def test_lore_enemies_biome_consistent(graph):
    """Jeder Feind aus lore.md §7 gehört zu einem Biome, das im Graph existiert."""
    import re

    biome_names = {b["name_de"]: b["id"] for b in graph["biomes"]}
    text = LORE_PATH.read_text(encoding="utf-8")
    section = text.split("## 7. Feindtypen", 1)[1]
    rows: list[tuple[str, str]] = []
    for line in section.splitlines():
        m = re.match(r"^\|\s*`([a-z0-9_]+)`\s*\|[^|]*\|\s*([^|]+?)\s*\|", line)
        if m and m.group(1).startswith("enemy_"):
            rows.append((m.group(1), m.group(2)))
    assert rows, "Keine Feind-Zeilen in lore.md §7 gefunden"
    for enemy_id, biome_cell in rows:
        # Zellen wie "Lumenbrunnen (Hub)" → Namensteil vor der Klammer extrahieren.
        name = re.split(r"\s*\(", biome_cell)[0].strip()
        assert name in biome_names, f"Feind {enemy_id} referenziert unbekanntes Biome '{biome_cell}'"
