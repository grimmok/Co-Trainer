# Co-Trainer Teil 4: README, Lizenzhinweise, Release – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Co-Trainer ist als `Co-Trainer.exe` mit README, vollständigen Lizenzhinweisen (Repo und Programm) und einem GitHub-Release v0.1.0 verteilbar.

**Architecture:** Ein Entwicklerskript `tools/third_party.py` sammelt die Lizenztexte aller Pakete, die in die `.exe` gebündelt werden, plus Python, in `THIRD_PARTY_LICENSES.txt` (eingecheckt, von `build.ps1` neu erzeugt und mitgepackt). `cotrainer/about.py` liest diese Datei im Programm; `Api.about()` gibt sie an die Oberfläche, die sie im Fenster „Über Co-Trainer“ zeigt. README und Release-Text erklären Start, Windows-Schutzhinweis und WebView2.

**Tech Stack:** Python 3.12 (`importlib.metadata`, `packaging.markers` nur im Entwicklerskript), PyInstaller, pywebview, Vanilla JS, `gh` (über den Token in `GITHUB_PERSONAL_ACCESS_TOKEN`).

**Spec:** `docs/superpowers/specs/2026-11-09-fm-scout-app-design.md` (Abschnitte 2.1, 9, 10 „Entscheidungen von Claude“), dazu `HANDOFF.md` „Nächste Schritte“ Punkt 1–2.

## Global Constraints

- Oberfläche, README und Release-Text auf Deutsch, mit den deutschen FM27-Begriffen.
- Keine Online-Funktionen: Das Programm lädt nichts nach und öffnet keine Webseiten. URLs erscheinen im Programm nur als Text, nicht als anklickbare Links (ein Link würde das Programmfenster wegnavigieren).
- Keine erzeugte HTML-Datei auf der Festplatte, keine Batch-Datei.
- CA, PA und versteckte Werte erscheinen nirgends, auch nicht in README-Beispielen oder Screenshots.
- Lizenz des Repos: MIT (`LICENSE`, Copyright „grimmok“). Lizenzhinweis für fmsave (MIT) im Programm und im Repo.
- Die `.exe` ist nicht signiert; README und Release-Text erklären „Der Computer wurde durch Windows geschützt“ → „Weitere Informationen“ → „Trotzdem ausführen“.
- Version `0.1.0` (`cotrainer/__init__.py`, `pyproject.toml`), Tag `v0.1.0`.
- Keine persönlichen Daten in neuen Dateien: kein echter Name, keine Pfade unter `C:\Users\<Name>`; Pfade als `%USERPROFILE%\…` bzw. „Dokumente\Sports Interactive\…“.
- Das Repository bleibt privat. Claude schaltet die Sichtbarkeit nicht um (Entscheidung des Nutzers, 15.11.).
- Commits als `grimmok` mit `317344714+grimmok@users.noreply.github.com` (lokal eingestellt).

## Review Focus

1. **Lizenzdatei fehlt im gepackten Programm** (z. B. `build.ps1` ohne `--add-data`): „Über Co-Trainer“ öffnet trotzdem und sagt im Klartext, dass die Lizenzhinweise fehlen, statt abzustürzen. → Task 2, `test_about_without_notices_file`.
2. **Paket ohne Lizenztext** (proxy_tools 0.1.0 liefert keinen): Das Skript bricht nicht ab, sondern nennt Lizenz laut Paketangaben und Projektadresse. → Task 1, `test_license_text_falls_back_to_metadata`.
3. **Veraltete Lizenzliste nach einem Paket-Update:** Die eingecheckte Datei nennt jede gebündelte Laufzeitabhängigkeit mit der installierten Version. → Task 1, `test_checked_in_notices_match_installed_versions`.
4. **Klick auf eine Adresse im Fenster „Über“** würde die Oberfläche durch eine fremde Seite ersetzen: Das Fenster enthält keine `<a href="http…">`. → Task 2, `test_about_modal_has_no_external_links`.
5. **Entwicklermodus (`?dev=1`)** hat kein Python: Die nachgestellte API braucht `about`, sonst wirft der Klick einen Fehler. → Task 2, `test_dev_api_has_about`.

---

### Task 1: Lizenzen der mitgelieferten Software

**Files:**
- Create: `tools/third_party.py`
- Create: `THIRD_PARTY_LICENSES.txt` (erzeugt, eingecheckt)
- Modify: `build.ps1` (Skript vor PyInstaller ausführen; `--add-data 'THIRD_PARTY_LICENSES.txt;.'`)
- Test: `tests/test_third_party.py`

**Interfaces:**
- Produces: `tools/third_party.py` mit
  - `runtime_dists(root: str = 'cotrainer') -> list[importlib.metadata.Distribution]` – transitive Laufzeitabhängigkeiten von `root` (ohne `root` selbst), Marker mit `packaging.markers.Marker(...).evaluate({'extra': ''})` ausgewertet, Extras ignoriert, Namen normalisiert (`re.sub(r'[-_.]+', '-', n).lower()`), jede höchstens einmal.
  - `license_text(dist) -> str` – Inhalt der Dateien unter `licenses/` der dist-info, sonst `LICENSE*`/`COPYING*`/`NOTICE*` in `dist.files`, mehrere durch eine Leerzeile getrennt; ohne Datei: `"Kein Lizenztext im Paket enthalten. Lizenz laut Paketangaben: <License-Expression oder License oder Classifier 'License :: …'>. Projekt: <Home-page oder erste Project-URL>"`.
  - `render(dists, python_version: str, python_license: str) -> str` – Kopf, dann je Paket ein Block, fmsave zuerst, übrige alphabetisch (ohne Groß-/Kleinschreibung), zuletzt der Block „Python <python_version> – PSF-2.0“ (in `main` mit `platform.python_version()`).
  - `main(out: str = 'THIRD_PARTY_LICENSES.txt') -> None` – schreibt UTF-8 mit `\n`; Python-Lizenz aus `os.path.join(sys.base_prefix, 'LICENSE.txt')`.
- Blockformat (Task 2 zeigt die Datei unverändert an):

```
Co-Trainer – Lizenzen der mitgelieferten Software

Co-Trainer selbst steht unter der MIT-Lizenz (siehe LICENSE).
Die Datei Co-Trainer.exe enthält außerdem die folgenden Pakete.

======================================================================
fmsave 0.11.0 – MIT
======================================================================
<Lizenztext>
```

- [ ] **Step 1: Tests schreiben.** In `tests/test_third_party.py` das Modul über `importlib.util.spec_from_file_location('third_party', ROOT / 'tools' / 'third_party.py')` laden (das Repo-Wurzelverzeichnis liegt nicht im `sys.path`).

```python
def test_runtime_dists_closure():
    names = {norm(d.metadata['Name']) for d in tp.runtime_dists()}
    assert {'fmsave', 'pywebview', 'zstandard', 'backports-zstd', 'pythonnet', 'bottle', 'proxy-tools'} <= names
    assert not names & {'cotrainer', 'pytest', 'pyinstaller', 'packaging'}

def test_license_text_falls_back_to_metadata():
    d = next(d for d in tp.runtime_dists() if norm(d.metadata['Name']) == 'proxy-tools')
    t = tp.license_text(d)
    assert t.startswith('Kein Lizenztext im Paket enthalten.') and 'MIT' in t and 'github.com/jtushman/proxy_tools' in t

def test_render_order_and_blocks():
    t = tp.render(tp.runtime_dists(), '3.12.x', 'PSF LICENSE TEXT')
    ls = t.splitlines()
    heads = [ls[i + 1] for i in range(len(ls) - 2) if ls[i].startswith('====') and ls[i + 2].startswith('====')]
    assert heads[0].startswith('fmsave 0.11.0 – MIT') and heads[-1].startswith('Python 3.12.x')
    assert heads[1:-1] == sorted(heads[1:-1], key=str.lower)
    assert 'Permission is hereby granted' in t and 'PSF LICENSE TEXT' in t

def test_checked_in_notices_match_installed_versions():
    t = (ROOT / 'THIRD_PARTY_LICENSES.txt').read_text(encoding='utf-8')
    for d in tp.runtime_dists():
        assert f"{d.metadata['Name']} {d.version} – " in t, d.metadata['Name']
```

- [ ] **Step 2:** `.venv\Scripts\python -m pytest tests/test_third_party.py -q` → FAIL (Datei `tools/third_party.py` fehlt).
- [ ] **Step 3:** `tools/third_party.py` nach den Interfaces bauen; Aufruf `python tools/third_party.py` ruft `main()`. Lizenzname im Blockkopf: `License-Expression`, sonst `License` (nur erste Zeile, gekürzt auf 60 Zeichen), sonst Classifier, sonst „unbekannt“.
- [ ] **Step 4:** `.venv\Scripts\python tools\third_party.py`, dann Tests erneut → PASS. `THIRD_PARTY_LICENSES.txt` durchsehen: zwölf Blöcke (elf Pakete + Python), keine Pfade aus dem eigenen Rechner (`Select-String -Pattern 'Users\\' THIRD_PARTY_LICENSES.txt` → keine Treffer).
- [ ] **Step 5:** `build.ps1`: nach den Tests `& $python tools\third_party.py` (bei Fehler abbrechen wie bei den Tests), PyInstaller zusätzlich `--add-data 'THIRD_PARTY_LICENSES.txt;.'`. Kommentarzeile „Nur index.html und taktik.js werden eingepackt“ entsprechend anpassen.
- [ ] **Step 6: Commit** `git add tools/third_party.py THIRD_PARTY_LICENSES.txt tests/test_third_party.py build.ps1` – „Lizenzen der mitgelieferten Software sammeln und mitpacken“.

### Task 2: Fenster „Über Co-Trainer“

**Files:**
- Create: `cotrainer/about.py`
- Modify: `cotrainer/api.py` (Methode `about`)
- Modify: `cotrainer/ui/index.html` (Link in der Seitenleiste und im Fuß des Assistenten, Fenster, `about` in `devApi`)
- Test: `tests/test_api.py`, `tests/test_ui_static.py`

**Interfaces:**
- Consumes: `THIRD_PARTY_LICENSES.txt` aus Task 1 (im Repo-Wurzelverzeichnis; gepackt unter `sys._MEIPASS`).
- Produces:
  - `cotrainer/about.py`: `notices_path() -> str` (gepackt: `os.path.join(sys._MEIPASS, 'THIRD_PARTY_LICENSES.txt')`, sonst `<Repo>/THIRD_PARTY_LICENSES.txt` = eine Ebene über dem Paket), `notices_text(path: str | None = None) -> str | None` (UTF-8, `None` wenn die Datei fehlt).
  - `Api.about() -> dict(version=__version__, license='MIT', notices=str | None)`.
  - JS: `openAbout()` öffnet `#modal`, `closeModal()` (gibt es schon) schließt.
- Texte im Fenster (fest):
  - Überschrift „Über Co-Trainer“, Zeile „Version 0.1.0“ (aus `about().version`).
  - „Co-Trainer ist freie Software unter der MIT-Lizenz. Es liest Football-Manager-Spielstände nur und verändert sie nie.“
  - „Die Spielstände werden mit der Bibliothek fmsave gelesen (MIT-Lizenz, github.com/rhiever/fmsave).“
  - „Co-Trainer ist ein Fanprojekt und steht in keiner Verbindung zu Sports Interactive oder SEGA. Football Manager ist eine Marke von Sports Interactive.“
  - darunter „Lizenzen der mitgelieferten Software“ und der Text in einem scrollbaren `<pre>` (höchstens 50vh hoch, `white-space:pre-wrap`); ohne Datei stattdessen „Die Lizenzhinweise fehlen in dieser Programmversion. Sie stehen im Repository in der Datei THIRD_PARTY_LICENSES.txt.“
  - Knopf „Schließen“.
- Linktext: Seitenleiste unter „Ordner ändern…“ der Knopf „Über Co-Trainer“ (Klasse `lnk` wie die anderen); im Assistenten-Fuß hinter „Version …“ ` · <button class="lnk" onclick="openAbout()">Über Co-Trainer</button>`.

- [ ] **Step 1: Tests schreiben.**

```python
# tests/test_api.py
def test_about_reports_version_license_and_fmsave(api):
    a = api.about()
    assert a['version'] == cotrainer.__version__ and a['license'] == 'MIT'
    assert 'fmsave 0.11.0 – MIT' in a['notices']

def test_about_without_notices_file(api, monkeypatch, tmp_path):
    monkeypatch.setattr(api_mod.about, 'notices_path', lambda: str(tmp_path / 'fehlt.txt'))
    assert api.about()['notices'] is None

# tests/test_ui_static.py
def test_about_modal_has_no_external_links():
    body = HTML[HTML.index('function openAbout'):]
    body = body[:body.index('\nfunction ')]
    assert 'href="http' not in body and "href='http" not in body and 'fmsave' in body

def test_dev_api_has_about():
    dev = HTML[HTML.index('async function devApi'):HTML.index('async function boot')]
    assert 'about:' in dev
```

- [ ] **Step 2:** `.venv\Scripts\python -m pytest tests/test_api.py tests/test_ui_static.py -q` → die vier neuen Tests FAIL.
- [ ] **Step 3:** `cotrainer/about.py` und `Api.about` nach den Interfaces (`api.py` importiert `about`; `Api.about` ruft `about.notices_text(about.notices_path())`, damit der Test `notices_path` ersetzen kann).
- [ ] **Step 4:** Oberfläche: `openAbout()` (async, `await API.about()`), Fenster mit den festen Texten, Inhalt per `esc()`; `devApi` bekommt `about:async()=>({version:'Entwicklermodus',license:'MIT',notices:null})`. Tests → PASS.
- [ ] **Step 5: Prüfen im Browser** (CLAUDE.md „Oberfläche im Browser prüfen“): Seitenleiste „Über Co-Trainer“ öffnet das Fenster mit dem Hinweis „Die Lizenzhinweise fehlen …“ (Entwicklermodus), „Schließen“ schließt; im Assistenten derselbe Link; hell und dunkel lesbar; Konsole ohne Fehler.
- [ ] **Step 6:** `.\build.ps1`, `dist\Co-Trainer.exe` starten, „Über Co-Trainer“ zeigt die Lizenzliste mit fmsave oben.
- [ ] **Step 7: Commit** – „Fenster „Über Co-Trainer“ mit Lizenzhinweisen“.

### Task 3: README

**Files:**
- Create: `README.md`
- Modify: `pyproject.toml` (`readme = "README.md"`, `license = "MIT"`)

**Interfaces:** keine Codeschnittstellen.

Abschnitte und Pflichtinhalte (Deutsch, kurz, ohne CA/PA-Beispiele):

1. **Co-Trainer** – ein Satz, was es tut (Spielstand von Football Manager 27 lesen; Kader, Transfers, Taktik, Training). Hinweis: Fanprojekt, keine Verbindung zu Sports Interactive/SEGA.
2. **Was Co-Trainer macht** – die fünf Bereiche (Kaderanalyse, Transfervorschläge, Taktik, Training, Kaderliste) mit je einem Satz; die drei Informationsstufen der Transfervorschläge (Aus, Scoutbericht, Werte), Standard „Aus“, weil genaue Werte ungescouteter Spieler das Spiel verändern. CA, PA und versteckte Attribute zeigt Co-Trainer nie.
3. **Starten** – `Co-Trainer.exe` aus dem neuesten Release laden, Doppelklick. Windows-Schutzhinweis: „Der Computer wurde durch Windows geschützt“ → „Weitere Informationen“ → „Trotzdem ausführen“ (das Programm ist nicht signiert). Voraussetzungen: Windows 10/11 mit Microsoft-Edge-WebView2 (normalerweise vorhanden, sonst über Windows Update oder microsoft.com), Football Manager 27 (die Spielinstallation liefert Liga- und Rollennamen; ohne sie wird trotzdem eingelesen). Ablauf in drei Schritten wie im Programm: Spielstand-Ordner (Vorschlag `Dokumente\Sports Interactive\Football Manager …\games`), Spielstand bestätigen, Analyse wählen. Das Einlesen dauert rund zwei Minuten.
4. **Sicherheit und Daten** – liest Spielstände nur, schreibt nie hinein; keine Internetverbindung, keine Telemetrie; Einstellungen in `%APPDATA%\Co-Trainer\settings.json`; Entfernen = `Co-Trainer.exe` und diesen Ordner löschen. Speichert das Spiel während des Einlesens, später neu einlesen.
5. **Grenzen** – nur Windows und Deutsch; unbekannte Rollen erscheinen als „?“ mit Standardrolle; Teamanweisungen werden noch nicht gelesen; Nationaltrainer-Karrieren und Spielstände mit zwei menschlichen Managern finden keinen Kader (Meldung im Programm).
6. **Aus dem Quellcode** – Python 3.12, `python -m uv venv --python 3.12 .venv`, `python -m uv pip install --python .venv -e ".[dev]"`, Start `.venv\Scripts\python -m cotrainer`, Tests `.venv\Scripts\python -m pytest tests -q -m "not save"` (Tests mit echten Spielständen brauchen `COTRAINER_TEST_SAVE`), `.exe` mit `.\build.ps1`.
7. **Lizenz** – MIT (`LICENSE`); mitgelieferte Software siehe `THIRD_PARTY_LICENSES.txt`, Spielstände gelesen mit [fmsave](https://github.com/rhiever/fmsave) (MIT).

- [ ] **Step 1:** `README.md` mit den sieben Abschnitten schreiben; `pyproject.toml` ergänzen.
- [ ] **Step 2: Prüfen:** `.venv\Scripts\python -m uv pip install --python .venv -e ".[dev]"` läuft ohne Fehler (pyproject gültig); `git grep -n -I "Users\\\\[A-Z]" README.md` → keine Treffer; jeder genannte Befehl und Pfad stimmt mit `CLAUDE.md` und dem Code überein (`settings.settings_path()`, `saves.default_saves_dir()`).
- [ ] **Step 3: Commit** – „README“.

### Task 4: Pull Request und Release v0.1.0

**Files:**
- Modify: `HANDOFF.md` („Was bisher gemacht wurde“ neuer Punkt für Teil 4; „Nächste Schritte“ Punkt 2 erledigt)

**Interfaces:**
- Consumes: Branch `teil-4-release` mit Task 1–3; `GH_TOKEN` aus der Benutzervariable `GITHUB_PERSONAL_ACCESS_TOKEN` (nie ausgeben); Push über einmaligen `http.extraheader` wie in `HANDOFF.md` Punkt 1 beschrieben.

- [ ] **Step 1:** Ganze Suite `.venv\Scripts\python -m pytest tests -q` (mit Spielständen, rund 6–12 Minuten) → alle grün; Ergebnis notieren.
- [ ] **Step 2:** `HANDOFF.md` nachtragen, committen, Branch pushen, Pull Request `teil-4-release` → `main` mit `gh pr create` (Titel „Teil 4: README, Lizenzhinweise, Release“, Beschreibung auf Deutsch: was drin ist, Testergebnis, offene Punkte; Abschlusszeile laut Commit-Anweisung).
- [ ] **Step 3: Nutzer fragen**, ob gemergt und das Release angelegt werden soll (Release ist sichtbar für alle, die Zugriff auf das Repo haben). Erst nach Ja weiter.
- [ ] **Step 4:** PR mergen (`gh pr merge --merge`), `main` lokal aktualisieren, `.\build.ps1` auf `main`, SHA-256 der `.exe` (`Get-FileHash dist\Co-Trainer.exe`).
- [ ] **Step 5:** `gh release create v0.1.0 dist\Co-Trainer.exe --title "Co-Trainer 0.1.0" --notes-file <Scratchpad>\release-notes.md --target main`. Release-Text: Kurzbeschreibung, Starten mit Windows-Schutzhinweis, WebView2, „liest nur, keine Internetverbindung“, bekannte Grenzen (aus README Abschnitt 5), SHA-256.
- [ ] **Step 6: Prüfen:** `gh release view v0.1.0 --json assets,tagName` zeigt `Co-Trainer.exe` mit der gebauten Größe; Repo weiterhin `PRIVATE` (`gh repo view --json visibility`).
