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
  - `Haribaert Kachinski – Ravenna.fm`: zuletzt gespeichert am 07.11. um 23:24 und damit derzeit der neueste Stand
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
- **Nicht ausgelesen werden:** Scoutingbudget, Trainer- und Staffattribute sowie Teamanweisungen.
- **Torwartwahl:** Durch die Gewichtung „Ballspielender Torwart“ wählt das Programm bei Paris Nkambadio statt Trapp.
- **Spielstandwahl nicht gefiltert:** `find_save` nimmt den neuesten `.fm` aus *allen* `Football Manager*\games`-Ordnern. Damit kann auch `last save overwrite backup.fm` oder eine andere Karriere gewählt werden.
- **Ungeprüfte Werte:** Das garantierte Mindestbudget für die nächste Saison ist nicht mit dem Spiel abgeglichen. Persönlichkeitsreihenfolge und Wechselchance sind Annahmen.

## Nächste Schritte

1. **Rollentest abschließen.** Ablauf:
   - Der Nutzer benennt eine Kopie seiner Taktik in „Test 1“ (dann „Test 2“ usw.) um.
   - Er stellt an allen Positionen neue Rollen ein, mit Ball und gegen den Ball. Doppelte Positionen bekommen zwei verschiedene Rollen.
   - Spieleranweisungen bleiben unverändert.
   - Er speichert und schickt die ausgefüllte Liste (TW, RV, IV rechts, IV links, LV, DM, ZM, ZOM, RA, LA, ST jeweils „mit Ball / gegen den Ball“).
   - Danach die Taktik namens „Test N“ parsen (`read_tactics` liefert alle Taktiken) und die neuen Fingerabdrücke in `ROLE_FP` eintragen.
   - Fehlende Rollen in `ROLES` in `app.html` ergänzen, mit Schlüsselattributen laut FM27.
   - Geplant sind 4–5 Durchgänge, am Ende einer mit anderer Formation (z. B. 3-4-3) für Flügelverteidiger, Libero sowie RM/LM mit Ball.
2. Prüfen, ob Spieleranweisungen den Fingerabdruck verändern. Falls ja: nur die rollenbestimmenden Unterblöcke vergleichen.
3. Teamanweisungen aus dem Kopf der Taktik dekodieren. Zwischen Name und erstem Slot stehen rund 16 Byte Einstellungen und der Stil-Code, z. B. `TREV` (vertikal) oder `EGEG` (Gegenpressing). Damit würde `config.json` für Taktiken überflüssig.
4. `find_save` auf Karrieren des Nutzers einschränken: Backups ausschließen und ggf. eine Auswahlliste anbieten.
5. Kaderfilter für die erste Mannschaft; fehlende Spieler (Otávio) und Leihspieler klären.
6. Optional: Scoutingbudget sowie Trainer- und Staffattribute aus `game_db` lesen.
