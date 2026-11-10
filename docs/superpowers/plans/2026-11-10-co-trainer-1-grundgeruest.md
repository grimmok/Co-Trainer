# Co-Trainer, Teil 1: Grundgerüst – Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aus dem Skript `extract.py` + `app.html` wird ein Programm `Co-Trainer.exe`: ein Fenster, geführter Start in vier Schritten, dieselben fünf Bereiche wie heute, ohne Batch-Datei und ohne erzeugte HTML-Datei.

**Architecture:** Python-Paket `cotrainer`. Die Leselogik aus `extract.py` wird zur Funktion `analyse()`, die ein Wörterbuch liefert statt HTML zu schreiben. Ein pywebview-Fenster (Edge WebView2) zeigt `cotrainer/ui/index.html`; die Oberfläche ruft Python über eine `Api`-Klasse und bekommt Fortschritt und Ergebnis per `evaluate_js` zurück. Eine Schutzfunktion prüft jedes Ergebnis, bevor es die Oberfläche erreicht.

**Tech Stack:** Python 3.12 (venv über `python -m uv`), `zstandard`, `pywebview` (WebView2), `pytest`, `PyInstaller` (eine `.exe`), Vanilla JS.

**Spec:** `docs/superpowers/specs/2026-11-09-fm-scout-app-design.md` (freigegeben am 10.11.2026). Projektwissen: `HANDOFF.md`, `CLAUDE.md`.

## Aufteilung des Umbaus

Die Spezifikation umfasst vier unabhängige Teile. Jeder ergibt für sich lauffähige Software und bekommt einen eigenen Plan:

| Teil | Inhalt | Spec-Abschnitte |
|---|---|---|
| **1 (dieser Plan)** | Paket, Fenster, geführter Start, Bereiche ein-/ausblenden, hell/dunkel, Einstellungen, `.exe` | 2.1–2.3, 2.6, 6, 8.2 (Programmeinstellungen), 9 |
| 2 | fmsave als Datenquelle, Kader nur erste Mannschaft, Nationalität, Scoutinggebiet als Filter, drei Informationsstufen der Transfervorschläge | 7.2, 8.1, 11 (Scoutinggebiet) |
| 3 | Neuer Taktik-Reiter (Schwachstellen, Verursacher, Abhilfe), Trainerbewertungen, Auswahl der Trainertendenzen, Trainingsfokus | 7.3, 7.4, 8.3, 8.4 |
| 4 | README, Lizenzhinweise, GitHub-Release | 9, 10 |

Die Pläne 2–4 werden geschrieben, wenn Teil 1 läuft.

## Global Constraints

- **CA, PA und versteckte Attribute** (Cons, Dirt, ImpM, InjPr, Vers) erscheinen nie in der Oberfläche und verlassen nie den Python-Teil Richtung Oberfläche. Das gilt auch für Persönlichkeitswerte und die Zahlen der Trainerbewertungen und Neigungen.
- **Potenzial** nur als Text, nie als Zahl.
- **Spielstände nur lesen.** Kein Aufruf öffnet eine `.fm`-Datei zum Schreiben.
- **Geld:** im Spielstand GBP, Anzeige in EUR, Faktor **1,1641**.
- **Attributblock zuordnen nur über `Block-ID (u32 bei −43) = Personen-ID − 1`.**
- **Neue Rollen-Fingerabdrücke** und **neu dekodierte Werte** nur nach Bestätigung durch den Nutzer. Dieser Plan dekodiert nichts Neues.
- **Oberfläche und Texte auf Deutsch**, mit den deutschen FM27-Begriffen.
- **Name:** Das Programm heißt „Co-Trainer“, die Datei `Co-Trainer.exe`, das Paket `cotrainer`, der Einstellungsordner `%APPDATA%\Co-Trainer`.
- **Keine Online-Funktionen:** kein Netzwerkzugriff zur Laufzeit.
- **Nur Windows.** Python **≥ 3.12** (Vorgriff auf fmsave in Teil 2).
- **Keine erzeugte HTML-Datei auf der Festplatte, keine Batch-Datei.**
- **Stil „Dunkel & neutral“** (Standard): Hintergrund `#0f1216`, Karten `#161a20`, Rand `#232a33`, Text `#e6e8eb`, Akzent `#4fd1a5`, Warnung Rand `#f0a020` auf `#2a1f12` mit Text `#f5c27a`. **„Hell & klar“:** Hintergrund `#f5f6f8`, Karten `#ffffff`, Rand `#e3e6ea`, Text `#1c2128`, Akzent `#0e7a45`, Warnung Rand `#f0a020` auf `#fff4e5` mit Text `#8a4b00`. Schrift `Segoe UI, system-ui, sans-serif`.
- Erkundungsskripte und entpackte Spielstand-Teile gehören ins Scratchpad, nicht ins Repo.

## Review Focus

1. **Gemerkter Spielstand-Ordner existiert nicht mehr** (umbenannt, Laufwerk fehlt): Das Programm zeigt wieder Schritt 1 mit Hinweis, statt mit einer leeren Liste oder einem Fehler zu starten. → Test in Task 5.
2. **Spielstand lässt sich nicht lesen** (ältere Spielversion, beschädigt, gerade vom Spiel geschrieben): Klartext-Fehlermeldung mit „Anderen Spielstand wählen“, kein hängender Fortschritt. → Tests in Task 1 und 5.
3. **Spielstand ohne eigene Taktik und ohne `config.json`** (wie Paris): Alle Bereiche werden trotzdem gezeichnet, mit Standardformation. → Test in Task 1.
4. **Doppelklick auf „Analyse starten“ oder „Neu einlesen“, während das Einlesen läuft:** Es läuft nur ein Einlesen, der zweite Aufruf wird abgewiesen. → Test in Task 5.
5. **Beschädigte `settings.json`:** Das Programm startet mit Standardwerten, statt abzustürzen. → Test in Task 4.

---

## Dateistruktur

| Datei | Aufgabe |
|---|---|
| `pyproject.toml` | Paketdaten, Abhängigkeiten, pytest-Einstellungen |
| `cotrainer/__init__.py` | `__version__ = "0.1.0"` |
| `cotrainer/extract.py` | Leselogik (aus `extract.py` verschoben): `analyse()`, Konsolenaufruf |
| `cotrainer/guard.py` | `assert_public()` – Schutz gegen versteckte Werte |
| `cotrainer/saves.py` | Spielstand-Ordner finden, Spielstände auflisten, Kurzinfo lesen |
| `cotrainer/settings.py` | Programmeinstellungen in `%APPDATA%\Co-Trainer\settings.json` |
| `cotrainer/api.py` | Brücke Oberfläche ↔ Python |
| `cotrainer/app.py`, `cotrainer/__main__.py` | Fenster erzeugen und starten |
| `cotrainer/ui/index.html` | Oberfläche (aus `app.html` verschoben und erweitert) |
| `tests/…` | Tests je Modul; `tests/conftest.py` mit dem Testspielstand |
| `build.ps1` | Baut `dist\Co-Trainer.exe` |

Entfallen: `extract.py` (Wurzel), `app.html`, `FM-Scout starten.bat`, `FM-Scout.html`. `config.json` bleibt nur als Entwicklerhilfe und wird nicht mitgeliefert.

---

### Task 1: Paket anlegen, Leselogik als `analyse()`

**Files:**
- Create: `pyproject.toml`, `cotrainer/__init__.py`, `tests/conftest.py`, `tests/test_extract.py`
- Move: `extract.py` → `cotrainer/extract.py`
- Modify: `.gitignore` (zusätzlich `.venv/`, `dist/`, `build/`, `cotrainer/ui/dev-data.json`)

**Interfaces:**
- Produces:
  - `cotrainer.extract.analyse(save_path: str, cfg: dict | None = None, progress: Callable[[str], None] | None = None) -> dict` – dasselbe Wörterbuch, das heute als JSON in `FM-Scout.html` steht (`meta`, `coach`, `tactic`, `squad`, `pool`, `training`).
  - `cotrainer.extract.SaveReadError(Exception)` – mit deutschem Klartext als Meldung.
  - `cotrainer.extract.PROGRESS_STEPS: tuple[str, ...]` – die Texte, die `progress` in dieser Reihenfolge erhält: `"Spielstand wird geöffnet …"`, `"Spieler werden gelesen …"`, `"Verträge und Vereine werden gelesen …"`, `"Ligen und Finanzen werden gelesen …"`, `"Training und Taktik werden gelesen …"`, `"Kader wird ausgewertet …"`.
  - Konsolenaufruf `python -m cotrainer.extract [Pfad.fm | Nummer] [--list] [--dump Datei.json]` – wie bisher inklusive `FMS_DEBUG` und `FMS_ROLES`; schreibt nur mit `--dump` eine Datei.
  - Fixture `ravenna_save` in `tests/conftest.py`: Pfad aus der Umgebungsvariable `COTRAINER_TEST_SAVE`, sonst `~\Documents\Sports Interactive\Football Manager 26\games\Haribaert Kachinski – Ravenna.fm`; `pytest.skip`, wenn die Datei fehlt. Fixture `ravenna_data` (Session-Scope) = `analyse(ravenna_save)`.

- [ ] **Step 1: Umgebung anlegen.** `python -m uv venv --python 3.12 .venv`; `pyproject.toml` mit `name = "cotrainer"`, `requires-python = ">=3.12"`, Abhängigkeiten `zstandard`, `pywebview`, Entwickler-Abhängigkeiten `pytest`, `pyinstaller`, und `[tool.pytest.ini_options] markers = ["save: braucht einen echten Spielstand"]`. `python -m uv pip install -e ".[dev]"`. Prüfen: `.venv\Scripts\python -c "import zstandard, webview"` läuft ohne Fehler.

- [ ] **Step 2: Fehlschlagende Tests schreiben** (`tests/test_extract.py`):

```python
import pytest
from cotrainer import extract

@pytest.mark.save
def test_analyse_ravenna(ravenna_data):
    m = ravenna_data["meta"]
    assert m["manager"] == "Haribaert Kachinski"
    assert m["club"] == "Ravenna Football Club 1913"
    assert m["scout_area"] == 4 and m["scout_area_name"] == "Eigenes Land"
    assert m["finances"]["transfer_budget"] == 604815
    assert ravenna_data["tactic"]["source"] == "Spielstand"
    assert ravenna_data["tactic"]["style_name"] == "Gegenpressing"
    assert len(ravenna_data["squad"]) > 20 and len(ravenna_data["pool"]) > 1000
    assert ravenna_data["coach"]["coaching"]["Torhüter"] == "Sehr schlecht"

@pytest.mark.save
def test_progress_steps_in_order(ravenna_save):
    seen = []
    extract.analyse(ravenna_save, progress=seen.append)
    assert tuple(seen) == extract.PROGRESS_STEPS

def test_no_config_and_no_own_tactic_still_has_slots():
    # Review Focus 3: read_tactics liefert nichts, cfg ist leer
    t = extract.default_tactic()
    assert len(t["slots"]) == 11 and t["source"] == "Standard"

def test_unreadable_file_raises_clear_error(tmp_path):
    f = tmp_path / "kaputt.fm"; f.write_bytes(b"kein spielstand" * 100)
    with pytest.raises(extract.SaveReadError, match="kein lesbarer FM27-Spielstand"):
        extract.analyse(str(f))

def test_save_is_opened_read_only(monkeypatch, tmp_path):
    f = tmp_path / "x.fm"; f.write_bytes(b"x")
    modes = []
    real_open = open
    monkeypatch.setattr("builtins.open", lambda p, mode="r", *a, **k: (modes.append((str(p), mode)), real_open(p, mode, *a, **k))[1])
    with pytest.raises(extract.SaveReadError):
        extract.analyse(str(f))
    assert all("w" not in m and "a" not in m and "+" not in m for p, m in modes if p.endswith(".fm"))
```

Den genauen Wert von `transfer_budget` vor dem Eintragen aus einem Lauf des heutigen `extract.py` ablesen (laut `HANDOFF.md` 604.815 €); weicht er ab, den abgelesenen Wert eintragen und im Commit vermerken.

- [ ] **Step 3: Tests laufen lassen.** `.venv\Scripts\python -m pytest tests/test_extract.py -v` → FAIL (`cotrainer.extract` fehlt).

- [ ] **Step 4: `extract.py` verschieben und umbauen.** `git mv extract.py cotrainer/extract.py`. Den Rumpf von `main()` ab dem Einlesen in `analyse(save_path, cfg=None, progress=None)` verschieben; `analyse` gibt `data` zurück und schreibt keine Datei. `main()` behält `--list`, die Spielstandwahl und `config.json` (nur wenn im aktuellen Ordner vorhanden) und bekommt `--dump`. Jede Ausnahme beim Öffnen oder Dekodieren (fehlender Abschnitt `game_db`, zstd-Fehler, `KeyError`, `struct.error`, `IndexError`) wird in `SaveReadError("Das ist kein lesbarer FM27-Spielstand: <Dateiname>")` gewandelt. Neu `default_tactic() -> dict`: 4-2-3-1 mit `ROLE_DEFAULT`-Rollen und `source="Standard"`; `analyse` nimmt sie, wenn weder Spielstand noch `cfg` Slots liefern.

- [ ] **Step 5: Tests laufen lassen.** Gleiches Kommando → PASS. Zusätzlich `.venv\Scripts\python -m cotrainer.extract --list` zeigt die Spielstandliste.

- [ ] **Step 6: Commit.** `git add -A && git commit -m "Paket cotrainer: Leselogik als analyse() statt HTML-Ausgabe"`

---

### Task 2: Schutz gegen versteckte Werte

**Files:**
- Create: `cotrainer/guard.py`, `tests/test_guard.py`

**Interfaces:**
- Produces: `cotrainer.guard.assert_public(data: dict) -> dict` (gibt `data` unverändert zurück) und `cotrainer.guard.HiddenValueError(Exception)`.
- Regeln: Kein Schlüssel auf irgendeiner Ebene darf (ohne Beachtung der Groß-/Kleinschreibung) in `{"ca", "pa", "pers", "cons", "dirt", "impm", "injpr", "vers", "_w", "q"}` liegen. In `squad[*].a` und `pool[*].a` sind genau die 49 Schlüssel `ATTR_KEYS − HIDDEN` erlaubt. `coach.coaching` und `coach.mental` dürfen nur Zeichenketten als Werte haben. Der Schlüssel `tendencies` darf nur eine Liste von Zeichenketten sein.

- [ ] **Step 1: Fehlschlagende Tests schreiben:**

```python
import copy, pytest
from cotrainer.guard import assert_public, HiddenValueError

OK = {"meta": {}, "coach": {"coaching": {"Taktik": "Gut"}, "mental": {}, "tendencies": ["Taktiktüftler"]},
      "squad": [{"id": 1, "a": {"Pas": 12}}], "pool": []}

def test_clean_data_passes():
    assert assert_public(OK) is OK

@pytest.mark.parametrize("path,key,value", [
    (("squad", 0), "ca", 120), (("squad", 0), "PA", 150), (("squad", 0), "pers", [1] * 8),
    (("squad", 0, "a"), "Cons", 9), (("squad", 0, "a"), "InjPr", 12), (("meta",), "q", 3),
])
def test_forbidden_keys_raise(path, key, value):
    d = copy.deepcopy(OK); node = d
    for p in path: node = node[p]
    node[key] = value
    with pytest.raises(HiddenValueError):
        assert_public(d)

def test_coach_numbers_raise():
    d = copy.deepcopy(OK); d["coach"]["coaching"]["Taktik"] = 16
    with pytest.raises(HiddenValueError):
        assert_public(d)

def test_numeric_tendencies_raise():
    d = copy.deepcopy(OK); d["coach"]["tendencies"] = {"Offensive": 10}
    with pytest.raises(HiddenValueError):
        assert_public(d)

@pytest.mark.save
def test_real_result_is_public(ravenna_data):
    assert_public(ravenna_data)
```

- [ ] **Step 2:** `.venv\Scripts\python -m pytest tests/test_guard.py -v` → FAIL (Modul fehlt).
- [ ] **Step 3:** `assert_public` in `cotrainer/guard.py` umsetzen (rekursiver Durchlauf über Wörterbücher und Listen; Fehlermeldung nennt den Pfad des Verstoßes).
- [ ] **Step 4:** Gleiches Kommando → PASS. Schlägt `test_real_result_is_public` fehl, den Verstoß in `cotrainer/extract.py` beheben, nicht die Regel lockern.
- [ ] **Step 5: Commit.** `git commit -am "Schutzfunktion: versteckte Werte erreichen die Oberfläche nie"`

---

### Task 3: Spielstände finden und Kurzinfo lesen

**Files:**
- Create: `cotrainer/saves.py`, `tests/test_saves.py`
- Modify: `cotrainer/extract.py` (`list_saves`, `find_save`, `print_saves` nutzen `cotrainer.saves`)

**Interfaces:**
- Produces:
  - `default_saves_dir() -> str | None` – der `games`-Ordner unter `~\Documents\Sports Interactive\Football Manager*\` mit dem jüngsten Spielstand; `None`, wenn es keinen gibt.
  - `@dataclass SaveInfo: path: str, name: str, saved: str` (`saved` als ISO-Zeit der letzten Änderung).
  - `list_saves(folder: str) -> list[SaveInfo]` – nur `*.fm`, neueste zuerst, ohne Dateien, deren Name `backup` oder `autosave` enthält (Groß-/Kleinschreibung egal). Fehlt der Ordner: leere Liste.
  - `read_summary(path: str) -> dict` mit `manager`, `club`, `game_date` (ISO) – liest nur das Inhaltsverzeichnis und den Abschnitt `save_game_summary`, nicht `game_db`. Wirft `extract.SaveReadError` bei unlesbarer Datei.

- [ ] **Step 1: Fehlschlagende Tests schreiben:**

```python
import os, time, pytest
from cotrainer import saves
from cotrainer.extract import SaveReadError

def _mk(folder, name, age):
    p = folder / name; p.write_bytes(b"x"); t = time.time() - age; os.utime(p, (t, t)); return p

def test_list_newest_first_without_backups(tmp_path):
    _mk(tmp_path, "alt.fm", 300); _mk(tmp_path, "neu.fm", 10)
    _mk(tmp_path, "last save overwrite backup.fm", 1); _mk(tmp_path, "Autosave 3.fm", 2); _mk(tmp_path, "notiz.txt", 1)
    assert [s.name for s in saves.list_saves(str(tmp_path))] == ["neu.fm", "alt.fm"]

def test_missing_folder_gives_empty_list(tmp_path):
    assert saves.list_saves(str(tmp_path / "gibt-es-nicht")) == []

def test_summary_of_garbage_raises(tmp_path):
    p = _mk(tmp_path, "kaputt.fm", 1)
    with pytest.raises(SaveReadError):
        saves.read_summary(str(p))

@pytest.mark.save
def test_summary_ravenna_is_fast(ravenna_save):
    t = time.time(); s = saves.read_summary(ravenna_save)
    assert s["manager"] == "Haribaert Kachinski" and "Ravenna" in s["club"]
    assert s["game_date"][:4] == "2026"
    assert time.time() - t < 5
```

- [ ] **Step 2:** `.venv\Scripts\python -m pytest tests/test_saves.py -v` → FAIL.
- [ ] **Step 3:** `cotrainer/saves.py` umsetzen. `read_summary` sucht den letzten zstd-Frame (Magic `28 b5 2f fd`) rückwärts, liest daraus den Eintrag `save_game_summary` (`Offset + 26`) und entpackt nur diesen Frame; Manager, Verein und Datum werden mit demselben Code gelesen wie in `analyse` (dort in eine gemeinsame Funktion `parse_summary(raw: bytes) -> dict` auslagern).
- [ ] **Step 4:** Gleiches Kommando → PASS; danach `pytest tests -v` komplett → PASS.
- [ ] **Step 5: Commit.** `git commit -am "Spielstände auflisten und Kurzinfo lesen"`

---

### Task 4: Programmeinstellungen

**Files:**
- Create: `cotrainer/settings.py`, `tests/test_settings.py`

**Interfaces:**
- Produces:
  - `@dataclass Settings: saves_dir: str | None = None, game_dir: str | None = None, theme: str = "dark", info_level: str = "aus", skip_spoiler_warning: bool = False`
  - `settings_path() -> str` → `%APPDATA%\Co-Trainer\settings.json`
  - `load(path: str | None = None) -> Settings` – fehlende oder beschädigte Datei ergibt Standardwerte; unbekannte Schlüssel werden ignoriert; `theme` außerhalb `{"dark", "light"}` wird `"dark"`, `info_level` außerhalb `{"aus", "scoutbericht", "werte"}` wird `"aus"`.
  - `save(s: Settings, path: str | None = None) -> None` – legt den Ordner an, schreibt UTF-8.

`info_level` und `skip_spoiler_warning` werden in Teil 2 benutzt und hier nur gespeichert.

- [ ] **Step 1: Fehlschlagende Tests schreiben:**

```python
from cotrainer import settings as st

def test_roundtrip(tmp_path):
    p = str(tmp_path / "a" / "settings.json")
    st.save(st.Settings(saves_dir=r"C:\x", theme="light"), p)
    s = st.load(p)
    assert s.saves_dir == r"C:\x" and s.theme == "light" and s.info_level == "aus"

def test_missing_file_gives_defaults(tmp_path):
    assert st.load(str(tmp_path / "nix.json")) == st.Settings()

def test_corrupt_file_gives_defaults(tmp_path):      # Review Focus 5
    p = tmp_path / "settings.json"; p.write_text("{kaputt", encoding="utf-8")
    assert st.load(str(p)) == st.Settings()

def test_invalid_values_fall_back(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text('{"theme": "lila", "info_level": "alles", "fremd": 1}', encoding="utf-8")
    s = st.load(str(p))
    assert s.theme == "dark" and s.info_level == "aus"

def test_path_is_under_appdata(monkeypatch):
    monkeypatch.setenv("APPDATA", r"C:\Users\x\AppData\Roaming")
    assert st.settings_path() == r"C:\Users\x\AppData\Roaming\Co-Trainer\settings.json"
```

- [ ] **Step 2:** `.venv\Scripts\python -m pytest tests/test_settings.py -v` → FAIL.
- [ ] **Step 3:** `cotrainer/settings.py` umsetzen.
- [ ] **Step 4:** Gleiches Kommando → PASS.
- [ ] **Step 5: Commit.** `git commit -am "Programmeinstellungen in %APPDATA%\Co-Trainer"`

---

### Task 5: Brücke zwischen Oberfläche und Python

**Files:**
- Create: `cotrainer/api.py`, `tests/test_api.py`

**Interfaces:**
- Consumes: `extract.analyse`, `extract.SaveReadError`, `guard.assert_public`, `saves.default_saves_dir`, `saves.list_saves`, `saves.read_summary`, `settings.load`, `settings.save`.
- Produces: `class Api` mit `__init__(self, settings_file: str | None = None)` und `self.window = None` (wird von `app.py` gesetzt). Alle Methoden geben JSON-taugliche Wörterbücher zurück:
  - `get_state() -> dict` → `{"saves_dir": str | None, "suggested_dir": str | None, "theme": str, "version": str, "saves": [ {path, name, saved} … ]}`. Ist ein gemerkter Ordner nicht mehr vorhanden, ist `saves_dir` `None` und zusätzlich `"notice": "Der gemerkte Spielstand-Ordner wurde nicht gefunden."`.
  - `set_saves_dir(path: str) -> dict` → `{"ok": True, "count": int}` und speichert; bei fehlendem Ordner `{"ok": False, "error": "Ordner nicht gefunden."}`, bei 0 Spielständen `{"ok": False, "error": "In diesem Ordner liegen keine Spielstände (.fm)."}`.
  - `browse_saves_dir() -> dict` → öffnet den Ordnerdialog von pywebview, `{"path": str | None}`.
  - `list_saves() -> dict` → `{"saves": [...]}`.
  - `summary(path: str) -> dict` → `{"ok": True, "manager", "club", "game_date"}` oder `{"ok": False, "error": str}`.
  - `analyse(path: str) -> dict` → startet einen Thread und gibt sofort `{"started": True}` zurück; läuft schon ein Einlesen: `{"started": False, "error": "Es wird bereits ein Spielstand eingelesen."}`. Der Thread ruft in der Oberfläche `CT.onProgress(index, total, text)`, am Ende genau eines von `CT.onResult(data)` oder `CT.onError(text)` auf, jeweils über `self.window.evaluate_js`. `data` geht vorher durch `assert_public`. Unerwartete Ausnahmen ergeben `CT.onError("Unerwarteter Fehler beim Einlesen: <Typ>")`; `HiddenValueError` ergibt `CT.onError("Interner Schutz hat ausgelöst – bitte melden.")`.
  - `set_theme(theme: str) -> dict` → speichert, `{"ok": True}`.
  - `set_game_dir(path: str) -> dict` → `{"ok": True}`, wenn darunter `shared\data\database\db¸0¸0_fm\lang_db.dat` liegt, und speichert; sonst `{"ok": False, "error": "In diesem Ordner wurde die Sprachdatenbank des Spiels nicht gefunden."}`. `get_state()` enthält zusätzlich `"lang_db_found": bool` (gemerkter Spielordner oder automatische Suche aus `extract.find_lang_db`). `analyse` gibt den gefundenen Pfad als `cfg={"lang_db": …}` an `extract.analyse` weiter.
  - `join(timeout: float = 120) -> None` – wartet auf den Thread (für Tests).

- [ ] **Step 1: Fehlschlagende Tests schreiben:**

```python
import json, threading, pytest
from cotrainer import api as api_mod, extract

class FakeWindow:
    def __init__(self): self.calls = []
    def evaluate_js(self, js): self.calls.append(js)

@pytest.fixture
def api(tmp_path):
    a = api_mod.Api(settings_file=str(tmp_path / "settings.json")); a.window = FakeWindow(); return a

def test_state_reports_missing_remembered_folder(api, tmp_path):        # Review Focus 1
    assert api.set_saves_dir(str(tmp_path / "weg"))["ok"] is False
    (tmp_path / "g").mkdir(); (tmp_path / "g" / "a.fm").write_bytes(b"x")
    assert api.set_saves_dir(str(tmp_path / "g")) == {"ok": True, "count": 1}
    (tmp_path / "g" / "a.fm").unlink(); (tmp_path / "g").rmdir()
    s = api.get_state()
    assert s["saves_dir"] is None and "nicht gefunden" in s["notice"]

def test_game_dir_without_lang_db_is_rejected(api, tmp_path):
    assert api.set_game_dir(str(tmp_path))["ok"] is False
    d = tmp_path / "shared" / "data" / "database" / "db" / "2700" / "2700_fm"; d.mkdir(parents=True); (d / "lang_db.dat").write_bytes(b"x")
    assert api.set_game_dir(str(tmp_path)) == {"ok": True}

def test_empty_folder_is_rejected(api, tmp_path):
    assert api.set_saves_dir(str(tmp_path))["error"] == "In diesem Ordner liegen keine Spielstände (.fm)."

def test_analyse_reports_progress_then_result(api, monkeypatch):
    def fake(path, cfg=None, progress=None):
        for s in extract.PROGRESS_STEPS: progress(s)
        return {"meta": {"club": "X"}, "coach": {}, "squad": [], "pool": []}
    monkeypatch.setattr(extract, "analyse", fake)
    assert api.analyse("x.fm") == {"started": True}; api.join()
    calls = api.window.calls
    assert sum(c.startswith("CT.onProgress(") for c in calls) == len(extract.PROGRESS_STEPS)
    assert calls[-1].startswith("CT.onResult(") and json.loads(calls[-1][len("CT.onResult("):-1])["meta"]["club"] == "X"

def test_unreadable_save_reports_error(api, monkeypatch):                # Review Focus 2
    def fake(path, cfg=None, progress=None): raise extract.SaveReadError("Das ist kein lesbarer FM27-Spielstand: x.fm")
    monkeypatch.setattr(extract, "analyse", fake)
    api.analyse("x.fm"); api.join()
    assert api.window.calls[-1] == 'CT.onError("Das ist kein lesbarer FM27-Spielstand: x.fm")'

def test_hidden_value_never_reaches_window(api, monkeypatch):
    monkeypatch.setattr(extract, "analyse", lambda p, cfg=None, progress=None: {"squad": [{"ca": 150}]})
    api.analyse("x.fm"); api.join()
    assert all("150" not in c for c in api.window.calls) and api.window.calls[-1].startswith("CT.onError(")

def test_second_analyse_is_rejected_while_running(api, monkeypatch):    # Review Focus 4
    gate = threading.Event()
    monkeypatch.setattr(extract, "analyse", lambda p, cfg=None, progress=None: (gate.wait(5), {"squad": [], "pool": []})[1])
    assert api.analyse("x.fm")["started"] is True
    assert api.analyse("x.fm") == {"started": False, "error": "Es wird bereits ein Spielstand eingelesen."}
    gate.set(); api.join()
    assert sum(c.startswith("CT.onResult(") for c in api.window.calls) == 1
```

- [ ] **Step 2:** `.venv\Scripts\python -m pytest tests/test_api.py -v` → FAIL.
- [ ] **Step 3:** `cotrainer/api.py` umsetzen. `Api.analyse` ruft `extract.analyse` über den Modulnamen auf (damit `monkeypatch` greift) und gibt Texte mit `json.dumps(..., ensure_ascii=False)` an `evaluate_js` weiter.
- [ ] **Step 4:** Gleiches Kommando → PASS.
- [ ] **Step 5: Commit.** `git commit -am "Api: Zustand, Spielstandwahl, Einlesen mit Fortschritt"`

---

### Task 6: Oberfläche – geführter Start, Bereiche, hell/dunkel

**Files:**
- Move: `app.html` → `cotrainer/ui/index.html`
- Modify: `cotrainer/ui/index.html`, `.claude/launch.json` (Vorschau liefert weiter den Repo-Ordner aus; Adresse wird `http://127.0.0.1:8765/cotrainer/ui/index.html?dev=1&v=…`)

**Interfaces:**
- Consumes: die `Api`-Methoden aus Task 5 über `window.pywebview.api.<name>(…)` (liefern Promises).
- Produces: globales Objekt `CT` mit `CT.onProgress(index, total, text)`, `CT.onResult(data)`, `CT.onError(text)`.
- Entwicklermodus: Mit `?dev=1` und ohne `window.pywebview` lädt die Seite `dev-data.json` aus demselben Ordner (erzeugt mit `python -m cotrainer.extract --dump cotrainer/ui/dev-data.json`) und überspringt die Schritte 1–2. Die Datei ist in `.gitignore`.

Inhalt, festgelegt durch Spec Abschnitt 6 und den Entwurf `.superpowers/brainstorm/ablauf-v2.html`:

- **Schritt 1 „Wo liegen deine Football-Manager-Spielstände?“** – nur wenn `get_state().saves_dir` leer ist. Feld mit `suggested_dir`, Knopf „Durchsuchen…“ (`browse_saves_dir`), Rückmeldung „✓ Ordner gefunden – N Spielstände (Sicherungen ausgeblendet)“ oder die Fehlermeldung aus `set_saves_dir`, Knopf „Weiter“. Ein `notice` aus `get_state` steht darüber.
- **Schritt 2 „Diesen Spielstand laden?“** – neuester Spielstand mit Name, „gespeichert TT.MM.JJJJ, HH:MM“, Verein und „TT.MM.JJJJ im Spiel“ (aus `summary`). Knöpfe „Ja, laden“ und „Anderen Spielstand wählen…“ (Liste aller Spielstände). Liefert `summary` einen Fehler, steht er an der Karte und „Ja, laden“ ist gesperrt.
- **Schritt 3 „Welche Analyse möchtest du sehen?“** – sechs Karten: „Alles“, „Nur Kaderanalyse“, „Nur Transfervorschläge“, „Nur Trainer & Taktik“, „Nur Trainingsvorschlag“, „Nur Kaderliste“; Knopf „Analyse starten“.
- **Einlesen** – Fortschrittsbalken und der Text aus `CT.onProgress`. Bei `CT.onError`: Meldung, Knöpfe „Anderen Spielstand wählen…“ und „Nochmal versuchen“.
- **Schritt 4 Ergebnis** – links Spalte „Anzeigen“ mit fünf Häkchen (Kaderanalyse, Transfervorschläge, Trainer & Taktik, Training, Kaderliste), darunter „Spielstand wechseln…“, „Neu einlesen“, „Hell/Dunkel“, „Ordner ändern…“. Rechts stehen die angehakten Bereiche untereinander in dieser Reihenfolge; die bisherigen Funktionen `vKader`, `vTransfer`, `vTaktik`, `vTraining`, `vSpieler` liefern weiter den Inhalt. Die Reiterleiste (`TABS`) entfällt. Welche Bereiche sichtbar sind, wird je Karriere im vorhandenen `localStorage`-Zustand gespeichert (`S.visible`); die Wahl aus Schritt 3 überschreibt ihn beim Start.
- **Spielordner** – ist `lang_db_found` falsch, steht in Schritt 2 ein Hinweis „Ligen- und Rollennamen fehlen, weil die Spielinstallation nicht gefunden wurde.“ mit Knopf „Spielordner wählen…“ (`set_game_dir`). Das Einlesen funktioniert auch ohne.
- **Farben** – die bisherigen CSS-Variablen in `:root` bekommen die Werte aus „Global Constraints“; `html[data-theme="light"]` setzt die hellen Werte. Umschalten ruft `set_theme` und setzt das Attribut.
- **Titel** – „Co-Trainer · <Verein> · <Liga>“; überall im Text „Co-Trainer“ statt „FM-Scout“.

- [ ] **Step 1:** `git mv app.html cotrainer/ui/index.html`; `const DATA=/*__DATA__*/null;` durch `let DATA=null;` ersetzen und das bisherige Starten in `function start(data)` fassen. `python -m cotrainer.extract --dump cotrainer/ui/dev-data.json` ausführen.
- [ ] **Step 2:** Entwicklermodus, `CT`-Objekt und die Schritte 1–3 samt Einlese-Ansicht einbauen.
- [ ] **Step 3:** Ergebnisansicht mit Spalte „Anzeigen“ und gestapelten Bereichen einbauen, Reiterleiste entfernen.
- [ ] **Step 4:** Farbvariablen und Umschalter hell/dunkel einbauen; „FM-Scout“ in sichtbaren Texten ersetzen.
- [ ] **Step 5: Im Browser prüfen.** Vorschau „fmscout“ starten, `…/cotrainer/ui/index.html?dev=1&v=<Zahl>` laden. Erwartet: Schritt 3 erscheint; nach „Alles“ + „Analyse starten“ stehen fünf Bereiche untereinander; jedes Häkchen blendet seinen Bereich aus und wieder ein; „Hell/Dunkel“ wechselt die Farben; die Konsole zeigt keine Fehler. Zusätzlich in der Konsole prüfen: `JSON.stringify(DATA).match(/"(ca|pa|pers|Cons|Dirt|ImpM|InjPr|Vers)":/i)` ergibt `null`.
- [ ] **Step 6: Commit.** `git add -A && git commit -m "Oberfläche: geführter Start, Bereiche ein-/ausblendbar, hell/dunkel"`

---

### Task 7: Fenster und Programmstart

**Files:**
- Create: `cotrainer/app.py`, `cotrainer/__main__.py`, `tests/test_app.py`

**Interfaces:**
- Consumes: `api.Api`, `settings.settings_path`.
- Produces:
  - `app.ui_path() -> str` – Pfad zu `ui/index.html`, auch im gepackten Programm (`sys._MEIPASS`).
  - `app.main() -> None` – erzeugt das Fenster (`title="Co-Trainer"`, 1280 × 860, Mindestgröße 1000 × 700, `js_api=Api()`), setzt `api.window`, startet mit `webview.start(private_mode=False, storage_path=<%APPDATA%\Co-Trainer\webview>)`, damit `localStorage` zwischen Starts erhalten bleibt.
  - Fehlt WebView2 (pywebview meldet einen Fehler beim Start), zeigt `main()` ein Windows-Meldungsfenster: „Co-Trainer braucht die Microsoft-Edge-WebView2-Laufzeit. Sie ist bei Windows 10/11 normalerweise vorhanden. Bitte über Windows Update oder von microsoft.com nachinstallieren.“
  - `python -m cotrainer` ruft `app.main()`.

- [ ] **Step 1: Fehlschlagenden Test schreiben:**

```python
import os
from cotrainer import app

def test_ui_path_exists():
    assert os.path.isfile(app.ui_path()) and app.ui_path().endswith(os.path.join("ui", "index.html"))

def test_ui_path_in_frozen_app(monkeypatch, tmp_path):
    (tmp_path / "cotrainer" / "ui").mkdir(parents=True); (tmp_path / "cotrainer" / "ui" / "index.html").write_text("x")
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path), raising=False); monkeypatch.setattr("sys.frozen", True, raising=False)
    assert app.ui_path() == str(tmp_path / "cotrainer" / "ui" / "index.html")
```

- [ ] **Step 2:** `.venv\Scripts\python -m pytest tests/test_app.py -v` → FAIL.
- [ ] **Step 3:** `cotrainer/app.py` und `cotrainer/__main__.py` umsetzen.
- [ ] **Step 4:** Gleiches Kommando → PASS.
- [ ] **Step 5: Von Hand prüfen.** `.venv\Scripts\python -m cotrainer`. Erwartet: Fenster „Co-Trainer“; beim ersten Start Schritt 1 mit vorgeschlagenem Ordner; Schritt 2 zeigt den neuesten Spielstand mit Verein und Spieldatum; nach Schritt 3 läuft der Fortschritt durch sechs Texte; das Ergebnis erscheint. Programm schließen und neu starten: Schritt 1 wird übersprungen, hell/dunkel und die angehakten Bereiche sind erhalten. Im Spielstand-Ordner hat sich kein Änderungsdatum einer `.fm`-Datei geändert.
- [ ] **Step 6: Commit.** `git commit -am "Programmfenster mit pywebview"`

---

### Task 8: `Co-Trainer.exe` bauen, Altes entfernen, Doku anpassen

**Files:**
- Create: `build.ps1`
- Delete: `FM-Scout starten.bat`, `FM-Scout.html` (lokal, nicht im Repo)
- Modify: `CLAUDE.md`, `HANDOFF.md`, `.gitignore`, `.claude/launch.json`

**Interfaces:**
- Produces: `.\build.ps1` erzeugt `dist\Co-Trainer.exe` (PyInstaller, eine Datei, ohne Konsolenfenster, `cotrainer/ui` als Daten ohne `dev-data.json`, Name `Co-Trainer`). `config.json` wird nicht eingepackt.

- [ ] **Step 1:** `build.ps1` schreiben: führt erst `.venv\Scripts\python -m pytest tests -q` aus und bricht bei Fehlern ab, dann `.venv\Scripts\python -m PyInstaller --noconfirm --onefile --windowed --name Co-Trainer --add-data "cotrainer/ui/index.html;cotrainer/ui" cotrainer/__main__.py`.
- [ ] **Step 2:** `.\build.ps1` ausführen. Erwartet: Tests grün, `dist\Co-Trainer.exe` vorhanden.
- [ ] **Step 3: Von Hand prüfen.** `dist\Co-Trainer.exe` in einen leeren Ordner kopieren und per Doppelklick starten. Erwartet: derselbe Ablauf wie in Task 7 Step 5, ohne Konsolenfenster; neben der `.exe` entsteht keine Datei. Größe der `.exe` und Startzeit bis zum Fenster notieren.
- [ ] **Step 4:** `FM-Scout starten.bat` löschen (`git rm`). `CLAUDE.md` anpassen: Name „Co-Trainer“; Aufruf `python -m cotrainer` bzw. `python -m cotrainer.extract [Pfad.fm]` für Kontrollläufe mit `FMS_DEBUG`; Oberfläche liegt in `cotrainer/ui/index.html`; Vorschau-Adresse mit `?dev=1`; die Regel „Änderungen immer in `app.html`“ durch „in `cotrainer/ui/index.html`“ ersetzen. `HANDOFF.md`: Dateitabelle, Aufrufe und „Nächste Schritte“ auf den neuen Stand bringen, Teil 1 als erledigt vermerken, Teile 2–4 als nächste Pläne nennen.
- [ ] **Step 5:** `.venv\Scripts\python -m pytest tests -v` → alle PASS.
- [ ] **Step 6: Commit.** `git add -A && git commit -m "Co-Trainer.exe bauen; Batch-Datei und HTML-Ausgabe entfernt"`
