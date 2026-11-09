# FM-Scout als eigenständiges Programm – Design

Stand: 09.11.2026 · Grundlage: Gespräch mit dem Nutzer · Projektwissen: `HANDOFF.md`, `CLAUDE.md`

## 1. Absicht und Warum

FM-Scout liest einen Football-Manager-27-Spielstand und hilft, Kader, Taktik, Transfers und Training zu verbessern. Heute ist es ein Python-Skript (`extract.py`), das über eine Batch-Datei gestartet wird und eine 4-MB-HTML-Datei (`FM-Scout.html`) erzeugt, die dann im Browser geöffnet wird.

Der Nutzer will **ein einziges Programm**: Doppelklick, ein Fenster, fertig – keine Batch-Datei, keine erzeugte HTML-Seite, kein Python-Wissen nötig. Das Programm soll **öffentlich auf GitHub** liegen und von anderen FM-Spielern (z. B. aus einem Discord) benutzt werden.

Ein zweiter, gleich wichtiger Grund: FM-Scout darf das **Spielerlebnis nicht ungewollt verändern**. Wer genaue Werte ungescouteter Spieler sieht, spielt ein anderes, leichteres Spiel. Deshalb ist alles, was über das im Spiel ohne Scouting Sichtbare hinausgeht, standardmäßig aus und nur bewusst, mit Hinweis, einschaltbar.

## 2. Ziele

1. Ein Windows-Programm `FM-Scout.exe`, das ohne installiertes Python läuft und als Release auf GitHub verteilt wird.
2. Geführter Start: Spielstand-Ordner → letzten Spielstand bestätigen → Analyse wählen → Ergebnis.
3. Sechs Bereiche, jederzeit einzeln ein- und ausblendbar: Kaderanalyse, Transfervorschläge, Taktik, Training, Kaderliste (plus „Alles“ als Startwahl).
4. Transfervorschläge mit dreistufiger Informationstiefe (Aus / Scoutbericht / Werte), Standard „Aus“.
5. Neuer Taktik-Reiter, der **Schwachstellen der eigenen Taktik** zeigt, **wer sie verursacht** und **was hilft**.
6. Moderne, übersichtliche Oberfläche, dunkel als Standard, umschaltbar auf hell.
7. Funktioniert für jeden Nutzer ohne Handarbeit (keine `config.json` pflegen).

## 3. Nicht-Ziele

- Keine englische Oberfläche (vorerst nur Deutsch, mit deutschen FM27-Begriffen).
- Kein macOS/Linux (vorerst nur Windows).
- Keine Bewertung „Infos zum nächsten Spiel“ (Gegnerbericht) – gehört nicht zu FM-Scout.
- Kein Schreiben in Spielstände, kein Ändern von Spieldateien.
- Keine Online-Funktionen: kein Upload, keine Telemetrie, kein Server.
- Trainerbewertungen des menschlichen Managers (Offensive, Taktik, Torhüter …) werden **nicht** gelesen: Ein Testspielstand mit zwei Trainern unterschiedlicher Lizenz hat gezeigt, dass das Spiel sie sehr wahrscheinlich berechnet statt speichert.

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
- **Vorauswahl über das Scoutinggebiet** (vom Nutzer so beschrieben): In FM27 stellt man ein Scoutinggebiet ein (Weltweit / Europa / Südeuropa / Italien – vermutlich Kontinent / Region / eigenes Land). Die Spielerdatenbank im Spiel zeigt dann automatisch die Spieler dieses Gebiets und lässt nach Wechselbereitschaft filtern. Was das Spiel so offen zeigt, darf FM-Scout auch zeigen: Die Transfervorschläge enthalten nur Spieler aus dem eingestellten Scoutinggebiet; die Wechselchance darf in Stufe „Aus“ erscheinen. Die bisherige Vorauswahl über CA/PA entfällt dadurch weitgehend.
- *(Annahme Claude)* Ein Schalter „Auch außerhalb meines Scoutinggebiets suchen“ ist eine weitere bewusste Abkürzung mit demselben Hinweis wie die Stufen.

### 7.3 Taktik (ersetzt „Trainer & Taktik“; vom Nutzer so festgelegt)
Ziel: **Wo sind die Schwachstellen meiner Taktik, und wer verursacht sie?** – das, was der FM27-Bildschirm „Taktische Effektivität“ nicht sagt.

- Oben: Taktik aus dem Spielstand – Formation, Rollen mit und gegen den Ball, Spielstil (z. B. „Gegenpressing“, gelesen aus dem Taktikkopf).
- Darunter Bereiche angelehnt an FM27: Formation mit Ball, Passstil, Spielaufbau, Chancen kreieren, Formation ohne Ball, Pressinglinie, Pressingintensität, Pressingfalle. Pro Bereich eine Einschätzung (z. B. gut/mittel/schwach) aus den Attributen der eingesetzten Spieler und ihrer Rollen.
- Bei schwachen Bereichen: **wer** (Spieler + Position + verantwortliche Attribute mit Wert, eigener Kader) und **was hilft** (Rolle ändern, im Training fördern, Transfer).
- Verknüpfung: Schwache Bereiche werden Fokus im Trainingsvorschlag und Suchkriterium bei Transfervorschlägen.
- **Trainertendenzen** (z. B. „Spielt offensiven Fußball“, „Taktiktüftler“) fließen ein, weil FM27 sie bei der Spielerüberzeugung berücksichtigt; Hinweis, wenn Taktik und Tendenzen sich widersprechen. Herkunft siehe 8.3.
- Kein Trainerprofil-Formular mehr; Trainerbewertungen entfallen.

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
- Spielstand-Ordner, Spielinstallation, hell/dunkel, Informationsstufe, „Nicht mehr fragen“: Programmeinstellungen des Nutzers (z. B. in `%APPDATA%\FM-Scout`).
- Pro Karriere: eigene Rollenwahl, Filter, gespeicherte Wochenpläne, Trainertendenzen (falls von Hand gesetzt).
- `config.json` des Repos entfällt für Endnutzer.

### 8.3 Trainertendenzen
Zuerst versuchen, sie aus dem Spielstand zu lesen. Gelingt das nicht, wählt der Nutzer sie einmal pro Karriere aus einer Liste (≈ 5 Klicks). Ohne Angabe entfällt nur der Tendenzen-Hinweis.

### 8.4 Bekannte Korrektur
Persönlichkeitsreihenfolge ist Anpassung, Ehrgeiz, Loyalität, Druck, Professionalität, Sportsgeist, Temperament, Kontroversität (bisher falsch angenommen; `willingness()` las Druck statt Loyalität). Laut Regel vor Übernahme mit Screenshot des Nutzers abgleichen.

## 9. Gestalt und Technik (Entscheidung von Claude, nicht vom Nutzer)

- Ein natives Programmfenster, dessen Oberfläche mit Web-Technik gezeichnet wird (Windows-eigene Edge-WebView2), Python im Hintergrund – so lässt sich die vorhandene Oberfläche aus `app.html` weiterverwenden und modern gestalten.
- Ausgeliefert als **eine** `FM-Scout.exe` (alles gebündelt), als GitHub-Release; Quellcode im Repo.
- Keine erzeugte HTML-Datei auf der Festplatte, keine Batch-Datei.
- Stil (vom Nutzer gewählt): **„Dunkel & neutral“** – fast schwarzer Hintergrund, Karten mit dezentem Rand, ein türkisgrüner Akzent, gelb/orange für Warnungen. Umschaltbar auf **„Hell & klar“** – weiß, grüne Akzente. Wahl wird gespeichert.
- Lizenzhinweis für fmsave (MIT) im Programm und im Repo.

## 10. Dem Builder überlassen

- Konkrete Bibliotheken für Fenster und Bündelung, Projektstruktur, Build-Skript und Release-Ablauf.
- Wie Python und Oberfläche Daten austauschen (die Regel aus Abschnitt 5 muss dabei gelten: CA/PA/versteckte Werte erreichen die Oberfläche nie).
- Formeln für die Bereichs-Einschätzungen in 7.3 (welche Attribute pro Bereich und Rolle), solange sie nachvollziehbar und begründbar sind.
- Ob das Einlesen im Hintergrund zwischengespeichert wird, um den zweiten Start zu beschleunigen.
- Tests und Prüfungen, mit echtem Spielstand des Nutzers als Abnahme.

### Entscheidungen von Claude (vom Nutzer noch nicht bestätigt)

- **fmsave** wird als veröffentlichtes Paket in fester Version eingebunden (nicht der lokale Klon); Updates bewusst.
- **`extract.py`** bleibt als Modul für die Leselogik erhalten; die alte Ausgabe als HTML-Datei und `FM-Scout starten.bat` entfallen.
- Der bisherige Inhalt von „Trainer & Taktik“ (Rangliste der Spielstile nach Kaderpassung) wandert in den Taktik-Reiter als Vorschlag „Diese Spielstile passen besser zu deinem Kader“.
- Die gewählte Informationsstufe der Transfervorschläge wird gespeichert und gilt beim nächsten Start weiter.
- Die `.exe` ist anfangs **nicht signiert**; Windows zeigt beim ersten Start „Der Computer wurde durch Windows geschützt“. Die README erklärt, wie man trotzdem startet.
- Lizenz des FM-Scout-Repos: **MIT** (wie fmsave). Kann der Nutzer ändern.
- Die Transferliste zeigt eine überschaubare Zahl an Vorschlägen (z. B. die besten 50 je Filter) statt Tausender Zeilen – gegen „unübersichtlich“.

## 11. Offene Punkte

- **Scoutinggebiet auslesen:** In `scout_man` steht ein 4-Zeichen-Code, der sich mit dem Gebiet ändert: Italien = `AcSP`, Europa = `blcP` (Vergleich zweier Ravenna-Spielstände, sonst unverändert). Es fehlen die Codes für Weltweit und Südeuropa sowie die Bestätigung, dass „Italien“ allgemein „eigenes Land“ bedeutet. Außerdem nötig: Zuordnung Land → Region/Kontinent (vermutlich aus der Spieldatenbank).
- Ob die Hintergrundrechnung in Stufe „Aus“ weiterhin CA/PA nutzen darf (z. B. damit nicht viel zu schwache Spieler oben stehen), ist mit dem Scoutinggebiet weniger dringend, aber nicht abschließend geklärt.
- Das Design-Dokument ist **vom Nutzer noch nicht freigegeben**.
- Teamanweisungen (16 Byte im Taktikkopf) sind nicht dekodiert; bis dahin zeigt der Taktik-Reiter keine Teamanweisungen.
- Rollentest für weitere Rollen-Fingerabdrücke steht weiter aus (siehe `HANDOFF.md`).
