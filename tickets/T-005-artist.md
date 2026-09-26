# T-005 — Artist: Pixel-Art-Assets (2.5D, 1280×720)

**Owner:** artist | **Abhängigkeit:** T-001 (GDD), `world/map_graph.json` (fertig & abgenommen — Paletten-Hints sind der Vertrag)
**Blockiert:** T-004-Presentation-Layer (Parallax + Spieler-Sprite), UI-Set für HUD

**Ziel:** Komplettes Asset-Set für v1-Scope: 5 Biome-Paletten, Parallax-Layer, Spieler, Feinde, Bosse, UI. Keine neuen Basisfarben — `palette_hint` aus dem Graph ist verbindlich.

## Deliverables (in dieser Reihenfolge)

1. **`assets/CONVENTIONS.md` finalisieren** — Sprite-Größen (Spieler 32×48 px, Feinde 32–64 px, UI auf 960×540 @ 1280×720), Transparenz-Regeln (PNG mit Alpha, kein Weißrand), Biome-Paletten 1:1 aus `palette_hint`, Rarity-Hex-Codes (common/uncommon/rare/epic) als Teil der Konvention
2. **Parallax-Layer** — pro Biome 3 Ebenen: `assets/<biome_id>/parallax_{far,mid,near}.png` (IDs exakt: `lumen_well`, `aschen_wald`, `glut_hoehlen`, `frost_hallen`, `hohle_tiefen`) → 15 Dateien; positionskritisch, Auswahl per headless-Pixelanalyse (erste Nicht-Himmels-Zeile je Spalte), nicht per Bauchgefühl
3. **Spieler-Sprite** — Schwertkämpfer: idle/run/jump/attack/hurt als Framesheet, 32×48 px pro Frame
4. **Feinde + Bosse** — 8 Feindtypen (32–64 px) nach Zonenidentitäten aus `world/lore.md`; 2 Boss-Baseframes (`boss_aschen_waechter`, `boss_frost_koenigin`)
5. **UI-Set** — HUD (HP/XP/Lumen), Item-Rarity-Farbcodes; Hex-Werte müssen mit den Rarity-Keys in `balance/items.json` (@systems) kompatibel sein

## Akzeptanzkriterien

- [ ] `CONVENTIONS.md` final: alle Größen, Pfade und Paletten dokumentiert; jede Biome-Palette deckt die `palette_hint`-Farben aus `map_graph.json` ab (Test: Pixel-Vergleich headless)
- [ ] Alle 15 Parallax-Dateien existieren unter den exakten Pfaden; horizontale Deckung ohne Lücken (Test: Datei-Existenz + Mindestbreite, headless)
- [ ] Spieler-Framesheet enthält alle 5 Zustände (idle/run/jump/attack/hurt), Frames 32×48 px (Test: Dimensions-Check headless)
- [ ] 8 Feind-Sprites + 2 Boss-Baseframes existieren; keine Datei mit Weißrand statt Alpha (Test: Eckpixel-Transparenz, headless)
- [ ] UI-Rarity-Farbcodes sind in `CONVENTIONS.md` als Hex definiert und unterscheiden sich visuell klar voneinander (mind. 1 Farbkanal-Differenz ≥ 64 pro Paar)

## Definition of Done

Alle Boxen grün + QA bestätigt die headless-Asset-Checks + Abnahme durch Designer. Max. 2 Korrekturrunden, danach Scope-Kürzung (Kandidaten: Boss-Baseframes auf 1 Frame je Boss, Feind-Varianten reduzieren).
