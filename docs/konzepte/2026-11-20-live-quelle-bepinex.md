# Konzept: Live-Datenquelle über BepInEx

Stand 20.11.2026. Entwurf, noch nicht freigegeben. Nichts davon ist gebaut oder geprüft.

## 1. Idee

Co-Trainer liest heute die Spielstand-Datei (`fmsave` und als Rückfall der eigene Leser). Ein **optionales Add-on** soll als dritte Quelle die Daten direkt aus dem laufenden Spiel liefern.

Das Add-on ist ein BepInEx-Plugin im Spielordner. Es liest im Spiel Daten aus und schreibt einen Schnappschuss, den Co-Trainer einliest.

```
Football Manager 27 (läuft)
 └─ BepInEx 6 (IL2CPP) ── Plugin „CoTrainer.Live“ (C#, nur lesend)
                              │  Schnappschuss als JSON
                              ▼
          %APPDATA%\Co-Trainer\live\snapshot.json
                              │
Co-Trainer (Python) ── cotrainer/live.py ── gleiches Datenmodell wie analyse()
                              │  guard.assert_public
                              ▼
                       Oberfläche (index.html)
```

Ohne Add-on oder ohne laufendes Spiel arbeitet Co-Trainer wie bisher mit dem Spielstand. Das Add-on ersetzt die beiden Leser nicht.

## 2. Was zuerst geklärt werden muss (Schritt 0, vor jeder Planung)

Diese Punkte entscheiden, ob das Add-on überhaupt machbar ist:

1. **Bauart des Spiels:** Liegt `GameAssembly.dll` im Spielordner, ist FM27 ein IL2CPP-Build und braucht BepInEx 6 (Bleeding Edge, `IL2CPP-win-x64`). Liegt dort `…_Data\Managed\Assembly-CSharp.dll`, reicht BepInEx 5.
2. **Wo die Daten liegen. Das ist das größte Risiko.** FM hat seit jeher eine eigene, native Spiellogik in C++. Vermutlich ist Unity in FM26/27 vor allem die Oberfläche, die über eine Brücke an diese Logik angeschlossen ist. Dann erreicht ein Plugin nur das, was die Brücke an Unity weitergibt, also etwa die Datenobjekte der Bildschirme (View-Models), nicht die ganze Datenbank. Zu prüfen ist, ob es Klassen für Personen, Spieler, Vereine und Taktik mit Attributen gibt oder nur Bildschirm-Objekte.
3. **Läuft BepInEx überhaupt mit FM27?** Dafür reicht ein leeres Plugin, das nur „geladen“ ins Protokoll schreibt. Zu klären ist dabei auch, ob das Spiel einen Manipulationsschutz hat, der die Proxy-DLL `winhttp.dll` ablehnt.
4. **Klassen ansehen:** Nach dem ersten Start mit BepInEx 6 liegen die Interop-Assemblies unter `BepInEx\interop\`. Mit ILSpy oder dnSpy sieht man dort Klassennamen, Felder und Methoden. Daraus ergibt sich eine Liste, welche Daten erreichbar sind.

Ergebnis von Schritt 0 ist eine Liste „erreichbar, nicht erreichbar, nur über Bildschirm“. Erst danach lohnt sich ein Plan.

## 3. Aufbau

### 3.1 Plugin (C#)

- **BepInEx 6, IL2CPP**, .NET 6, Klasse mit `[BepInPlugin("de.cotrainer.live", "Co-Trainer Live", "0.1.0")]`, erbt von `BasePlugin`.
- **Nur lesen.** HarmonyX wird ausschließlich für **Postfixes** verwendet, um Zeitpunkte zu erkennen, zum Beispiel „Verarbeitung beendet“, „Spieltag vorbei“ oder „Spielstand geladen“. Kein Prefix überspringt Spielcode, kein Wert im Spiel wird verändert. Diese Regel steht im Plugin-Code als Kommentar und wird bei jeder Durchsicht geprüft.
- **Wann geschrieben wird:**
  - nach jeder Verarbeitung im Spiel, also wenn der Kalender weiterläuft;
  - nach dem Laden eines Spielstands;
  - auf Tastendruck, zum Beispiel Strg+Umschalt+C. Die Taste ist in `BepInEx\config\de.cotrainer.live.cfg` einstellbar.
- **Wie geschrieben wird:** zuerst als `snapshot.json.tmp`, dann umbenannt. So liest Co-Trainer nie eine halbe Datei. Dazu kommt eine kleine `status.json` mit Spielversion, Plugin-Version, Zeitpunkt und Spielstand-Namen.
- **Versionsschutz:** Das Plugin kennt die Builds, für die es geprüft ist, zum Beispiel 27.1.0. Bei einem unbekannten Build schreibt es nur `status.json` mit dem Hinweis „Spielversion nicht geprüft“ und keine Daten. Co-Trainer bleibt dann beim Spielstand.
- **Fehler** landen in `BepInEx\LogOutput.log`, nie im Spiel. Ein Fehler im Plugin darf das Spiel nicht stören, deshalb läuft jede Ausleseroutine in `try/catch`.
- **Nicht in Online-Partien:** Erkennt das Plugin eine Online-Karriere, schreibt es nichts.

### 3.2 Übergabe an Co-Trainer

Die Übergabe läuft über **eine Datei**, nicht über einen Netzwerk-Port:

- Es gibt keinen offenen Port. Damit kommt das Add-on der Regel „keine Online-Funktionen“ nicht einmal nahe.
- Spiel und Co-Trainer müssen nicht gleichzeitig laufen. Der letzte Schnappschuss bleibt nach dem Beenden des Spiels lesbar.
- Eine Datei ist leicht zu prüfen, man kann sie einfach öffnen.

Eine Named Pipe (`\\.\pipe\cotrainer-live`) wäre die spätere Ausbaustufe, falls Daten nahezu sofort übertragen werden sollen, etwa während eines Spiels. Für den Anfang reicht eine Datei mit Dateiüberwachung.

### 3.3 Python-Seite

- **`cotrainer/live.py`** liest `snapshot.json` und baut daraus **dasselbe Datenmodell wie `extract.analyse()`**. Die Oberfläche muss dafür kaum geändert werden.
- **`meta.source`** erhält einen dritten Wert: `live`. Die Oberfläche zeigt die Quelle und das Alter an, etwa „Live aus dem Spiel, Stand Sa 14.03.2027, vor 2 Min.“.
- **`guard.assert_public`** prüft auch dieses Ergebnis, ohne Ausnahme. Das Plugin darf intern Werte wie CA oder PA liefern, wenn Co-Trainer sie für Rechnungen braucht, zum Beispiel für den Potenzialtext. Sie gelangen wie beim Spielstand nie in die Oberfläche. Sauberer ist, wenn das Plugin nur exportiert, was gebraucht wird.
- **Personen-IDs:** Die IDs des Spiels werden nicht über die Zahl mit den IDs von `fmsave` oder dem eigenen Leser verbunden (Regel aus `CLAUDE.md`). Daten aus mehreren Quellen werden wie in `map_ratings` über Name und Geburtsdatum zusammengeführt.
- **Dateiüberwachung:** Ändert sich `snapshot.json`, meldet `Api` das der Oberfläche über das JS-Objekt `CT`. Diese zeigt dann „Neue Daten aus dem Spiel, jetzt aktualisieren?“ oder aktualisiert selbst, je nach Einstellung.
- **Einstellungen** in `%APPDATA%\Co-Trainer\settings.json`: `live_enabled` (an/aus) und `live_auto_refresh`.
- **Rangfolge der Quellen:** Ist der Live-Schnappschuss neuer als der Spielstand und gehört er zur selben Karriere, wird er genommen, sonst der Spielstand. Der Nutzer kann die Quelle in der Oberfläche umschalten.

### 3.4 Installation

- Das Add-on ist ein **eigener, optionaler Download**: BepInEx 6 und `CoTrainer.Live.dll` in einem Zip-Archiv. Co-Trainer selbst bleibt eine einzelne `.exe`.
- Installiert wird durch Entpacken in den Spielordner. Deinstalliert wird, indem man `winhttp.dll`, `doorstop_config.ini` und den Ordner `BepInEx` löscht.
- **Offene Entscheidung (Nutzer):** Soll Co-Trainer eine Schaltfläche „Live-Add-on installieren“ bekommen, die diese Dateien in den eingestellten Spielordner kopiert? Die Regel „Spielstände nur lesen“ wäre davon nicht berührt. Co-Trainer würde aber zum ersten Mal in den Spielordner schreiben.
- Hinweis in der Anleitung: Ein Steam-Update kann BepInEx unbrauchbar machen. „Dateien überprüfen“ in Steam entfernt die Proxy-DLL nicht zuverlässig. Zum sauberen Entfernen gilt die Liste oben.

## 4. Neue Möglichkeiten

Was davon tatsächlich geht, hängt von Schritt 0 ab. Die Liste ist nach Nutzen geordnet.

### 4.1 Offene Probleme, die sich damit lösen ließen

| Offenes Problem (`HANDOFF.md`) | Mit Live-Daten |
|---|---|
| Einlesen dauert rund zwei Minuten | Ein Schnappschuss ist in Sekunden eingelesen, weil nichts entpackt werden muss. |
| Nur 19 Rollen bekannt, ZOM-Rolle unsicher, Rollen-Fingerabdrücke (`ROLE_FP`) | Die Rollen-ID der aktuellen Taktik kommt direkt aus dem Spiel. Den Namen liefert `lang_db` (IDs 1800–1884). Das Raten über Fingerabdrücke entfällt. Jede neue Zuordnung wird trotzdem einmal mit dir per Screenshot abgeglichen. |
| Teamanweisungen und Spieleranweisungen nicht ausgelesen, Stil steht nur in `config.json` | Auslesbar, falls die Taktikklassen erreichbar sind. Damit ließe sich die Taktikanalyse (`taktik.js`) mit echten Anweisungen füttern. |
| Paris-Spielstand ohne eigene Taktik | Die aktive Taktik kommt aus dem Spiel und nicht aus `tactics_man`. |
| Nationaltrainer-Karrieren und Spielstände mit zwei Managern ohne Kader | Das Spiel weiß, welcher Manager gerade spielt und welche Mannschaft er betreut. |
| Trainertendenzen und Führungsstil („Ihr Stil“) unbekannt | Die gewählten Karten könnten direkt gelesen werden. Die Auswahl pro Karriere in Co-Trainer wäre dann nicht mehr nötig. |
| Scoutingbudget und Staffattribute anderer Trainer | Auslesbar, falls erreichbar. Die Trainerbewertungen erscheinen weiter nur als Text. |
| Abgleich der Bereiche mit „Taktische Effektivität“ (seit 27.1.0 neu gewichtet) | Den Wert, den das Spiel selbst anzeigt, auslesen und neben die eigene Einschätzung stellen. Angezeigt wird er so, wie das Spiel ihn zeigt, also als Stufe oder Text. |
| „Spiel läuft“: Speichern während des Einlesens bricht `fmsave` ab | Der Schnappschuss wird atomar geschrieben, der Konflikt entfällt. |

### 4.2 Neue Funktionen

1. **Spieltags-Assistent.** Vor jedem Spiel stellt Co-Trainer Folgendes zusammen:
   - Kondition, Spielfitness, Sperren und Verletzungen auf dem aktuellen Stand;
   - einen Vorschlag für die Aufstellung nach der eigenen Rollenbewertung;
   - den nächsten Gegner mit Kader, Formation, Form und wichtigsten Spielern.
   Heute ginge das nur, wenn du vor jedem Spiel speicherst und zwei Minuten wartest.
2. **Entwicklungsverlauf.** Co-Trainer legt pro Spielwoche einen Schnappschuss ab, im Ordner `%APPDATA%\Co-Trainer\live\verlauf\`. Daraus entstehen Kurven der **sichtbaren** Attribute, der Spielminuten und der Noten pro Spieler. Fragen wie „Wer entwickelt sich, wer stagniert?“ lassen sich dann über die Zeit beantworten. Das Potenzial bleibt Text, und CA und PA erscheinen auch hier nicht.
3. **Training nachsteuern.** Nach jeder Woche vergleicht Co-Trainer, wie sich die Attribute der Spieler mit Trainingsschwerpunkt verändert haben, und schlägt Anpassungen der Wochenpläne vor.
4. **Transfers live.** Neue Angebote, Spieler auf der Transferliste und Einschätzungen der Scouts erscheinen ohne neues Einlesen. Am Deadline-Day ist das besonders nützlich.
5. **Belastung und Rotation.** Spielminuten der letzten Wochen, Kondition und Spielplan werden zu einem Rotationsvorschlag für englische Wochen verdichtet. Das Verletzungsrisiko (InjPr) ist versteckt, darf also höchstens intern einfließen und wird nicht angezeigt.
6. **Zweiter Bildschirm.** Co-Trainer läuft neben dem Spiel und aktualisiert sich selbst. Ein Overlay im Spiel wäre technisch möglich, gehört aber nicht zu diesem Konzept.

### 4.3 Was ausdrücklich nicht gemacht wird

- **Nichts im Spiel verändern:** keine Werte setzen, keine Entscheidungen auslösen, keine Spielfunktionen aufrufen, die etwas verändern. Das Add-on ist ein Beobachter und kein Cheat.
- **Keine versteckten Werte in der Oberfläche,** auch wenn sie im Speicher frei zugänglich sind (Regel aus `CLAUDE.md`).
- **Keine Netzwerkverbindung,** auch nicht lokal über TCP, solange die Datei ausreicht.
- **Kein Einsatz in Online-Partien.**

## 5. Risiken

| Risiko | Folge | Gegenmaßnahme |
|---|---|---|
| Spieldaten liegen im nativen Teil, nicht in Unity | Nur Bildschirmdaten erreichbar, also deutlich weniger als erhofft | Schritt 0; notfalls nur das auslesen, was auf Bildschirmen erscheint, oder das Vorhaben einstellen |
| Jedes Spiel-Update kann Klassen umbenennen | Das Add-on liefert nach einem Patch nichts mehr | Versionsschutz; Co-Trainer fällt auf den Spielstand zurück; nach jedem Patch prüfen |
| BepInEx 6 ist Bleeding Edge | Abstürze oder Inkompatibilität | Feste BepInEx-Version mitliefern; jede Routine in `try/catch` |
| Zweite Sprache (C#) im Projekt | Mehr Pflegeaufwand, eigener Build | Plugin klein halten: nur auslesen und schreiben, alle Auswertung bleibt in Python |
| Rechtliches und Nutzungsbedingungen | Modding der Spieldateien ist bei FM üblich, aber nicht offiziell unterstützt | Nur lesen, nur Einzelspieler, kein Weitergeben von Spieldaten; Hinweis in der Anleitung |
| Personen-IDs verschiedener Quellen | Falsche Zuordnung von Spielern | Nur über Name und Geburtsdatum verbinden (wie `map_ratings`) |

## 6. Vorgehen in Stufen

1. **Machbarkeit (Schritt 0):** Bauart des Spiels prüfen, BepInEx und das leere Plugin starten, Klassen ansehen. Ergebnis ist die Liste der erreichbaren Daten. Dafür ist dein Rechner mit FM27 nötig.
2. **Prototyp:** Das Plugin schreibt nur den eigenen Kader (Name, Geburtsdatum, Position, sichtbare Attribute, Kondition) auf Tastendruck. `live.py` liest ihn ein, und Co-Trainer zeigt ihn als Quelle `live`. Abgleich mit dem Spielstand und mit Screenshots.
3. **Lücken schließen:** Rollen, Taktik und Anweisungen, Führungsstil, Taktische Effektivität. Jeder neue Wert wird vor dem Einsatz mit Screenshots bestätigt.
4. **Live-Funktionen:** automatisches Schreiben nach der Verarbeitung, Dateiüberwachung, Spieltags-Assistent, Entwicklungsverlauf.
5. **Auslieferung:** Zip-Archiv, Anleitung, eventuell eine Schaltfläche zum Installieren (siehe 3.4).

## 7. Offene Fragen an den Nutzer

1. Ist FM27 ein IL2CPP-Build? Liegt `GameAssembly.dll` im Spielordner?
2. Darf Co-Trainer später selbst in den Spielordner schreiben, um das Add-on zu installieren? Oder installierst du es von Hand?
3. Welche neue Funktion aus 4.2 ist dir am wichtigsten? Davon hängt ab, welche Daten der Prototyp zuerst ausliest.
4. Soll Co-Trainer automatisch aktualisieren, sobald neue Live-Daten da sind, oder erst nachfragen?
