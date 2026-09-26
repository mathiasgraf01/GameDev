"""Headless-Modus (T-004, Deliverable 7) — deterministischer Run-Simulator.

Vertrag für T-006 (@qa):
- CLI: `python main.py --headless --seed <int> --runs N`
- Alle Zufallsquellen laufen über EINEN `random.Random(seed)` pro Run →
  gleicher Seed = byte-identische Reports (zweiter Lauf überschreibt).
- Kein Display (`SDL_VIDEODRIVER=dummy`), kein pygame-Import nötig.
- Per-Run-Report als JSON, ein File pro Run; Pfad deterministisch aus
  Seed + run_id: `reports/<seed>/<run_id>.json`.

Pflichtfelder (fixiert von @qa — nie umbenennen):
    seed, run_id, outcome ("clear"|"death"), duration_s,
    death_zone (<biome_id>|null), death_cause (<enemy_type|boss|fall|hunger...>|null),
    last_node (<node_id>), items_picked ([{"id","rarity"}]), abilities_gained ([<ability_id>])
Zusätzliche Felder sind erlaubt.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from .constants import (
    COMBAT_MAX_ROUNDS,
    DAMAGE_VARIANCE,
    ENCOUNTER_CHANCE,
    HAZARD_FALL_CHANCE,
    RUN_STEP_BUDGET,
)
from .data import GameData
from .drops import roll_drop
from .enemies import enemies_for_biome, make_boss, make_enemy
from .navigation import neighbors
from .player import Player

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"

# Simulierte Zeit pro Aktion (Sekunden) — reine Engine-Mechanik.
TIME_PER_TRAVERSAL_S = 8.0
TIME_PER_COMBAT_ROUND_S = 1.5


def report_path(seed: int, run_id: int) -> Path:
    """Deterministischer Report-Pfad aus Seed + run_id."""
    return REPORTS_DIR / str(seed) / f"{run_id}.json"


class RunResult(dict):
    pass


def _combat(rng: random.Random, data: GameData, player: Player, enemy: dict, depth: float) -> tuple[bool, int]:
    """Rundenbasiertem Kampf; liefert (spieler_gewonnen, Runden)."""
    mult = data.depth_row(depth)
    hp = player.max_hp
    enemy_hp = enemy["hp"]
    rounds = 0
    while rounds < COMBAT_MAX_ROUNDS:
        rounds += 1
        # Spielerangriff (Krit-Chance/-Damage aus Stats + Items)
        crit = rng.random() * 100.0 < player.crit_chance
        dmg = player.attack * rng.uniform(*DAMAGE_VARIANCE)
        if crit:
            dmg *= 1.0 + player.crit_damage / 100.0
        enemy_hp -= dmg
        if enemy_hp <= 0:
            return True, rounds
        # Gegentreffer (Defense mindert flat; i-Frames lassen jeden 4. Treffer durchrutschen)
        if rng.random() < 0.25:
            continue
        taken = max(1.0, enemy["damage"] * rng.uniform(*DAMAGE_VARIANCE) - player.defense)
        hp -= taken
        if hp <= 0:
            return False, rounds
    # Runde-Obergrenze: Unentschieden → Spieler verliert (Determinismus-Garantie)
    return False, rounds


def simulate_run(data: GameData, seed: int, run_id: int = 1) -> dict:
    """Ein deterministischer Run; liefert den Report-Dict (Pflichtfelder + Extras).

    Determinismus-Vertrag: gleicher Seed → byte-identische Reports. Die Runs
    innerhalb einer Seed-Serie werden über `run_id` abgeleitet, damit sie sich
    unterscheiden, aber pro (seed, run_id) exakt reproduzierbar bleiben.
    """
    rng = random.Random(f"{seed}:{run_id}")
    player = Player(data)
    node = data.start_node
    player.visited_nodes.add(node)

    duration_s = 0.0
    steps = 0
    items_picked: list[dict] = []
    abilities_gained: list[str] = []
    outcome = "death"
    death_zone: str | None = data.biome_of(node)
    death_cause: str | None = None

    def _grant_node_grants(current: str) -> None:
        for ability_id in data.grants_at(current):
            if not player.has_ability(ability_id):
                player.grant(ability_id)
                abilities_gained.append(ability_id)

    _grant_node_grants(node)

    while steps < RUN_STEP_BUDGET:
        # Ziel erreicht?
        if node == data.final_node:
            outcome = "clear"
            death_zone = None
            break

        # Nächsten Node wählen: unbebesuchte Nachbarn bevorzugen (BFS-Ordnung),
        # sonst zufälliger Nachbar — Auswahl über den einzigen Run-RNG.
        options = neighbors(data, node, player.abilities, player.bosses_defeated)
        if not options:
            death_cause = "hunger"  # Sackgasse ohne Rückweg → Run endet
            break
        unvisited = [t for t, _e in options if t not in player.visited_nodes]
        pool = unvisited or [t for t, _e in options]
        target, edge = (None, None)
        chosen_target = rng.choice(pool)
        for t, e in options:
            if t == chosen_target:
                target, edge = t, e
                break

        # Traversal: Fall-Hazard des Ziel-Biomes
        steps += 1
        duration_s += TIME_PER_TRAVERSAL_S
        biome = data.biome_of(target)
        fall_chance = HAZARD_FALL_CHANCE.get(biome, 0.0)
        if rng.random() < fall_chance:
            node = target
            death_zone = biome
            death_cause = "fall"
            break

        node = target
        player.visited_nodes.add(node)
        _grant_node_grants(node)

        # Run-Tiefe wächst mit Fortschritt (difficulty.json skaliert Feinde/XP)
        depth = min(5.0, 1.0 + steps / 20.0)

        node_info = data.nodes[node]
        boss_id = node_info.get("boss_id")
        if boss_id and boss_id not in player.bosses_defeated:
            # Boss-Kampf (Siegel des Risses; guaranteed Drop nach Sieg)
            enemy = make_boss(rng, data, boss_id, depth)
            won, rounds = _combat(rng, data, player, enemy, depth)
            duration_s += rounds * TIME_PER_COMBAT_ROUND_S
            if not won:
                death_zone = biome
                death_cause = boss_id
                break
            player.bosses_defeated.add(boss_id)
            player.gain_xp(enemy["xp_reward"] * data.depth_row(depth)["xp_reward_multiplier"])
            player.gain_lumen(25.0)
            drop = roll_drop(rng, data, boss_id)  # guaranteed → immer ein Item
            if drop:
                items_picked.append({"id": drop["id"], "rarity": drop["rarity"]})
                player.equip(drop)
        elif rng.random() < ENCOUNTER_CHANCE and enemies_for_biome(biome):
            enemy_id = rng.choice(enemies_for_biome(biome))
            enemy = make_enemy(rng, data, enemy_id, depth)
            won, rounds = _combat(rng, data, player, enemy, depth)
            duration_s += rounds * TIME_PER_COMBAT_ROUND_S
            if not won:
                death_zone = biome
                death_cause = enemy_id
                break
            player.gain_xp(enemy["xp_reward"] * data.depth_row(depth)["xp_reward_multiplier"])
            player.gain_lumen(5.0)
            drop = roll_drop(rng, data, biome)  # Biome-Tabelle; Rest = nur Lumen
            if drop:
                items_picked.append({"id": drop["id"], "rarity": drop["rarity"]})
                player.equip(drop)

    report = {
        "seed": seed,
        "run_id": run_id,
        "outcome": outcome,
        "duration_s": round(duration_s, 2),
        "death_zone": death_zone if outcome == "death" else None,
        "death_cause": death_cause if outcome == "death" else None,
        "last_node": node,
        "items_picked": items_picked,
        "abilities_gained": abilities_gained,
        # Zusätzliche Felder (erlaubt):
        "level_reached": player.level,
        "lumen_earned": round(player.lumen, 2),
        "nodes_visited": len(player.visited_nodes),
    }
    return report


def write_report(report: dict) -> Path:
    """Report deterministisch schreiben (sort_keys → byte-stabil)."""
    path = report_path(report["seed"], report["run_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def run_headless(data: GameData, seed: int, runs: int = 1) -> list[dict]:
    """N Runs mit derselben Seed simulieren und Reports schreiben."""
    reports = []
    for run_id in range(1, runs + 1):
        report = simulate_run(data, seed, run_id=run_id)
        write_report(report)
        reports.append(report)
    return reports
