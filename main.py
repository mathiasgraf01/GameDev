"""Lumenfall — Entry-Point (T-004).

Verwendung:
    python main.py                          # Display-Modus (pygame, 1280×720)
    python main.py --headless               # Headless-Smoke-Run (Seed 1, 1 Run)
    python main.py --headless --seed 42 --runs 3   # T-006-Vertrag: deterministische Reports

Alle Spieldaten kommen aus world/ + balance/ (datengetrieben); Assets nur aus assets/.
"""
from __future__ import annotations

import argparse
import os
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lumenfall", description="Lumenfall Engine-Kern")
    parser.add_argument("--headless", action="store_true", help="ohne Display simulieren (T-006)")
    parser.add_argument("--seed", type=int, default=1, help="Zufalls-Seed (deterministisch pro Seed)")
    parser.add_argument("--runs", type=int, default=1, help="Anzahl Runs im Headless-Modus")
    args = parser.parse_args(argv)

    # Daten-Layer: lädt + validiert world/ und balance/ (Fehler → klare Meldung)
    from engine.data import DataLoadError, GameData

    try:
        data = GameData()
    except DataLoadError as exc:
        print(f"[Lumenfall] Datenfehler: {exc}", file=sys.stderr)
        return 2

    if args.headless:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        from engine.headless import run_headless

        reports = run_headless(data, seed=args.seed, runs=max(1, args.runs))
        for report in reports:
            print(f"[Lumenfall] Run {report['run_id']}: outcome={report['outcome']} "
                  f"node={report['last_node']} duration={report['duration_s']}s "
                  f"items={len(report['items_picked'])} abilities={report['abilities_gained']}")
        print(f"[Lumenfall] {len(reports)} Report(s) unter reports/{args.seed}/ geschrieben.")
        return 0

    # Display-Modus: Save laden (falls vorhanden), sonst frischer Start.
    from engine.game import Game
    from engine.player import Player
    from engine.savegame import has_save, load_game, save_game

    if has_save():
        player, node, depth = load_game(data)
        print(f"[Lumenfall] Save geladen (Node {node}, Tiefe {depth:.1f}).")
    else:
        player, node, depth = Player(data), data.start_node, 1.0

    game = Game(data, player, seed=args.seed)
    try:
        game.run()
    finally:
        save_game(data, player, game.node_id, depth)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
