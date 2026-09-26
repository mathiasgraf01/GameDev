# Asset-Konventionen — Lumenfall v1

**Status:** FINAL (T-005, Deliverable 1) | **Owner:** artist
Alle Assets in `assets/` folgen dieser Datei. Kein Asset wird produziert, das hier nicht spezifiziert ist.
Farbvertrag: Die Biome-Paletten sind **1:1 aus den `palette_hint`-Arrays** in `world/map_graph.json` — keine neuen Basisfarben (Designer-Freigabe).

## 0. Zielplattform & Pipeline

- Fenstermodus **1280×720**, UI-Layout auf **960×540** zentriert (sicherer Bereich, Rest = Letterbox-Marge)
- Alle Assets: PNG mit Alpha-Kanal (RGBA), sRGB
- Produktions-Pipeline (ComfyUI → Konvention): Generierung in hoher Auflösung → Zuschneiden → Nearest-Neighbor-Skalierung auf Zielgröße → Alpha-Matting → Palette-Quantisierung auf die Biome-Palette (Sprites) bzw. Rarity-Farben (UI). Kein Asset landet mit fremden Farben im Repo.

## 1. Sprite-Größen

| Asset | Größe | Pfad |
|---|---|---|
| Spieler (Schwertkämpfer), pro Frame | **32×48 px** | `assets/player/swordfighter_frames.png` |
| Feinde, pro Frame | **32–64 px** (Höhe ≤ 64) | `assets/enemies/<enemy_id>.png` |
| Boss-Baseframes | **96×128 px** | `assets/bosses/<boss_id>_base.png` |
| Parallax-Layer (alle 3 Ebenen) | **1536×720 px**, horizontal kachelbar | `assets/<biome_id>/parallax_{far,mid,near}.png` |
| UI-Elemente | Layout auf 960×540, Einzelteile ≤ 256×256 px | `assets/ui/` |

### Spieler-Framesheet (`swordfighter_frames.png`)

Eine Datei, **Zeilen = Zustände** in fester Reihenfolge, Spalten = Frames (horizontal):

| Zeile | Zustand | Frames |
|---|---|---|
| 0 | idle | 4 |
| 1 | run | 6 |
| 2 | jump | 1 |
| 3 | attack | 4 |
| 4 | hurt | 1 |

Jeder Frame exakt **32×48 px**, Sheet-Höhe = 5 × 48 = 240 px, Breite = max. Frames pro Zeile (6) × 32 = 192 px. Leere Zellen am Zeilenende: Alpha=0.

### Feind-IDs

`<enemy_id>` kommt von @worldbuilder (lore.md / GDD-Scope „8 Feindtypen"); bis dahin keine eigenen IDs erfinden. Bosse: `boss_aschen_waechter`, `boss_frost_koenigin` (exakt aus dem Graph).

## 2. Biome-Paletten (Vertrag, 1:1 aus map_graph.json)

Jede Palette = die 4 `palette_hint`-Farben des Biomes + **eine Akzentfarbe für UI/Partikel**, die ebenfalls nur aus den vorhandenen Hint-Farben gewählt wird (Designer-Freigabe).

| Biome-ID | Basis-Palette (Hint 1–4) | Akzent (UI/Partikel) |
|---|---|---|
| `lumen_well` | #f5f1e6, #c9d8e8, #7fa8c9, #2b3a4a | **#f5f1e6** (Lumen-Weiß, Partikel) |
| `aschen_wald` | #1a2418, #3d5c3a, #9fd670, #e8f5c8 | **#9fd670** (Sporen-Glow) |
| `glut_hoehlen` | #241010, #8c3b2e, #f28c38, #ffd9a0 | **#f28c38** (Glut/Lava) |
| `frost_hallen` | #0e1c26, #3a7ca5, #9fd8ef, #f0fbff | **#9fd8ef** (Eis-Brechung) |
| `hohle_tiefen` | #140f24, #4a3d78, #9b7fd4, #ffe9a0 | **#ffe9a0** (Lumen-Gold am Kern) |

Regeln:
- Sprites eines Biomes werden ausschließlich auf die 5 Farben des Biomes quantisiert.
- Der Akzent darf nur für Partikel, Glow und UI-Highlights innerhalb dieses Biomes verwendet werden — nie als Flächenfarbe.
- QA-Check (headless): Jedes Asset-Pixel muss zu einer Farbe der zugehörigen Palette gehören (Toleranz: exakt nach Quantisierung).

## 3. Parallax-Layer (2.5D, positionskritisch)

Pro Biome **drei Ebenen**, exakte Pfade (Coder-Vertrag):
`assets/<biome_id>/parallax_far.png`, `parallax_mid.png`, `parallax_near.png` → **15 Dateien**.

- Größe: 1536×720 px, **horizontal kachelbar** (linke/rechte Kante nahtlos)
- Scroll-Geschwindigkeiten (Engine): far = 0.2×, mid = 0.5×, near = 0.8× der Kamera
- **Höhen-Freigabe:** Die oberen 40 % (Zeilen 0–287) jeder Ebene enthalten nur Himmel/Atmosphäre — keine Silhouetten, keine Objekte. Der Horizont/die erste Nicht-Himmels-Zeile liegt je Spalte bei y ≥ 288
- `far`: weite Silhouette + Atmosphäre; `mid`: mittlere Struktur (Bäume/Felsen/Säulen); `near`: Vordergrund-Rahmen (Wurzeln, Felslippen), darf unten ausbluten
- Keine Textelemente, keine Figuren in Parallax-Layern

**Produktionsregel:** Positionskritische Ebenen werden nie aus einem einzigen Seed generiert. Pro Ebene: 3–4 Seeds parallel → headless-Pixelanalyse (erste Nicht-Himmels-Zeile je Spalte, muss ≥ 288 sein; plus Kachelbarkeit-Check der Kanten) → bestes Bild wird gepickt. Seed + Analyse-Ergebnis landen im Commit-Log.

## 4. Transparenz

- Alle Sprites (Spieler, Feinde, Bosse): PNG RGBA, **alle vier Eckpixel mit Alpha = 0** (kein Weißrand, kein Bounding-Box-Rand)
- Parallax-Layer: ohne Alpha (volle Fläche), Ausnahme `near`-Ebene unten erlaubt weiche Ausblutung nur innerhalb der Biome-Palette
- Framesheet-leere Zellen: Alpha = 0

## 5. UI & Rarity-Farbcodes

UI-Elemente (`assets/ui/`): HUD-Hintergrund, HP-/XP-Balken, Lumen-Zähler, Item-Rahmen. Layout auf 960×540; Farben aus der `lumen_well`-Palette (Meta-Ort) + Rarity-Farben für Item-Rahmen/-Glow.

**Rarity-Hex-Codes** — Keys exakt wie in @systems' `balance/items.json`:

| Rarity-Key | Hex |
|---|---|
| common | #b8b8b8 |
| uncommon | #4caf50 |
| rare | #3b82f6 |
| epic | #bf5af2 |

Verträglichkeitsnachweis (mind. 1 Kanal-Differenz ≥ 64 pro Paar): common–uncommon ΔR=108, common–rare ΔR=125, common–epic ΔG=94, uncommon–rare ΔB=166, uncommon–epic ΔR=115, rare–epic ΔR=132. ✓

## 6. Pfad-Index (vollständig für v1)

```
assets/CONVENTIONS.md
assets/player/swordfighter_frames.png
assets/enemies/<enemy_id>.png            # ×8, IDs von @worldbuilder
assets/bosses/boss_aschen_waechter_base.png
assets/bosses/boss_frost_koenigin_base.png
assets/lumen_well/parallax_{far,mid,near}.png
assets/aschen_wald/parallax_{far,mid,near}.png
assets/glut_hoehlen/parallax_{far,mid,near}.png
assets/frost_hallen/parallax_{far,mid,near}.png
assets/hohle_tiefen/parallax_{far,mid,near}.png
assets/ui/{hud_bg,bar_hp,bar_xp,lumen_counter,item_frame}.png
```
