# Co-Trainer (früher „FM-Scout“) – Übergabe

Stand: 14.11.2026

## Ziel

Ein eigenes Windows-Programm (`Co-Trainer.exe`), das einen **Football-Manager-27-Spielstand (`.fm`)** liest und in einem Fenster analysiert. Vorbild ist die Seite `FM27 Transfer-Scout.html` des Nutzers (liegt in seinem Downloads-Ordner).

Die Seite soll:

- analysieren, wie gut der Kader zur eigenen Taktik passt, und Schwächen zeigen;
- passende Transfers vorschlagen, jeweils mit geschätzter Wechselchance;
- bewerten, wie der eigene Trainer zur Taktik passt, und eine Taktik-Empfehlung geben (Trainerpräferenz + Spielerattribute);
- eine Trainingswoche für die Taktik vorschlagen;
- Verein, Liga, Budget und Gehaltsbudget automatisch eintragen.

**Harte Vorgabe des Nutzers:** CA, PA und versteckte Attribute dürfen in der Oberfläche nie erscheinen. Das Potenzial wird nur als Text gezeigt, z. B. „Kann sich zu einem guten Zweitliga-Spieler entwickeln“.

**Neue Richtung (09.11.):** FM-Scout wird zu **einem eigenständigen Windows-Programm** (`FM-Scout.exe`, ohne Batch-Datei, ohne erzeugte HTML-Seite), das öffentlich auf GitHub geteilt wird. Der vollständige Entwurf steht in [docs/superpowers/specs/2026-11-09-fm-scout-app-design.md](docs/superpowers/specs/2026-11-09-fm-scout-app-design.md). **Vom Nutzer am 10.11. freigegeben.** Das Programm heißt „Co-Trainer“. **Teil 1 (Grundgerüst) ist seit 14.11. gebaut**, siehe „Was bisher gemacht wurde“ Punkt 15 und „Nächste Schritte“.

## Dateien

| Datei | Zweck |
|---|---|
| `cotrainer/extract.py` | Leselogik. `analyse(Pfad, cfg=None, progress=None)` liefert das Wörterbuch `meta`, `coach`, `tactic`, `squad`, `pool`, `training`. Unlesbare Dateien ergeben `SaveReadError`. Konsolenaufruf: `python -m cotrainer.extract [Pfad.fm \| Nummer] [--list] [--dump Datei.json]`. |
| `cotrainer/guard.py` | `assert_public(data)`: Schutz gegen versteckte Werte (CA, PA, Persönlichkeit, versteckte Attribute, Zahlen bei Trainerbewertungen). Jedes Ergebnis geht hier durch, bevor es die Oberfläche erreicht. |
| `cotrainer/saves.py` | Spielstand-Ordner finden, Spielstände auflisten (ohne Sicherungen), Kurzinfo (`read_summary`: Manager, Verein, Spieldatum) in Millisekunden lesen. |
| `cotrainer/settings.py` | Programmeinstellungen in `%APPDATA%\Co-Trainer\settings.json`. |
| `cotrainer/api.py` | Brücke Oberfläche ↔ Python (Klasse `Api`). Das Einlesen läuft in einem Thread und meldet sich über `CT.onProgress`, `CT.onResult`, `CT.onError`. |
| `cotrainer/app.py`, `cotrainer/__main__.py` | Fenster (pywebview, Edge WebView2). Start: `python -m cotrainer`. |
| `cotrainer/ui/index.html` | Oberfläche (Vanilla JS): geführter Start in drei Schritten, Ergebnis mit ein-/ausblendbaren Bereichen, hell/dunkel. |
| `tests/` | 55 Tests (pytest); fünf davon brauchen echte Spielstände (Marke `save`). |
| `build.ps1` | Führt die Tests aus und baut `dist\Co-Trainer.exe` (PyInstaller, eine Datei). |
| `pyproject.toml` | Paketdaten und Abhängigkeiten (`zstandard`, `pywebview`; Entwicklung: `pytest`, `pyinstaller`). Python ≥ 3.12 in `.venv`. |
| `config.json` | Nur noch Entwicklerhilfe für Kontrollläufe in der Konsole (Trainerprofil und Taktik pro Verein aus Screenshots). Das Programm benutzt sie nicht. |
| `docs/superpowers/specs/2026-11-09-fm-scout-app-design.md` | Freigegebenes Design für das Programm „Co-Trainer“. |
| `docs/superpowers/plans/2026-11-10-co-trainer-1-grundgeruest.md` | Umsetzungsplan Teil 1 (Grundgerüst), am 14.11. ausgeführt. |

Entfallen sind `extract.py` (Wurzel), `app.html`, `FM-Scout starten.bat` und die erzeugte `FM-Scout.html`.

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
2. `extract.py`, `app.html` und `config.json` gebaut (heute `cotrainer/extract.py` und `cotrainer/ui/index.html`). Die Oberfläche hat fünf Bereiche:
   - **Kader-Analyse:** Spielfeld mit beste Elf und Schwachstellen
   - **Transfervorschläge:** Filter nach Position, Alter, Wechselchance, Budget und ablösefrei
   - **Trainer & Taktik:** Passung Trainer ↔ Taktik, Rangliste der Spielstile, Prüfung der Teamanweisungen
   - **Training:** Wochenplan mit echten FM27-Einheiten, Trainingsbewertungen, gespeicherte Wochenpläne
   - **Kaderliste**
3. Finanzen mit Screenshots des Nutzers abgeglichen. Alle geprüften Werte stimmen:
   - Ravenna: Transferbudget 604.815 €, Gehaltsbudget 98.362 €/Woche, Kontostand 1,38 Mio. €
   - Paris: Transferbudget 4,99 Mio. €, Gehaltsbudget 719.189 €/Woche, Kontostand 80,07 Mio. €
   - Osijek (Screenshot 14.11.): Kontostand 6,71 Mio. €, Transferbudget 499 K €, Gehaltsbudget 2.623.451 €/Jahr (50.451 €/Woche), Gehaltskosten 45.680 €/Woche
4. Verträge mit Screenshots abgeglichen (Soleri, Spini, Tenkorang, Maggio).
5. Trainerprofil und Taktik für Paris aus Screenshots in `config.json` übernommen. Der Nutzer hat das Profil „Offensiv/Entwickler“ gewählt.
6. **Taktik aus dem Spielstand:** Positionen und Rollen werden jetzt aus `tactics_man` gelesen (`read_tactics` in `cotrainer/extract.py`). Beim Ravenna-Spielstand werden alle 22 Rollen erkannt. Neu in der Oberfläche:
   - die Rolle gegen den Ball und die Position ohne Ball werden auf dem Spielfeld angezeigt;
   - Rolle `cfo` (Mittelstürmer gegen den Ball);
   - FM27-Rollennamen;
   - Schlüsselattribute des Halbraumstürmers laut Screenshot.
7. Eine kurze Vorstellung des Programms für einen FM-Discord-Mod-Kanal geschrieben (nur im Chat).
8. **Spielstandwahl (09.11.):** `find_save` lässt Sicherungen (`backup`, `autosave`) aus. `python -m cotrainer.extract --list` zeigt alle Spielstände mit Nummer; `python -m cotrainer.extract 2` nimmt Nummer 2.
9. **Rollentest-Hilfe (09.11.):** `FMS_ROLES=1` gibt für jede Taktik alle 22 Fingerabdrücke aus, unbekannte als `UNBEKANNT`. Die Schlüssel lassen sich direkt in `ROLE_FP` kopieren.
10. **Spielstil aus dem Taktikkopf (09.11.):** Stilname und 4-Zeichen-Code werden gelesen (`STYLE_CODES` in `cotrainer/extract.py`: `TREV` → `vertical_tikitaka`, `EGEG` → `gegenpress`) und haben Vorrang vor `config.json`. Die Oberfläche übernimmt den Stil, sobald er sich im Spielstand ändert (`styleSeen` im `localStorage`).
    - **Aktive Taktik = Index vor dem ersten Taktikkopf (15.11.):** Die 6 Byte direkt vor dem ersten Kopf in `tactics_man` sind `<u32 Index> <u16 Index+1>` (`active_index`); `read_tactics` markiert den Datensatz mit `slot == Index` als `chosen`, `pick_tactic` nimmt ihn. Beleg: „Ravenna 2 spieltaktik“ (Nutzer wählte Platz 2): `01 00 00 00 02 00`, aktiv ist „5-2-3 DM Breit (Kontrolliert) – Ballbesitzspiel“ (`TNOC`); alle früheren Spielstände haben `00 00 00 00 01 00`. „Erster Platz = aktiv“ bleibt nur als Rückfall, wenn der Index fehlt oder ungültig ist (`u16 != u32 + 1`). Das Byte `02` im Kopf ist kein Aktiv-Merkmal (vermutlich Standardname „Taktik“). Codes (rückwärts geschrieben): `TNOC` Ballbesitzspiel → `tikitaka` (angenähert), `IKIT` Tiki-Taka → `tikitaka`, `TUOR` Langer Hafer → `direct`, `TREV` Vertikales Tiki-Taka → `vertical_tikitaka`, `EGEG` Gegenpressing → `gegenpress`, `GNIW` Flügelspiel → `wings` (Osijek), `ERID` Direktes Kontern → `counter`, `ETAC` Catenaccio → `counter`, `KRAP` Beton anrühren → `counter`, `IULF` Dynamisches Kontern → `counter` (die vier Konter-Stile sind angenähert, Co-Trainer hat nur sechs Stilfamilien). Die frühere Annahme „ERID = Catenaccio“ war falsch. Tests `test_active_index`, `test_pick_tactic_prefers_chosen`, `test_ravenna_saves_pick_chosen_tactic`.
    - Ravenna: aktive Taktik „Taktik“ = **Gegenpressing**, „4-1-1-3-1 DM Breit – Vertikales Tiki-Taka“ = Vertikales Tiki-Taka. Gegenpressing für „Taktik“ hat der Nutzer am 10.11. bestätigt; damit gilt der Code `EGEG` als geprüft. `TREV` ist durch „Ravenna vert tiki taka“ bestätigt.
11. **fmsave getestet (09.11.):** siehe Abschnitt „Abgleich mit fmsave“.
12. **Brainstorming zum Umbau als Programm (09.11.):** Ablauf, Bereiche, Transfer-Informationsstufen, neuer Taktik-Reiter, Stil (dunkel/hell) mit dem Nutzer festgelegt → Design-Dokument (siehe oben). Entwürfe als HTML in `.superpowers/brainstorm/` (lokal, nicht im Repo): `ablauf-v2.html`, `transfer-werte.html`, `stil-v2.html`.
13. **Trainerbewertungen und Neigungen gefunden (10.11.):** per Editor-Test, siehe „Trainer des menschlichen Managers“. Die Aussage vom 09.11. („werden berechnet“) ist widerlegt.
14. **Scoutinggebiet dekodiert (10.11.):** siehe „Scoutinggebiet“.
15. **Teil 1 des Umbaus gebaut (14.11.): Programm „Co-Trainer“.** Paket `cotrainer`, Fenster mit geführtem Start, `Co-Trainer.exe`.
    - **Ablauf:** Schritt 1 Spielstand-Ordner (nur beim ersten Start, Vorschlag aus `Dokumente\Sports Interactive\Football Manager*\games`), Schritt 2 neuesten Spielstand bestätigen oder anderen wählen (mit Verein und Spieldatum), Schritt 3 Analyse wählen, dann Einlesen mit sechs Fortschrittstexten und das Ergebnis. Links „Anzeigen“ mit fünf Häkchen, darunter „Spielstand wechseln…“, „Neu einlesen“, „Hell/Dunkel“, „Ordner ändern…“.
    - **Geprüft mit dem Ravenna-Spielstand im echten Fenster:** Einlesen 68 s, fünf Bereiche, Fenstertitel „Co-Trainer · Ravenna · Serie C/B“, keine versteckten Werte in den Daten, Änderungsdatum aller `.fm`-Dateien unverändert. Nach einem Neustart sind Ordner, Farbschema und angehakte Bereiche erhalten.
    - **`Co-Trainer.exe`:** 12,1 MB, Fenster nach rund 2 s, legt neben sich keine Datei an. Aus der `.exe` heraus geprüft sind Start, Einstellungen und die Kurzinfo in Schritt 2; **das vollständige Einlesen aus der `.exe` hat noch niemand durchgeklickt** (derselbe Code läuft über `python -m cotrainer`).
    - **Abweichungen vom Plan, die man kennen muss:**
      - Das Fenster steht in `Api._window` (nicht `Api.window`), weil pywebview jedes öffentliche Attribut der `Api` für die Oberfläche offenlegt.
      - pywebview liefert die Oberfläche über einen eingebauten HTTP-Server aus. Damit `localStorage` (Rollenwahl, Filter, sichtbare Bereiche je Karriere) zwischen Starts erhalten bleibt, ist der Port fest: `UI_PORT = 47127` in `app.py`. Ist er belegt, nimmt das Programm einen zufälligen Port und vergisst diesen Zustand für den Lauf.
      - Fehlt WebView2, würde pywebview still auf den Internet Explorer ausweichen. `app.py` prüft deshalb vorher die Registry und zeigt sonst ein Meldungsfenster.
      - Schritt 1 merkt sich einen gültigen Ordner schon bei der Rückmeldung „✓ Ordner gefunden“, nicht erst bei „Weiter“.
      - Der Schlüssel im `localStorage` heißt jetzt `cotrainer:<Verein>|<Manager>`.
    - **Andere Spielstände am 14.11. gelesen wie im Programm (ohne `config.json`):** Paris FC läuft mit Standardformation (78 Spieler im Kader, Scouting „Kontinent“, Budget 4,99 Mio. €). Bei den **Nationaltrainer-Karrieren (Südkorea 2028, Curaçao) und dem Zwei-Manager-Spielstand `Trainertest .fm` findet der Leser keinen eigenen Kader.** Das Programm zeigt dann statt eines leeren Ergebnisses die Meldung „In diesem Spielstand wurde kein Kader des eigenen Vereins gefunden …“ (`require_squad`). Ob fmsave (Teil 2) diese Fälle löst, ist offen.
    - **Bekannte Grenzen von Teil 1:** Der Bereich „Trainer & Taktik“ hat noch den alten Inhalt (Teil 3 ersetzt ihn); Stil und Tendenzen des Trainers fehlen ohne `config.json`, dann entfallen die zugehörigen Zeilen. Transfervorschläge zeigen weiter die bisherige Informationstiefe (die drei Stufen kommen in Teil 2). Bei einem Spielstand ohne eigene Taktik (Paris) wird eine Standardformation 4-2-3-1 benutzt.

16. **Durchsicht von Teil 1 und fmsave-Probe (14.11.):**
    - **Unabhängige Durchsicht** (`/code-review high main...programm-entwurf`) ergab zehn Befunde. **Behoben** (55 Tests grün, Oberfläche im Entwicklermodus in Edge ohne Fenster durchgeklickt):
      - „Neu einlesen“ las die Auswahl aus Schritt 2 statt des angezeigten Spielstands (jetzt `W.cur`; `W.run` = gerade eingelesen).
      - Schritt 1: „Weiter“ konnte eine noch laufende Ordnerprüfung überholen; veraltete Antworten werden jetzt verworfen.
      - `analyse()` meldete jeden `KeyError`/`IndexError` der Auswertung als „kein lesbarer FM27-Spielstand“. Jetzt gilt das nur noch für das Öffnen des Containers und die Pflichtabschnitte (`REQUIRED_SECTIONS`); Fehler danach erscheinen als „Unerwarteter Fehler beim Einlesen“.
      - `assert_public` läuft jetzt in `analyse()` selbst, also auch beim Konsolenlauf mit `--dump`.
      - `read_coach` mit leerem Managernamen durchsuchte die ganze Datenbank Byte für Byte.
      - Schlug das Anzeigen des Ergebnisses fehl, blieb die Seite beim Fortschrittsbalken stehen; jetzt erscheint eine Meldung mit „Nochmal versuchen“.
      - `read_summary`: der Rückfall auf die ganze Datei kopiert nicht mehr je Versuch und entpackt höchstens 16 MB je Kandidat.
      - `render()` rechnete die beste Elf bis zu fünfmal je Klick; jetzt einmal je Durchlauf (`AN_MEMO`).
    - **Offen gelassen:**
      - `read_coach` ordnet den Staff-Block über die Nähe zum Namen zu, ohne ID-Prüfung (gleiche Schwäche wie früher bei den Spielerblöcken); Anpassungsfähigkeit wird ohne Bereichsprüfung 1–20 übernommen. Braucht die Dekodierung der Block-ID des Staff-Blocks.
      - `app.main` zeigt die WebView2-Meldung bei jedem Startfehler. Außerdem nimmt pywebview bei belegtem Port 47127 keinen zufälligen, sondern den festen Port 42001 (Kommentar in `app.py` und Testname stimmen nicht).
      - Schritt 1 speichert den Ordner schon bei der Prüfung (so gewollt, siehe Punkt 15).
    - **fmsave 0.11.0 an fünf Spielständen probiert:** Ravenna 33 Spieler (27 erste Mannschaft, 6 zweites Team, 1 Leihe), Paris 79 (23 / 28 / 28). `team_slot == 0` ist die erste Mannschaft; damit ist der Kaderfilter gelöst. **Curaçao und Südkorea 2028 sind FM26-Spielstände** (26.3.1 und 26.3.2) und liefern `managed_clubs() == []`; Nationaltrainer löst fmsave also nicht. `Trainertest .fm` lässt sich weiter nicht öffnen. Dauer 19–34 s je Spielstand. `ManagedClub` liefert auch Kontostand und Scoutingbudget.

17. **Teil 2: `Co-Trainer.exe` mit fmsave (14.11.):** `build.ps1` packt fmsave (`--collect-submodules fmsave --copy-metadata fmsave --collect-all backports.zstd`). Bau mit `-MitSpielstand`: 66 Tests grün, `dist\Co-Trainer.exe` 13,3 MB. Probelauf aus der `.exe` (Fernsteuerung von WebView2, Fenster bis zum Ergebnis durchgeklickt):
    - **NK Osijek** (`Ivan Kurasic – NK Osijek.fm`): Titel „Co-Trainer · NK Osijek · First League“, Quelle `fmsave`, Kader 27, fünf Bereiche, kein JS-Fehler, keine versteckten Werte, 126 s.
    - **Ravenna**: Titel „Co-Trainer · Ravenna · Serie C/B“, Quelle `fmsave`, Kader 27, fünf Bereiche, kein JS-Fehler, 78 s.
    - Änderungsdatum aller 45 `.fm`-Dateien blieb unverändert.
    - Osijek-Finanzen per Screenshot bestätigt (14.11.). Ein Einlesen dauert nun rund 1,5 bis 2 Minuten, weil beide Leser entpacken.

18. **Teil 2b (15.11.): Scouting im Transferbereich.** Branch `teil-2b-scouting`, sechs Tasks.
    - `cotrainer/nations.py`: Kontinent und Region je Land aus der Nationentabelle; alle 251 Länder mit deutschem Namen (502 Namen gelesen). Die alte Regex hörte bei 195 auf, weil das Byte nach einem Namen ein Grammatik-Flag 0–4 ist und manche Einträge kein Kürzel haben.
    - fmsave liefert jetzt Nationalität der Spieler sowie Land und Reputation der Vereine. Der fmsave-Verein mit uid 0 (KS Besa) wird intern zu `2**31`, weil 0 „vereinslos“ heißt.
    - Ligastufe aus der mittleren Vereinsreputation; Staffeln über `league_base` zusammengefasst (Ravenna: Serie A 1, Serie BKT 2, Serie C 3; Serie D hat keine Spiele im Spielstand).
    - Pool nach Scoutinggebiet. Sichtbare Auswahl `vis` (4.000, ohne CA/PA/Attribute; Reihenfolge: Nähe – Liga des eigenen Landes mit Stufe ± 1 zuerst, dann Vereine des eigenen Landes ohne spielbare Liga und vereinslose Landsleute, dann der Rest –, Wechselchance-Band, Abstand zur eigenen Vereinsreputation, vereinslos, Vertragsende; vereinslose Spieler unter 18 nicht in `vis`) plus Qualitätsauswahl (4.000). Feld `near_league` = Liga mit Stufe ± 1 im eigenen Land.
    - Wechselchance aus der Vereinsreputation statt der Vereinsstärke (fmsave-Weg): Grundwert 68 (`WILL_BASE`), der Abstand nach unten ist auf −4 begrenzt (`REP_DIFF_MIN`), Vereinslose −10. Der eigene Leser nutzt keinen Vereinsabstand mehr (0, Vereinslose −10), weil die Vereinsstärke aus CA käme.
    - `weaker_league` auch für Vereine ohne spielbare Liga im eigenen Land: Vereinsreputation unter 95 % des Mittels der eigenen Liga.
    - Stufe „Aus“, Empfehlung: vereinslos +8, Liga deines Niveaus (`near_league`) +10 mit Grund „Spielt in einer Liga deines Niveaus“. Fußnote zur Wechselchance je nach Quelle (fmsave / eigener Leser).
    - Scoutinggebiet 3 ohne tiefere spielbare Liga: Hinweis in `meta.scout_note`; die Oberfläche zeigt Gebiet und Hinweis zusammen.
    - Drei Informationsstufen in der Oberfläche (Aus, Scoutbericht, Werte) mit Hinweis vor dem Hochschalten; gespeichert in `settings.json`.
    - **Ravenna:** Scoutinggebiet 4 (Eigenes Land), 6.953 Spieler im Gebiet, Pool 4.657, davon 4.000 `vis` (3.149 aus Serie BKT/Serie C, 851 Vereine ohne Liga oder vereinslos, 585 vereinslos). Wechselchance in `vis`: 20er 236, 30er 441, 40er 580, 50er 320, 60er 192, 70er 1.099, 80er 385, 90er 580 (unter 20: 167). Serie BKT 1.056 in `vis`, `weaker_league` bei 165 Pool-Spielern.

19. **Teil 3 (15.11.): Reiter Taktik.** Branch `teil-3-taktik`, vier Tasks.
    - `cotrainer/ui/taktik.js` (globales `TAKTIK`, reine Logik, Node-Tests in `tests/js/`): acht Bereiche, die den Trainingseinheiten entsprechen (Formation mit/ohne Ball, Passstil, Spielaufbau, Chancen kreieren, Pressinglinie, Pressingintensität, Pressingfalle).
    - **Rechenregel:** Je Spieler auf den Positionen des Bereichs in der Startelf der gewichtete Mittelwert der Bereichsattribute (Schlüsselattribute der gespielten Rolle zählen doppelt), je Bereich der Mittelwert über diese Spieler. Die Karte „Taktische Bereiche“ zeigt den Wert (Daten des eigenen Kaders, erlaubt). Bei Bereichen gegen den Ball zählt die Position gegen den Ball (`op`), bei Bereichen mit Ball die normale Position. Stufen: ab 13 „gut“, ab 11 „mittel“, darunter „schwach“; ohne passende Spieler keine Stufe. Verursacher = bis zu drei Spieler unter 11, schwächster zuerst; dazu Abhilfe (bessere Rolle, Training, Transfer).
    - **Baustellen** (`focusAreas`): alle „schwachen“ Bereiche plus Bereiche mit Verursachern (Spieler unter 11), deren Wert mindestens 0,3 unter dem Mittel aller bewerteten Bereiche liegt, aufsteigend sortiert. Verursacher und Abhilfe werden für jeden Bereich mit Verursachern gezeigt (bei Baustellen offen, sonst eingeklappt). Training, Transferfilter, Aus-Grund und Trainerhinweise hängen an den Baustellen, nicht mehr nur am Band „schwach“.
    - **Coaching-Lücken** (`tacticCoachGaps`): in der Karte „Trainer“ die für den Spielstil wichtigen Trainerbereiche mit „Schlecht“/„Sehr schlecht“ (Ballbesitz/Techniken/Taktik/Fitness für Ballbesitz usw.).
    - Trainerbewertungen als Textstufen; der Führungsstil (Training/Mental) wird pro Karriere gewählt und im `localStorage` gespeichert.
    - **Verknüpfung:** Baustellen werden im Training vorgezogen (Pille „Baustelle“, Text unter der Überschrift). Im Transferbereich gibt es den Filter „Nur Positionen mit Taktik-Baustellen“ (`S.f.weak`, Plätze der Verursacher, geschnitten mit dem Positionsfilter); in Stufe „Aus“ zusätzlich der Grund „Spielt <Position> – dort liegt die Baustelle „<Bereich>““. Beides nutzt nur Positionen, nichts aus CA/PA/Attributen fremder Spieler.
    - Prüfung im Browser mit künstlich geschwächter Startelf (nur im Speicher): Passstil, Spielaufbau, Pressinglinie, Pressingfalle schwach, Pille und Filter wirken (Aus: 3769 → 1940 Spieler, gleiche Reihenfolge), Meldung bei Filter ohne Schnittmenge.
    - Mit den Grenzen 13/11 hat Ravenna in den echten Daten keinen schwachen Bereich (alle acht „mittel“), aber Baustellen über die Regel mit 0,3.
    - **Vom Nutzer zu bestätigen:** die Grenze 0,3 unter dem Schnitt für Baustellen (Schätzung, nicht aus dem Spiel).

20. **Kleinigkeiten aus Teil 3 erledigt (15.11. spät).**
    - Training: Reihenfolge der Einheiten in `TAKTIK.sessionOrder` (Taktik-Feedback, dann Baustellen, schwächste zuerst, dann die Grundliste; vorher galt bei mehreren Baustellen die Reihenfolge der Grundliste). `TAKTIK.trainingWeak`: Pressing-Baustellen (Pressinglinie, -intensität, -falle) zieht nur ein Stil mit Pressing vor (Gegenpressing, Vertikales Tiki-Taka oder Pressinglinie „Hoch“ in `config.json`); sonst bleiben sie weg, mit Satz unter der Überschrift („… ist nicht vorgezogen, weil „Konterfußball“ nicht hoch presst“).
    - Bereiche und Baustellen werden nur einmal je Analyse gerechnet (`areaInfo`, `WeakMap`); `renderSug` hält die Analyse wie `render` (`withAnalysis`), `weakIdx` ist weg.
    - Karte „Trainer“: die Tabellen „Training“ und „Mentales“ erscheinen nur, wenn sie Werte haben.
    - Python: `read_tactics` gibt `active_slot` (gewählter Platz laut Index, nur wenn es den Kopf gibt) statt des ungenutzten `active`. Zeigt der Index auf einen nicht lesbaren Kopf, setzt `chosen_unread` `tactic.chosen_unread` (Platz ab 1); die Taktik-Karte warnt dann, welche Taktik stattdessen gezeigt wird.
    - Tests: Plätze 2/3, übersprungener Kopf behält die Platznummer, nicht lesbare Spieltaktik, Index außerhalb (synthetisches `tactics_man`); JS: Randfälle `helpFor` (Grenze +1,0, Phase/Position, ohne Verursacher, unbekannte Rolle), alle Regeln von `leadHints`, `trainingWeak`, `sessionOrder`. Oberfläche im Entwicklermodus geprüft (Edge headless über DevTools-Protokoll, keine Konsolenfehler).
    - **Fehler Osijek behoben:** Die Oberfläche zeigte bei Osijek nichts, weil die Spielstile „Flügelspiel“ und „Direkt / lange Bälle“ die Positionsgruppe `ST` nutzen, die in `PG` fehlte (`TypeError … reading 'some'` in `styleMods`). Aufgefallen ist es erst, seit `GNIW` als Flügelspiel erkannt wird; vorher stürzte nur die Handauswahl dieser Stile ab. `PG.ST` ergänzt, Test `tests/test_ui_static.py` (jede in Stil-Modifikatoren benutzte Gruppe muss in `PG` stehen). Osijek und Ravenna mit allen sechs Stilen in der Oberfläche geprüft.

21. **Teil 4 (15.11. abends): README, Lizenzhinweise, Version 1.0.0.** Branch `teil-4-release`, Plan `docs/superpowers/plans/2026-11-15-co-trainer-4-release.md`.
    - `tools/third_party.py` sammelt die Lizenzen aller gebündelten Pakete (Laufzeitabhängigkeiten von `cotrainer` laut Paketangaben), Python, der DLLs ohne Python-Paket (OpenSSL, libffi, Expat, libmpdec, WebView2 SDK 1.0.3856.49; Texte aus den Originalquellen in `tools/licenses/`) und von PyInstaller in `THIRD_PARTY_LICENSES.txt`. `build.ps1` erzeugt die Datei neu und packt sie ein. Kommt ein Paket oder eine DLL dazu (Liste: `build/Co-Trainer/Analysis-00.toc`), muss `NATIVE` in `tools/third_party.py` nachgezogen werden.
    - `build.ps1` schließt `setuptools`, `packaging` und `_distutils_hack` aus; cffi zog sie über `setuptools_ext` hinein, zur Laufzeit braucht sie niemand. Die `.exe` ist dadurch 12,1 statt 13,4 MB.
    - Fenster „Über Co-Trainer“ (Seitenleiste und Fuß des Assistenten): Version, MIT, fmsave, Hinweis „Fanprojekt, keine Verbindung zu Sports Interactive oder SEGA“, Lizenzliste; Adressen nur als Text. `cotrainer/about.py`, `Api.about()`.
    - `README.md` (Starten mit Windows-Schutzhinweis, Voraussetzungen, Sicherheit und Daten, Grenzen, Bauen aus dem Quellcode, Lizenz). Version 1.0.0 (Wunsch des Nutzers).
    - Geprüft: gebaute `.exe` gestartet und über den WebView2-Debugport (`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=…`) `API.about()` aufgerufen: Version 1.0.0, Liste vollständig. Dieser Weg eignet sich allgemein, um die echte `.exe` automatisch zu prüfen.
    - Abschließende Durchsicht durch einen frischen Reviewer: zwei wichtige Funde (fehlende Lizenzen für DLLs und PyInstaller, setuptools in der `.exe`) behoben. Zurückgestellt: `build.ps1` erzeugt die Lizenzliste erst nach den Tests (nach einem Paket-Update scheitert der Build deshalb an `test_checked_in_notices_match_installed_versions`; dann zuerst `.venv\Scripts\python tools\third_party.py` ausführen); `tools/third_party.py` prüft nicht, ob `cotrainer` installiert ist; `about.notices_text` fängt keinen Dekodierfehler.

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
- Attributreihenfolge: siehe `ATTR_KEYS` in `cotrainer/extract.py`. Versteckt sind: Cons, Dirt, ImpM, InjPr, Vers.
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
- Budgetblock innerhalb von 120 Byte nach dem Kurznamen: `01 Start Aktuell Garantiert 00 x y W` (alle i32 in GBP). W = Gehaltskosten/Woche (`wage_payroll_week`); das Gehaltsbudget/Woche (`wage_budget_week`) steht als i32 bei Blockstart+63.
- Kontostand: `ff 00 <i32> xxxx (01 00 6c 07)×3 00×5`, innerhalb von 4000 Byte nach dem Namen.

### Wettbewerbe

- In `comp_<id>` stehen Teamzeilen `id 00 ff×6` mit festem Abstand (genommen wird die längste Folge mit gleichem Abstand).
- Die Namen kommen aus `lang_db.dat`.

### Training (`training_man`)

- Wochenpläne: `0b Datum(2) Jahr(2) 01 7×(04 u16×3 00) len Name`.
- Bewertungsliste: `count`, dann pro Spieler `pid 01 02 00 00 00 float float`.

### Taktik (`tactics_man`)

Kopf einer eigenen Taktik: `22 44 00 1b 00 <?> 00 <Art> <len u32> Name`.

- Das Byte `<?>` ist meist 00, in mehreren Ravenna-Spielständen aber 01 (vert tiki taka, angrenzende Ligen, kein Scouting, liga, südeuropa). Bis Commit e5a68f9 fielen diese Spielstände auf die Standardformation zurück; jetzt werden alle drei Taktiken erkannt. Der Stilcode `TREV` = „Vertikales Tiki-Taka“ ist durch den Spielstand „Ravenna vert tiki taka“ bestätigt.
- `<Art>` ist das Flag:

- Flag `02`: bei Standardnamen „Taktik“ immer 02, bei den fünf neuesten Ravenna-Spielständen (15.11.) sogar bei allen drei Plätzen: **kein Aktiv-Merkmal**, Bedeutung unklar
- Flag `00`: weitere eigene Taktik
- Flag `01`: Formationsvorlage des Spiels

Danach folgen **22 Slot-Einträge**, abwechselnd mit Ball und gegen den Ball:

```
44 00 02 | Position u16 | Seite u16 | 00 01 01 | n u32 | Gruppe u64 | n × (02 02 02, 8×00, ff, 4×00, u64-Bits)
```

- Positions-Bits: GK 1, SW 2, DR 4, DL 8, DC 10, WBR 20, WBL 40, DM 80, MR 100, ML 200, MC 400, AMR 800, AML 1000, AMC 2000, ST 4000.
- Seite: 0x20 = rechts, 0x10 = links.
- Die Rolle wird über einen Fingerabdruck erkannt: (Phase, Gruppen-Bit, Bitlisten der Unterblöcke) → Tabelle `ROLE_FP` in `cotrainer/extract.py`.
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
- **Fundort:** Abschnitt `humans`, ein Byte im Muster `33 00 <Stufe> <u32> 20 00 <u16> <Datum>`. Das `u16` ist bei Ravenna 1, bei Osijek 5 (15.11.; bis dahin verlangte das Muster 1, deshalb „nicht gefunden“). Seitdem wird statt der 1 ein Jahr 2000–2047 im Datum verlangt. Osijek: Stufe 7 = Weltweit (Screenshot des Nutzers: die unteren Stufen sind nicht gewählt). Gelesen von `read_scout_area` in `cotrainer/extract.py`; steht als `meta.scout_area` (Zahl) und `meta.scout_area_name` in den Daten; die Transfervorschläge filtern seit Teil 2b danach.
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
- Das Muster greift nicht bei `Trainertest .fm` (zwei Manager) und nicht bei den älteren Karrieren (Ndoye, Curaçao, China; ältere Spielversion). Dort meldet `cotrainer/extract.py` „nicht gefunden“.
- **Verworfen:** Der 4-Zeichen-Code in `scout_man` (`AcSP`/`blcP`) und der Filterblock daneben sind nicht das Scoutinggebiet. Sie gehören zur Spielersuche (Sortierspalte und ein Filter) und sind in allen Gebiets-Spielständen vom 10.11. gleich. Die Marken stehen rückwärts im Spielstand (`blcP` = `Pclb`, `manP` = `Pnam`, `frlp` = `plrf`).
- **Angrenzende Ligen (vom Nutzer am 10.11. genannt):** bei Ravenna (Serie C/B) sind das Serie B, Serie C und Serie D, also die eigene Spielklasse plus je eine Stufe darüber und darunter im selben Land. Nicht geklärt: ob bei „Serie C“ alle Staffeln gemeint sind (Annahme Claude: ja). Seit Teil 2b wird die Ligastufe aus der mittleren Vereinsreputation abgeleitet (Annahme, nicht bestätigt). Die Zuordnung Land → Region/Kontinent ist gelöst, siehe unten.
- **Ländernamen (10.11.):** `lang_db.dat`, Frame 64 (deutsch): Einträge `Datenbank-Nr.(4) len Name 00 len Kurzname 00 03 00 00 00 Kürzel len Adjektiv 00`, z. B. 776 Italien ITA, 769 Frankreich FRA, 771 Deutschland GER, 1657 Uruguay URU. 195 Länder so gelesen (Stand 10.11.; seit 15.11. alle 251 in `cotrainer/nations.py`, siehe Punkt 18). Die Nummern gruppieren sich grob nach Kontinent (Afrika 5–55, Asien 106–145, Nord-/Mittelamerika 359–389, Europa 752–802, Ozeanien 1435–1444, Südamerika 1649–1662), mit Ausreißern (z. B. Montenegro, Gibraltar, Monaco weit außerhalb). Regionennamen („Südeuropa“) stehen weder in `lang_db.dat` noch in `lang_db_general.dat`. fmsave liefert je Spieler `nation_id` und die Tabelle `nation_id → database_id`, aber keine Kontinente oder Regionen.
- **Kontinent und Region je Land (10.11., aus `game_db`):** Die Nationentabelle (251 Zeilen, Aufbau wie `NATION_TABLE` in fmsave, `_layouts/fm26_26_3_2.py`) lässt sich mit den dortigen 14 Schritten ablaufen. Im 9. Schritt (24 feste Bytes) stehen:
  - Byte 1 = **Kontinent**: 0 Afrika, 1 Asien (inkl. Australien), 2 Europa, 3 Nord-/Mittelamerika, 4 Ozeanien, 5 Südamerika, 255 keiner (aufgelöste Staaten u. Ä.). Stimmt bei allen geprüften Ländern.
  - Bytes 5–8 (u32) = **Regions-Nummer**, sehr wahrscheinlich das, was das Spiel als Region nimmt. Europa: 4 = Österreich, Belgien, Tschechien, Deutschland, Liechtenstein, Luxemburg, Polen …; 5 = Bulgarien, Ungarn, Rumänien, Serbien …; **11 = Albanien, Bosnien und Herzegowina, Kroatien, Italien, Malta, San Marino, Slowenien, Montenegro**; 12 = England, Nordirland, Irland, Schottland, Wales; 24 = Dänemark, Finnland, Island, Norwegen, Schweden; 25 = Andorra, Frankreich, Portugal, Spanien, Gibraltar; 26 = Armenien, Aserbaidschan, Zypern, Georgien, Griechenland, Nordmazedonien; 27 = Belarus, Estland, Lettland, Litauen, Russland. Südamerika: 21 = Argentinien, Brasilien, Chile, Paraguay, Uruguay; 22 = Bolivien, Kolumbien, Ecuador, Peru, Venezuela.
  - **Vom Nutzer am 10.11. bestätigt:** Das Scoutinggebiet „Südeuropa“ (Ravenna) ist genau Region 11. Scoutingstufe 5 („Region“) = alle Länder mit derselben Regions-Nummer wie das Land des eigenen Vereins; Stufe 6 („Kontinent“) = derselbe Kontinent-Code. Für andere Regionen als 11 ist das eine Übertragung, nicht einzeln geprüft.
  - Seit 15.11. haben alle 251 Länder einen deutschen Namen (`cotrainer/nations.py`, 502 Namen); der Fehler war, dass das Byte nach dem Namen ein Grammatik-Flag 0–4 ist und manche Einträge kein Kürzel haben.
  - Kosovo liegt laut Nationentabelle ebenfalls in Region 11 (Südeuropa), steht aber nicht in der Liste oben.
- Die Gebiets-Spielstände sind Build 27.0.1+2494687 (vorher 27.0.0+2493426).

## Getroffene Entscheidungen

- Der Spielstand wird **nur gelesen, nie verändert**.
- Das Programm schlägt den neuesten `.fm` des gemerkten Ordners vor. Im Konsolenlauf wird ohne Pfad der neueste `.fm` verwendet, außer `config.json` gibt mit `save` einen anderen vor.
- **CA, PA und versteckte Attribute** werden nur intern benutzt (Bewertung, Wechselchance, Marktwert). Die JSON-Ausgabe enthält sie nicht. Spielerqualität erscheint nur als Text (`pot`, `lvl`) bzw. als relative Einordnung (`rel`).
- **Wechselchance** ist eine eigene Schätzung (0–100). Sie berücksichtigt:
  - Abstand der Vereinsreputation (fmsave); im eigenen Leser gelten alle Vereine als gleich groß
  - Restlaufzeit des Vertrags, Alter, Vereinslosigkeit
  - Unbekannte Vereine gelten als neutral.
  - **Keine Persönlichkeit** (Ehrgeiz, Loyalität) und keine Spielerqualität: beides sieht man im Spiel ohne Scouting nicht (Entscheidung des Nutzers, 15.11.).
- **Stufe „Aus“, Sortierung „Empfehlung“, gemischt über die Ligen** (Entscheidung des Nutzers, 15.11.): `mixLeagues` in `index.html`; jeder weitere Spieler derselben Liga (Staffeln zusammengefasst, vereinslos und „ohne Liga“ je eine Gruppe) zählt `MIX_PEN` = 4 Punkte weniger. Ravenna, erste 80: Serie C 23, Serie BKT 19, ohne Liga 19, vereinslos 19 (vorher 80 × Serie C). Die anderen Sortierungen mischen nicht.
- **Schalter „Auch außerhalb meines Scoutinggebiets suchen“** (15.11., Spec 7.2): Python liefert zusätzlich eine kleinere Auswahl außerhalb des Gebiets (`OUT_VIS_POOL` 2000 ohne CA/PA, `OUT_QUALITY_POOL` 2000), markiert mit `out: true`, und `meta.scout_outside`. Die Oberfläche zeigt sie nur bei eingeschaltetem Schalter (`S.f.outside`, im `localStorage`), mit Markierung „außerhalb“. Einschalten zeigt denselben Hinweis wie die Stufen; „Nicht mehr fragen“ gilt für beide. Kein Schalter bei „Weltweit“ oder ohne erkanntes Gebiet. Ravenna: 73.021 Spieler außerhalb, 3.720 im Pool; `dev-data.json` wächst dadurch von 3,8 auf 6,8 MB.
- **Stufe „Scoutbericht“** zeigt keine Zahlen „Fit“ und „+ zur Startelf“; die gibt es nur in „Werte“ (Entscheidung des Nutzers, 15.11.).
- **Marktwert** ist eine eigene Schätzung: `2200·e^((CA−50)/12,5)` mit Faktoren für Alter, Vertrag und Liga. Es ist kein Spielwert.
- **Eigener Verein:** der Verein mit den meisten Spielern in den Trainingsbewertungen; sonst der Name aus `save_game_summary`.
- **Taktik:**
  - Positionen und Rollen kommen aus dem Spielstand, sobald dort eine eigene Taktik steht.
  - Teamanweisungen und Feedback kommen weiter aus `config.json`.
  - Ist eine Rolle unbekannt, wird eine Standardrolle eingesetzt und das Kürzel als „?“ angezeigt.
- **Teamanweisungen**, Stil und Tendenzen des Trainers stehen nur in `config.json` (aus Screenshots übernommen), weil sie noch nicht aus dem Spielstand gelesen werden. Das Programm selbst liest `config.json` nicht; die Trainerbewertungen kommen aus dem Spielstand.
- Die Oberfläche speichert eigene Rollenwahl, Filter, Wochenpläne und sichtbare Bereiche im `localStorage`, Schlüssel `cotrainer:<Verein>|<Manager>`. Die Wahl aus Schritt 3 überschreibt die sichtbaren Bereiche bei jedem Start.
- Die Oberfläche ist auf Deutsch, mit deutschen FM27-Begriffen.

## Offene Probleme

- **Paris-Spielstand ohne eigene Taktik:** In `tactics_man` stehen nur Formationsvorlagen. Das Programm nimmt dann die Standardformation 4-2-3-1 (`default_tactic`), ein Konsolenlauf mit `config.json` die Taktik von dort. Warum das so ist, ist ungeklärt.
- **Spielstände ohne gefundenen Kader:** Bei Nationaltrainer-Karrieren (Südkorea 2028, Curaçao) und bei zwei menschlichen Managern (`Trainertest .fm`) findet der Leser keinen eigenen Kader; das Programm meldet das im Klartext (`require_squad`). Bei den alten Karrieren greifen außerdem die Muster für Scoutinggebiet und teils Trainerwerte nicht.
- **Fester Port 47127** für die Oberfläche (`UI_PORT` in `app.py`): Ist er belegt, vergisst das Programm für diesen Lauf Rollenwahl, Filter und sichtbare Bereiche.
- **Nur 19 Rollen bekannt:** Bekannt sind nur die Rollen der aktuellen Taktik. Alle anderen erscheinen als „?“ mit Standardrolle. Der Rollentest läuft, siehe „Nächste Schritte“.
- **Zuordnung ZOM-Rolle unsicher:** Für die Rolle mit Ball am ZOM (Kürzel „F“) ist „Freie Rolle“ angenommen. Der genaue FM27-Name ist unbestätigt (in `lang_db` fehlen u. a. die IDs 1810, 1826, 1828–1833, 1848, 1870).
- **Unbekannter Einfluss der Spieleranweisungen:** Ob individuelle Spieleranweisungen die Unterblöcke verändern und damit den Fingerabdruck brechen, ist ungeprüft.
- **Fehlende Spieler:** Beim eigenen Leser (Rückfall) fehlen einzelne Spieler, z. B. Otávio und Ikoné bei Paris, und Leihspieler werden nicht immer erkannt. Mit fmsave als Quelle ist das gelöst.
- **Einlesen dauert rund zwei Minuten:** Beide Leser (fmsave und der eigene) entpacken den Spielstand je einmal.
- **Nicht ausgelesen werden:** Scoutingbudget, Staffattribute anderer Trainer, Teamanweisungen (fmsave liest Scoutingbudget und Staffattribute). Die Ligastufe wird nur aus der Vereinsreputation abgeleitet.
- **Trainertendenzen:** Die 15 Neigungen des eigenen Managers werden gelesen, stehen aber überall auf 10. Im Spiel ergeben sich die Tendenzen aus dem Führungsstil („Ihr Stil“: 3 Trainings-, 2 Mentalkarten); Co-Trainer lässt diese Karten pro Karriere auswählen (Teil 3). Ob die Wahl im Spielstand steht, ist offen.
- **Zielstrebigkeit und Streitlust des Managers ändern sich zwischen Spielständen ohne Zutun** (z. B. Paris: 14 → 10); Ursache unbekannt.
- **Torwartwahl:** Durch die Gewichtung „Ballspielender Torwart“ wählt das Programm bei Paris Nkambadio statt Trapp.
- **Spielstandwahl:** Backups sind ausgeschlossen, aber `find_save` nimmt weiterhin den neuesten Spielstand *jeder* Karriere (keine Einschränkung auf einen Manager).
- **Ungeprüfte Werte:** Das garantierte Mindestbudget für die nächste Saison ist nicht mit dem Spiel abgeglichen. Die Wechselchance ist eine Annahme (seit Teil 2b aus der Vereinsreputation).
- **Osijek-Kontostand:** Der Test prüft nur „> 0“, weil der Nutzer mit Osijek weiterspielt. Abgleich per Screenshot am 15.11.: 6,82 Mio. € im Spiel, gelesen 6.824.841 €; Transferbudget, Gehaltskosten (2,37 Mio. €/J.) und verfügbares Gehaltsbudget (248K €/J.) stimmen ebenfalls.
- **Ligen ohne Namen:** Einige Wettbewerbe heißen „Wettbewerb 6026“, „Wettbewerb 6027“ (u. a.), weil ihr Name in `lang_db` fehlt; sie erscheinen so in der Spalte „Liga“. „Testimonial“ (Abschiedsspiele) wurde als Liga erkannt und ist seit 15.11. in `CUP_WORDS` ausgeschlossen.
- **Spiel läuft:** Speichert das Spiel während des Einlesens, bricht fmsave ab (`SaveChangedError`) und der eigene Leser findet bei Osijek keinen Kader. Dann den Spielstand später neu einlesen.

## Nächste Schritte

### Als Nächstes (Stand 15.11. abends, `main` = Teile 1–4, Version 1.0.0, Release `v1.0.0` auf GitHub, 150 Tests grün)

1. ~~GitHub einrichten~~ erledigt am 15.11.: Remote `origin` = https://github.com/grimmok/Co-Trainer (privat, MIT-Lizenz aus GitHub übernommen), `main` verfolgt `origin/main`.
   - **Persönliche Daten aus der ganzen Historie entfernt** (Entscheidung des Nutzers, 15.11.): Autor und Committer heißen `grimmok` mit der noreply-Adresse `317344714+grimmok@users.noreply.github.com` (auch der von GitHub angelegte Startcommit); Benutzerpfade stehen als `%USERPROFILE%\…`, der Vorname ist entfernt. Danach Force-Push. `user.email` des Projekts steht auf der noreply-Adresse, `user.name` sollte für neue Commits ebenfalls `grimmok` sein. Die lokalen Zweige `backup-vor-noreply` und `backup-vor-grimmok` (und `refs/original`) halten die alten Stände mit den privaten Angaben; sie werden nie gepusht und können gelöscht werden.
   - `gh` ist weiter nicht angemeldet. Der Token steht in der Benutzervariable `GITHUB_PERSONAL_ACCESS_TOKEN`; Claude pusht damit über einen einmaligen `http.extraheader` (nichts gespeichert). Der GitHub-MCP-Server sieht den Token erst nach einem Neustart von Claude Code.
   - Das Repository bleibt privat, bis der Nutzer es selbst öffentlich schaltet (Entscheidung 15.11.). `config.json` (Karrieredaten aus dem Spiel, Entwicklerhilfe) ist eingecheckt.
2. ~~Teil 4~~ erledigt (Punkt 21): PR #1 gemergt, Release https://github.com/grimmok/Co-Trainer/releases/tag/v1.0.0 mit `Co-Trainer.exe` (12,1 MB, SHA-256 `49a46e96ee0c382ee1bf05e243a10fa73df88f6f08bbe0ad8174b03ce106a19b`). Das Repo ist privat; öffentlich schaltet der Nutzer selbst (dann sind README und Release für den Discord nutzbar). Für das nächste Release: Version in `pyproject.toml` und `cotrainer/__init__.py` erhöhen, `.\build.ps1`, `gh release create`.
3. **Rollentest (B.1)** hat Vorrang bei der Dekodierung: bei Osijek sind 17 von 22 Rollen unbekannt, bei „Ravenna 2 spieltaktik“ (5-2-3) 20.
4. **Vom Nutzer zu bestätigen:** siehe A.7 (offen: Konter-/Ballbesitz-Annäherungen der Stil-Codes, Karte → Tendenz bei `sure:false`, Bereiche und Baustellen-Grenze 0,3 gegen „Taktische Effektivität“, ob in „2 spieltaktik“ die 5-2-3-Taktik die Spieltaktik ist, Stufengrenzen der Trainerbewertungen, Name „Co-Trainer“).
5. ~~Zurückgestellte Kleinigkeiten aus Teil 3~~ erledigt (Punkt 20). Aufgefallen: Durchschnitte im Training und im Taktik-Reiter stehen mit Punkt statt Komma (z. B. „Ø 10.4“).
6. **Mögliche Verbesserungen:** Wechselchance für frisch gewechselte Spieler (`club_join_date` unklar), Ligen ohne Namen („Wettbewerb 6026“), „Kein Scouting“ (welche Spieler den Mitarbeitern bekannt sind), Zwischenspeicher fürs Einlesen.

### A. Umbau zum Programm „Co-Trainer“ (Vorrang)

Stand 15.11.: **Teile 1, 2, 2b und 3 sind gebaut und in `main`**, siehe „Was bisher gemacht wurde“ Punkte 15–19.

1. ~~Nutzer probiert `dist\Co-Trainer.exe` aus~~: Probelauf aus der `.exe` siehe Punkt 17, zuletzt am 15.11. mit Teil 2b neu gebaut und gestartet. Ursprüngliche Prüfliste:
   - erster Start zeigt Schritt 1 mit dem vorgeschlagenen Ordner (die echten Einstellungen in `%APPDATA%\Co-Trainer` sind noch nicht angelegt);
   - Ravenna bis zum Ergebnis, alle fünf Bereiche, Häkchen, „Hell/Dunkel“, „Neu einlesen“, „Spielstand wechseln…“;
   - Paris FC (ohne eigene Taktik → Standardformation 4-2-3-1);
   - ein Nationaltrainer-Spielstand (Südkorea 2028 oder Curaçao) → erwartet ist die Meldung „kein Kader des eigenen Vereins gefunden“ mit „Anderen Spielstand wählen…“;
   - Programm schließen und neu starten: Schritt 1 entfällt, Farbschema bleibt.
   - Windows zeigt beim ersten Start „Der Computer wurde durch Windows geschützt“, weil die `.exe` nicht signiert ist.
2. ~~Unabhängige Durchsicht des Codes~~ erledigt am 14.11., siehe „Was bisher gemacht wurde“ Punkt 16. Die Korrekturen stecken in der `.exe` (neu gebaut am 15.11.).
3. ~~Branch `programm-entwurf` nach `main` übernehmen~~ erledigt am 15.11. (in `main` gemergt).
4. **Zurückgestellte Kleinigkeiten aus Teil 1** (nur auf Wunsch des Nutzers):
   - Rollenbeschriftungen auf dem Spielfeld überlappen bei benachbarten Spielern (war schon in der alten Seite so).
   - `app.main` zeigt die WebView2-Meldung bei jedem Startfehler, auch bei einem anderen.
   - Die nachgestellte `Api` des Entwicklermodus (`?dev=1`, rund 12 Zeilen) wird mit ausgeliefert.
   - Alte Spielstände (China 2028) brauchen rund 160 s; es gibt keinen Zwischenspeicher.
   - Die Wahl aus Schritt 3 überschreibt bei jedem Start die gemerkten sichtbaren Bereiche (so im Plan; ggf. die letzte Wahl vorbelegen).
5. **Danach je einen Plan schreiben und bauen** (Skill `superpowers:writing-plans`, dann `superpowers:executing-plans`):
   - ~~Teil 2~~ gebaut (fmsave als Datenquelle, Kader nur erste Mannschaft, Nationalität, Scoutinggebiet als Filter, drei Informationsstufen; Punkte 17 und 18), bis auf die Bestätigungen unter Punkt 7.
   - ~~Teil 3: neuer Taktik-Reiter~~ gebaut am 15.11. (Punkt 19)
   - Teil 4: README, Lizenzhinweise, GitHub-Release.
   - Für den Plan von Teil 2 geklärt (Punkt 16): fmsave löst weder Nationaltrainer noch zwei Manager; die Meldung `require_squad` und der eigene Leser als Rückfall bleiben. Gepackt wird fmsave über `build.ps1` (siehe Punkt 17).
6. **Für Teil 2 noch zu dekodieren:**
   - ~~Ligastufe je Wettbewerb~~ (aus Reputation abgeleitet, Bestätigung offen), ~~56 Länder ohne Namen~~ und ~~Nationentabelle~~ erledigt in Teil 2b.
   - Optional: welche Spieler den Mitarbeitern bekannt sind (für „Kein Scouting“; bis dahin gilt die Regel „vertragslose Spieler der Vereinsnation“).
7. **Vom Nutzer zu bestätigen, wenn es sich ergibt:**
   - ~~Taktik: ob man im Spiel Platz 2 oder 3 als Spieltaktik wählen kann~~ geklärt: ja, der Index vor dem ersten Kopf zeigt es (Beleg „Ravenna 2 spieltaktik“, 15.11.);
   - Taktik: ob die Annäherungen Ballbesitzspiel → Tiki-Taka und Konter-Stile (ERID, ETAC, KRAP, IULF) → Konterfußball passen;
   - ~~ob bei „Angrenzende Ligen“ alle Serie-C-Staffeln gemeint sind~~ und ~~Ligastufe aus Reputation~~: vom Spiel bestätigt (Screenshot 15.11.): Ravenna „Angrenzende Ligen“ = „Serie BKT, Serie C, LND“ (LND = Serie D, nicht spielbar), „Serie C“ = „Spieler in unserer Liga“. Seitdem umfasst auch „Eigene Liga“ alle Staffeln (vorher nur die eigene);
   - ~~Regionen~~ am 15.11. mit der Nationenliste des Editors abgeglichen (Screenshots in `%USERPROFILE%\Pictures\fm tool\region`, 212 von 251 Ländern abgeschrieben): alle 24 Regionen stimmen, jede Region hat genau einen Code, alle Kontinente stimmen, Kosovo (217945) liegt in Südeuropa. „Eindeutige ID“ im Editor = Datenbank-Nr. im Programm (13 = Zentralafrikanische Rep.). Codes: 2 Karibik, 3 Zentralamerika, 4 Mitteleuropa, 5 Osteuropa, 6 Naher Osten, 7 Nordafrika, 8 Nordamerika, 9 Ozeanien, 11 Südeuropa, 12 Großbritannien & Irland, 13 Zentralasien, 14 Ostasien, 15 Südasien, 16 Südostasien, 17 Westafrika, 18 Zentralafrika, 19 Ostafrika, 20 Südliches Afrika, 21 Südamerika (Süd), 22 Südamerika (Nord), 24 Nordeuropa, 25 Westeuropa, 26 Südosteuropa, 27 Nordosteuropa;
   - ~~neue Wechselchance (aus Vereinsreputation)~~ vom Nutzer am 15.11. im Spiel bestätigt (Ravenna): Spaggiari 83 % → bereit zu Gesprächen, Luzi 49 % → will mehr. Ausnahme Finotti (49 %): „nicht interessiert, noch nicht lange bei meinem neuen Verein“ (im Juli gewechselt). Frisch gewechselte Spieler kennt die Wechselchance noch nicht. fmsave hat `Player.club_join_date`, aber im Ravenna-Spielstand (Spieldatum 8.8.2026) steht bei Finotti 1.9.2026 (Spiel: „im Juli gewechselt“) und bei Luzi 1.8.2026 (trotzdem verhandlungsbereit). Bedeutung des Felds unklar, deshalb noch nicht eingebaut;
   - ~~neuer Screenshot der Osijek-Finanzen~~ (15.11., stimmt);
   - Angrenzende Ligen bei Osijek laut Spiel: „HNL und 1. NL“ (eigene Liga plus eine darunter, darüber gibt es keine). Passt zur Regel „Stufe ± 1“; ob das Programm genau diese beiden Ligen wählt, ist mit Osijek noch nicht geprüft;
   - ~~der Schalter „Auch außerhalb meines Scoutinggebiets suchen“~~ gebaut am 15.11. (siehe „Getroffene Entscheidungen“).
   - ~~Stil-Code `TREV` = Vertikales Tiki-Taka~~ bestätigt durch den Spielstand „Ravenna vert tiki taka“ (15.11.);
   - Taktik: Zuordnung Karte → Tendenz bei den Karten mit `sure:false` prüfen;
   - Taktik: ob der gewählte Führungsstil im Spielstand steht (dann könnte Co-Trainer ihn lesen);
   - Taktik: Einschätzung der Bereiche mit dem Bildschirm „Taktische Effektivität“ im Spiel vergleichen. Mit den Grenzen 13/11 hat Ravenna keinen schwachen Bereich (alle „mittel“, 11,4–12,2); seit der Korrekturrunde zählen deshalb auch „Baustellen“ (Spieler unter 11, mindestens 0,3 unter dem Schnitt): bei Ravenna Passstil und Spielaufbau. Der Nutzer soll beurteilen, ob das zum Spiel passt oder Grenzen und 0,3 geändert werden müssen;
   - Taktik: ob in „Ravenna 2 spieltaktik“ die Taktik „5-2-3 DM Breit (Kontrolliert) – Ballbesitzspiel“ die Spieltaktik ist (so liest es Co-Trainer);
   - Stufengrenzen der Trainerbewertungen unterhalb von 18 (bisher nur aus Profil-Screenshots abgeleitet);
   - ob der Name „Co-Trainer“ frei ist (nicht geprüft).

Entscheidungen des Nutzers vom 10.11. (alle im Design-Dokument eingearbeitet): Design samt „Entscheidungen von Claude“ freigegeben; Programmname „Co-Trainer“ (`Co-Trainer.exe`), weil „FM Scout“ eine große FM-Website ist; Trainerbewertungen bleiben im Taktik-Reiter; Trainertendenzen per Auswahl pro Karriere; bei „Kein Scouting“ trotzdem Vorschläge (bevorzugt vertragslose Spieler der Vereinsnation, auch schwächere). Der Ordner und das Repo heißen weiter `fmscout`; die Dateien sind seit Teil 1 umbenannt.

Der Nutzer hat jetzt den **Ingame-Editor** (muss beim Anlegen eines Spielstands aktiviert sein; Testkarriere `Haribaert Kachinski – Paris FC test.fm`, Testspielstände `Trainertest 2 …`). Damit lassen sich Werte gezielt setzen und im Spielstand wiederfinden. Das Vorgehen hat sich bewährt: Ausgangsstand speichern, auffällige, verschiedene Werte setzen (3, 5, 7 …), Screenshot, unter neuem Namen speichern, ohne einen Tag weiterzuspielen.

### B. Dekodierung und Datenqualität (laufend)

1. **Rollentest abschließen.** Ablauf:
   - Der Nutzer benennt eine Kopie seiner Taktik in „Test 1“ (dann „Test 2“ usw.) um.
   - Er stellt an allen Positionen neue Rollen ein, mit Ball und gegen den Ball. Doppelte Positionen bekommen zwei verschiedene Rollen.
   - Spieleranweisungen bleiben unverändert.
   - Er speichert und schickt die ausgefüllte Liste (TW, RV, IV rechts, IV links, LV, DM, ZM, ZOM, RA, LA, ST jeweils „mit Ball / gegen den Ball“).
   - Mit dem Ingame-Editor geht das jetzt schneller (Testkarriere statt echter Karriere).
   - Danach `FMS_ROLES=1` setzen und `python -m cotrainer.extract` laufen lassen; die Zeilen der Taktik „Test N“ mit der Liste abgleichen und die neuen Fingerabdrücke in `ROLE_FP` eintragen.
   - Fehlende Rollen in `ROLES` in `cotrainer/ui/index.html` ergänzen, mit Schlüsselattributen laut FM27.
   - Geplant sind 4–5 Durchgänge, am Ende einer mit anderer Formation (z. B. 3-4-3) für Flügelverteidiger, Libero sowie RM/LM mit Ball.
2. Prüfen, ob Spieleranweisungen den Fingerabdruck verändern. Falls ja: nur die rollenbestimmenden Unterblöcke vergleichen.
3. Teamanweisungen aus dem Kopf der Taktik dekodieren (Stil-Code ist erledigt). Aufbau nach dem Namen: 12×`00`, 16 Byte Einstellungen, `00 00 ff`, `len u32`, Stilname, Code4. Bisher gesehen:
   - „Taktik“ (Gegenpressing): `04 01 04 07 02 03 80 00 00 00 0a 40 50 22 62 90`
   - „4-1-1-3-1 … Tiki-Taka“: `04 03 04 07 02 03 88 10 8a 10 0a 10 61 22 64 80`
   - Wirkt bitgepackt. Zum Dekodieren: Kopie einer Taktik, jeweils **eine** Anweisung ändern, speichern, vergleichen.
4. Kaderfilter für die erste Mannschaft über `squad_status` aus fmsave; fehlende Spieler (Otávio, Zagré, Ilari, Vinícius) und Leihspieler sind mit fmsave gelöst.
5. ~~Spielstandwahl~~, ~~Scoutinggebiet~~, ~~Persönlichkeitsreihenfolge~~, ~~Trainerbewertungen~~ erledigt (10.11.).
6. Verhandlungsgeschick und Taktische Kenntnisse des Managers zuordnen (Attribute 7 und 23 im Staff-Block, per Editor-Test mit zwei verschiedenen Werten).
