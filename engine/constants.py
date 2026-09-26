"""Engine-Konstantenblock (T-004, Deliverable 3).

Alle Physik-/Engine-Zahlen an einem Ort — keine Balance-Werte aus balance/
hier duplizieren (die kommen immer aus den JSONs), nur reine Engine-Mechanik.
"""

# --- Zeitbasis -------------------------------------------------------------
FPS = 60                      # Ziel-Framerate (GDD §5)
FIXED_DT = 1.0 / FPS          # Fixed-Timestep-Update in Sekunden
WINDOW_W, WINDOW_H = 1280, 720   # GDD §5: Fenstermodus 1280×720

# --- Physik (Side Scrolling) ----------------------------------------------
GRAVITY = 2000.0              # px/s^2
JUMP_VELOCITY = -540.0        # px/s (negativ = nach oben)
MOVE_SPEED = 260.0            # px/s horizontal
AIR_CONTROL = 0.85            # Faktor für horizontale Steuerung in der Luft
MAX_FALL_SPEED = 900.0        # px/s Terminalgeschwindigkeit

# --- Fähigkeiten (Mechanik; IDs/Grant-Nodes kommen aus map_graph.json) -----
DOUBLE_JUMP_FACTOR = 1.0      # zweite Sprungstärke = 100 % der ersten
DASH_SPEED = 720.0            # px/s während Dash
DASH_TICKS = 8                # Dauer des Dashes in Update-Ticks
WALL_SLIDE_FALL_SPEED = 90.0  # px/s Sinkgeschwindigkeit beim Wandgleiten
WALL_JUMP_VX = 420.0          # px/s horizontale Abstoßung
WALL_JUMP_VY = -500.0         # px/s vertikale Abstoßung

# --- Kampf (Mechanik; Stat-Werte kommen aus balance/) ----------------------
ATTACK_COOLDOWN_TICKS = 30    # ~0,5 s zwischen Schwingschlägen
ATTACK_ACTIVE_TICKS = 8       # Hitbox aktiv während dieser Ticks
IFRAME_TICKS = 30             # i-Frames nach Treffer (~0,5 s)
CRIT_CHANCE_BASE = 5.0        # % Basis-Krit-Chance (Items addieren darüber)
CRIT_DAMAGE_BASE = 50.0       # % zusätzlicher Kritschaden

# --- Headless-Simulation (T-006-Vertrag) -----------------------------------
RUN_STEP_BUDGET = 60          # Kanten-Traversals pro Run; danach Tod durch Hunger
ENCOUNTER_CHANCE = 0.55       # Wahrscheinlichkeit eines Feind-Kampfes beim Betreten eines Raums
COMBAT_MAX_ROUNDS = 120       # harte Runde-Obergrenze (Determinismus, kein Endloskampf)
DAMAGE_VARIANCE = (0.85, 1.15)  # Zufallsband pro Treffer

# Fall-Hazard pro Biome (pro Kanten-Traversal); 0 = sicher
HAZARD_FALL_CHANCE = {
    "glut_hoehlen": 0.04,     # Lavafälle
    "hohle_tiefen": 0.03,     # Schacht-Lücken
}

# --- Raum-Geometrie (Display-Modus) ----------------------------------------
NODE_WORLD_W = 1920           # Weltbreite pro Node (px), Kamera scrollt darin
NODE_WORLD_H = 720            # Welthöhe pro Node (px)
CAMERA_LOOKAHEAD = 160.0      # px Lookahead in Blickrichtung
