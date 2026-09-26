"""Lumenfall Engine-Kern (T-004, Owner: coder).

Module-Layout:
    constants.py   Physik-/Engine-Konstanten (ein einziger Konstantenblock)
    data.py        Daten-Layer: lädt world/ + balance/, validiert gegen Schemas
    drops.py       Drop-Wurf + Affix-Roll (Vertrag: balance/schema.md)
    player.py      Spieler-Entity (Stats, Fähigkeiten, i-Frames)
    enemies.py     Feind-/Boss-Spawns aus Biome + Run-Tiefe
    navigation.py  Graph-Navigation + Gating-Check
    rooms.py       Deterministische Raum-Layouts aus dem Graphen (keine Koordinaten im Datenformat)
    savegame.py    Metroidvania-Persistenz (JSON unter saves/)
    headless.py    Deterministischer Run-Simulator + Report-Vertrag für T-006
    game.py        pygame-Loop: Fixed-Timestep, Kamera, Parallax (Display-Modus)
"""

__version__ = "0.1.0"
