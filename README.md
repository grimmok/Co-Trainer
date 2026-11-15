# Co-Trainer

Co-Trainer liest deinen Spielstand von **Football Manager 27** und hilft dir, Kader, Transfers, Taktik und Training zu verbessern. Es ist ein Windows-Programm: herunterladen, doppelklicken, fertig.

Co-Trainer ist ein Fanprojekt und steht in keiner Verbindung zu Sports Interactive oder SEGA. Football Manager ist eine Marke von Sports Interactive.

## Was Co-Trainer macht

- **Kaderanalyse:** deine beste Startelf für die eigene Taktik, Stärken und Lücken je Position, Finanzen auf einen Blick.
- **Transfervorschläge:** Spieler, die deine schwächsten Positionen verbessern, mit geschätzter Wechselchance und Marktwert, gefiltert nach deinem Scoutinggebiet.
- **Taktik:** zeigt die Schwachstellen deiner Taktik in den acht Trainingsbereichen, wer sie verursacht und was hilft (andere Rolle, Training, Transfer), dazu deine Trainerbewertungen und welche Spielstile zu deinem Kader passen.
- **Training:** eine Trainingswoche mit den echten FM27-Einheiten, abgestimmt auf Spielstil und Baustellen, dazu die Trainingsbewertungen deiner Spieler.
- **Kaderliste:** alle Spieler deiner ersten Mannschaft mit Positionen, Vertrag und Gehalt.

Die Transfervorschläge haben drei Informationsstufen: **Aus**, **Scoutbericht** und **Werte**. Voreingestellt ist „Aus“. Dann zeigt Co-Trainer über fremde Spieler nur, was du im Spiel auch ohne Scouting siehst, denn genaue Werte ungescouteter Spieler machen das Spiel leichter. Höhere Stufen schaltest du bewusst ein, mit Hinweis vorher.

Aktuelle und potenzielle Fähigkeit als Zahl sowie versteckte Attribute zeigt Co-Trainer nie, auch nicht in der Stufe „Werte“. Potenzial erscheint höchstens als Text, zum Beispiel „Kann sich zu einem guten Zweitliga-Spieler entwickeln“.

## Starten

1. `Co-Trainer.exe` aus dem neuesten [Release](../../releases/latest) herunterladen.
2. Doppelklick. Beim ersten Start zeigt Windows „Der Computer wurde durch Windows geschützt“, weil das Programm nicht signiert ist. Dann auf **Weitere Informationen** und **Trotzdem ausführen** klicken.
3. Co-Trainer führt dich in drei Schritten zum Ergebnis:
   - **Spielstand-Ordner** wählen (vorgeschlagen wird `Dokumente\Sports Interactive\Football Manager …\games`),
   - den neuesten **Spielstand** bestätigen oder einen anderen wählen,
   - die **Analyse** wählen (ein Bereich oder alles).

Das Einlesen dauert rund zwei Minuten.

**Voraussetzungen:**

- Windows 10 oder 11 mit der Microsoft-Edge-WebView2-Laufzeit. Sie ist normalerweise schon installiert; falls nicht, meldet Co-Trainer das, und du bekommst sie über Windows Update oder von microsoft.com.
- Football Manager 27. Aus der Spielinstallation kommen die Namen von Ligen und Rollen. Findet Co-Trainer das Spiel nicht, kannst du den Spielordner selbst wählen; eingelesen wird auch ohne.

## Sicherheit und Daten

- Co-Trainer **liest Spielstände nur** und schreibt nie hinein.
- Co-Trainer nutzt **keine Internetverbindung**: kein Upload, keine Telemetrie, keine Updates im Hintergrund.
- Einstellungen (Spielstand-Ordner, Spielordner, hell/dunkel, Informationsstufe) liegen in `%APPDATA%\Co-Trainer\settings.json`.
- Zum Entfernen `Co-Trainer.exe` und den Ordner `%APPDATA%\Co-Trainer` löschen.
- Speichert das Spiel, während Co-Trainer einliest, kann das Einlesen scheitern. Dann den Spielstand einfach noch einmal einlesen.

## Grenzen

- Nur Windows, nur Deutsch, nur Football Manager 27.
- Noch nicht alle Rollen sind bekannt. Unbekannte Rollen erscheinen mit „?“ und einer Standardrolle; du kannst die Rolle in der Kaderanalyse selbst wählen.
- Teamanweisungen werden noch nicht aus dem Spielstand gelesen.
- Bei Nationaltrainer-Karrieren und Spielständen mit zwei menschlichen Managern findet Co-Trainer keinen Vereinskader und sagt das.
- Wechselchance und Marktwert sind eigene Schätzungen, keine Werte aus dem Spiel.

## Aus dem Quellcode

Voraussetzung ist Python 3.12.

```powershell
python -m uv venv --python 3.12 .venv
python -m uv pip install --python .venv -e ".[dev]"
.venv\Scripts\python -m cotrainer                         # Programm starten
.venv\Scripts\python -m pytest tests -q -m "not save"     # Tests ohne echte Spielstände
.\build.ps1                                               # baut dist\Co-Trainer.exe
```

Die Tests mit echten Spielständen (Marke `save`) sind auf die Testspielstände des Autors zugeschnitten und werden ohne sie übersprungen; für eigene Prüfungen gibt es den Konsolenlauf `.venv\Scripts\python -m cotrainer.extract`. Die Taktiklogik in `tests/js/` braucht Node.js.

## Lizenz

Co-Trainer steht unter der [MIT-Lizenz](LICENSE). Die Spielstände werden mit [fmsave](https://github.com/rhiever/fmsave) gelesen (MIT). Die Lizenzen aller Pakete, die in `Co-Trainer.exe` stecken, stehen in [THIRD_PARTY_LICENSES.txt](THIRD_PARTY_LICENSES.txt) und im Programm unter „Über Co-Trainer“.
