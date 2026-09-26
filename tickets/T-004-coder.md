# T-004 — Coder: Engine-Kern (pygame, 2.5D Side Scrolling)

**Owner:** coder | **Abhängigkeit:** T-003 (Schemas + Balance-JSONs), T-002 (`world/map_graph.json`, fertig & QA-grün)
**Blockiert:** T-006 (QA Playtest-Bot) — braucht definierten Headless-Modus.

**Ziel:** Lauffähiger Engine-Kern, der das Spiel rein datengetrieben aus `world/` + `balance/` lädt. Kein Hardcoden von Räumen, Items oder Stats im Code.

## Deliverables (in dieser Reihenfolge)

1. **Repo-Gerüst** — `engine/` (Python 3.12, pygame), `main.py`-Entry-Point, feste Verzeichnis-Konventionen (Assets nur aus `assets/`, Daten nur aus `world/` + `balance/`)
2. **Daten-Layer** — Loader für `map_graph.json` (Knoten/Kanten/Gating) und alle `balance/*.json`; Validierung gegen die Schemas von T-003 beim Start, Fehler → klare Headless-Fehlermeldung statt Crash-Mystery
3. **Engine-Loop + Kamera** — Fixed-Timestep-Update (60 Hz), Rendering 2.5D: Parallax-Layer pro Biome-Palette aus `assets/`, Side-Scrolling-Kamera mit Lookahead; Physik-Konstanten (Gravitation, Sprunggeschwindigkeit) als Konstantenblock in `engine/constants.py`
4. **Spieler-Entity** — Kämpfer mit Schwert: Bewegung, Sprung, Angriff (Hitbox), i-Frames, HP aus Stat-Schema; Fähigkeiten aus dem Graph (`ability_double_jump`, `ability_dash`, `ability_wall_slide`, `ability_light_step`) als registrierte Ability-Handler, die bei `granted_at`-Knoten aktiviert werden
5. **Raum-Navigation** — Raumwechsel über Kanten des Graphs: Gating-Check gegen Spieler-Fähigkeiten/Keys (`requires`), bidirektional wie in `meta.edge_semantics`; Startknoten `hub_01`, Zielknoten `hd_05`
6. **Save-System** — Metroidvania-Persistenz: Fähigkeiten, Keys, besiegte Bosse, erreichte Knoten; JSON-Save unter `saves/`, Load beim Start
7. **Headless-Modus (Vertrag für T-006)** — CLI: `python main.py --headless --seed <int> --runs N`; deterministisch pro Seed (alle Zufallsquellen über einen einzigen `random.Random(seed)`), kein Display (`SDL_VIDEODRIVER=dummy`). **Per-Run-Report = fester JSON-Vertrag (fixiert von @qa):** Pflichtfelder exakt `{"seed", "run_id", "outcome": "clear"|"death", "duration_s", "death_zone": <biome_id>|null, "death_cause": <enemy_type|boss|fall|hunger...>|null, "last_node": <node_id>, "items_picked": [{"id","rarity"}], "abilities_gained": [<ability_id>...]}` — zusätzliche Felder erlaubt, Pflichtfelder nie umbenennen. Ein Report-File pro Run (Pfad deterministisch aus Seed+run_id), damit @qa byte-Vergleich fahren kann
8. **Tests** — `tests/test_engine.py`: Daten-Layer lädt echte Artefakte; Gating-Logik (Kante mit `requires` blockiert ohne Fähigkeit); deterministischer Headless-Smoke-Run (gleicher Seed → gleiche Report-Zeile)

## Akzeptanzkriterien

- [ ] Spiel startet headless und mit Display gegen die echten `world/` + `balance/`-Dateien, ohne dass eine Zeile Content im Code hartkodet ist
- [ ] Alle 6 Fähigkeiten/Keys aus dem Graph werden korrekt an ihren `granted_at`-Knoten vergeben und öffnen exakt ihre Kanten (Test)
- [ ] Save/Load: nach Reload sind Fähigkeit, Keys, Boss-State identisch (Test)
- [ ] Headless: `--seed 42 --runs 3` liefert 3 deterministische JSON-Reports; zweiter Lauf mit gleichem Seed → byte-identische Reports
- [ ] Full-Suite (`pytest tests/`) grün headless vor Merge — bestehende Tests (T-002, T-003) dürfen nicht brechen

## Definition of Done

Alle Boxen grün + QA bestätigt den Headless-Lauf (Seed-Reproduzierbarkeit) + Screenshot/Log als Beweis im Ticket. Max. 2 Korrekturrunden, danach Scope-Kürzung (Kamera-Lookahead und Parallax sind die Kürzungs-Kandidaten).
