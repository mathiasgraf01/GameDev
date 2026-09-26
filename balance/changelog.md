# Balance-Changelog — Lumenfall (T-003)

Jede Kurven-/Datenänderung wird hier mit Begründung protokolliert.

## v1.0 — 2026-09-26 (systems)

Erstauslieferung aller T-003-Daten. Auslöser: Ticket T-003; keine Playtest-Reports
vorhanden (T-006 noch blockiert), daher Basiskurven aus GDD-Zielen abgeleitet.

### Stat-Kurven (`stat_curves.json`)
- **XP:** `40 * 1.1^(level-1)` → L1=40, L20=245. ~10 %/Level, kein Sprung > 50 % (T-003-Cap).
  Begründung: Runs sind 15–20 Min (GDD-Pillar 1); ein typischer Run erreicht Level 8–12,
  also muss die Kurve im unteren Bereich flach genug sein, um mehrere Level pro Run zu geben.
- **Damage:** `base_attack = 10 * 1.08^(level-1)` → L1=10, L20=43 (~8 %/Level). Bewusst
  langsamer als die Feind-Kurve (difficulty.json), damit Items/Affixe den Unterschied machen —
  GDD-Pillar 3 („Builds über Buttons").
- **HP:** linear `100 + 8*(level-1)` → L20=252. Linear, weil HP der am einfachsten zu
  kompensierenden Stat ist (Items/Affixe liefern flat HP).

### Items (`items.json`) — 40 Items
- Verteilung: Waffe 16 / Rüstung 12 / Accessoire 12; Rarity 24/10/4/2 = 60/25/10/5 % (exakt an den T-003-Caps).
- Affix-Anzahl pro Rarity: common 0–1, uncommon 1–2, rare 2–3, epic 3–4 — seltene Items sind
  nicht nur stärker, sondern auch *variabler* (Build-Tiefe, GDD-Pillar 3).
- 4 Trade-off-Affixe (Glutblut, Glasklinge, Schattenritt, Omen) für Build-Entscheidungen.

### Drops (`drops.json`)
- Biome-Tabellen: ~35 % Chance auf ein Item pro Beute-Ereignis; Rest = Lumen nur.
  Begründung: Items sollen spürbar sein, aber kein Run durch Pech verloren gehen — die
  Meta-Währung fließt immer (GDD-Pillar 1). QA misst in T-006 die tatsächliche Verteilung.
- Boss-Tabellen `guaranteed=true`: Aschewächter → Morgenbrecher (epic Waffe, 65 %),
  Frostkönigin → Krone der Frostkönigin (epic Accessoire, 65 %). Bosse sind Biom-Gates und
  müssen immer belohnen.

### Difficulty (`difficulty.json`)
- HP: 1.0/1.35/1.8/2.4/3.2, Damage: 1.0/1.2/1.45/1.75/2.1, XP: 1.0/1.15/1.3/1.45/1.6.
- Belohnung skaliert ab Tiefe 3 langsamer als Gefahr — der Vorsprung muss aus Build und
  Meta-Unlocks kommen (GDD-Pillar 1). Tiefe 5 = Endgame eines Runs (~20 Min).

### Schemas & Tests
- 6 JSON-Schemas (Draft-07) + `tests/test_balance.py` (13 Tests) + `tests/test_balance_refs.py`
  (5 Referenzintegritäts-Tests). Alle 20 Tests grün.
