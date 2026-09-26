# Balance-Schemas — Lumenfall (T-003)

**Owner:** systems | **Version:** 1.0 | **Status:** final für T-004

Alle Spieldaten liegen als JSON in `balance/`. Die Engine liest nur diese Dateien — keine
hartkodierten Werte (GDD §5). Jede Datei validiert gegen ihr Schema in `balance/schema/`
(geprüft headless: `pytest tests/test_balance.py`).

## Dateiverzeichnis

| Datei | Inhalt | Schema |
|---|---|---|
| `stat_curves.json` | XP-Kurve, HP/Damage-Scaling Level 1–20 | `schema/stat_curves.schema.json` |
| `items.json` | 40 Items (Waffe/Rüstung/Accessoire) mit Rarity | `schema/items.schema.json` |
| `affixes.json` | Affix-Pool mit Min/Max-Bereichen in % des Basiswerts | `schema/affixes.schema.json` |
| `drops.json` | Drop-Tabellen pro Biome (5) und Boss (2) | `schema/drops.schema.json` |
| `difficulty.json` | Feind-Scaling Run-Tiefe 1–5 | `schema/difficulty.schema.json` |
| `schema/stats.schema.json` | Stat-Vokabular: die einzigen erlaubten Stat-Keys | — (Referenz) |

## Stat-Vokabular (`stats.schema.json`)

Die einzigen gültigen Stat-Keys — Items, Affixe und Kurven dürfen nur diese verwenden:

| Key | Typ | Semantik |
|---|---|---|
| `max_hp` | int | Zusätzliche maximale Lebenspunkte (flat) |
| `attack` | int | Zusätzlicher Basisangriff (flat) |
| `defense` | int | Zusätzliche Verteidigung (flat) |
| `speed` | float | Bewegungs-/Aktionsgeschwindigkeit in % des Basiswerts |
| `crit_chance` | float | Krit-Chance in Prozentpunkten (flat) |
| `crit_damage` | float | Zusätzlicher Kritschaden in % |
| `lumen_gain` | float | Bonus auf Lumen-Ertrag in % (Meta-Währung, GDD-Pillar 1) |

## ID-Konventionen

- **Items:** `item_{w|a|z}_{name}` — w=Waffe, a=Rüstung, z=Accessoire
- **Affixe:** `affix_{name}`
- **Quellen (source):** Biome-ID oder Boss-ID aus `world/map_graph.json`, oder `"any"`

## Verträge für die Engine (T-004)

1. **Affix-Roll:** Wert wird uniform zwischen `min_pct` und `max_pct` des *Basiswerts* der
   Stat gezogen (Basiswert = `stat_curves.json` + Item-`base_stats`). Kein Roll außerhalb ±100 %.
2. **Drop-Wurf (Biome):** Einträge werden mit ihren Wahrscheinlichkeiten gewürfelt; die
   Restwahrscheinlichkeit (Summe < 1.0) bedeutet „kein Item, nur Lumen".
3. **Drop-Wurf (Boss):** `guaranteed: true` — genau ein Eintrag wird nach Renormierung der
   Wahrscheinlichkeiten gewürfelt. Bosse belohnen immer (Roguelike-Fairness).
4. **Run-Tiefe:** Feind-HP/Schaden werden mit den Multiplikatoren aus `difficulty.json`
   skaliert; XP-Belohnung ebenfalls, aber langsamer (Belohnung < Gefahr ab Tiefe 3).
5. **Referenzintegrität:** Jede Kreuzreferenz (Item→Affix, Drop→Item, Tabelle→Biome/Boss)
   wird in `tests/test_balance_refs.py` geprüft — neue Daten müssen die Tests grün lassen.

## Erweiterung ohne Code

Neues Item = Eintrag in `items.json` + Eintrag in einer Drop-Tabelle. Neues Affix =
Eintrag in `affixes.json`. Neue Run-Tiefe = Zeile in `difficulty.json`. In keinem Fall
muss Engine-Code geändert werden; die Schemas legen die Grenzen fest, die Tests wachen darüber.
