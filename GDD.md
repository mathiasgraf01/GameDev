# GDD — LUMENFALL (Arbeitstitel)

**Version:** 0.2 | **Owner:** Designer (Leitung) | **Status:** T-002 abgenommen; T-003/T-004/T-005/T-006 in Arbeit

## Ticket-Status

| Ticket | Owner | Status |
|---|---|---|
| T-001 GDD & Repo-Gerüst | designer | ✅ Abgeschlossen |
| T-002 Raumgraph + Lore | worldbuilder | ✅ **Abgenommen** (QA 13/13 grün; 31 Nodes, 6 Gates, 4 Quest-Hooks verifiziert) |
| T-003 Schemas + Balance | systems | 🔄 In Arbeit — Blocker für T-004-Balance-Teile |
| T-004 Engine-Kern | coder | 🔄 In Arbeit (Daten-Layer gegen fertigen Graph; Balance-Teile warten auf T-003) |
| T-005 Assets | artist | ⏳ Freigegeben — CONVENTIONS.md zuerst, dann Parallax/Sprites |
| T-006 Playtest-Bot | qa | ⏳ Blockiert durch T-004 (Headless-Modus) |

**Reihenfolge:** T-003 → T-004 voll → T-005 parallel ab CONVENTIONS.md → T-006 nach T-004.

## 1. Spielvision

Lumenfall ist ein Metroidvania mit RPG- und Roguelike-Elementen: Der Spieler erkundet eine
zusammenhängende Unterwelt aus Licht und Dunkelheit, kämpft sich durch ability-gated Areale
und baut seinen Charakter über Stats, Items und Affixe — behält nach jedem Tod aber
Meta-Fortschritt bei, der den nächsten Run tiefer und stärker macht.

Fantasy in einem Satz: *Jeder Tod bringt dich näher an den Kern.*

## 2. Design-Pillars

1. **Jeder Tod lehrt.** Runs sind kurz (Ziel 15–20 Min). Der Tod ist kein Rückschlag,
   sondern ein Fortschrittsschritt: Die Meta-Währung „Lumen" bleibt erhalten und schaltet
   neue Inhalte, Items und Start-Boni frei.
2. **Die Welt ist die Karte.** Ein zusammenhängender Raum ohne Ladescreens zwischen Biomen.
   Fortschritt entsteht durch Fähigkeiten, die die Map gateen (Double Jump, Dash, Schlüssel) —
   nicht allein über Levelzahlen.
3. **Builds über Buttons.** Tiefe kommt aus Build-Entscheidungen (Stats, Affixe, Item-Synergien),
   nicht aus Buttonmashing. Eine Klasse, viele tragfähige Builds; kein Pflicht-Gear.

## 3. Core Loop

- **Innere Schleife (Sekunden):** Bewegen → Kämpfen → Beute/Affix-Rolls einsammeln
- **Mittlere Schleife (Minuten):** Biom erkunden → Fähigkeit/Schlüssel finden → neues Map-Areal freischalten
- **Äußere Schleife (Runs):** Am Boss sterben oder freiwillig aussteigen → Lumen + Meta-Unlocks behalten → nächster Run mit stärkerem Build und tieferem Zugang

## 4. Scope v1

**Drin:**
- 1 Hub + 4 Biome, ≥ 30 Map-Nodes (world/map_graph.json)
- 2 Bosse als Biom-Gates
- 6 Gating-Fähigkeiten (z. B. Double Jump, Dash, Wandgleiten, Schlüssel ×2)
- 8 Feindtypen, 1 Klasse mit Build-Tiefe
- ~30 Items (Waffe/Rüstung/Accessoire), Affix-System mit Rarity-Stufen
- Meta-Fortschritt: Lumen-Währung + Unlock-Baum (~15 Nodes)
- 1 Save-Slot, headless testbar

**Nicht drin (v1):**
- Multiplayer / Co-op
- Crafting und Inventar-Management über ein einfaches Raster hinaus
- Dialogbäume (nur kurze Zeilen für NPCs)
- Controller-Support (Tastatur), Mobile/andere Plattformen
- Mehrere Charaktere/Klassen
- Dynamisches Musikstreaming (Loops sind OK)

## 5. Zielplattform & Tech

- **Plattform:** Windows, Fenstermodus 1280×720, Ziel 60 FPS
- **Engine:** Python 3.12+, Pygame 2.x
- **Datenantrieb:** Alle Spieldaten als JSON (world/, balance/). Der Code liest nur Schemas —
  keine hartkodeten Werte in der Engine.
- **Tests:** pytest, headless (ohne Display lauffähig)

## 6. Repo-Struktur & Ownership

| Pfad | Inhalt | Owner |
|---|---|---|
| world/ | map_graph.json, lore.md (Lore-Bibel), Quests | Worldbuilder |
| balance/ | Schemas + Stat-Kurven, Items, Affixe, Drops, Difficulty | Systems |
| assets/ | Sprites, Backgrounds, UI + CONVENTIONS.md | Artist |
| src/ | Engine-Code (wird in T-004 angelegt) | Coder |
| tests/ | Headless-Tests für alle Daten und Systeme | QA / Coder |

## 7. Offene Punkte

- Finaler Name: „Lumenfall" ist Arbeitstitel — Entscheidung vor Asset-Produktion (T-005).
- Exakte Fähigkeit-IDs: Worldbuilder definiert sie in map_graph.json; Systems referenziert sie.
