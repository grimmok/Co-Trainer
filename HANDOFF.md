# FM-Scout – Übergabe

Stand: 10.11.2026

## Ziel

Ein eigenes Programm, das einen **Football-Manager-27-Spielstand (`.fm`)** liest und daraus eine Analyse-Seite (`FM-Scout.html`) erzeugt. Vorbild ist die Seite `FM27 Transfer-Scout.html` des Nutzers (liegt in seinem Downloads-Ordner).

Die Seite soll:

- analysieren, wie gut der Kader zur eigenen Taktik passt, und Schwächen zeigen;
- passende Transfers vorschlagen, jeweils mit geschätzter Wechselchance;
- bewerten, wie der eigene Trainer zur Taktik passt, und eine Taktik-Empfehlung geben (Trainerpräferenz + Spielerattribute);
- eine Trainingswoche für die Taktik vorschlagen;
- Verein, Liga, Budget und Gehaltsbudget automatisch eintragen.

**Harte Vorgabe des Nutzers:** CA, PA und versteckte Attribute dürfen in der Oberfläche nie erscheinen. Das Potenzial wird nur als Text gezeigt, z. B. „Kann sich zu einem guten Zweitliga-Spieler entwickeln“.

**Neue Richtung (09.11.):** FM-Scout wird zu **einem eigenständigen Windows-Programm** (`FM-Scout.exe`, ohne Batch-Datei, ohne erzeugte HTML-Seite), das öffentlich auf GitHub geteilt wird. Der vollständige Entwurf steht in [docs/superpowers/specs/2026-11-09-fm-scout-app-design.md](docs/superpowers/specs/2026-11-09-fm-scout-app-design.md). **Vom Nutzer am 10.11. freigegeben.** Das Programm heißt künftig „Co-Trainer“. Nächster Schritt: Umsetzungsplan.

## Dateien

| Datei | Zweck |
|---|---|
| `extract.py` | Liest den Spielstand und schreibt `FM-Scout.html`. Aufruf: `python extract.py [Pfad.fm]`. Ohne Pfad wird der neueste `.fm` genommen. |
| `app.html` | Vorlage der Oberfläche (Vanilla JS). `extract.py` ersetzt darin `/*__DATA__*/null` durch die Daten als JSON. |
| `config.json` | Pro Verein (`clubs` → Kurzname oder Name): Trainerprofil (`coach`) und Taktik (`tactic`: Anweisungen, Feedback, Ersatz-Slots). `save` erzwingt einen bestimmten Spielstand, `lang_db` den Pfad zur Sprachdatenbank. |
| `FM-Scout starten.bat` | Installiert bei Bedarf `zstandard`, startet `extract.py` und öffnet die Seite. |
| `FM-Scout.html` | Erzeugte Ausgabe (ca. 4,4 MB). Wird bei jedem Lauf überschrieben. |
| `docs/superpowers/specs/2026-11-09-fm-scout-app-design.md` | Freigegebenes Design für das Programm „Co-Trainer“. |
| `docs/superpowers/plans/2026-11-10-co-trainer-1-grundgeruest.md` | Umsetzungsplan Teil 1 (Grundgerüst), noch nicht ausgeführt. |

Die Dateien `Ravenna_Kader.*` und `Ravenna_Training.*` im übergeordneten Ordner sind frühe Einzelexporte. **`Ravenna_Kader` enthält falsch zugeordnete Attribute**, siehe Abschnitt „Erkenntnisse“.

Nutzerdaten:

- Spielstände: `%USERPROFILE%\Documents\Sports Interactive\Football Manager 26\games\` (der Ordner heißt „26“, das Spiel ist FM27 27.0.0)
  - `Haribaert Kachinski – Paris FC.fm`: aktuelle Karriere
  - `Haribaert Kachinski – Ravenna.fm`: zuletzt gespeichert am 07.11. um 23:24; Scoutinggebiet „Italien“
  - `Haribaert Kachinski – Ravenna europa.fm`: Testspielstand, identisch bis auf Scoutinggebiet „Europa“
  - `Trainertest 2.fm` (Trainer „Trainer Test Zwei“, Albion FC) und `Trainertest 2 spieler.fm` (Figueroa per Ingame-Editor geändert): Editor-Tests vom 10.11. Der Nutzer hat jetzt den Ingame-Editor und kann Werte gezielt ändern.
  - `Trainertest .fm`: Testspielstand mit zwei menschlichen Managern („Trainer Test“ C-Lizenz, „Trainer Test Zwei“ Pro-Lizenz); wird nicht mehr gebraucht
- Spielinstallation: `G:\SteamLibrary\steamapps\common\Football Manager 27`
- Sprachdatenbank (Wettbewerbs- und Rollennamen): `shared\data\database\db\2700\2700_fm\lang_db.dat`

## Was bisher gemacht wurde

1. Das Containerformat entschlüsselt und Kader, Attribute, Verträge, Vereine, Finanzen, Ligen und Training ausgelesen.
2. `extract.py`, `app.html` und `config.json` gebaut. Die Oberfläche hat fünf Reiter:
   - **Kader-Analyse:** Spielfeld mit beste Elf und Schwachstellen
   - **Transfervorschläge:** Filter nach Position, Alter, Wechselchance, Budget und ablösefrei
   - **Trainer & Taktik:** Passung Trainer ↔ Taktik, Rangliste der Spielstile, Prüfung der Teamanweisungen
   - **Training:** Wochenplan mit echten FM27-Einheiten, Trainingsbewertungen, gespeicherte Wochenpläne
   - **Kaderliste**
3. Finanzen mit Screenshots des Nutzers abgeglichen. Alle geprüften Werte stimmen:
   - Ravenna: Transferbudget 604.815 €, Gehaltsbudget 98.362 €/Woche, Kontostand 1,38 Mio. €
   - Paris: Transferbudget 4,99 Mio. €, Gehaltsbudget 719.189 €/Woche, Kontostand 80,07 Mio. €
4. Verträge mit Screenshots abgeglichen (Soleri, Spini, Tenkorang, Maggio).
5. Trainerprofil und Taktik für Paris aus Screenshots in `config.json` übernommen. Der Nutzer hat das Profil „Offensiv/Entwickler“ gewählt.
6. **Taktik aus dem Spielstand:** Positionen und Rollen werden jetzt aus `tactics_man` gelesen (`read_tactics` in `extract.py`). Beim Ravenna-Spielstand werden alle 22 Rollen erkannt. Neu in der Oberfläche:
   - die Rolle gegen den Ball und die Position ohne Ball werden auf dem Spielfeld angezeigt;
   - Rolle `cfo` (Mittelstürmer gegen den Ball);
   - FM27-Rollennamen;
   - Schlüsselattribute des Halbraumstürmers laut Screenshot.
7. Eine kurze Vorstellung des Programms für einen FM-Discord-Mod-Kanal geschrieben (nur im Chat).
8. **Spielstandwahl (09.11.):** `find_save` lässt Sicherungen (`backup`, `autosave`) aus. `python extract.py --list` zeigt alle Spielstände mit Nummer; `python extract.py 2` nimmt Nummer 2.
9. **Rollentest-Hilfe (09.11.):** `FMS_ROLES=1` gibt für jede Taktik alle 22 Fingerabdrücke aus, unbekannte als `UNBEKANNT`. Die Schlüssel lassen sich direkt in `ROLE_FP` kopieren.
10. **Spielstil aus dem Taktikkopf (09.11.):** Stilname und 4-Zeichen-Code werden gelesen (`STYLE_CODES` in `extract.py`: `TREV` → `vertical_tikitaka`, `EGEG` → `gegenpress`) und haben Vorrang vor `config.json`. Die Oberfläche übernimmt den Stil, sobald er sich im Spielstand ändert (`styleSeen` im `localStorage`).
    - Ravenna: aktive Taktik „Taktik“ = **Gegenpressing**, „4-1-1-3-1 DM Breit – Vertikales Tiki-Taka“ = Vertikales Tiki-Taka. Gegenpressing für „Taktik“ hat der Nutzer am 10.11. bestätigt; damit gilt der Code `EGEG` als geprüft. `TREV` ist noch unbestätigt.
11. **fmsave getestet (09.11.):** siehe Abschnitt „Abgleich mit fmsave“.
12. **Brainstorming zum Umbau als Programm (09.11.):** Ablauf, Bereiche, Transfer-Informationsstufen, neuer Taktik-Reiter, Stil (dunkel/hell) mit dem Nutzer festgelegt → Design-Dokument (siehe oben). Entwürfe als HTML in `.superpowers/brainstorm/` (lokal, nicht im Repo): `ablauf-v2.html`, `transfer-werte.html`, `stil-v2.html`.
13. **Trainerbewertungen und Neigungen gefunden (10.11.):** per Editor-Test, siehe „Trainer des menschlichen Managers“. Die Aussage vom 09.11. („werden berechnet“) ist widerlegt.
14. **Scoutinggebiet dekodiert (10.11.):** siehe „Scoutinggebiet“.

## Erkenntnisse zum Spielstand-Format

### Container

- Eine `.fm`-Datei besteht aus einem 26 Byte langen Header und vielen zstd-Frames (Magic `28 b5 2f fd`).
- Der **letzte Frame ist das Inhaltsverzeichnis**. Jeder Eintrag: `len u32, name, ".dat"(len 4), u64 offset, u64 comp, u64 raw`. Der Frame liegt bei `offset + 26`.
- Wichtige Sektionen:
  - `game_db`: die Hauptdatenbank, ca. 200–330 MB entpackt
  - `save_game_summary`: Managername, Vereinsname, Datum
  - `training_man`, `tactics_man`
  - `comp_<id>`: Wettbewerbe

### Geld

FM speichert Geld in **GBP**. Für die Anzeige gilt: **EUR = GBP × 1,1641** (exakt verifiziert).

### Spieler-Attributblock

- Aufbau: 15 Positionsbytes (Werte 1–20), danach 54 Attribute (Werte 1–100; Anzeigewert = Wert / 5, gerundet).
- Positionsreihenfolge: GK SW DL DC DR DM ML MC MR AML AMC AMR ST WBL WBR.
- Attributreihenfolge: siehe `ATTR_KEYS` in `extract.py`. Versteckt sind: Cons, Dirt, ImpM, InjPr, Vers.
- Präfix vor dem Block:
  - u32 bei −43 = **Personen-ID − 1**
  - CA (u16) bei −24
  - PA (u16) bei −22
- **Wichtig:** Der Block liegt **vor** dem Vertrags- und Personenkopf des Spielers. Die Zuordnung läuft ausschließlich über `Block-ID = pid − 1`. Die erste Version hat Blöcke der nachfolgenden Person zugeordnet; deshalb ist `Ravenna_Kader.*` falsch.

### Vertrag

- Muster: `..[\x6c-\x7f]\x07\x00 pid(4) club(4) 00×4 Wochengehalt_GBP(4)`.
- Das Enddatum steht nach dem letzten `ff×8` vor dem Vertrag.
- Plausibilitätsprüfung: Der Block `bpid[pid-1]` liegt 300–4000 Byte vor dem Vertrag.

### Personenkopf

- Muster: `Vorname-ID(4) 00 Nachname-ID(4) 00 ff×4 00 len(4) [voller Name] Geburtsdatum`.
- Datumsformat: u16 Tag-im-Jahr & 0x1ff, gefolgt von u16 Jahr.
- Persönlichkeit: 8 Byte bei `dob_pos + 22`. Reihenfolge: Anpassungsfähigkeit, Ehrgeiz, Loyalität, Druck, Professionalität, Fairplay, Temperament, Streitlust (so heißen die Felder im Ingame-Editor; Fairplay = Sportsgeist, Streitlust = Kontroversität). **Alle acht Positionen am 10.11. bestätigt:** Der Nutzer hat Tobías Figueroa in `Trainertest 2 spieler.fm` per Editor auf 2, 4, 6, 17, 10, 11, 15, 13 gesetzt; gelesen wurden genau diese Rohbytes. Im selben Abgleich stimmen auch die fünf versteckten Attribute (Vielseitigkeit 11, Konstanz 9, Unsportlichkeit 8, Wichtige Spiele 10, Verletzungsanfälligkeit 12).
- Namenstabellen: Ketten aus `id, len, utf8`. Die zwei größten Tabellen sind Vor- und Nachnamen.

### Vereine

- Name und Kurzname stehen als Paar.
- Vereins-ID: Marker `ff <id> 00×6 04 1d`, etwa 2–3 KB nach dem Namen.
- Budgetblock innerhalb von 120 Byte nach dem Kurznamen: `01 Start Aktuell Garantiert 00 x y Gehalt/Woche` (alle i32 in GBP).
- Kontostand: `ff 00 <i32> xxxx (01 00 6c 07)×3 00×5`, innerhalb von 4000 Byte nach dem Namen.

### Wettbewerbe

- In `comp_<id>` stehen Teamzeilen `id 00 ff×6` mit festem Abstand (genommen wird die längste Folge mit gleichem Abstand).
- Die Namen kommen aus `lang_db.dat`.

### Training (`training_man`)

- Wochenpläne: `0b Datum(2) Jahr(2) 01 7×(04 u16×3 00) len Name`.
- Bewertungsliste: `count`, dann pro Spieler `pid 01 02 00 00 00 float float`.

### Taktik (`tactics_man`)

Kopf einer eigenen Taktik: `22 44 00 1b 00 00 00 <flag> <len u32> Name`.

- Flag `02`: aktive Taktik
- Flag `00`: weitere eigene Taktik
- Flag `01`: Formationsvorlage des Spiels

Danach folgen **22 Slot-Einträge**, abwechselnd mit Ball und gegen den Ball:

```
44 00 02 | Position u16 | Seite u16 | 00 01 01 | n u32 | Gruppe u64 | n × (02 02 02, 8×00, ff, 4×00, u64-Bits)
```

- Positions-Bits: GK 1, SW 2, DR 4, DL 8, DC 10, WBR 20, WBL 40, DM 80, MR 100, ML 200, MC 400, AMR 800, AML 1000, AMC 2000, ST 4000.
- Seite: 0x20 = rechts, 0x10 = links.
- Die Rolle wird über einen Fingerabdruck erkannt: (Phase, Gruppen-Bit, Bitlisten der Unterblöcke) → Tabelle `ROLE_FP` in `extract.py`.
  - Gleiche Rollen an verschiedenen Positionen ergeben identische Daten.
  - Bestätigt per Screenshot: ST mit Ball = Halbraumstürmer, gegen den Ball = Mittelstürmer.
- Eine Role-ID wie in `lang_db` (1800–1884) steht nicht direkt in den Daten.

### Sonstiges

- **Rollennamen FM27:** `lang_db`, Frame 74, Einträge `id(4) 01 02 08 len Name`, IDs 1800–1884.
- **Exportierte Taktiken (`.fmf`)** sind verschlüsselt und nicht lesbar.
- Der Datensatz `I RB` in `tactics_man` (AI-artig, mit `05 u16`-Positionscodes) enthält die Aufstellung eines Vereins (Spieler-IDs), aber keine Rollen.

### Abgleich mit fmsave (09.11.)

Bibliothek [rhiever/fmsave](https://github.com/rhiever/fmsave) 0.11.0 (MIT), lokal geklont nach `%USERPROFILE%\Projekte\fmsave`, venv `.venv` mit Python 3.12 (über `python -m uv`). Ravenna-Spielstand ist Build 27.0.0+2493426; fmsave kennt offiziell nur +2486695, liest aber trotzdem fast alles (Ausnahmen: `officials`, `squad_planner`, `sponsorships`). Vergleichsskripte lagen im Scratchpad.

- **Gleich:** Bei allen 51.208 Spielern, die wir finden, stimmen CA/PA, alle Attribute und Positionen exakt überein. Kontostand stimmt (1.185.695 £ = 1.380.268 €), ebenso die vier per Screenshot geprüften Verträge, Taktiknamen und Stil „Gegenpressing“.
- **Persönlichkeit falsch angenommen:** Richtige Bytefolge (bei 51.208 von 51.208 Spielern): Anpassung, Ehrgeiz, **Loyalität, Druck, Professionalität, Sportsgeist, Temperament, Kontroversität**. `willingness()` las Loyalität deshalb aus dem falschen Byte (`p[3]` = Druck statt `p[2]`). **Korrigiert am 10.11.** Abgleich: Nicolas Viola hat die Rohbytes `11 12 16 12 18 11 12 3` und im Spiel die Persönlichkeit „Professionell“; das passt nur, wenn Byte 5 (Wert 18) die Professionalität ist (alte Annahme: 11). Die übrigen Positionen sind inzwischen per Editor-Test bestätigt, siehe „Personenkopf“. `FMS_DEBUG` gibt die Rohbytes jetzt mit aus.
- **fmsave findet mehr:** 86.402 statt 51.210 Spieler. Im Ravenna-Kader fehlen bei uns u. a. Zagré, Ilari und Vinícius.
- **Abweichungen bei uns:** Vertragsende bei rund 12.000 Spielern anders (z. B. De Silvestri: wir 29.07.2026, fmsave 30.06.2027), Gehalt bei rund 3.000.
- **Neu verfügbar:** Kaderstatus (`squad_status`, z. B. `regular_starter`, `emergency_backup`), Leihen, Scoutingbudget, Staff-Attribute (für diesen Build bestätigt). Die Attribute des menschlichen Managers liefert fmsave nicht (`None`).
- fmsave gibt fast alle Felder als „unconfirmed“ an; gegen das Spiel bestätigt sind für FM27 nur Staff-Felder.
- **fmsave scheitert** an einem Spielstand mit zwei menschlichen Managern (`Trainertest .fm`: „FM27 summary does not fit its structured clock layout“). Deshalb muss der eigene Leser als Rückfall bleiben.

### Trainer des menschlichen Managers (neu am 10.11., Editor-Test)

Grundlage: `Trainertest 2.fm` (unverändert) gegen `Trainertest 2 traainer.fm` (der Nutzer hat „Trainer Test Zwei“ im Ingame-Editor geändert, Screenshots vorher/nachher). **Die Annahme vom 09.11., die Werte würden nicht gespeichert, war falsch.**

- **Personenkopf** in `game_db` wie bei anderen Personen (`… ff×4 00 len "Voller Name" Geburtsdatum`), Vorname nicht aus der Namenstabelle. Persönlichkeit bei `dob + 22`: Byte 1 blieb im Test unverändert (17), Bytes 2–8 = Ehrgeiz, Loyalität, Druck, Professionalität, Fairplay, Temperament, Streitlust (gesetzt 3, 5, 7, 9, 11, 13, 15; genau so gelesen).
- **Staff-Block vor dem Personenkopf** (Abstand zum Namen 450–558 Byte, gleicher Aufbau wie `STAFF` in fmsave): Marke `0c` (12), dann **26 Neigungen** (1–20, Slot 13 ist 0–100), dann **26 Attribute** (1–100, Anzeige = Wert / 5), dann `ff×4`.
- **Neigungen**, Slot → Name im Editor; alle 15 im Test gesetzten Werte wurden exakt gelesen:

  | Slot | Neigung | Slot | Neigung |
  |---|---|---|---|
  | 0 | Offensive | 15 | Psychologische Spielchen |
  | 1 | Geschäftliches | 19 | Defensivlinie (in fmsave unbenannt) |
  | 3 | Vertikaler Stil | 21 | Flexibilität |
  | 6 | Eingreifen | 22 | Trainingsintensität |
  | 9 | Geduld | 23 | Rotation |
  | 10 | Pressingauslösung | 24 | Tempo |
  | 11 | Finanzmittel | 25 | Breite |
  | 14 | Spieler kaufen | | |

  Unbekannt: Slots 2, 5, 7, 8, 16, 17, 18, 20 (überall 10) sowie 4, 12 und 13 (je Trainer verschieden; Slot 13 fiel beim Bearbeiten von 70 auf 50). „Lässt unsportliche Aktionen durchgehen“ zeigt der Editor ohne Wert.
- **Bei den menschlichen Managern des Nutzers stehen alle 15 Neigungen auf 10** (Ravenna, Paris, beide Testtrainer). Die im Spiel angezeigten „Trainertendenzen“ kommen also nicht aus diesen Werten, solange man sie nicht per Editor ändert. Woher das Spiel sie nimmt, ist offen.
- **Trainerbewertungen**, zugeordnet per zweitem Editor-Test (`Trainertest 2 trainer attribute.fm`, Screenshots vorher/nachher; alle 14 gesetzten Werte exakt gelesen). Anzeige 1–20:

  | Bewertung | Fundort | Bewertung | Fundort |
  |---|---|---|---|
  | Offensive | Attribut 8 (/5) | Nachwuchsarbeit | Neigungs-Slot 12 |
  | Defensive | Attribut 9 (/5) | Anpassungsfähigkeit | Persönlichkeit Byte 1 |
  | Athletik (Fitness) | Attribut 10 (/5) | Autorität | Neigungs-Slot 4 |
  | Torwarttraining | Attribut 1 (/5) | Zielstrebigkeit | Neigungs-Slot 13 (/5) |
  | Ballbesitz | Attribut 11 (/5) | Motivationsfähigkeit | Attribut 5 (/5) |
  | Standardsituationen | Attribut 25 (/5) | Führungsqualitäten | Attribut 4 (/5) |
  | Taktik | Attribut 13 (/5) | Spielerfähigkeiten beurteilen | Attribut 2 (/5) |
  | Techniken | Attribut 12 (/5) | Spielerpotenzial beurteilen | Attribut 3 (/5) |
  | Vielseitigkeit | Attribut 17 (/5) | Mitarbeiterbeurteilung | Attribut 24 (/5) |
  | Datenanalyse | Attribut 18 (/5) | | |

  Unklar: Attribute 7 und 23 (im Test 50 → 1 bzw. 50 → 5; vermutlich Verhandlungsgeschick und Taktische Kenntnisse, die der Editor mit 0 zeigte). Streitlust (Persönlichkeit Byte 8) sprang beim Attribut-Test ohne Eingabe von 0 auf 11.
- **Gegenprobe Ravenna:** Die gelesenen Werte passen in allen 14 Feldern zu den Textstufen aus den Profil-Screenshots in `config.json` (z. B. Torwart 5 = „Sehr schlecht“, Offensive 11 = „Durchschnitt“, Autorität 12 = „Gut“). Beobachtete Stufen: bis 6 sehr schlecht, 7–9 schlecht, 10–11 Durchschnitt, 12–15 gut, ab 16 sehr gut (Grenzen nur aus diesen Beispielen), 18–19 = „Herausragend“, 20 = „Elite“ (beides vom Nutzer am 10.11. bestätigt).
- **Gegenprobe Paris:** Editor-Screenshot des Nutzers aus dem neu angelegten `Haribaert Kachinski – Paris FC test.fm` (Editor muss beim Anlegen aktiviert sein; Profil unbearbeitet übernommen): alle 14 gelesenen Werte stimmen. Das Profil in `config.json` (Offensive „Sehr gut“ usw.) war demnach nicht der Stand des Spielstands.
- **Unerklärt:** In `Paris FC Frankreich`/`Liga` und nach den Editor-Tests steht Slot 13 (Zielstrebigkeit) auf 50 statt 70 und Streitlust auf 11 statt 0, ohne dass der Nutzer diese Felder geändert hat. In der China-Karriere fiel Slot 13 von 70 auf 28. Zielstrebigkeit kann sich also zwischen Spielständen ändern.
- **In `extract.py`:** `read_coach` liest Bewertungen und Neigungen; `coach_band` macht daraus die Textstufen. Sie ersetzen `coach.coaching` und `coach.mental` aus `config.json` (`coach.source = 'Spielstand'`). Zahlen und Neigungen gehen nur ins Protokoll. Stil, Tendenzen-Texte und Lizenz kommen weiter aus `config.json`.
- **Ändern sich die Neigungen im Lauf der Karriere?** (Vermutung des Nutzers.) In der China-Karriere stehen die 15 benannten Neigungen am Start und sieben Spielmonate später (01/2027) unverändert auf 10, obwohl sich die Bewertungen in derselben Zeit entwickelt haben. Für die Spielstände von 2028 greift das Suchmuster nicht; dort ungeprüft.
- „Bevorzugtes System“ und „Taktischer Stil“ im Trainerprofil leitet das Spiel laut Nutzer aus der eingestellten Taktik ab.

### Scoutinggebiet (gelöst am 10.11.)

- Einstellung im Spiel, sieben Stufen. Die Spielerdatenbank im Spiel zeigt dann automatisch Spieler dieses Gebiets.
- **Fundort:** Abschnitt `humans`, ein Byte im Muster `33 00 <Stufe> <u32> 20 00 01 00 <Datum>`. Gelesen von `read_scout_area` in `extract.py`; steht als `meta.scout_area` (Zahl) und `meta.scout_area_name` in den Daten, die Oberfläche nutzt es noch nicht.
- **Werte**, abgeglichen mit benannten Spielständen des Nutzers (Ravenna alle sieben, Paris 2 und 4):

  | Wert | Stufe | Beispiel Ravenna |
  |---|---|---|
  | 1 | Kein Scouting | |
  | 2 | Eigene Liga | |
  | 3 | Angrenzende Ligen | |
  | 4 | Eigenes Land | Italien |
  | 5 | Region | Südeuropa |
  | 6 | Kontinent | Europa |
  | 7 | Weltweit | |

- Das `u32` nach der Stufe ist bei Ravenna 1, bei Paris 7; Bedeutung unbekannt.
- Der alte Paris-Spielstand (`… Paris FC.fm`, 07.11.) liefert 6 = Kontinent; der Nutzer hat „Europa“ bestätigt.
- Bei „Kein Scouting“ zeigt das Spiel laut Nutzer nur Spieler, die den Mitarbeitern bekannt sind. Wo diese Bekanntheit im Spielstand steht, ist nicht untersucht.
- Das Muster greift nicht bei `Trainertest .fm` (zwei Manager) und nicht bei den älteren Karrieren (Ndoye, Curaçao, China; ältere Spielversion). Dort meldet `extract.py` „nicht gefunden“.
- **Verworfen:** Der 4-Zeichen-Code in `scout_man` (`AcSP`/`blcP`) und der Filterblock daneben sind nicht das Scoutinggebiet. Sie gehören zur Spielersuche (Sortierspalte und ein Filter) und sind in allen Gebiets-Spielständen vom 10.11. gleich. Die Marken stehen rückwärts im Spielstand (`blcP` = `Pclb`, `manP` = `Pnam`, `frlp` = `plrf`).
- **Angrenzende Ligen (vom Nutzer am 10.11. genannt):** bei Ravenna (Serie C/B) sind das Serie B, Serie C und Serie D, also die eigene Spielklasse plus je eine Stufe darüber und darunter im selben Land. Nicht geklärt: ob bei „Serie C“ alle Staffeln gemeint sind (Annahme Claude: ja) und wie die Ligastufe aus dem Spielstand gelesen wird (bisher nicht dekodiert). Die Zuordnung Land → Region/Kontinent ist gelöst, siehe unten.
- **Ländernamen (10.11.):** `lang_db.dat`, Frame 64 (deutsch): Einträge `Datenbank-Nr.(4) len Name 00 len Kurzname 00 03 00 00 00 Kürzel len Adjektiv 00`, z. B. 776 Italien ITA, 769 Frankreich FRA, 771 Deutschland GER, 1657 Uruguay URU. 195 Länder so gelesen. Die Nummern gruppieren sich grob nach Kontinent (Afrika 5–55, Asien 106–145, Nord-/Mittelamerika 359–389, Europa 752–802, Ozeanien 1435–1444, Südamerika 1649–1662), mit Ausreißern (z. B. Montenegro, Gibraltar, Monaco weit außerhalb). Regionennamen („Südeuropa“) stehen weder in `lang_db.dat` noch in `lang_db_general.dat`. fmsave liefert je Spieler `nation_id` und die Tabelle `nation_id → database_id`, aber keine Kontinente oder Regionen.
- **Kontinent und Region je Land (10.11., aus `game_db`):** Die Nationentabelle (251 Zeilen, Aufbau wie `NATION_TABLE` in fmsave, `_layouts/fm26_26_3_2.py`) lässt sich mit den dortigen 14 Schritten ablaufen. Im 9. Schritt (24 feste Bytes) stehen:
  - Byte 1 = **Kontinent**: 0 Afrika, 1 Asien (inkl. Australien), 2 Europa, 3 Nord-/Mittelamerika, 4 Ozeanien, 5 Südamerika, 255 keiner (aufgelöste Staaten u. Ä.). Stimmt bei allen geprüften Ländern.
  - Bytes 5–8 (u32) = **Regions-Nummer**, sehr wahrscheinlich das, was das Spiel als Region nimmt. Europa: 4 = Österreich, Belgien, Tschechien, Deutschland, Liechtenstein, Luxemburg, Polen …; 5 = Bulgarien, Ungarn, Rumänien, Serbien …; **11 = Albanien, Bosnien und Herzegowina, Kroatien, Italien, Malta, San Marino, Slowenien, Montenegro**; 12 = England, Nordirland, Irland, Schottland, Wales; 24 = Dänemark, Finnland, Island, Norwegen, Schweden; 25 = Andorra, Frankreich, Portugal, Spanien, Gibraltar; 26 = Armenien, Aserbaidschan, Zypern, Georgien, Griechenland, Nordmazedonien; 27 = Belarus, Estland, Lettland, Litauen, Russland. Südamerika: 21 = Argentinien, Brasilien, Chile, Paraguay, Uruguay; 22 = Bolivien, Kolumbien, Ecuador, Peru, Venezuela.
  - **Vom Nutzer am 10.11. bestätigt:** Das Scoutinggebiet „Südeuropa“ (Ravenna) ist genau Region 11. Scoutingstufe 5 („Region“) = alle Länder mit derselben Regions-Nummer wie das Land des eigenen Vereins; Stufe 6 („Kontinent“) = derselbe Kontinent-Code. Für andere Regionen als 11 ist das eine Übertragung, nicht einzeln geprüft.
  - 56 der 251 Länder haben in der Namensliste aus `lang_db.dat` noch keinen Namen (Regex zu eng); noch nicht in `extract.py`.
- Die Gebiets-Spielstände sind Build 27.0.1+2494687 (vorher 27.0.0+2493426).

## Getroffene Entscheidungen

- Der Spielstand wird **nur gelesen, nie verändert**.
- Ohne Pfad wird der neueste `.fm` verwendet, außer `config.json` gibt mit `save` einen anderen vor.
- **CA, PA und versteckte Attribute** werden nur intern benutzt (Bewertung, Wechselchance, Marktwert). Die JSON-Ausgabe enthält sie nicht. Spielerqualität erscheint nur als Text (`pot`, `lvl`) bzw. als relative Einordnung (`rel`).
- **Wechselchance** ist eine eigene Schätzung (0–100). Sie berücksichtigt:
  - Vereinsstärke: Mittelwert der Top-16-CA
  - Ehrgeiz und Loyalität aus der Persönlichkeit
  - Restlaufzeit des Vertrags, Alter, Vereinslosigkeit
  - Unbekannte Vereine gelten als neutral.
- **Marktwert** ist eine eigene Schätzung: `2200·e^((CA−50)/12,5)` mit Faktoren für Alter, Vertrag und Liga. Es ist kein Spielwert.
- **Eigener Verein:** der Verein mit den meisten Spielern in den Trainingsbewertungen; sonst der Name aus `save_game_summary`.
- **Taktik:**
  - Positionen und Rollen kommen aus dem Spielstand, sobald dort eine eigene Taktik steht.
  - Teamanweisungen und Feedback kommen weiter aus `config.json`.
  - Ist eine Rolle unbekannt, wird eine Standardrolle eingesetzt und das Kürzel als „?“ angezeigt.
- **Trainerprofil** und **Teamanweisungen** stehen in `config.json` (aus Screenshots übernommen), weil sie noch nicht aus dem Spielstand gelesen werden.
- Die Oberfläche speichert eigene Rollenwahl, Filter und Wochenpläne im `localStorage`, Schlüssel `fmscout:<Verein>|<Manager>`.
- Die Oberfläche ist auf Deutsch, mit deutschen FM27-Begriffen.

## Offene Probleme

- **Paris-Spielstand ohne eigene Taktik:** In `tactics_man` stehen nur Formationsvorlagen. Für Paris greift deshalb `config.json`. Warum das so ist, ist ungeklärt.
- **Nur 19 Rollen bekannt:** Bekannt sind nur die Rollen der aktuellen Taktik. Alle anderen erscheinen als „?“ mit Standardrolle. Der Rollentest läuft, siehe „Nächste Schritte“.
- **Zuordnung ZOM-Rolle unsicher:** Für die Rolle mit Ball am ZOM (Kürzel „F“) ist „Freie Rolle“ angenommen. Der genaue FM27-Name ist unbestätigt (in `lang_db` fehlen u. a. die IDs 1810, 1826, 1828–1833, 1848, 1870).
- **Unbekannter Einfluss der Spieleranweisungen:** Ob individuelle Spieleranweisungen die Unterblöcke verändern und damit den Fingerabdruck brechen, ist ungeprüft.
- **Fehlende Spieler:** Bei Paris fehlen einzelne Spieler, z. B. Otávio und Ikoné (Ikoné steht aber in der Aufstellung). Leihspieler werden nicht immer erkannt.
- **Kader nicht gefiltert:** Der Kader enthält Reserve und Jugend (Paris: 78 Spieler). Es gibt keinen Filter auf die erste Mannschaft.
- **Nicht ausgelesen werden:** Scoutingbudget, Staffattribute anderer Trainer, Teamanweisungen und die Ligastufe (fmsave liest Scoutingbudget und Staffattribute). Das Scoutinggebiet wird gelesen, aber die Transfervorschläge filtern noch nicht danach.
- **Trainertendenzen:** Die 15 Neigungen des eigenen Managers werden gelesen, stehen aber überall auf 10. Woher das Spiel die angezeigten Tendenzen nimmt, ist offen; im Programm werden sie pro Karriere ausgewählt.
- **Zielstrebigkeit und Streitlust des Managers ändern sich zwischen Spielständen ohne Zutun** (z. B. Paris: 14 → 10); Ursache unbekannt.
- **`FM-Scout.html` zeigt den zuletzt gelaufenen Spielstand**, auch wenn das ein Testspielstand war. Für eine Karriere `python extract.py --list` und die Nummer angeben.
- **Torwartwahl:** Durch die Gewichtung „Ballspielender Torwart“ wählt das Programm bei Paris Nkambadio statt Trapp.
- **Spielstandwahl:** Backups sind ausgeschlossen, aber `find_save` nimmt weiterhin den neuesten Spielstand *jeder* Karriere (keine Einschränkung auf einen Manager).
- **Ungeprüfte Werte:** Das garantierte Mindestbudget für die nächste Saison ist nicht mit dem Spiel abgeglichen. Die Wechselchance ist eine Annahme.

## Nächste Schritte

### A. Umbau zum Programm „Co-Trainer“ (Vorrang)

Stand 10.11. abends: Design freigegeben, Plan für Teil 1 geschrieben, **noch nichts gebaut**.

1. **Nutzer sieht den Plan für Teil 1 durch** (`docs/superpowers/plans/2026-11-10-co-trainer-1-grundgeruest.md`) und wählt die Ausführungsart: mit Unteragenten (Skill `superpowers:subagent-driven-development`) oder direkt in der Sitzung (`superpowers:executing-plans`). Empfehlung von Claude: direkt, weil die acht Schritte eng aufeinander aufbauen.
2. **Teil 1 bauen** (acht Tasks): Paket `cotrainer` mit `analyse()`, Schutzfunktion gegen versteckte Werte, Spielstandliste, Einstellungen in `%APPDATA%\Co-Trainer`, Brücke zur Oberfläche, Oberfläche mit geführtem Start, Fenster (pywebview), `Co-Trainer.exe` (PyInstaller). Braucht Python 3.12 über `python -m uv venv --python 3.12 .venv` (installiert ist 3.10).
3. **Danach je einen Plan schreiben und bauen:**
   - Teil 2: fmsave als Datenquelle, Kader nur erste Mannschaft, Nationalität, Scoutinggebiet als Filter, drei Informationsstufen der Transfervorschläge.
   - Teil 3: neuer Taktik-Reiter (Schwachstellen, Verursacher, Abhilfe), Trainerbewertungen als Textstufen, Auswahl der Trainertendenzen pro Karriere, Trainingsfokus.
   - Teil 4: README, Lizenzhinweise, GitHub-Release.
4. **Für Teil 2 noch zu dekodieren:**
   - Ligastufe je Wettbewerb (für „Angrenzende Ligen“ = eigene Spielklasse ± 1 im selben Land).
   - Die 56 Länder ohne deutschen Namen (Regex für `lang_db.dat`, Frame 64, ist zu eng).
   - Nationentabelle (Kontinent, Region) in den Leser übernehmen; bisher nur im Scratchpad erkundet.
   - Optional: welche Spieler den Mitarbeitern bekannt sind (für „Kein Scouting“; bis dahin gilt die Regel „vertragslose Spieler der Vereinsnation“).
5. **Vom Nutzer zu bestätigen, wenn es sich ergibt:**
   - ob bei „Angrenzende Ligen“ alle Serie-C-Staffeln gemeint sind (Annahme Claude: ja);
   - Stil-Code `TREV` = Vertikales Tiki-Taka;
   - Stufengrenzen der Trainerbewertungen unterhalb von 18 (bisher nur aus Profil-Screenshots abgeleitet);
   - ob der Name „Co-Trainer“ frei ist (nicht geprüft).

Entscheidungen des Nutzers vom 10.11. (alle im Design-Dokument eingearbeitet): Design samt „Entscheidungen von Claude“ freigegeben; Programmname „Co-Trainer“ (`Co-Trainer.exe`), weil „FM Scout“ eine große FM-Website ist; Trainerbewertungen bleiben im Taktik-Reiter; Trainertendenzen per Auswahl pro Karriere; bei „Kein Scouting“ trotzdem Vorschläge (bevorzugt vertragslose Spieler der Vereinsnation, auch schwächere). Ordner, Repo und bestehende Dateien werden erst beim Umbau umbenannt.

Der Nutzer hat jetzt den **Ingame-Editor** (muss beim Anlegen eines Spielstands aktiviert sein; Testkarriere `Haribaert Kachinski – Paris FC test.fm`, Testspielstände `Trainertest 2 …`). Damit lassen sich Werte gezielt setzen und im Spielstand wiederfinden. Das Vorgehen hat sich bewährt: Ausgangsstand speichern, auffällige, verschiedene Werte setzen (3, 5, 7 …), Screenshot, unter neuem Namen speichern, ohne einen Tag weiterzuspielen.

### B. Dekodierung und Datenqualität (laufend)

1. **Rollentest abschließen.** Ablauf:
   - Der Nutzer benennt eine Kopie seiner Taktik in „Test 1“ (dann „Test 2“ usw.) um.
   - Er stellt an allen Positionen neue Rollen ein, mit Ball und gegen den Ball. Doppelte Positionen bekommen zwei verschiedene Rollen.
   - Spieleranweisungen bleiben unverändert.
   - Er speichert und schickt die ausgefüllte Liste (TW, RV, IV rechts, IV links, LV, DM, ZM, ZOM, RA, LA, ST jeweils „mit Ball / gegen den Ball“).
   - Mit dem Ingame-Editor geht das jetzt schneller (Testkarriere statt echter Karriere).
   - Danach `FMS_ROLES=1` setzen und `extract.py` laufen lassen; die Zeilen der Taktik „Test N“ mit der Liste abgleichen und die neuen Fingerabdrücke in `ROLE_FP` eintragen.
   - Fehlende Rollen in `ROLES` in `app.html` ergänzen, mit Schlüsselattributen laut FM27.
   - Geplant sind 4–5 Durchgänge, am Ende einer mit anderer Formation (z. B. 3-4-3) für Flügelverteidiger, Libero sowie RM/LM mit Ball.
2. Prüfen, ob Spieleranweisungen den Fingerabdruck verändern. Falls ja: nur die rollenbestimmenden Unterblöcke vergleichen.
3. Teamanweisungen aus dem Kopf der Taktik dekodieren (Stil-Code ist erledigt). Aufbau nach dem Namen: 12×`00`, 16 Byte Einstellungen, `00 00 ff`, `len u32`, Stilname, Code4. Bisher gesehen:
   - „Taktik“ (Gegenpressing): `04 01 04 07 02 03 80 00 00 00 0a 40 50 22 62 90`
   - „4-1-1-3-1 … Tiki-Taka“: `04 03 04 07 02 03 88 10 8a 10 0a 10 61 22 64 80`
   - Wirkt bitgepackt. Zum Dekodieren: Kopie einer Taktik, jeweils **eine** Anweisung ändern, speichern, vergleichen.
4. Kaderfilter für die erste Mannschaft über `squad_status` aus fmsave; fehlende Spieler (Otávio, Zagré, Ilari, Vinícius) und Leihspieler sind mit fmsave gelöst.
5. ~~Spielstandwahl~~, ~~Scoutinggebiet~~, ~~Persönlichkeitsreihenfolge~~, ~~Trainerbewertungen~~ erledigt (10.11.).
6. Verhandlungsgeschick und Taktische Kenntnisse des Managers zuordnen (Attribute 7 und 23 im Staff-Block, per Editor-Test mit zwei verschiedenen Werten).
