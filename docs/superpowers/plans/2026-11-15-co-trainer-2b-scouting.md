# Co-Trainer Teil 2b: Scoutinggebiet, Nationalität, drei Informationsstufen – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transfervorschläge enthalten nur Spieler aus dem eingestellten Scoutinggebiet, zeigen die Nationalität und haben die drei Informationsstufen Aus / Scoutbericht / Werte mit Spoiler-Hinweis.

**Architecture:** Python liest zusätzlich Kontinent und Region je Land (Nationentabelle in `game_db`, Ablauf über die Tabellenbeschreibung von fmsave) und die deutschen Ländernamen (`lang_db.dat`). `_analyse` leitet die Ligastufe aus der mittleren Vereinsreputation ab, filtert den Pool nach Scoutinggebiet und markiert jeden Pool-Spieler mit `vis` (ohne CA/PA ausgewählt). Die Oberfläche zeigt je nach Stufe nur sichtbare Angaben (Aus), Texteinschätzungen (Scoutbericht) oder Attributwerte (Werte); die Stufe liegt in `settings.json`.

**Tech Stack:** Python 3.12, fmsave 0.11.0 (fest), pywebview, Vanilla JS in `cotrainer/ui/index.html`, pytest.

**Spec:** `docs/superpowers/specs/2026-11-09-fm-scout-app-design.md` (Abschnitte 7.2, 8.2, 11) · Format-Wissen: `HANDOFF.md` („Scoutinggebiet“, „Kontinent und Region je Land“, „Ländernamen“).

## Global Constraints

- CA, PA, Persönlichkeit und versteckte Attribute (Cons, Dirt, ImpM, InjPr, Vers) verlassen nie den Python-Teil; `guard.assert_public` prüft jedes Ergebnis. Schlägt sie an, wird der Leser korrigiert, nicht die Regel.
- Potenzial nur als Text, nie als Zahl.
- Spielstände nur lesen. Geld intern in EUR (Faktor 1,1641 beim Einlesen).
- Personen- und Vereins-IDs von fmsave und eigenem Leser nie über die Zahl verbinden.
- **Stufe „Aus“ verrät nichts, auch nicht indirekt:** keine Reihenfolge, kein Text, keine Farbe und kein Filter, der aus CA, PA oder Attributen fremder Spieler abgeleitet ist (Spec 7.2).
- Sichtbar in „Aus“ (Spec 7.2): Name, Alter, Positionen, Verein, Liga, Vertragsende, Wechselchance, Grund für den Vorschlag (dazu Nationalität aus diesem Plan).
- Hinweistext beim Hochschalten mit „Trotzdem einblenden“ / „Abbrechen“ und „Nicht mehr fragen“; Stufe und „Nicht mehr fragen“ werden gespeichert (`settings.json`, Felder `info_level`, `skip_spoiler_warning` gibt es schon).
- Scoutinggebiet-Stufen (Spec 11, HANDOFF): 1 Kein Scouting, 2 Eigene Liga, 3 Angrenzende Ligen, 4 Eigenes Land, 5 Region, 6 Kontinent, 7 Weltweit.
- Kontinent-Codes: 0 Afrika, 1 Asien, 2 Europa, 3 Nord-/Mittelamerika, 4 Ozeanien, 5 Südamerika, 255 keiner.
- Oberfläche und Texte auf Deutsch. Keine Online-Funktionen.

## Entscheidungen von Claude in diesem Plan (vom Nutzer zu bestätigen)

1. **Ligastufe** wird nicht gelesen, sondern abgeleitet: Ligen eines Landes werden nach ihrem Grundnamen zusammengefasst (`Serie C/A`, `Serie C/B`, `Serie C/C` → `Serie C`) und nach mittlerer Vereinsreputation geordnet; Stufe 1 = höchste. Ravenna: Serie A 1, Serie BKT 2, Serie C 3. Nicht spielbare Ligen (Serie D) haben keine Spiele im Spielstand und fehlen deshalb bei „Angrenzende Ligen“.
2. **Wechselchance ohne Spielerqualität:** Der Abzug „Spieler deutlich besser als unser Niveau“ (nutzt die CA des Spielers) entfällt, weil die Wechselchance in Stufe „Aus“ sichtbar ist. Vereinsstärke (Mittel der Vereins-CA) bleibt drin.
3. **Zwei Auswahlen im Pool:** bis zu 3.000 Spieler ohne CA/PA ausgewählt (`vis: true`, nur diese zeigt „Aus“) plus bis zu 4.000 nach dem bisherigen Qualitätsfenster (für Scoutbericht und Werte). Beide nur aus dem Scoutinggebiet.
4. Der Schalter „Auch außerhalb meines Scoutinggebiets suchen“ kommt **nicht** in diesen Plan.
5. Ohne fmsave (eigener Leser) oder ohne gelesenes Scoutinggebiet gilt „Weltweit“; die Oberfläche sagt das.

## Review Focus

1. Stufe „Aus“: Spielerdetail (Schublade) eines Pool-Spielers zeigt keine Attribute, kein Potenzial, keine Einordnung, keinen Preis – Test in Task 5 (Browserprüfung) und `vis`-Auswahl ohne CA in Task 3.
2. Spielstand ohne Scoutinggebiet oder mit eigenem Leser → keine Ausnahme, Pool wie „Weltweit“, `meta.scout_note` gesetzt – Test in Task 3.
3. „Kein Scouting“ in einem Land ohne vertragslose Spieler → leere Liste mit verständlichem Text statt leerer Tabelle – Task 5.
4. Land ohne deutschen Namen → Kürzel oder „–“, keine `undefined`-Anzeige – Test in Task 1 (Rückfall) und Task 5.
5. Verein ohne Liga (Liga nicht spielbar) bei Stufe 2/3 → nicht im Pool, bei Stufe 4–7 über das Vereinsland drin – Test in Task 3.

---

### Task 1: Kontinent, Region und Ländernamen

**Files:**
- Create: `cotrainer/nations.py`
- Test: `tests/test_nations.py`

**Interfaces:**
- Produces:
  - `nation_geo(game_db: bytes) -> dict[int, tuple[int, int]]` – Datenbank-Nr. → (Kontinent, Region); `{}`, wenn die Tabelle nicht genau einmal gefunden wird.
  - `nation_names(lang_path: str | None) -> dict[int, tuple[str, str]]` – Datenbank-Nr. → (deutscher Name, Kürzel); `{}` ohne Datei.
  - `nation_label(names: dict, db_id: int | None) -> tuple[str, str]` – (Kürzel, Name); fehlt der Eintrag: `('–', '')`.

- [ ] **Step 1: Tests schreiben**

```python
# tests/test_nations.py
import pytest
from cotrainer import nations as N

def test_label_fallback():
    assert N.nation_label({776: ('Italien', 'ITA')}, 776) == ('ITA', 'Italien')
    assert N.nation_label({}, 999) == ('–', '')
    assert N.nation_label({}, None) == ('–', '')

def test_geo_without_table():
    assert N.nation_geo(b'\x00' * 1000) == {}

@pytest.mark.save
def test_geo_ravenna(ravenna_game_db):
    g = N.nation_geo(ravenna_game_db)
    assert g[776] == (2, 11)          # Italien: Europa, Südeuropa (vom Nutzer bestätigt)
    assert g[769] == (2, 25)          # Frankreich
    assert g[771] == (2, 4)           # Deutschland
    assert g[1657] == (5, 21)         # Uruguay
    assert len(g) == 251

@pytest.mark.save
def test_names_lang_db(lang_db_path):
    n = N.nation_names(lang_db_path)
    assert n[776] == ('Italien', 'ITA') and n[769] == ('Frankreich', 'FRA')
    assert n[771] == ('Deutschland', 'GER') and n[1657] == ('Uruguay', 'URU')
    assert len(n) >= 230
```

Fixtures in `tests/conftest.py` ergänzen: `ravenna_game_db` (Sitzungs-Fixture: `game_db`-Abschnitt des Ravenna-Testspielstands über `extract.read_frames`/`directory`, überspringen wie die vorhandenen Spielstand-Fixtures, wenn die Datei fehlt) und `lang_db_path` (`extract.find_lang_db({})`, sonst `pytest.skip`).

- [ ] **Step 2: Laufen lassen, Fehlschlag sehen** – `.venv\Scripts\python -m pytest tests/test_nations.py -q` → ImportError.

- [ ] **Step 3: `nation_geo` umsetzen.** Tabelle suchen und ablaufen wie `fmsave.readers.nations.read_nations` (`_nation_scan(find_nation_table_layout(4000, ''))` bzw. das Layout `NATION_TABLE` aus `fmsave._layouts.fm27_27_0_0`; die Suche muss genau eine ablaufbare Tabelle ergeben, sonst `{}`). Beim Ablaufen jedes Datensatzes den Beginn von Schritt 9 (Index 8, 24 feste Bytes) merken: Kontinent = Byte 1, Region = `u32` ab Byte 5 (HANDOFF „Kontinent und Region je Land“). Schlüssel ist die Datenbank-Nr. aus dem Abschlusskopf. Interna von fmsave sind erlaubt, weil die Version fest ist; Import-Fehler → `{}` und `log`.

- [ ] **Step 4: `nation_names` umsetzen.** `lang_db.dat` wie `extract.comp_names` Frame für Frame entpacken; Einträge `Datenbank-Nr.(4) len Name 00 len Kurzname 00 03 00 00 00 Kürzel len Adjektiv 00` (HANDOFF „Ländernamen“; bisher 195 von 251 gefunden, Muster zu eng). Den Frame mit `Italien` und `ITA` wählen. Erreicht der Test die 230 nicht: tatsächliche Anzahl und fehlende Nummern im Bericht nennen, Schwelle nicht senken.

- [ ] **Step 5: Tests grün** – `.venv\Scripts\python -m pytest tests/test_nations.py -q` (mit Spielstand: alle 4 grün).

- [ ] **Step 6: Commit** – `git add cotrainer/nations.py tests/test_nations.py tests/conftest.py && git commit -m "Kontinent, Region und Ländernamen je Land"`

---

### Task 2: Nationalität und Reputation aus fmsave

**Files:**
- Modify: `cotrainer/fms.py` (`player_record`, `read`, `FmsData`)
- Test: `tests/test_fms.py`

**Interfaces:**
- Consumes: fmsave `Player.nation_id`, `Club.nation_id`, `Club.reputation`, `CareerSave.nations()` (`nation_id` → `database_id`).
- Produces:
  - `player_record(p, nat_db: dict[int, int] | None = None)` – zusätzlich `nat`: Datenbank-Nr. der Nation oder `None`.
  - `club_record(c, nat_db: dict[int, int]) -> dict` mit `name`, `short` (leer → `name`), `nat` (Datenbank-Nr. oder `None`), `rep` (`int`, fehlend 0); `FmsData.clubs` besteht daraus.
  - Die Geodaten holt `_analyse` selbst mit `nations.nation_geo` (Task 3), nicht `fms.py`.

- [ ] **Step 1: Tests** (mit der vorhandenen Hilfsfunktion `player(**kw)` in `tests/test_fms.py`; sie muss `nation_id` annehmen, Standard `None`; Vereine als `NS(...)`):

```python
def test_player_nation_maps_to_database_id():
    p = player(nation_id=150)
    assert fms.player_record(p, {150: 776})['nat'] == 776
    assert fms.player_record(p, {})['nat'] is None
    assert fms.player_record(player(nation_id=None), {150: 776})['nat'] is None
    assert fms.player_record(p)['nat'] is None

def test_club_record_has_nation_and_reputation():
    c = NS(uid=7, name='Ravenna Football Club 1913', short_name='Ravenna', nation_id=150, reputation=4337)
    assert fms.club_record(c, {150: 776}) == dict(name='Ravenna Football Club 1913', short='Ravenna', nat=776, rep=4337)
    c2 = NS(uid=8, name='X', short_name='', nation_id=None, reputation=None)
    assert fms.club_record(c2, {}) == dict(name='X', short='X', nat=None, rep=0)
```

- [ ] **Step 2:** Fehlschlag sehen.
- [ ] **Step 3:** `club_record(c, nat_db) -> dict` neu (ersetzt das Wörterbuch in `read`); `player_record` bekommt `nat_db`; in `read` einmal `nat_db = {n.nation_id: n.database_id for n in s.nations()}` bilden.
- [ ] **Step 4:** `.venv\Scripts\python -m pytest tests/test_fms.py -q` grün.
- [ ] **Step 5: Commit** – `"fmsave: Nationalität der Spieler, Land und Reputation der Vereine"`

---

### Task 3: Ligastufe, Scoutinggebiet und Pool

**Files:**
- Modify: `cotrainer/extract.py` (`_analyse`, `willingness`, `out_player`, Pool-Aufbau)
- Test: `tests/test_extract.py`

**Interfaces:**
- Consumes: Task 1 (`nation_geo`, `nation_names`, `nation_label`), Task 2 (`pl['nat']`, `club['nat']`, `club['rep']`).
- Produces (reine Hilfsfunktionen auf Modulebene):
  - `league_base(name: str) -> str` – entfernt eine Staffelendung: `/A`–`/Z` bzw. `/1`–`/9` am Ende sowie ` Girone X`, ` Gruppe X`, ` Staffel X`, ` Group X`, ` Grupo X`.
  - `league_tiers(league_list: dict, club_map: dict) -> dict[int, tuple[int | None, int]]` – Liga-ID → (Land, Stufe). Land = häufigstes `nat` der Vereine; gleiche (Land, `league_base`) bilden eine Gruppe; Gruppen eines Landes nach mittlerer `rep` ihrer Vereine absteigend, Stufe 1 = höchste.
  - `@dataclass ScoutCtx(area, nat, continent, region, league_teams: set, adjacent_teams: set, geo: dict, club_map: dict)`.
  - `in_scout_area(pl: dict, ctx: ScoutCtx | None) -> bool` – Regeln unten.
- Neue Felder in den Daten: Pool-Spieler `nat` (Kürzel), `nat_name`, `vis` (bool), `weaker_league` (bool); `meta.scout_filter` (benutzte Stufe oder `None`), `meta.scout_note` (Text oder `None`), `meta.nat` (Kürzel des Vereinslandes).

**Regeln `in_scout_area`** (Land eines Spielers = Land seines Vereins, bei Vereinslosen `pl['nat']`):
| Stufe | im Gebiet, wenn |
|---|---|
| `ctx is None` oder 7 | immer |
| 1 | vereinslos (`club == 0`) und `pl['nat'] == ctx.nat` |
| 2 | Verein in `ctx.league_teams` |
| 3 | Verein in `ctx.adjacent_teams` (alle Ligen desselben Landes mit Stufe eigene ± 1, eigene Liga eingeschlossen) |
| 4 | Land == `ctx.nat` |
| 5 | `geo[Land]` hat dieselbe Region und denselben Kontinent wie das Vereinsland |
| 6 | `geo[Land]` hat denselben Kontinent (nicht 255) |

- [ ] **Step 1: Tests**

```python
def test_league_base():
    assert X.league_base('Serie C/B') == 'Serie C'
    assert X.league_base('Serie A') == 'Serie A'
    assert X.league_base('Regionalliga Gruppe Nord') == 'Regionalliga'

def test_league_tiers_groups_and_order():
    clubs = {i: dict(nat=776, rep=r) for i, r in [(1, 7000), (2, 7200), (3, 5600), (4, 5500), (5, 4300), (6, 4400), (7, 4500)]}
    ll = {22: dict(name='Serie A', teams=[1, 2]), 23: dict(name='Serie BKT', teams=[3, 4]),
          3484: dict(name='Serie C/A', teams=[5]), 3485: dict(name='Serie C/B', teams=[6]), 3486: dict(name='Serie C/C', teams=[7])}
    t = X.league_tiers(ll, clubs)
    assert t[22] == (776, 1) and t[23] == (776, 2)
    assert t[3484] == t[3485] == t[3486] == (776, 3)

def _ctx(area):
    geo = {776: (2, 11), 1: (2, 11), 769: (2, 25), 1657: (5, 21)}
    cm = {10: dict(nat=776), 11: dict(nat=776), 12: dict(nat=769), 13: dict(nat=1657), 14: dict(nat=1)}
    return X.ScoutCtx(area=area, nat=776, continent=2, region=11, league_teams={10}, adjacent_teams={10, 11},
                      geo=geo, club_map=cm)

@pytest.mark.parametrize('area,club,nat,expected', [
    (1, 0, 776, True), (1, 0, 769, False), (1, 10, 776, False),
    (2, 10, 769, True), (2, 11, 776, False),
    (3, 11, 776, True), (3, 12, 776, False),
    (4, 11, 769, True), (4, 0, 776, True), (4, 12, 776, False),
    (5, 14, 769, True), (5, 12, 776, False),
    (6, 12, 1657, True), (6, 13, 776, False),
    (7, 13, 1657, True),
])
def test_in_scout_area(area, club, nat, expected):
    assert X.in_scout_area(dict(club=club, nat=nat), _ctx(area)) is expected

def test_no_ctx_means_worldwide():
    assert X.in_scout_area(dict(club=12, nat=None), None) is True

def test_club_without_league_outside_league_areas():
    pl = dict(club=99, nat=776)                     # Verein ohne spielbare Liga
    ctx = _ctx(2); ctx.club_map[99] = dict(nat=776)
    assert X.in_scout_area(pl, ctx) is False
    ctx.area = 4
    assert X.in_scout_area(pl, ctx) is True
```

Spielstand-Test (Marke `save`, nutzt die vorhandene Ravenna-Fixture des vollen Durchlaufs):

```python
@pytest.mark.save
def test_ravenna_scout_area(ravenna_data):
    m = ravenna_data['meta']
    assert m['scout_filter'] == m['scout_area'] and m['nat'] == 'ITA'
    pool = ravenna_data['pool']
    assert pool and all(p['nat'] != '–' for p in pool[:200])
    assert any(p['vis'] for p in pool) and sum(p['vis'] for p in pool) <= 3000
    assert len(pool) <= 7000
    assert all(isinstance(p['weaker_league'], bool) for p in pool)
```

(`ravenna_data` ist die vorhandene Sitzungs-Fixture in `tests/conftest.py`; nicht ein zweites Mal einlesen.)

- [ ] **Step 2:** Fehlschlag sehen (`-m "not save"` und einmal mit Spielstand).
- [ ] **Step 3: Umsetzen in `_analyse`:**
  - Nach dem Abschnitt Ligen: `tiers = league_tiers(league_list, club_map)`; `geo = nations.nation_geo(db.d)` und `nnames = nations.nation_names(lang)` nur auf dem fmsave-Weg.
  - `ScoutCtx` nur bauen, wenn fmsave lief, `scout_area` gelesen wurde und das Vereinsland bekannt ist; sonst `ctx = None` und `meta.scout_note`: „Scoutinggebiet nicht gefunden – Vorschläge aus allen Ländern.“ bzw. „Ohne fmsave kann das Scoutinggebiet nicht angewendet werden – Vorschläge aus allen Ländern.“ Fehlen bei Stufe 5/6 die Geodaten des Vereinslandes: ebenfalls `ctx = None` mit dem ersten Text.
  - `willingness`: den Block `lvl_gap` streichen (Entscheidung 2).
  - Pool: `area = [pl … if in_pool_scope(…) and 16 <= Alter <= 35 and in_scout_area(pl, ctx)]`. `vis`-Auswahl: die ersten 3.000 nach (`willingness` absteigend, Vertragsende aufsteigend, vertragslos zuerst) – **kein** `ca`/`pa` im Schlüssel. Qualitätsauswahl: bisheriges Fenster und bisherige Sortierung auf `area`, die ersten 4.000. Vereinigung ohne Doppelte; `vis` = in der ersten Auswahl. `cfg['pool_size']` entfällt.
  - `out_player` (nur Pool): `nat`, `nat_name` über `nation_label`, `weaker_league` = mittlere `rep` der Liga des Spielers < der eigenen Liga (beide bekannt, sonst `False`).
  - `meta`: `scout_filter`, `scout_note`, `nat`.
- [ ] **Step 4:** Alle Tests grün: `.venv\Scripts\python -m pytest tests -q` (rund sechs Minuten).
- [ ] **Step 5: Commit** – `"Transferpool nach Scoutinggebiet, Ligastufe aus Reputation, Wechselchance ohne Spielerqualität"`

---

### Task 4: Informationsstufe in der Schnittstelle

**Files:**
- Modify: `cotrainer/api.py` (`get_state`, neue Methode `set_info_level`)
- Test: `tests/test_api.py`

**Interfaces:**
- Produces: `get_state()` enthält `info_level` und `skip_spoiler_warning`; `Api.set_info_level(level: str, skip_warning: bool | None = None) -> dict` → `{'ok': True}` bzw. `{'ok': False, 'error': 'Unbekannte Informationsstufe.'}`; speichert sofort.

- [ ] **Step 1: Tests**

```python
def test_info_level_roundtrip(tmp_path):
    f = tmp_path / 'settings.json'
    a = Api(settings_file=str(f))
    assert a.get_state()['info_level'] == 'aus'
    assert a.set_info_level('werte', True) == {'ok': True}
    s = Api(settings_file=str(f)).get_state()
    assert s['info_level'] == 'werte' and s['skip_spoiler_warning'] is True

def test_info_level_rejects_unknown(tmp_path):
    a = Api(settings_file=str(tmp_path / 's.json'))
    assert a.set_info_level('alles')['ok'] is False
    assert a.get_state()['info_level'] == 'aus'
```

- [ ] **Step 2:** Fehlschlag sehen. **Step 3:** umsetzen (`skip_warning is None` lässt den gespeicherten Wert unverändert). **Step 4:** `pytest tests/test_api.py -q` grün.
- [ ] **Step 5: Commit** – `"Schnittstelle: Informationsstufe der Transfervorschläge speichern"`

---

### Task 5: Drei Stufen in der Transferansicht

**Files:**
- Modify: `cotrainer/ui/index.html` (`vTransfer`, `renderSug`, `openPlayer`, Entwicklermodus-Ersatz der `Api`, Zustand aus `get_state`)

**Interfaces:**
- Consumes: Task 3 (`p.vis`, `p.nat`, `p.nat_name`, `p.weaker_league`, `meta.scout_area_name`, `meta.scout_note`), Task 4 (`CT.set_info_level`, `state.info_level`, `state.skip_spoiler_warning`).
- Produces: JS-Zustand `W.info` (`'aus' | 'scoutbericht' | 'werte'`).

Festgelegte Texte:
- Umschalter über der Tabelle: „Informationsstufe“ mit „Aus“, „Scoutbericht“, „Werte“.
- Hinweis beim Hochschalten (Dialog): Überschrift „Mehr zeigen, als dein Scouting weiß?“, Text „Diese Stufe zeigt Einschätzungen fremder Spieler, die du im Spiel erst durch Scouting bekommst. Das verändert dein Spielerlebnis und macht es leichter.“, Knöpfe „Trotzdem einblenden“ / „Abbrechen“, Häkchen „Nicht mehr fragen“. Herunterschalten fragt nie.
- Zeile über der Tabelle: „Spieler aus deinem Scoutinggebiet: {scout_area_name}“ oder `meta.scout_note`.
- Gründe (höchstens zwei, in dieser Reihenfolge): „Spielt {Position} – dort ist deine schwächste Position“, „Vereinslos – ablösefrei“, „Vertrag läuft {MM/JJJJ} aus“ (Ende innerhalb von 12 Monaten), „Kommt aus einer schwächeren Liga – Wechsel wahrscheinlich“ (`weaker_league`), „Jung ({Alter}) – Platz zum Entwickeln“ (bis 21).
- Leere Liste in „Aus“ bei Stufe 1: „In deinem Scoutinggebiet (Kein Scouting) gibt es gerade keine passenden vertragslosen Spieler aus {Land}.“; sonst wie bisher „Keine passenden Kandidaten – Filter lockern …“.

**Stufe „Aus“** (nur `p.vis`):
- Spalten: Spieler (Name; darunter Alter · Nation-Kürzel), Positionen (Positionen mit Wert ≥ 15, wie in `openPlayer`), Verein · Liga, Vertrag bis, Wechselchance, Grund.
- „Passt zur Position“ heißt: Positionswert des Spielers für die Position des Platzes ≥ 15 (Positionen sind im Spiel sichtbar). Schwächster Platz = Platz der Startelf mit dem niedrigsten Wert des eigenen Spielers (`an.assign`).
- Empfehlung (Standardsortierung): +40 spielt die schwächste Position, +15 spielt eine der drei schwächsten, +20 vereinslos, +15 Vertrag endet innerhalb von 12 Monaten, +0,3 × Wechselchance, +5 bis 21 Jahre. Weitere Sortierungen: „Wechselchance“, „Jüngste zuerst“, „Vertragsende“.
- Filter: Position, Max. Alter, Min. Wechselchance, „nur ablösefrei/auslaufend“. Ausgeblendet: „im Transferbudget“ und die Sortierungen „Verbesserung“ und „Preis“.
- Keine Spalten Fit, „+ zur Startelf“, Entwicklung, Preis, Gehalt; keine Farben aus Werten.
- Schublade eines Pool-Spielers: Name, Alter, Nation, Verein, Liga, Positionen, Vertrag, Wechselchance; keine Attribute, kein Potenzial, keine Einordnung, kein Preis, kein Gehalt. Eigene Spieler unverändert.

**Stufe „Scoutbericht“:** Tabelle wie heute plus Spalte „Einordnung“ (`p.rel`) und „Bericht“: „Stärken: …“ (bis zu drei Schlüsselattribute der Rolle mit Wert ≥ 14, absteigend) und „Schwächen: …“ (bis zu zwei mit Wert ≤ 10, aufsteigend), Attributnamen aus `AN`. Schublade: statt Attributwerten dieselben zwei Zeilen plus Potenzial-Text und Einordnung.

**Stufe „Werte“:** wie heute.

- [ ] **Step 1:** Entwicklermodus-Ersatz (`?dev=1`) um `set_info_level` und die beiden Felder in `get_state` ergänzen; `dev-data.json` neu erzeugen (`.venv\Scripts\python -m cotrainer.extract --dump cotrainer/ui/dev-data.json`).
- [ ] **Step 2:** Umsetzen wie oben.
- [ ] **Step 3: Browserprüfung** (Vorschau „fmscout“, `…/index.html?dev=1&v=<neu>`), jeweils Konsole ohne Fehler:
  - Stufe „Aus“: im DOM von `#sug` und der Schublade eines Pool-Spielers kein Text aus `p.pot`, `p.rel`, kein Preis, keine Zahl aus `p.a` (per `Runtime.evaluate` prüfen: `document.querySelector('#sug').innerText` enthält keinen `pot`-Text der angezeigten Spieler).
  - Hochschalten auf „Werte“ zeigt den Dialog; „Abbrechen“ lässt „Aus“; „Nicht mehr fragen“ + „Trotzdem einblenden“ → nach Neuladen Stufe „Werte“ ohne Dialog.
  - Stufe „Scoutbericht“ zeigt „Stärken:“ und keine Attributzahlen in der Schublade.
  - Screenshot je Stufe ins Scratchpad.
- [ ] **Step 4:** `.venv\Scripts\python -m pytest tests -q -m "not save"` grün.
- [ ] **Step 5: Commit** – `"Transfervorschläge: Informationsstufen Aus, Scoutbericht, Werte mit Hinweis"`

---

### Task 6: Doku und `.exe`

**Files:**
- Modify: `HANDOFF.md` (Punkt 18 unter „Was bisher gemacht wurde“, „Offene Probleme“, „Nächste Schritte“: Entscheidungen 1–5 zur Bestätigung durch den Nutzer), `CLAUDE.md` (Anzahl der Spielstand-Tests, falls geändert)

- [ ] **Step 1:** Doku anpassen; die Annahmen „Ligastufe aus Reputation“ und „Regionen außer 11 übertragen“ als vom Nutzer zu bestätigen eintragen (Abgleich: Spielerdatenbank im Spiel mit Scoutinggebiet „Angrenzende Ligen“ bzw. „Region“).
- [ ] **Step 2:** `.\build.ps1` (in PowerShell über `powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1`, weil Hinweise auf stderr sonst als Fehler gelten) → `dist\Co-Trainer.exe` startet; volle Tests grün.
- [ ] **Step 3: Commit** – `"Doku Teil 2b"`
