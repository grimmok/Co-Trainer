# Co-Trainer Teil 2a: fmsave als Quelle für Spieler, Vereine und Ligen – Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Spielstände, bei denen der eigene Leser den Verein nicht findet (Auslöser: `Ivan Kurasic – NK Osijek.fm`), werden mit Spielern, Verträgen, Vereinen und Ligen aus fmsave eingelesen; der Kader zeigt nur die erste Mannschaft.

**Architecture:** Neues Modul `cotrainer/fms.py` liest mit fmsave und gibt die Daten im **internen Format, das `_analyse` heute schon benutzt** (Spieler-Wörterbuch, Verträge, Vereine, Wettbewerbe wie `competitions()`). `_analyse` nimmt diese Daten, wenn fmsave einen betreuten Verein liefert, sonst wie bisher die des eigenen Lesers (Rückfall). Taktik, Trainingspläne, Trainingsbewertungen, Trainerwerte, Scoutinggebiet und Finanzen kommen weiter aus dem eigenen Leser.

**Tech Stack:** Python 3.12, fmsave 0.11.0 (PyPI, MIT), pytest, PyInstaller.

**Spec:** `docs/superpowers/specs/2026-11-09-fm-scout-app-design.md` (Abschnitt 8.1 „Lesen“, Abschnitt 10 „fmsave als veröffentlichtes Paket in fester Version“). Hintergrund und Messwerte: `HANDOFF.md` Punkt 16 und dieser Plan, Abschnitt „Befunde“.

## Befunde, auf denen der Plan beruht (14.11., gemessen)

- **IDs sind verschieden:** Spieler-IDs (`pid` des eigenen Lesers) und Vereins-IDs (Verträge, `comp_<id>`-Teamzeilen, `clubs()`) haben eine andere Nummerierung als fmsave (`Player.uid`, `club_uid`). Gleiche Zahl ≠ gleiche Person. **Nie über die Zahl verbinden.**
- **Trainingsbewertungen** (`training()` des eigenen Lesers) sind nach eigener `pid` geschlüsselt; keine passt zu `uid` oder `unique_id` von fmsave. Verbindung nur über (Name, Geburtsdatum) mit dem Spieler-Wörterbuch des eigenen Lesers.
- **Liga:** `league_tables()` hat leere `club_uid`. `fixtures()` hat `home_club_uid`/`away_club_uid`, `home_team_slot`/`away_team_slot`, `competition_id`. `competitions()` hat `database_id`; das ist der Schlüssel von `comp_names()` (Ravenna: Wettbewerb 3485 → db 43127173 → „Serie C/B“, 20 Vereine; Osijek: 193 → 129645 → „First League“, 10 Vereine).
- **Finanzen aus fmsave stimmen nicht** mit den per Screenshot geprüften Ravenna-Werten (fmsave Transferbudget 515.419 £, geprüft 519.556 £; Kontostand 1.261.137 £, geprüft 1.185.695 £; fmsave liefert Vormonats-Schnappschüsse). Finanzen bleiben beim eigenen Leser (`club_finances` am Namensdatensatz des Vereins).
- **Attribute in fmsave:** 52 Felder auf der Anzeigeskala 1–20, gleiche Reihenfolge wie `ATTR_KEYS` ohne `LFoot`/`RFoot` (die stehen als `Player.left_foot`/`right_foot`). Positionen: 15 Felder in der Reihenfolge von `POS_KEYS` (`stc` = ST). Persönlichkeit: 8 Felder in der bestätigten Reihenfolge.
- **Erste Mannschaft:** `Player.team_slot == 0`. Ravenna 27 von 33, Paris 23 von 79, Osijek 27 von 58.
- fmsave öffnet Nationaltrainer-Spielstände (FM26), liefert dort aber `managed_clubs() == []`; `Trainertest .fm` wirft `ReaderCheckError`. Beides → Rückfall.
- fmsave 0.11.0 ist auf PyPI; einzige Abhängigkeit `backports.zstd` (Python < 3.14).

## Global Constraints

- CA, PA, versteckte Attribute (Cons, Dirt, ImpM, InjPr, Vers), Persönlichkeit und Trainerzahlen verlassen nie den Python-Teil; jedes Ergebnis läuft durch `guard.assert_public` (passiert in `analyse()`).
- Spielstände nur lesen. fmsave öffnet nur lesend; nichts darf in den Spielstand-Ordner geschrieben werden.
- Geld bleibt intern in GBP (`wage_week`, Finanzen); die Oberfläche rechnet mit 1,1641 um. fmsave liefert Löhne in gespeicherten Einheiten (GBP, pro Woche).
- fmsave in **fester Version** `fmsave==0.11.0` aus PyPI, nicht der lokale Klon.
- Ausgabeformat für die Oberfläche (`meta`, `coach`, `tactic`, `squad`, `pool`, `training`) bleibt gleich; neu ist nur `meta.source` (`'fmsave'` oder `'eigener Leser'`).
- `PROGRESS_STEPS` bleiben unverändert (Test prüft die Reihenfolge).
- Neu dekodierte Werte gelten erst als korrekt, wenn der Nutzer sie mit Screenshots abgeglichen hat (betrifft die Osijek-Finanzen).
- Oberfläche und Meldungen auf Deutsch.

## Review Focus

1. **fmsave wirft beim Öffnen oder Lesen** (unbekannter Build, `ReaderCheckError`, `UnsupportedGameError`) → das Einlesen läuft mit dem eigenen Leser weiter, keine Fehlermeldung. Test in Task 1 (`test_read_returns_none_when_fmsave_fails`).
2. **fmsave liefert keinen betreuten Verein** (Nationaltrainer) → Rückfall; ohne Kader bleibt die bekannte Meldung „kein Kader des eigenen Vereins“. Test in Task 1 (`test_read_returns_none_without_managed_club`) und Task 3 (`test_two_manager_save_reports_missing_squad` bleibt grün).
3. **Spieler ohne Geburtsdatum, ohne Verein oder mit fehlendem Potenzial** in fmsave → ohne Geburtsdatum übergehen, ohne Verein = vertragslos (`club 0`), fehlendes/negatives Potenzial = CA. Test in Task 1 (`test_player_record_edge_cases`).
4. **Zwei Vereine gleichen Namens** (z. B. „FC Bayern München“ zweimal) beim Suchen des Namensdatensatzes für die Finanzen → der Datensatz, dessen Name *und* Kurzname passen und für den `club_finances` Werte liefert. Test in Task 2 (`test_find_club_record_prefers_exact_pair_with_finances`).
5. **Trainingsbewertungen, die sich keinem fmsave-Spieler zuordnen lassen** (Namensschreibung verschieden) → fehlen bei diesem Spieler („–“), alle anderen erscheinen. Test in Task 3 (`test_map_ratings_by_name_and_birthdate`).

---

## Dateien

| Datei | Änderung |
|---|---|
| `pyproject.toml` | Abhängigkeit `fmsave==0.11.0` |
| `cotrainer/fms.py` (neu) | fmsave lesen, ins interne Format wandeln, Wettbewerbe aus Spielplänen |
| `cotrainer/extract.py` | `find_club_record`, `map_ratings`, Quellenwahl in `_analyse`, Kader = erste Mannschaft |
| `tests/test_fms.py` (neu) | Umwandlung mit nachgestellten fmsave-Objekten |
| `tests/test_extract.py`, `tests/conftest.py` | Spielstand-Tests Osijek/Ravenna, Zuordnung der Bewertungen |
| `build.ps1` | fmsave in die `.exe` packen |
| `CLAUDE.md`, `HANDOFF.md` | Stand nachtragen |

---

### Task 1: `cotrainer/fms.py` – fmsave lesen und umwandeln

**Files:**
- Modify: `pyproject.toml` (`dependencies = ["zstandard", "pywebview", "fmsave==0.11.0"]`)
- Create: `cotrainer/fms.py`
- Test: `tests/test_fms.py`

**Interfaces:**
- Consumes: `extract.ATTR_KEYS`, `extract.POS_KEYS`, `extract.CUP_WORDS`, `extract.log`; `cnames` = Rückgabe von `extract.comp_names()` (`{database_id: (lang, kurz)}`).
- Produces:
  - `@dataclass FmsData`: `players: dict[int, dict]` (Schlüssel `uid`; Werte wie `_analyse` sie heute baut: `id, name, dob: date, club: int, ca: int, pa: int, pos: list[int] (15, 1–20), attrs: list[int] (54, Rohskala = Anzeige × 5), pers: list[int] | None`, zusätzlich `team_slot: int | None`); `contracts: dict[int, dict]` (`wage_week: int | None` in GBP, `end: str | None` ISO); `clubs: dict[int, dict]` (`name`, `short`); `comps: dict[int, dict]` (gleiche Form wie `extract.competitions()`: `name`, `long`, `teams: list[int]`); `own_club: int`.
  - `player_record(p) -> dict | None`
  - `comps_from_fixtures(fixtures, comp_db: dict[int, int], cnames: dict) -> dict[int, dict]`
  - `pick_own_club(managed, club_name: str) -> int | None`
  - `read(path: str, cnames: dict, club_name: str) -> FmsData | None`

- [ ] **Step 1: fmsave installieren**

Run: `python -m uv pip install --python .venv -e ".[dev]"` (nach der Änderung in `pyproject.toml`)
Expected: `+ fmsave==0.11.0`, `+ backports-zstd==…`

- [ ] **Step 2: Failing tests schreiben** (`tests/test_fms.py`, fmsave-Objekte mit `types.SimpleNamespace` nachstellen)

```python
from types import SimpleNamespace as NS
import datetime, pytest
from cotrainer import fms, extract

ATTR_NAMES = [  # fmsave-Reihenfolge (52 Felder)
    'crossing','dribbling','finishing','heading','long_shots','marking','off_the_ball','passing','penalty_taking',
    'tackling','vision','handling','aerial_reach','command_of_area','communication','kicking','throwing','anticipation',
    'decisions','one_on_ones','positioning','reflexes','first_touch','technique','flair','corners','teamwork',
    'work_rate','long_throws','eccentricity','rushing_out','punching','acceleration','free_kick_taking','strength',
    'stamina','pace','jumping_reach','leadership','dirtiness','balance','bravery','consistency','aggression','agility',
    'important_matches','injury_proneness','versatility','natural_fitness','determination','composure','concentration']
POS_NAMES = ['gk','sw','dl','dc','dr','dm','ml','mc','mr','aml','amc','amr','stc','wbl','wbr']

def player(**kw):
    base = dict(uid=7, name='Max Muster', birth_date=datetime.date(2000, 5, 1), club_uid=11, team_slot=0,
                ability=NS(current=120, potential=140),
                attributes=NS(**{n: (i % 20) + 1 for i, n in enumerate(ATTR_NAMES)}),
                positions=NS(**{n: 20 if n == 'stc' else 1 for n in POS_NAMES}),
                personality=NS(adaptability=1, ambition=2, loyalty=3, pressure=4, professionalism=5,
                               sportsmanship=6, temperament=7, controversy=8),
                left_foot=6, right_foot=20,
                contract=NS(wage=4008, end=datetime.date(2027, 6, 30)))
    base.update(kw); return NS(**base)

def test_player_record_maps_attributes_feet_positions_personality():
    r = fms.player_record(player())
    assert len(r['attrs']) == len(extract.ATTR_KEYS) == 54
    assert r['attrs'][extract.ATTR_KEYS.index('Cro')] == 5          # 1 × 5
    assert r['attrs'][extract.ATTR_KEYS.index('Tec')] == 24 * 5
    assert r['attrs'][extract.ATTR_KEYS.index('LFoot')] == 30 and r['attrs'][extract.ATTR_KEYS.index('RFoot')] == 100
    assert r['attrs'][extract.ATTR_KEYS.index('Fla')] == 25 * 5
    assert r['pos'][extract.POS_KEYS.index('ST')] == 20 and len(r['pos']) == 15
    assert r['pers'] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert (r['id'], r['club'], r['ca'], r['pa'], r['team_slot']) == (7, 11, 120, 140, 0)

def test_player_record_edge_cases():
    assert fms.player_record(player(birth_date=None)) is None
    assert fms.player_record(player(club_uid=None))['club'] == 0
    assert fms.player_record(player(ability=NS(current=90, potential=None)))['pa'] == 90
    assert fms.player_record(player(ability=NS(current=90, potential=-75)))['pa'] == 90
    assert fms.player_record(player(personality=None))['pers'] is None

def test_comps_from_fixtures_uses_first_team_league_matches():
    fx = [NS(competition_id=5, home_club_uid=a, away_club_uid=b, home_team_slot=0, away_team_slot=0)
          for a, b in [(1, 2), (3, 4), (5, 6), (1, 3), (2, 4), (6, 5)]]
    fx += [NS(competition_id=9, home_club_uid=1, away_club_uid=2, home_team_slot=1, away_team_slot=1)]  # U-Mannschaft
    c = fms.comps_from_fixtures(fx, {5: 4312, 9: 99}, {4312: ('Italian Serie C/B', 'Serie C/B')})
    assert c == {5: {'name': 'Serie C/B', 'long': 'Italian Serie C/B', 'teams': [1, 2, 3, 4, 5, 6]}}

def test_pick_own_club_prefers_summary_name():
    m = [NS(club_uid=1, club_name='A', club_short_name='A'), NS(club_uid=2, club_name='NK Osijek', club_short_name='Osijek')]
    assert fms.pick_own_club(m, 'Osijek') == 2 and fms.pick_own_club(m, 'X') == 1 and fms.pick_own_club([], 'X') is None

def test_read_returns_none_when_fmsave_fails(monkeypatch):
    def boom(path): raise RuntimeError('summary does not fit')
    monkeypatch.setattr(fms.fmsave, 'open', boom)
    assert fms.read('x.fm', {}, 'X') is None

def test_read_returns_none_without_managed_club(monkeypatch):
    class Save:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def managed_clubs(self): return []
    monkeypatch.setattr(fms.fmsave, 'open', lambda path: Save())
    assert fms.read('x.fm', {}, 'X') is None
```

- [ ] **Step 3: Tests laufen lassen, Fehlschlag prüfen**

Run: `.venv\Scripts\python -m pytest tests/test_fms.py -q`
Expected: FAIL (`ModuleNotFoundError: cotrainer.fms`)

- [ ] **Step 4: `cotrainer/fms.py` umsetzen**

- `import fmsave` auf Modulebene (Tests ersetzen `fms.fmsave.open`).
- `player_record`: Attributliste in `ATTR_KEYS`-Reihenfolge aus den 52 fmsave-Feldern × 5, `LFoot`/`RFoot` aus `left_foot`/`right_foot` × 5 hinter `technique` einfügen; fehlender Einzelwert → 5 (Anzeige 1). `pa` = `current`, wenn `potential` fehlt oder ≤ 0. `pers` nur, wenn alle acht Werte 1–20 sind, sonst `None` (wie bisher).
- `comps_from_fixtures`: nur Spiele mit `home_team_slot == 0 and away_team_slot == 0` und beiden `club_uid` gesetzt; je Wettbewerb die Menge der Vereine, sortiert; Name aus `cnames[comp_db[cid]]` (fehlt er: `name = long = f'Wettbewerb {cid}'`); Wettbewerbe, deren langer Name auf `CUP_WORDS` passt oder die weniger als 6 Vereine haben, weglassen.
- `pick_own_club`: Verein, dessen `club_name` oder `club_short_name` gleich `club_name` ist, sonst der erste, leer → `None`.
- `read`: unter `warnings.catch_warnings()` + `simplefilter('ignore')` `with fmsave.open(path) as s:`; `managed_clubs()` → `pick_own_club`, `None` → Rückgabe `None`; dann `players()`, `clubs()` (`{uid: dict(name, short=short_name or name)}`), `competitions()` (`{id: database_id}`), `fixtures()`. Verträge aus `player.contract` (`wage`, `end.isoformat()`). Jede Ausnahme (`except Exception`) → `log('fmsave nicht nutzbar:', type(e).__name__)` und `None`. Erfolgreich: `log('fmsave:', Spieler, Vereine, Wettbewerbe, 'eigener Verein', uid)`.

- [ ] **Step 5: Tests laufen lassen**

Run: `.venv\Scripts\python -m pytest tests/test_fms.py -q`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml cotrainer/fms.py tests/test_fms.py
git commit -m "fmsave als Datenquelle: Spieler, Vereine und Ligen ins interne Format"
```

---

### Task 2: Namensdatensatz des eigenen Vereins für die Finanzen

**Files:**
- Modify: `cotrainer/extract.py` (neue Funktion bei `club_finances`)
- Test: `tests/test_extract.py`

**Interfaces:**
- Consumes: `DB`, `club_finances(db, c)` (braucht `c['end']`).
- Produces: `find_club_record(db, name: str, short: str) -> dict | None` – `{'name', 'short', 'end'}` des Namenspaars im ersten Zehntel von `game_db` (Bereich wie `clubs()`).

- [ ] **Step 1: Failing test**

```python
def _pair(name, short):
    n, s = name.encode(), short.encode()
    return bytes([len(n)]) + b'\x00\x00\x00' + n + bytes([len(s)]) + b'\x00\x00\x00' + s + b'\x00'

def test_find_club_record_prefers_exact_pair_with_finances(monkeypatch):
    d = b'\x00' * 50 + _pair('NK Osijek', 'Osijek') + b'\x00' * 200 + _pair('NK Osijek', 'NK Osijek') + b'\x00' * 50
    d += b'\x00' * (len(d) * 10)              # Namen liegen im ersten Zehntel
    db = extract.DB(d)
    monkeypatch.setattr(extract, 'club_finances', lambda db, c: {'transfer_budget': 1} if c['end'] > 200 else {})
    r = extract.find_club_record(db, 'NK Osijek', 'NK Osijek')
    assert r['short'] == 'NK Osijek' and r['end'] > 200
    assert extract.find_club_record(db, 'Gibt es nicht', 'X') is None
```

- [ ] **Step 2: Test laufen lassen** – `.venv\Scripts\python -m pytest tests/test_extract.py -q -k find_club_record` → FAIL (`AttributeError`)

- [ ] **Step 3: `find_club_record` umsetzen**

Mit dem Muster `pair` aus `clubs()` (als Modulkonstante `CLUB_PAIR` herausziehen, `clubs()` benutzt sie weiter) über `d[:len(d) // 10]` suchen; Kandidaten sind Paare mit `name` gleich (Groß-/Kleinschreibung egal) **und** Kurzname gleich `short`, danach nur Name gleich. Unter den Kandidaten den ersten, für den `club_finances` ein nicht leeres Ergebnis liefert, sonst den ersten Kandidaten, sonst `None`. Vor dem Durchsuchen mit `d.find(name.encode())` prüfen, ob der Name überhaupt vorkommt (schnell bei 260 MB).

- [ ] **Step 4: Tests laufen lassen** – `.venv\Scripts\python -m pytest tests -q -m "not save"` → alle grün

- [ ] **Step 5: Commit** – `git commit -m "Namensdatensatz des eigenen Vereins für die Finanzen suchen"`

---

### Task 3: fmsave in `_analyse` einbauen, Kader = erste Mannschaft

**Files:**
- Modify: `cotrainer/extract.py` (`_analyse`, neue Funktion `map_ratings`)
- Modify: `tests/conftest.py` (Fixture `osijek_save`)
- Test: `tests/test_extract.py`

**Interfaces:**
- Consumes: `fms.read(path, cnames, club_name) -> FmsData | None` (Task 1), `find_club_record` (Task 2).
- Produces: `map_ratings(rat: dict[int, tuple], old_players: dict[int, dict], new_players: dict[int, dict]) -> dict[int, tuple]` – Bewertungen von eigener `pid` auf fmsave-`uid` über `(name.casefold().strip(), dob)`; nicht eindeutige Schlüssel (zwei Spieler gleich) auslassen. `meta.source`.

- [ ] **Step 1: Failing tests**

```python
def test_map_ratings_by_name_and_birthdate():
    d1, d2 = datetime.date(2000, 1, 1), datetime.date(1999, 2, 2)
    old = {101: {'name': 'Nicolas Viola', 'dob': d1}, 102: {'name': 'Ohne Treffer', 'dob': d2}}
    new = {7: {'name': 'nicolas viola ', 'dob': d1}, 8: {'name': 'Anders Geschrieben', 'dob': d2}}
    assert extract.map_ratings({101: (6.8, 7.1), 102: (6.0, 6.2)}, old, new) == {7: (6.8, 7.1)}
```
(`import datetime` oben in `tests/test_extract.py` ergänzen.)

```python
@pytest.mark.save
def test_osijek_reads_first_team_from_fmsave(osijek_save):
    data = extract.analyse(osijek_save)
    m = data["meta"]
    assert m["source"] == "fmsave" and m["club"] == "NK Osijek" and m["manager"] == "Ivan Kurasic"
    assert m["league"] == "First League" and len(m["rivals"]) == 9
    assert 20 <= len(data["squad"]) <= 30 and len(data["pool"]) > 1000

@pytest.mark.save
def test_ravenna_reads_first_team_from_fmsave(ravenna_data):
    m = ravenna_data["meta"]
    assert m["source"] == "fmsave" and m["league"] == "Serie C/B"
    assert 24 <= len(ravenna_data["squad"]) <= 28                    # 27 in der ersten Mannschaft
    assert sum(1 for p in ravenna_data["squad"] if p.get("tr")) >= 20  # Bewertungen zugeordnet
```

`tests/conftest.py`: Fixture `osijek_save` wie `ravenna_save`, Datei `Ivan Kurasic – NK Osijek.fm`, Umgebungsvariable `COTRAINER_TEST_SAVE_OSIJEK`, fehlt sie → `pytest.skip`.
Die bestehenden Prüfungen in `test_analyse_ravenna` (Verein, Transferbudget 604815, Taktik, Stil, Trainer) bleiben unverändert und müssen weiter gelten.

- [ ] **Step 2: Tests laufen lassen** – `.venv\Scripts\python -m pytest tests/test_extract.py -q` → die drei neuen schlagen fehl

- [ ] **Step 3: `map_ratings` und Quellenwahl umsetzen**

In `_analyse` nach `comps = competitions(...)` (Schritt 3) `fd = fms.read(save, cnames, club_name)` aufrufen. Ist `fd` nicht `None`:
- `players, con, club_map, comps = fd.players, fd.contracts, fd.clubs, fd.comps`; `my_id = fd.own_club`; `rat = map_ratings(rat, alte players, fd.players)`; die Bestimmung von `my_id` über Trainingsbewertungen/Namen entfällt.
- `my = dict(club_map[my_id])`; Finanzen: `rec = find_club_record(db, my['name'], my['short'])`, `fin = club_finances(db, rec) if rec else {}`.
- Kader: `pl['club'] == my_id and pl['team_slot'] == 0`. Pool schließt weiter alle Spieler des eigenen Vereins aus (`pl['club'] != my_id`).
- `meta.source = 'fmsave'`, sonst `'eigener Leser'`.

Alles Übrige (Stärken, Ligen aus `comps`, Wechselchance, Marktwert, Taktik, Trainer) läuft unverändert auf diesen Wörterbüchern. `FMS_DEBUG` gibt die Zeilen auch für den fmsave-Weg aus (die Ausgabe hinter die Quellenwahl verschieben).

- [ ] **Step 4: Alle Tests laufen lassen**

Run: `.venv\Scripts\python -m pytest tests -q`
Expected: alle grün, auch `test_two_manager_save_reports_missing_squad` (fmsave scheitert → eigener Leser → Meldung).

- [ ] **Step 5: Kontrolllauf Paris und ein Nationaltrainer-Spielstand**

Run: `.venv\Scripts\python -m cotrainer.extract "<games>\Haribaert Kachinski – Paris FC.fm"` und `… "Jamal Vrede – Curaçao.fm"`
Expected: Paris `Kader 23` (± 2), Protokoll `fmsave: …`; Curaçao „kein Kader des eigenen Vereins gefunden“.

- [ ] **Step 6: Commit** – `git commit -m "Spieler, Vereine und Ligen aus fmsave; Kader nur erste Mannschaft"`

---

### Task 4: `.exe` mit fmsave bauen, Nachweis, Doku

**Files:**
- Modify: `build.ps1`, `CLAUDE.md`, `HANDOFF.md`

- [ ] **Step 1: `build.ps1`** – PyInstaller-Aufruf um `--collect-submodules fmsave --copy-metadata fmsave --collect-all backports.zstd` ergänzen (fmsave lädt Layouts je Build nach; `--copy-metadata` packt die MIT-Lizenz von fmsave mit ein).

- [ ] **Step 2: Bauen** – `.\build.ps1 -MitSpielstand` → `Fertig: …\dist\Co-Trainer.exe`, alle Tests grün.

- [ ] **Step 3: Nachweis aus der `.exe`** – `dist\Co-Trainer.exe` starten und Osijek bis zum Ergebnis einlesen (Probelauf-Skript im Scratchpad, Fernsteuerung von WebView2 über `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9333`). Erwartet: Titel „Co-Trainer · NK Osijek · First League“, fünf Bereiche, kein JS-Fehler, Änderungsdatum aller `.fm` unverändert. Gleiches für Ravenna.

- [ ] **Step 4: Doku** – `CLAUDE.md` (Abschnitt Arbeitsweise): fmsave ist Abhängigkeit in fester Version, eigener Leser ist Rückfall, IDs nie zwischen beiden über die Zahl verbinden. `HANDOFF.md`: Punkt 17 mit Ergebnis; offener Punkt „Osijek-Finanzen mit Screenshot abgleichen“ (Transferbudget, Gehaltsbudget, Kontostand).

- [ ] **Step 5: Commit** – `git commit -m "Co-Trainer.exe mit fmsave; Doku"`

- [ ] **Step 6: Nutzer bitten**, für NK Osijek einen Screenshot der Finanzübersicht (Transferbudget, Gehaltsbudget, Kontostand) zu schicken; erst danach gelten die Osijek-Finanzen als geprüft.
