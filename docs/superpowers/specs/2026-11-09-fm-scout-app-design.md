# Co-Trainer (bisher „FM-Scout“) als eigenständiges Programm – Design

Stand: 10.11.2026 (erstellt 09.11.) · Grundlage: Gespräch mit dem Nutzer · Projektwissen: `HANDOFF.md`, `CLAUDE.md`

## 1. Absicht und Warum

Co-Trainer liest einen Football-Manager-27-Spielstand und hilft, Kader, Taktik, Transfers und Training zu verbessern. Heute ist es ein Python-Skript (`extract.py`), das über eine Batch-Datei gestartet wird und eine 4-MB-HTML-Datei (`FM-Scout.html`) erzeugt, die dann im Browser geöffnet wird.

Der Nutzer will **ein einziges Programm**: Doppelklick, ein Fenster, fertig – keine Batch-Datei, keine erzeugte HTML-Seite, kein Python-Wissen nötig. Das Programm soll **öffentlich auf GitHub** liegen und von anderen FM-Spielern (z. B. aus einem Discord) benutzt werden.

Ein zweiter, gleich wichtiger Grund: Co-Trainer darf das **Spielerlebnis nicht ungewollt verändern**. Wer genaue Werte ungescouteter Spieler sieht, spielt ein anderes, leichteres Spiel. Deshalb ist alles, was über das im Spiel ohne Scouting Sichtbare hinausgeht, standardmäßig aus und nur bewusst, mit Hinweis, einschaltbar.

## 2. Ziele

1. Ein Windows-Programm `Co-Trainer.exe`, das ohne installiertes Python läuft und als Release auf GitHub verteilt wird.
2. Geführter Start: Spielstand-Ordner → letzten Spielstand bestätigen → Analyse wählen → Ergebnis.
3. Sechs Bereiche, jederzeit einzeln ein- und ausblendbar: Kaderanalyse, Transfervorschläge, Taktik, Training, Kaderliste (plus „Alles“ als Startwahl).
4. Transfervorschläge mit dreistufiger Informationstiefe (Aus / Scoutbericht / Werte), Standard „Aus“.
5. Neuer Taktik-Reiter, der **Schwachstellen der eigenen Taktik** zeigt, **wer sie verursacht** und **was hilft**.
6. Moderne, übersichtliche Oberfläche, dunkel als Standard, umschaltbar auf hell.
7. Funktioniert für jeden Nutzer ohne Handarbeit (keine `config.json` pflegen).

## 3. Nicht-Ziele

- Keine englische Oberfläche (vorerst nur Deutsch, mit deutschen FM27-Begriffen).
- Kein macOS/Linux (vorerst nur Windows).
- Keine Bewertung „Infos zum nächsten Spiel“ (Gegnerbericht) – gehört nicht zu Co-Trainer.
- Kein Schreiben in Spielstände, kein Ändern von Spieldateien.
- Keine Online-Funktionen: kein Upload, keine Telemetrie, kein Server.

## 4. Anti-Ziele (wäre ein Fehlschlag, auch wenn es technisch läuft)

- **Unübersichtlich**: zu viele Zahlen, Tabellen ohne Hierarchie, man findet die eigentliche Aussage nicht.
- **Altbacken**: klassische Windows-Formulare, graue Standard-Steuerelemente.
- **Spoiler ohne Zustimmung**: CA, PA oder versteckte Attribute erscheinen irgendwo; Werte oder Qualitätseinschätzungen fremder Spieler sind sichtbar, ohne dass der Nutzer es bewusst eingeschaltet hat.
- Ein Spielstand wird verändert.

## 5. Feste Regeln (aus `CLAUDE.md`, gelten unverändert)

- **CA, PA und versteckte Attribute** (Cons, Dirt, ImpM, InjPr, Vers) erscheinen nie in der Oberfläche und verlassen nie den Python-Teil Richtung Oberfläche. Nur interne Rechnung.
- **Potenzial** nur als Text („Kann sich zu einem guten Zweitliga-Spieler entwickeln“), nie als Zahl.
- **Spielstände nur lesen.**
- **Geld**: im Spielstand GBP, Anzeige in EUR, Faktor 1,1641.
- **Neu dekodierte Werte** gelten erst nach Abgleich mit Screenshots des Nutzers als korrekt.
- **Neue Rollen-Fingerabdrücke** nur nach Bestätigung durch den Nutzer.

## 6. Ablauf aus Nutzersicht (vom Nutzer so festgelegt)

Entwürfe: `.superpowers/brainstorm/ablauf-v2.html`, `transfer-werte.html`, `stil-v2.html` (lokal, nicht im Repo).

1. **Spielstand-Ordner festlegen** – nur beim ersten Start. Vorschlag: `Dokumente\Sports Interactive\Football Manager *\games` (der Ordner heißt beim Nutzer „Football Manager 26“, obwohl FM27). Anzeige, wie viele Spielstände gefunden wurden. Der Ordner wird gemerkt; „Ordner ändern“ bleibt in den Einstellungen erreichbar.
2. **Letzten Spielstand bestätigen** – der neueste Spielstand wird vorgeschlagen (Name, Speicherzeit, Verein, Spieldatum), mit „Ja, laden“ und „Anderen Spielstand wählen…“. Sicherungen (`backup`, `autosave`) sind ausgeblendet.
3. **Analyse wählen** – „Alles“, „Nur Kaderanalyse“, „Nur Transfervorschläge“, „Nur Taktik“, „Nur Trainingsvorschlag“, „Nur Kaderliste“. Das ist nur der Startzustand.
4. **Ergebnis** – die gewählten Bereiche erscheinen. Jeder Bereich lässt sich jederzeit ein- und ausblenden. Zusätzlich erreichbar: Spielstand wechseln, neu einlesen, hell/dunkel, Einstellungen.

Während des Einlesens (bisher 30–90 s je nach Spielstand) zeigt das Programm einen Fortschritt mit Klartext-Schritten („Spieler werden gelesen …“), damit es nicht hängend wirkt.

## 7. Die Bereiche

Die bestehende Logik aus `extract.py` und `app.html` bleibt die Grundlage; Unterschiede sind hier beschrieben.

### 7.1 Kaderanalyse
Wie bisher: Spielfeld mit bester Elf zur Taktik, Rollen mit/gegen den Ball, Schwachstellen. Werte der **eigenen** Spieler dürfen sichtbar sein (sieht man im Spiel auch).

### 7.2 Transfervorschläge – drei Stufen (vom Nutzer so festgelegt)

| Stufe | Sichtbar | Sortierung |
|---|---|---|
| **Aus** (Standard) | Name, Alter, Positionen, Verein, Liga, Vertragsende, Wechselchance, **Grund für den Vorschlag** | nur nach im Spiel ohne Scouting sichtbaren Kriterien |
| **Scoutbericht** | zusätzlich Stärken/Schwächen als Text, Potenzial-Text, Einordnung („stärker als dein Kader“) | nach Qualität und Taktik-Passung |
| **Werte** | Attributwerte statt Stärken/Schwächen-Text; Potenzial-Text und Einordnung bleiben | nach Qualität und Taktik-Passung |

- **Gründe in Stufe „Aus“** stützen sich nur auf Sichtbares, z. B. „Spielt Rechtsaußen – dort ist deine schwächste Position“, „Vertrag läuft 06/2027 aus“, „Ablösefrei“, „Kommt aus einer schwächeren Liga – Wechsel wahrscheinlich“, „Jung (19) – Platz zum Entwickeln“.
- **Sortierung in Stufe „Aus“** nach sichtbaren Kriterien: Position passt zu einer Schwachstelle, Alter, Vertragsende/ablösefrei, Wechselchance, Liga/Vereinsstärke. Nicht zufällig.
- **Beim Wechsel auf eine höhere Stufe** erscheint ein Hinweis, dass dies das Spielerlebnis verändert bzw. vereinfacht, mit „Trotzdem einblenden“ / „Abbrechen“ und „Nicht mehr fragen“.
- **Wichtig:** In Stufe „Aus“ darf auch indirekt nichts verraten werden – weder über die Reihenfolge noch über Texte, Farben oder Filter, die aus CA/PA oder Attributen abgeleitet sind.
- **Vorauswahl über das Scoutinggebiet** (vom Nutzer so beschrieben): In FM27 stellt man ein Scoutinggebiet ein (sieben Stufen: Kein Scouting / Eigene Liga / Angrenzende Ligen / Eigenes Land / Region / Kontinent / Weltweit). Die Spielerdatenbank im Spiel zeigt dann automatisch die Spieler dieses Gebiets und lässt nach Wechselbereitschaft filtern. Was das Spiel so offen zeigt, darf Co-Trainer auch zeigen: Die Transfervorschläge enthalten nur Spieler aus dem eingestellten Scoutinggebiet; die Wechselchance darf in Stufe „Aus“ erscheinen. Die bisherige Vorauswahl über CA/PA entfällt dadurch weitgehend.
- *(Annahme Claude)* Ein Schalter „Auch außerhalb meines Scoutinggebiets suchen“ ist eine weitere bewusste Abkürzung mit demselben Hinweis wie die Stufen.

### 7.3 Taktik (ersetzt „Trainer & Taktik“; vom Nutzer so festgelegt)
Ziel: **Wo sind die Schwachstellen meiner Taktik, und wer verursacht sie?** – das, was der FM27-Bildschirm „Taktische Effektivität“ nicht sagt.

- Oben: Taktik aus dem Spielstand – Formation, Rollen mit und gegen den Ball, Spielstil (z. B. „Gegenpressing“, gelesen aus dem Taktikkopf).
- Darunter Bereiche angelehnt an FM27: Formation mit Ball, Passstil, Spielaufbau, Chancen kreieren, Formation ohne Ball, Pressinglinie, Pressingintensität, Pressingfalle. Pro Bereich eine Einschätzung (z. B. gut/mittel/schwach) aus den Attributen der eingesetzten Spieler und ihrer Rollen.
- Bei schwachen Bereichen: **wer** (Spieler + Position + verantwortliche Attribute mit Wert, eigener Kader) und **was hilft** (Rolle ändern, im Training fördern, Transfer).
- Verknüpfung: Schwache Bereiche werden Fokus im Trainingsvorschlag und Suchkriterium bei Transfervorschlägen.
- **Trainertendenzen** (z. B. „Spielt offensiven Fußball“, „Taktiktüftler“) fließen ein, weil FM27 sie bei der Spielerüberzeugung berücksichtigt; Hinweis, wenn Taktik und Tendenzen sich widersprechen. Herkunft siehe 8.3.
- **Trainerbewertungen** (Offensive, Defensive, Fitness, Torhüter, Ballbesitz, Standardsituationen, Taktik, Techniken, Nachwuchsarbeit sowie Anpassungsfähigkeit, Autorität, Zielstrebigkeit, Motivationsfähigkeit, Führungsqualitäten) bleiben im Taktik-Reiter *(vom Nutzer am 10.11. entschieden)*. Sie werden aus dem Spielstand gelesen und als Textstufe wie im Spiel gezeigt: Sehr schlecht (bis 6), Schlecht (7–9), Durchschnitt (10–11), Gut (12–15), Sehr gut (16–17), Herausragend (18–19), Elite (20). Schwache Bewertungen, die die gewählte Taktik braucht, erscheinen als Hinweis.
- Kein Trainerprofil-Formular mehr: Der Nutzer tippt keine Bewertungen ein.

### 7.4 Training
Wie bisher (Wochenplan mit echten FM27-Einheiten, Trainingsbewertungen, gespeicherte Wochenpläne), zusätzlich mit Fokus auf die schwachen Taktikbereiche aus 7.3.

### 7.5 Kaderliste
Wie bisher.

## 8. Daten

### 8.1 Lesen
- **fmsave** (https://github.com/rhiever/fmsave, MIT, lokal unter `%USERPROFILE%\Projekte\fmsave`) wird Hauptquelle für Spieler, Verträge, Vereine, Finanzen, Wettbewerbe, Training. Abgleich am 09.11. (siehe `HANDOFF.md`): bei allen gemeinsam gefundenen 51.208 Spielern identische CA/PA, Attribute, Positionen; Kontostand und alle vier per Screenshot geprüften Verträge identisch; fmsave findet 86.402 statt 51.210 Spieler, liefert Kaderstatus, Leihen, Scoutingbudget und die korrekte Persönlichkeitsreihenfolge.
- **Eigener Leser bleibt** für Taktik (Rollen-Fingerabdrücke `ROLE_FP`, Stil-Code) und als Rückfall: fmsave scheitert z. B. an einem Spielstand mit zwei menschlichen Managern („summary does not fit its structured clock layout“) und kennt den Build des Nutzers (27.0.0+2493426) nur als „unverified“.
- Wettbewerbs- und Rollennamen weiter aus `lang_db.dat` der Spielinstallation (automatisch gesucht, sonst nachfragen).
- fmsave braucht Python ≥ 3.12; das gebündelte Programm bringt es mit.

### 8.2 Was ersetzt `config.json`
- Spielstand-Ordner, Spielinstallation, hell/dunkel, Informationsstufe, „Nicht mehr fragen“: Programmeinstellungen des Nutzers (z. B. in `%APPDATA%\Co-Trainer`).
- Pro Karriere: eigene Rollenwahl, Filter, gespeicherte Wochenpläne, Trainertendenzen (falls von Hand gesetzt).
- `config.json` des Repos entfällt für Endnutzer.

### 8.3 Trainertendenzen
Der Nutzer wählt sie einmal pro Karriere aus einer Liste (≈ 5 Klicks) *(vom Nutzer am 10.11. entschieden)*. Ohne Angabe entfällt nur der Tendenzen-Hinweis. Grund: Die 15 Neigungen sind zwar im Spielstand lesbar, stehen beim menschlichen Manager aber in allen geprüften Karrieren auf dem Startwert 10 und erklären die im Spiel angezeigten Tendenzen nicht.

### 8.4 Trainerbewertungen
Aus dem Staff-Block des menschlichen Managers in `game_db` (`read_coach` in `extract.py`; Zuordnung per Ingame-Editor-Test und Screenshots für Ravenna und Paris bestätigt, siehe `HANDOFF.md`). Wird der Block nicht gefunden, entfällt der Abschnitt im Taktik-Reiter.

### 8.5 Bekannte Korrektur
Persönlichkeitsreihenfolge ist Anpassung, Ehrgeiz, Loyalität, Druck, Professionalität, Sportsgeist, Temperament, Kontroversität (bisher falsch angenommen; `willingness()` las Druck statt Loyalität). Am 10.11. mit Screenshot (Viola, „Professionell“) abgeglichen und in `willingness()` korrigiert.

## 9. Gestalt und Technik (Entscheidung von Claude, nicht vom Nutzer)

- Ein natives Programmfenster, dessen Oberfläche mit Web-Technik gezeichnet wird (Windows-eigene Edge-WebView2), Python im Hintergrund – so lässt sich die vorhandene Oberfläche aus `app.html` weiterverwenden und modern gestalten.
- Ausgeliefert als **eine** `Co-Trainer.exe` (alles gebündelt), als GitHub-Release; Quellcode im Repo.
- Keine erzeugte HTML-Datei auf der Festplatte, keine Batch-Datei.
- Stil (vom Nutzer gewählt): **„Dunkel & neutral“** – fast schwarzer Hintergrund, Karten mit dezentem Rand, ein türkisgrüner Akzent, gelb/orange für Warnungen. Umschaltbar auf **„Hell & klar“** – weiß, grüne Akzente. Wahl wird gespeichert.
- Lizenzhinweis für fmsave (MIT) im Programm und im Repo.

## 10. Dem Builder überlassen

- Konkrete Bibliotheken für Fenster und Bündelung, Projektstruktur, Build-Skript und Release-Ablauf.
- Wie Python und Oberfläche Daten austauschen (die Regel aus Abschnitt 5 muss dabei gelten: CA/PA/versteckte Werte erreichen die Oberfläche nie).
- Formeln für die Bereichs-Einschätzungen in 7.3 (welche Attribute pro Bereich und Rolle), solange sie nachvollziehbar und begründbar sind.
- Ob das Einlesen im Hintergrund zwischengespeichert wird, um den zweiten Start zu beschleunigen.
- Tests und Prüfungen, mit echtem Spielstand des Nutzers als Abnahme.

### Entscheidungen von Claude (vom Nutzer am 10.11. bestätigt)

- **fmsave** wird als veröffentlichtes Paket in fester Version eingebunden (nicht der lokale Klon); Updates bewusst.
- **`extract.py`** bleibt als Modul für die Leselogik erhalten; die alte Ausgabe als HTML-Datei und `FM-Scout starten.bat` entfallen.
- Der bisherige Inhalt von „Trainer & Taktik“ (Rangliste der Spielstile nach Kaderpassung) wandert in den Taktik-Reiter als Vorschlag „Diese Spielstile passen besser zu deinem Kader“.
- Die gewählte Informationsstufe der Transfervorschläge wird gespeichert und gilt beim nächsten Start weiter.
- Die `.exe` ist anfangs **nicht signiert**; Windows zeigt beim ersten Start „Der Computer wurde durch Windows geschützt“. Die README erklärt, wie man trotzdem startet.
- Lizenz des Co-Trainer-Repos: **MIT** (wie fmsave). Kann der Nutzer ändern.
- Die Transferliste zeigt eine überschaubare Zahl an Vorschlägen (z. B. die besten 50 je Filter) statt Tausender Zeilen – gegen „unübersichtlich“.

## 11. Offene Punkte

- **Scoutinggebiet:** Auslesen ist gelöst (10.11., siehe `HANDOFF.md`): sieben Stufen – Kein Scouting, Eigene Liga, Angrenzende Ligen, Eigenes Land, Region, Kontinent, Weltweit. „Angrenzende Ligen“ sind laut Nutzer die eigene Spielklasse plus je eine Stufe darüber und darunter (Ravenna: Serie B, Serie C, Serie D); dafür muss die Ligastufe noch aus dem Spielstand gelesen werden. Offen ist außerdem, und woran man im Spielstand erkennt, welche Spieler den Mitarbeitern bekannt sind: Bei „Kein Scouting“ zeigt das Spiel laut Nutzer nur diese. **Bei „Kein Scouting“ gibt es trotzdem Vorschläge** *(vom Nutzer am 10.11. entschieden)*: bevorzugt vertragslose Spieler mit der Nationalität des Landes, in dem der eigene Verein spielt. Dass darunter auch zu schwache Spieler sind, nimmt der Nutzer in Kauf. *(Auslegung Claude: „der Nation angehören“ = Nationalität des Vereinslandes; weitere Gruppen kommen erst dazu, wenn die Bekanntheit bei den Mitarbeitern lesbar ist.)*
- **Ländernamen und Nationalität:** fmsave liefert je Spieler die Nation (spielstandinterne Nummer) und dazu die Datenbank-Nummer. Die deutschen Ländernamen mit Kürzel stehen in `lang_db.dat` (Frame 64, z. B. 776 = Italien/ITA, 769 = Frankreich/FRA). Die Nummern liegen grob nach Kontinent beieinander (Afrika 5–55, Asien 106–145, Nord-/Mittelamerika 359–389, Europa 752–802, Ozeanien 1435–1444, Südamerika 1649–1662), aber mit Ausreißern; als Zuordnung reicht das nicht. Kontinent und eine Regions-Nummer je Land stehen in der Nationentabelle des Spielstands (gefunden am 10.11., siehe `HANDOFF.md`); der Nutzer hat bestätigt, dass „Südeuropa“ genau Italiens Regionsgruppe ist (Italien, Malta, San Marino, Slowenien, Kroatien, Bosnien und Herzegowina, Albanien, Montenegro).
- **Name des Programms: „Co-Trainer“** *(vom Nutzer am 10.11. gewählt)*. Der frühere Arbeitstitel „FM-Scout“ entfällt, weil „FM Scout“ eine große FM-Website ist. Ob der Name anderweitig vergeben ist, wurde nicht geprüft. Ordner, Repo und die bestehenden Dateien (`FM-Scout.html`, `FM-Scout starten.bat`) heißen bis zum Umbau weiter wie bisher.
- Ob die Hintergrundrechnung in Stufe „Aus“ weiterhin CA/PA nutzen darf (z. B. damit nicht viel zu schwache Spieler oben stehen), ist mit dem Scoutinggebiet weniger dringend, aber nicht abschließend geklärt.
- **Freigabe:** Der Nutzer hat das Design am 10.11.2026 freigegeben, einschließlich der „Entscheidungen von Claude“ in Abschnitt 10. Die übrigen Punkte dieses Abschnitts bleiben offen und werden beim Bau geklärt.
- Teamanweisungen (16 Byte im Taktikkopf) sind nicht dekodiert; bis dahin zeigt der Taktik-Reiter keine Teamanweisungen.
- Rollentest für weitere Rollen-Fingerabdrücke steht weiter aus (siehe `HANDOFF.md`).
