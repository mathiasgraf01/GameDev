# T-003 — Systems: Daten-Schemas & Balance

**Owner:** systems | **Abhängigkeit:** T-001 (erledigt) | **Blockiert:** T-004 (Coder), QA-Bot
**Parallel zu:** T-002 (Worldbuilder) — beide hängen nur an T-001.

**Ziel:** Alle Daten-Schemas und Balance-Dateien liefern, damit der Coder gegen stabile Verträge baut.

## Deliverables

1. `balance/schema/*.json` — JSON-Schemas für Stats, Items, Affixe, Drops, Difficulty
2. `balance/stat_curves.json` — XP-Kurve, Damage-/HP-Scaling (Level 1–20)
3. `balance/items.json` — ≥ 30 Items mit Rarity-Stufen
4. `balance/affixes.json` — Affix-Pool mit Min/Max-Bereichen
5. `balance/drops.json` — Drop-Tabellen pro Biome/Boss
6. `balance/difficulty.json` — Feind-Scaling pro Run-Tiefe
7. `tests/test_balance.py` — headless Validierung (gemeinsam mit QA)

## Akzeptanzkriterien

- [x] Alle JSON-Dateien validieren gegen ihre Schemas (Test: jsonschema, headless)
- [x] stat_curves.json: XP- und Damage-Kurven monoton steigend für Level 1–20; kein Sprung > 50 % zwischen zwei benachbarten Levels
- [x] items.json: ≥ 30 Items über Waffe/Rüstung/Accessoire verteilt; jedes Item referenziert nur Stat-Keys, die im Schema definiert sind; Rarity-Verteilung common/uncommon/rare/epic ≤ 60/25/10/5 %
- [x] affixes.json: jedes Affix hat Min/Max-Bereich; kein einzelnes Affix überschreitet ±100 % des Basiswerts (Sanity-Grenze)
- [x] drops.json: Wahrscheinlichkeiten pro Tabelle summieren sich zu ≤ 1.0; jedes Biome und beide Bosse haben eine Drop-Tabelle
- [x] difficulty.json: Feind-HP/-Damage-Scaling für Run-Tiefe 1–5 definiert, monoton nicht-fallend
- [x] `tests/test_balance.py` läuft headless durch (pytest, ohne Display)

## Definition of Done

Alle Boxen grün + QA bestätigt den Testlauf + Abnahme durch Designer. Max. 2 Korrekturrunden, danach Scope-Kürzung.
