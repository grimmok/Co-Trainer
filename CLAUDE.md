# Co-Trainer (früher „FM-Scout“)

Windows-Programm, das einen Football-Manager-27-Spielstand (`.fm`) liest und Kader, Transfers, Taktik und Training analysiert. Projektstand, Format-Details und offene Punkte stehen in [HANDOFF.md](HANDOFF.md). Lies diese Datei zuerst. Das freigegebene Design steht in [docs/superpowers/specs/2026-11-09-fm-scout-app-design.md](docs/superpowers/specs/2026-11-09-fm-scout-app-design.md).

## Feste Regeln

- **CA, PA und versteckte Attribute** (Cons, Dirt, ImpM, InjPr, Vers) erscheinen nie in der Oberfläche und verlassen nie den Python-Teil Richtung Oberfläche. Das gilt auch für Persönlichkeitswerte und die Zahlen der Trainerbewertungen und Neigungen. Sie dürfen nur intern gerechnet werden. `cotrainer/guard.py` (`assert_public`) prüft jedes Ergebnis; schlägt die Prüfung an, wird der Leser korrigiert, nicht die Regel gelockert.
- **Potenzial** wird nur als Text angezeigt, z. B. „Kann sich zu einem guten Zweitliga-Spieler entwickeln“, niemals als Zahl.
- **Spielstände nur lesen**, nie schreiben oder verändern.
- **Geld** steht im Spielstand in GBP. Angezeigt wird in EUR: Faktor **1,1641**.
- **Attributblock zuordnen nur über `Block-ID (u32 bei −43) = Personen-ID − 1`.** Der Block liegt *vor* dem Personenkopf. Niemals „nächster Personenkopf“ verwenden.
- **Neue Rollen-Fingerabdrücke** (`ROLE_FP` in `cotrainer/extract.py`) nur eintragen, wenn der Nutzer die Rolle bestätigt hat (Liste oder Screenshot). Nicht raten.
- **Neu dekodierte Werte** (Finanzen, Verträge, Rollen) mit Screenshots des Nutzers abgleichen, bevor sie als korrekt gelten.
- **Oberfläche und Texte auf Deutsch**, mit den deutschen FM27-Begriffen (Rollennamen siehe `lang_db`, IDs 1800–1884).
- **Keine Online-Funktionen**, keine erzeugte HTML-Datei auf der Festplatte, keine Batch-Datei.
- **Programmeinstellungen** (Spielstand-Ordner, Spielordner, hell/dunkel) liegen in `%APPDATA%\Co-Trainer\settings.json`. `config.json` ist nur noch Entwicklerhilfe für Kontrollläufe in der Konsole und wird nicht mitgeliefert. Werte aus dem Spielstand haben Vorrang vor `config.json`.

## Arbeitsweise

- **Umgebung:** Python 3.12 in `.venv` (installiert ist sonst 3.10): `python -m uv venv --python 3.12 .venv`, dann `python -m uv pip install --python .venv -e ".[dev]"`.
- **fmsave:** Die Bibliothek `fmsave` (fest `0.11.0`, braucht `backports.zstd`) liefert Spieler, Vereine und Ligen (`cotrainer/fms.py`); der eigene Leser bleibt Rückfall (`meta.source`: `fmsave` oder `eigener Leser`). Personen-IDs der beiden Leser nie über die Zahl miteinander verbinden. Ein Einlesen dauert rund zwei Minuten, weil beide Leser den Spielstand entpacken.
- **Programm starten:** `.venv\Scripts\python -m cotrainer`.
- **Tests:** `.venv\Scripts\python -m pytest tests -q`. Die zehn Tests mit echten Spielständen (Marke `save`) dauern rund sechs Minuten (die ganze Suite rund 350 s); ohne sie: `-m "not save"`. Der Testspielstand ist `Haribaert Kachinski – Ravenna.fm` (anderer Pfad über `COTRAINER_TEST_SAVE`); zweiter Testspielstand ist `Ivan Kurasic – NK Osijek.fm` (Pfad über `COTRAINER_TEST_SAVE_OSIJEK`).
- **`.exe` bauen:** `.\build.ps1` → `dist\Co-Trainer.exe`.
- **Kontrolllauf in der Konsole:** `.venv\Scripts\python -m cotrainer.extract [Pfad.fm | Nummer]`, `--list` zeigt die Spielstände mit Nummer, `--dump Datei.json` schreibt das Ergebnis. Zum Prüfen einzelner Spieler die Umgebungsvariable `FMS_DEBUG=Name1,Name2` setzen. Dann werden Rohwerte inkl. CA/PA in die Konsole geschrieben; diese Werte nur zur Kontrolle verwenden, nie in die Oberfläche übernehmen. `FMS_ROLES=1` gibt die Rollen-Fingerabdrücke aus.
- **Oberfläche:** `cotrainer/ui/index.html` (Vanilla JS). Änderungen an der Oberfläche immer dort vornehmen. Python und Oberfläche reden über `cotrainer/api.py` (Methoden der Klasse `Api`) und das JS-Objekt `CT`.
- **Oberfläche im Browser prüfen:** einmal `.venv\Scripts\python -m cotrainer.extract --dump cotrainer/ui/dev-data.json` (Datei ist in `.gitignore`), dann die Vorschau „fmscout“ (`.claude/launch.json`, Port 8765) starten und `http://127.0.0.1:8765/cotrainer/ui/index.html?dev=1&v=<irgendwas>` laden. Ohne `v=` kommt eine gecachte Seite. Im Entwicklermodus stellt die Seite Python nach. Danach die Konsole auf Fehler prüfen.
- Erkundungsskripte und entpackte Spielstand-Teile gehören in das Scratchpad, nicht in diesen Ordner.
- Nutzerpfade:
  - Spielstände: `%USERPROFILE%\Documents\Sports Interactive\Football Manager 26\games\`
  - Spiel: `G:\SteamLibrary\steamapps\common\Football Manager 27`
