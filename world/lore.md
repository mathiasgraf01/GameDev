# LUMENFALL — Lore-Bibel

**Version:** 1.0 | **Owner:** worldbuilder (T-002) | **Status:** Freigegeben für T-004/T-005
**Vertrag:** Alle Biome-, NPC- und Item-Namen in `world/map_graph.json` sind hier definiert. Neue Einträge erst nach Prüfung gegen diese Bibel ins Repo.

## 1. Grundmythos (Kanon)

Die Welt von Lumenfall ruhte einst auf dem **Lumenkern**, einer Quelle reinen Lichts tief unter der Erde. Als die Kernhülle riss, sickerte das Licht in Schichten nach oben: Es nährte den Wald, schmolz die Tiefe zu Glut, fror die Hallen an und ließ den Brunnen am Ort des Risses sprudeln — den **Lumenbrunnen**.

Seitdem stirbt das Licht langsam. Jeder Tod eines Helden im Kernschacht speist einen Teil seines Lumen zurück in den Brunnen: *Jeder Tod bringt dich näher an den Kern.* Die Leuchtmutter sammelt dieses Lumen und schaltet damit neue Wege der Unterwelt frei — nicht als Gnade, sondern weil der Kern es verlangt.

Die vier Biome sind die vier Wunden des Risses: Wald (Asche), Tiefe (Glut), Hallen (Frost) und der Brunnen selbst (Licht).

## 2. Biome

| ID | Name | Rolle in der Welt | Visuelle Identität |
|---|---|---|---|
| `lumen_well` | **Lumenbrunnen** (Hub) | Meta-Ort: Lumen-Währung, Unlock-Baum, Leuchtmutter. Vier Ausgänge zu den Biomen + der Tiefe Brunnen. | Weißer Stein, schwebende Lichtpartikel, ruhige Partikeldichte. Palette: `#f5f1e6 #c9d8e8 #7fa8c9 #2b3a4a` |
| `aschen_wald` | **Aschewald** | Erste Erkundungszone. Der Wald trank das Licht und verdarb es zu Asche; nur Sporen leuchten noch. | Tote Eichen, grüne Sporenleuchte, Kronenpfade über dem Boden. Palette: `#1a2418 #3d5c3a #9fd670 #e8f5c8` |
| `glut_hoehlen` | **Gluthöhlen** | Die Tiefe schmolz unter der Last des Lichts. Korrin schmiedet hier die letzten Waffen aus Glutkern-Eisen. | Lavafälle, Klammbrücken, Hitze-Distortion. Palette: `#241010 #8c3b2e #f28c38 #ffd9a0` |
| `frost_hallen` | **Frosthallen** | Ein unterirdischer Palast, der das Licht fror statt es zu trinken — und damit die Frostkönigin weckte. | Spiegelnde Kuppeln, Eiskathedrale, klare Linien, Stille. Palette: `#0e1c26 #3a7ca5 #9fd8ef #f0fbff` |
| `hohle_tiefen` | **Hohle Tiefen** | Der Kernschacht selbst. Lumenadern pulsierten hier, bis der Riss sie zum Stillstand brachte. | Purpurnes Gestein, leuchtende Adern, Lichtbrücken über dem Schacht. Palette: `#140f24 #4a3d78 #9b7fd4 #ffe9a0` |

**Gating-Logik (Kanon):** Der Aschewächter hütet den Übergang Wald → Glut; die Frostkönigin hütet den Zugang zu den Hohlen Tiefen. Beide Bosse sind keine Hindernisse, sondern *Siegel* des Risses — wer sie bricht, lässt das Licht weiterfließen (und damit auch den Kern näher kommen).

## 3. NPCs

| ID | Name | Raum | Rolle & Tonfall |
|---|---|---|---|
| `leuchtmutter` | **Die Leuchtmutter** | Lumen-Schrein (`hub_02`) | Hüterin des Schreins. Sanft, rätselhaft. Erklärt Lumen und Meta-Fortschritt. Spricht nie über den Kern direkt. |
| `wurzelgeist` | **Wurzelgeist** | Wurzelkeller (`ag_05`) | Geist des Aschewalds, halb Licht, halb Wurzel. Verleiht den Glutdash. Warnend, poetisch. |
| `korin` | **Glutbarde Korrin** | Schmiedehalle (`ec_04`) | Letzter Schmied der Gluthöhlen. Knapp, praktisch. Verwahrt den Glutschlüssel — gibt ihn nur gegen eine Geschichte aus dem Wald weiter (Quest-Hook QH-2). |
| `der_stumme` | **Der Stumme** | Stille Kammer (`hd_03`) | Schatten ohne Stimme. Zeigt Visionen des Lumenkerns in Bildern, nie in Worten. Kein Dialogbaum — nur kurze Bild-Zeilen (GDD: keine Dialogbäume). |

## 4. Items & Fähigkeiten (Gating-Referenz)

Diese IDs sind die **kanonischen Gating-IDs** aus `map_graph.json` und werden von Systems (T-003) in den Item-/Stat-Schemata referenziert:

| ID | Name | Typ | Wird vergeben in | Öffnet |
|---|---|---|---|---|
| `ability_double_jump` | **Doppelhüpfen** | Fähigkeit | Hohler Eichenbaum (`ag_03`) | Kronenpfad → Lichtquelle (Aschewald) |
| `ability_dash` | **Glutdash** | Fähigkeit | Wurzelkeller (`ag_05`, vom Wurzelgeist) | Dornlabyrinth & Verlorene Lichtung (Aschewald) |
| `ability_wall_slide` | **Wandgleiten** | Fähigkeit | Lavafall (`ec_02`) | Klammbrücke (Gluthöhlen), Eisgrotte (Frosthallen) |
| `ability_light_step` | **Lichtschritt** | Fähigkeit | Lumenadern (`hd_02`) | Stille Kammer & Lichtbrücke (Hohle Tiefen) |
| `key_lumen_shard` | **Lumen-Splitter** | Schlüssel 1 | Lichtquelle (`ag_08`) | Frosttor im Lumenbrunnen → Frosthallen |
| `key_ember_key` | **Glutschlüssel** | Schlüssel 2 | Schmiedehalle (`ec_04`, von Korrin) | Kernschacht in den Hohlen Tiefen (nach Frostkönigin) |

Weitere Items (Waffen/Rüstung/Accessoires, ~30 Stück) definiert Systems in `balance/items.json`; ihre Namen müssen diese Bibel nicht referenzieren, aber neue *Gating*-Items immer.

## 5. Quest-Hooks

| ID | Hook | Trigger | Verknüpfung |
|---|---|---|---|
| **QH-1** | *Der erste Funke* | Leuchtmutter im Lumen-Schrein: „Trage dein Licht in den Wald, bis die Asche wieder atmet." | Führt zum Aschewald; Abschluss = Doppelhüpfen gefunden (`ag_03`). Tutorial-Hook. |
| **QH-2** | *Korrins Geschichte* | Korrin verlangt eine Geschichte aus dem Wald, bevor er den Glutschlüssel gibt. Der Wurzelgeist kennt sie („Die Nacht, als der Wald das Licht trank"). | Verbindet Aschewald ↔ Gluthöhlen narrativ; Abschluss = `key_ember_key` erhalten. |
| **QH-3** | *Visionen des Stummen* | In der Stillen Kammer zeigt Der Stumme drei Visionen: den Brunnen, die Frostkönigin, den Kern. Jede Vision markiert einen Ort auf der Karte (Meta-Marker). | Führt zu Frosthallen-Boss und Lumenkern; Abschluss = Zielraum `hd_05` erreicht. |
| **QH-4** | *Der leere Brunnen* (Sekret) | Im Tiefen Brunnen (`hub_05`) liegt ein erloschenes Licht, das erst nach dem Sieg über die Frostkönigin wieder aufleuchtet und den Weg in die Hohlen Tiefen zeigt. | Optionaler Lore-Pfad; verbindet Hub mit finaler Zone ohne Boss-Dialog. |

## 6. Benennungsregeln (für T-004/T-005)

1. Raumnamen aus `map_graph.json` sind kanonisch — keine Abweichungen in UI, Dialogen oder Assets.
2. Biome-IDs (`lumen_well`, `aschen_wald`, …) bleiben englische/snake_case-IDs; Anzeigennamen immer die deutschen aus dieser Bibel.
3. Fähigkeit-/Schlüssel-IDs sind fix (Abschnitt 4). Umbenennung nur per Ticket vom Designer.
4. Dialoge dürfen nie gegen das Map-Gating verstoßen: Ein NPC erwähnt ein Areal, das der Spieler noch nicht passieren kann, nur als *Ziel* („jenseits des Frosttors …"), nie als Ort, an dem man sich aufhalten kann.
