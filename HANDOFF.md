# FM-Scout – Übergabe

Stand: 09.11.2026

## Ziel

Ein eigenes Programm, das einen **Football-Manager-27-Spielstand (`.fm`)** liest und daraus eine Analyse-Seite (`FM-Scout.html`) erzeugt. Vorbild ist die Seite `FM27 Transfer-Scout.html` des Nutzers (liegt in seinem Downloads-Ordner).

Die Seite soll:

- analysieren, wie gut der Kader zur eigenen Taktik passt, und Schwächen zeigen;
- passende Transfers vorschlagen, jeweils mit geschätzter Wechselchance;
- bewerten, wie der eigene Trainer zur Taktik passt, und eine Taktik-Empfehlung geben (Trainerpräferenz + Spielerattribute);
- eine Trainingswoche für die Taktik vorschlagen;
- Verein, Liga, Budget und Gehaltsbudget automatisch eintragen.

**Harte Vorgabe des Nutzers:** CA, PA und versteckte Attribute dürfen in der Oberfläche nie erscheinen. Das Potenzial wird nur als Text gezeigt, z. B. „Kann sich zu einem guten Zweitliga-Spieler entwickeln“.

**Neue Richtung (09.11.):** FM-Scout wird zu **einem eigenständigen Windows-Programm** (`FM-Scout.exe`, ohne Batch-Datei, ohne erzeugte HTML-Seite), das öffentlich auf GitHub geteilt wird. Der vollständige Entwurf steht in [docs/superpowers/specs/2026-11-09-fm-scout-app-design.md](docs/superpowers/specs/2026-11-09-fm-scout-app-design.md). **Er ist vom Nutzer noch nicht freigegeben.** Vor der Freigabe wird nichts gebaut.

## Dateien

| Datei | Zweck |
|---|---|
| `extract.py` | Liest den Spielstand und schreibt `FM-Scout.html`. Aufruf: `python extract.py [Pfad.fm]`. Ohne Pfad wird der neueste `.fm` genommen. |
| `app.html` | Vorlage der Oberfläche (Vanilla JS). `extract.py` ersetzt darin `/*__DATA__*/null` durch die Daten als JSON. |
| `config.json` | Pro Verein (`clubs` → Kurzname oder Name): Trainerprofil (`coach`) und Taktik (`tactic`: Anweisungen, Feedback, Ersatz-Slots). `save` erzwingt einen bestimmten Spielstand, `lang_db` den Pfad zur Sprachdatenbank. |
| `FM-Scout starten.bat` | Installiert bei Bedarf `zstandard`, startet `extract.py` und öffnet die Seite. |
| `FM-Scout.html` | Erzeugte Ausgabe (ca. 4,4 MB). Wird bei jedem Lauf überschrieben. |

Die Dateien `Ravenna_Kader.*` und `Ravenna_Training.*` im übergeordneten Ordner sind frühe Einzelexporte. **`Ravenna_Kader` enthält falsch zugeordnete Attribute**, siehe Abschnitt „Erkenntnisse“.

Nutzerdaten:

- Spielstände: `%USERPROFILE%\Documents\Sports Interactive\Football Manager 26\games\` (der Ordner heißt „26“, das Spiel ist FM27 27.0.0)
  - `Haribaert Kachinski – Paris FC.fm`: aktuelle Karriere
  - `Haribaert Kachinski – Ravenna.fm`: zuletzt gespeichert am 07.11. um 23:24; Scoutinggebiet „Italien“
  - `Haribaert Kachinski – Ravenna europa.fm`: Testspielstand, identisch bis auf Scoutinggebiet „Europa“
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
    - Ravenna: aktive Taktik „Taktik“ = **Gegenpressing**, „4-1-1-3-1 DM Breit – Vertikales Tiki-Taka“ = Vertikales Tiki-Taka. **Vom Nutzer noch zu bestätigen.**
11. **fmsave getestet (09.11.):** siehe Abschnitt „Abgleich mit fmsave“.
12. **Brainstorming zum Umbau als Programm (09.11.):** Ablauf, Bereiche, Transfer-Informationsstufen, neuer Taktik-Reiter, Stil (dunkel/hell) mit dem Nutzer festgelegt → Design-Dokument (siehe oben). Entwürfe als HTML in `.superpowers/brainstorm/` (lokal, nicht im Repo): `ablauf-v2.html`, `transfer-werte.html`, `stil-v2.html`.
13. **Trainerbewertungen untersucht (09.11.):** mit `Trainertest .fm` und Screenshots. Ergebnis siehe „Trainer des menschlichen Managers“.
14. **Scoutinggebiet teilweise dekodiert (09.11.):** siehe „Scoutinggebiet“.

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
- Persönlichkeit: 8 Byte bei `dob_pos + 22`. Die Reihenfolge ist vermutlich Anpassung, Ehrgeiz, Kontroversität, Loyalität, Druck, Professionalität, Sportsgeist, Temperament – nicht verifiziert.
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
- **Persönlichkeit falsch angenommen:** Richtige Bytefolge (bei 51.208 von 51.208 Spielern): Anpassung, Ehrgeiz, **Loyalität, Druck, Professionalität, Sportsgeist, Temperament, Kontroversität**. `willingness()` liest Loyalität deshalb aus dem falschen Byte (`p[3]` = Druck statt `p[2]`). Noch nicht korrigiert.
- **fmsave findet mehr:** 86.402 statt 51.210 Spieler. Im Ravenna-Kader fehlen bei uns u. a. Zagré, Ilari und Vinícius.
- **Abweichungen bei uns:** Vertragsende bei rund 12.000 Spielern anders (z. B. De Silvestri: wir 29.07.2026, fmsave 30.06.2027), Gehalt bei rund 3.000.
- **Neu verfügbar:** Kaderstatus (`squad_status`, z. B. `regular_starter`, `emergency_backup`), Leihen, Scoutingbudget, Staff-Attribute (für diesen Build bestätigt). Die Attribute des menschlichen Managers liefert fmsave nicht (`None`).
- fmsave gibt fast alle Felder als „unconfirmed“ an; gegen das Spiel bestätigt sind für FM27 nur Staff-Felder.
- **fmsave scheitert** an einem Spielstand mit zwei menschlichen Managern (`Trainertest .fm`: „FM27 summary does not fit its structured clock layout“). Deshalb muss der eigene Leser als Rückfall bleiben.

### Trainer des menschlichen Managers (09.11.)

- Personenkopf in `game_db` wie bei anderen Personen, aber Vorname nicht aus der Namenstabelle (`Vorname-ID 00 Nachname-ID 00 ff×4 00 len "Voller Name" Geburtsdatum`). Persönlichkeit wie üblich bei `dob + 22` (beim Nutzer achtmal 10).
- **Coaching- und mentale Bewertungen (Offensive, Taktik, Torhüter, Autorität …) wurden nicht gefunden**: weder am Personenkopf, noch in `humans` (nur UI-Einstellungen, 2,6–8 KB), noch im Staff-Block-Aufbau von fmsave, noch per Mustersuche (Skala 1–20 und 1–100) über alle 1.187 Abschnitte. Schluss: Das Spiel **berechnet** sie sehr wahrscheinlich aus Lizenz, Spielerkarriere, Ansehen und Erfahrung.
- „Bevorzugtes System“ und „Taktischer Stil“ im Trainerprofil leitet das Spiel laut Nutzer aus der eingestellten Taktik ab; ohne Taktik sind sie bedeutungslos.
- **Trainertendenzen** sind relevant (FM27 zählt sie bei der Spielerüberzeugung, Bildschirm „Taktische Effektivität“). Bei beiden Testtrainern identisch, also nicht von der Lizenz abhängig. Ob sie gespeichert sind, ist ungeklärt.

### Scoutinggebiet (09.11.)

- Einstellung im Spiel: Weltweit / Europa / Südeuropa / Italien (beim Ravenna-Spielstand). Die Spielerdatenbank im Spiel zeigt dann automatisch Spieler dieses Gebiets.
- Vergleich `Ravenna.fm` (Italien) gegen `Ravenna europa.fm` (Europa): In `scout_man` ändert sich nur wenig. Ein 4-Zeichen-Code wechselt von `AcSP` (Italien) zu `blcP` (Europa), ca. Offset 1840. Ein Filterblock (`rfip … lvlf 01 12 88 13 rllp …`, enthält den Wert 5000) wandert dabei von Offset ~1269 hinter den Block `rrad … negm`.
- Weitere geänderte Abschnitte (vermutlich Nebeneffekte): `humans`, `memory_pools`, `media_man`, `training_man`, `news`, `backroom_advice_manager`.
- Offen: Codes für Weltweit und Südeuropa; ob „Italien“ allgemein „eigenes Land“ heißt; Zuordnung Land → Region/Kontinent.

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
- **Nicht ausgelesen werden:** Scoutingbudget, Scoutinggebiet, Staffattribute, Trainertendenzen und Teamanweisungen (fmsave liest Scoutingbudget und Staffattribute anderer Trainer).
- **Persönlichkeitsreihenfolge falsch:** siehe Abgleich mit fmsave; Korrektur wartet auf Screenshot-Abgleich (z. B. Viola: fmsave liest Loyalität 16, Druck 12, Professionalität 18, Kontroversität 3).
- **Torwartwahl:** Durch die Gewichtung „Ballspielender Torwart“ wählt das Programm bei Paris Nkambadio statt Trapp.
- **Spielstandwahl:** Backups sind ausgeschlossen, aber `find_save` nimmt weiterhin den neuesten Spielstand *jeder* Karriere (keine Einschränkung auf einen Manager).
- **Ungeprüfte Werte:** Das garantierte Mindestbudget für die nächste Saison ist nicht mit dem Spiel abgeglichen. Die Wechselchance ist eine Annahme.

## Nächste Schritte

### A. Umbau zum Programm (Vorrang)

1. **Design-Dokument vom Nutzer freigeben lassen:** `docs/superpowers/specs/2026-11-09-fm-scout-app-design.md`. Dabei die als „Entscheidung von Claude“ markierten Punkte bestätigen lassen (fmsave als Paket, `.exe` unsigniert, MIT-Lizenz, max. ~50 Vorschläge je Filter, Informationsstufe gespeichert).
2. **Vom Nutzer benötigt:**
   - Zwei weitere Spielstände nach dem Muster „Ravenna europa“: Scoutinggebiet „Weltweit“ und „Südeuropa“, sonst unverändert.
   - Welches Scoutinggebiet im Paris-Spielstand eingestellt ist (Test, ob „Italien“ = „eigenes Land“).
   - Screenshot der Persönlichkeit eines Spielers (z. B. Viola), um die Reihenfolge zu bestätigen.
   - Bestätigung, dass die aktive Ravenna-Taktik „Taktik“ auf Gegenpressing steht.
3. Nach Freigabe: Umsetzungsplan schreiben (Skill `superpowers:writing-plans`), dann bauen.
4. Beim Bauen klären: Zuordnung Land → Region/Kontinent für das Scoutinggebiet; Trainertendenzen im Spielstand suchen (sonst Auswahl pro Karriere im Programm).

### B. Dekodierung und Datenqualität (laufend)

1. **Rollentest abschließen.** Ablauf:
   - Der Nutzer benennt eine Kopie seiner Taktik in „Test 1“ (dann „Test 2“ usw.) um.
   - Er stellt an allen Positionen neue Rollen ein, mit Ball und gegen den Ball. Doppelte Positionen bekommen zwei verschiedene Rollen.
   - Spieleranweisungen bleiben unverändert.
   - Er speichert und schickt die ausgefüllte Liste (TW, RV, IV rechts, IV links, LV, DM, ZM, ZOM, RA, LA, ST jeweils „mit Ball / gegen den Ball“).
   - Danach `FMS_ROLES=1` setzen und `extract.py` laufen lassen; die Zeilen der Taktik „Test N“ mit der Liste abgleichen und die neuen Fingerabdrücke in `ROLE_FP` eintragen.
   - Fehlende Rollen in `ROLES` in `app.html` ergänzen, mit Schlüsselattributen laut FM27.
   - Geplant sind 4–5 Durchgänge, am Ende einer mit anderer Formation (z. B. 3-4-3) für Flügelverteidiger, Libero sowie RM/LM mit Ball.
2. Prüfen, ob Spieleranweisungen den Fingerabdruck verändern. Falls ja: nur die rollenbestimmenden Unterblöcke vergleichen.
3. Teamanweisungen aus dem Kopf der Taktik dekodieren (Stil-Code ist erledigt). Aufbau nach dem Namen: 12×`00`, 16 Byte Einstellungen, `00 00 ff`, `len u32`, Stilname, Code4. Bisher gesehen:
   - „Taktik“ (Gegenpressing): `04 01 04 07 02 03 80 00 00 00 0a 40 50 22 62 90`
   - „4-1-1-3-1 … Tiki-Taka“: `04 03 04 07 02 03 88 10 8a 10 0a 10 61 22 64 80`
   - Wirkt bitgepackt. Zum Dekodieren: Kopie einer Taktik, jeweils **eine** Anweisung ändern, speichern, vergleichen.
4. Kaderfilter für die erste Mannschaft über `squad_status` aus fmsave; fehlende Spieler (Otávio, Zagré, Ilari, Vinícius) und Leihspieler sind mit fmsave gelöst.
5. ~~Spielstandwahl~~ erledigt. ~~Trainerbewertungen lesen~~ verworfen (werden vom Spiel berechnet).
