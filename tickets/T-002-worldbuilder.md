# T-002 — World: Raumgraph & Lore-Bibel

**Owner:** worldbuilder | **Abhängigkeit:** T-001 (erledigt) | **Blockiert:** T-004 (Coder), T-005 (Artist)
**Parallel zu:** T-003 (Systems) — beide hängen nur an T-001.

**Ziel:** Kompletter Map-Graph und Lore-Fundament liefern, damit der Coder gegen stabile Daten bauen kann.

## Deliverables

1. `world/map_graph.json` — Raum-/Node-Graph mit Gating
2. `world/lore.md` — Lore-Bibel: Biome, NPCs, Items, Quest-Hooks
3. `tests/test_map_graph.py` — headless Validierung (gemeinsam mit QA)

## Akzeptanzkriterien

- [ ] map_graph.json enthält 1 Hub + 4 Biome und ≥ 30 Nodes
- [ ] Jeder Node ist vom Start-Node aus erreichbar; keine Orphan-Nodes (Test: BFS/DFS über alle Kanten)
- [ ] Jede gated Kante referenziert eine Fähigkeit-ID aus der GDD-Fähigkeitsliste; jede der 6 Fähigkeiten wird mindestens einmal als Gate verwendet
- [ ] 2 Boss-Räume sind so platziert, dass jeder ein Gate zu einem neuen Biome-Cluster ist
- [ ] Keine Zyklen im Gating (Fähigkeit A vor B, keine kreisförmigen Abhängigkeiten) — per Topologischer Sortierung testbar
- [ ] lore.md: konsistente Benennung aller in map_graph.json referenzierten Biome/NPCs/Items; ≥ 3 Quest-Hooks definiert
- [ ] `tests/test_map_graph.py` läuft headless durch (pytest, ohne Display)

## Definition of Done

Alle Boxen grün + QA bestätigt den Testlauf + Abnahme durch Designer. Max. 2 Korrekturrunden, danach Scope-Kürzung.
