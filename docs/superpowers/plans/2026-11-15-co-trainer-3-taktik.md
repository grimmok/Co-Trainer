# Teil 3: Taktik-Reiter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Der Bereich „Trainer & Taktik“ wird zum Reiter „Taktik“. Er zeigt acht taktische Bereiche mit Einschätzung und bei Schwächen, wer sie verursacht und was hilft. Dazu kommen alle Trainerbewertungen als Textstufe und der Führungsstil (daraus die Trainertendenzen) per Auswahl pro Karriere. Schwache Bereiche steuern den Trainingsvorschlag und einen Filter der Transfervorschläge.

**Architecture:** Die Rechenlogik (Bereiche, Verursacher, Abhilfe, Hinweise zu Trainer und Tendenzen) liegt als reine Funktionen ohne DOM in der neuen Datei `cotrainer/ui/taktik.js`. Sie wird in `index.html` per `<script src="taktik.js">` geladen und mit `node --test` getestet. `index.html` baut daraus die Ansicht. Python ändert sich nicht: Die Trainerbewertungen kommen schon als Textstufe aus `extract.py` (`coach.coaching`, `coach.mental`).

**Tech Stack:** Vanilla JS (Browser und Node ≥ 18, `node:test`), pytest als Rahmen, PyInstaller-Build über `build.ps1`.

**Spec:** `docs/superpowers/specs/2026-11-09-fm-scout-app-design.md`, Abschnitte 7.3, 7.4, 8.2, 8.3, 8.4.

## Global Constraints

- Oberfläche und Texte auf Deutsch, mit den deutschen FM27-Begriffen (Trainingseinheiten heißen wie in `SESS` in `index.html`).
- CA, PA, versteckte Attribute, Persönlichkeit und die Zahlen der Trainerbewertungen erreichen die Oberfläche nie. Trainerbewertungen erscheinen nur als Textstufe: Sehr schlecht (bis 6), Schlecht (7–9), Durchschnitt (10–11), Gut (12–15), Sehr gut (16–17), Herausragend (18–19), Elite (20).
- Werte des **eigenen** Kaders dürfen sichtbar sein (Spec 7.1). Die Taktikbereiche rechnen nur mit eigenen Spielern.
- In Transfer-Stufe „Aus“ darf nichts aus CA/PA/Attributen fremder Spieler abgeleitet sein (Spec 7.2). Der neue Schwachstellen-Filter nutzt nur Positionen.
- Kein Trainerprofil-Formular. Die Trainertendenzen ergeben sich wie im Spiel aus dem **Führungsstil**: 3 von 9 Karten unter „Training“, 2 von 6 unter „Mentales“. Der Nutzer wählt sie einmal pro Karriere; die Wahl liegt im `localStorage` unter dem Karriereschlüssel `KEY` (Spec 8.2, 8.3).
- Teamanweisungen sind nicht dekodiert: Der Taktik-Reiter zeigt keine Teamanweisungen (Spec 11).
- Keine Online-Funktionen, keine erzeugte HTML-Datei, keine Batch-Datei. Spielstände nur lesen.
- Arbeit auf dem Branch `teil-3-taktik`; Commit-Nachrichten auf Deutsch.

## Führungsstil und Tendenzen (Screenshots des Nutzers, 15.11., `%USERPROFILE%\Pictures\fm tool\Tendenzen`)

Im Spiel („Ihr Stil“) wählt man 3 von 9 Trainingskarten und 2 von 6 Mentalkarten; jede Karte bringt eine Tendenz ins Trainerprofil. Die Texte stehen nicht in `lang_db.dat`. Aus den Screenshots ist die Zuordnung Karte → Tendenz bei sechs Karten eindeutig; bei den übrigen ist nur die Gruppe sicher (die Karten wurden zusammen gewählt). Für sie gilt die Zuordnung nach dem Sinn, markiert mit `sure:false`, bis der Nutzer sie bestätigt. Die Taktik-Hinweise hängen deshalb am Kartennamen, nicht am Tendenztext.

## Review Focus

1. **Leere Plätze in der Startelf** (zu wenige passende Spieler): Bereiche rechnen nur mit besetzten Plätzen; ein Bereich ohne besetzten Platz zeigt „nicht bewertbar“ statt eines Fehlers. Test in Task 1.
2. **Unbekannte Rollen-ID** (z. B. aus einem älteren `localStorage`): Gewicht fällt auf 1 für alle Attribute zurück, kein Absturz. Test in Task 1.
3. **Fehlende Trainerbewertungen** (`coach.coaching` leer, Block nicht gefunden): keine Trainerhinweise, Hinweistext „Im Spielstand wurden keine Trainerbewertungen gefunden.“, Auswahl des Führungsstils funktioniert trotzdem. Test in Task 3.
4. **Gespeicherte Führungsstil-Wahl, die nicht (mehr) passt** (unbekannte Karte, mehr als 3 bzw. 2 Karten aus älterem `localStorage`): unbekannte Karten werden ignoriert, überzählige abgeschnitten, keine Fehlermeldung. Test in Task 3.
5. **Schwachstellen-Filter plus Positionsfilter ohne Schnittmenge**: klare Meldung statt leerer Tabelle. Prüfung im Browser-Skript von Task 4.

---

### Task 1: `taktik.js` mit den acht Bereichen und ihrer Einschätzung

**Files:**
- Create: `cotrainer/ui/taktik.js`
- Create: `tests/js/taktik.test.mjs`
- Create: `tests/test_taktik_js.py`
- Modify: `cotrainer/ui/index.html` (Script-Tag im `<head>` vor dem Haupt-Script)
- Modify: `build.ps1` (zweites `--add-data` für `cotrainer/ui/taktik.js;cotrainer/ui`)

**Interfaces:**
- Produces (global `TAKTIK` im Browser, `module.exports` in Node):
  - `AREAS`: Array von `{key, name, phase, pos, attrs, coach}`; `phase` ist `'ip'` oder `'oop'`, `pos` Positionsliste, `attrs` vier Attributkürzel, `coach` Namen der Trainerbewertungen.
  - `areaRatings(lineup, roles) -> [{key, name, phase, coach, avg, band, causers}]` (`coach` wie in `AREAS`)
    - `lineup`: `[{i, pos, ip, oop, player}]`, `player` ist `{id, n, a}` oder `null`.
    - `roles`: Objekt Rollen-ID → `{name, ph, pos, key}` (wie `ROLES` in `index.html`).
    - `band`: `'gut' | 'mittel' | 'schwach' | null` (null = nicht bewertbar).
    - `causers`: `[{i, id, n, pos, role, avg, weak}]`, `weak` = `[[Attribut, Wert]]`.

Die acht Bereiche (Namen exakt wie die FM27-Trainingseinheiten):

| key | name | phase | pos | attrs | coach |
|---|---|---|---|---|---|
| `fmb` | Formation mit Ball | ip | alle Feldspieler | OtB Tea Dec Ant | Taktik, Ballbesitz |
| `pass` | Passstil | ip | DC DL DR WBL WBR DM MC | Pas Vis Tec Fir | Ballbesitz, Techniken |
| `aufbau` | Spielaufbau | ip | GK DC DL DR WBL WBR DM | Pas Fir Cmp Dec | Ballbesitz, Taktik |
| `chancen` | Chancen kreieren | ip | MC ML MR AMC AML AMR ST | Vis Pas Dri Fla | Offensive, Techniken |
| `fob` | Formation ohne Ball | oop | alle Feldspieler | Pos Tea Cnt Dec | Defensive, Taktik |
| `linie` | Pressinglinie | oop | DC DL DR WBL WBR DM | Pac Acc Ant Pos | Defensive, Fitness |
| `intens` | Pressingintensität | oop | alle Feldspieler | Wor Sta Agg Acc | Fitness, Defensive |
| `falle` | Pressingfalle | oop | DL DR WBL WBR ML MR AML AMR DM MC | Ant Tck Wor Acc | Defensive, Taktik |

„Alle Feldspieler“ = `DC DL DR WBL WBR DM MC ML MR AMC AML AMR ST SW`.

Rechenregel (begründbar, Spec 10): Pro relevantem, besetztem Platz ist der Wert der gewichtete Mittelwert der vier Attribute des Spielers. Gewicht 2, wenn das Attribut zu `key` der Rolle dieses Platzes in der Phase des Bereichs gehört (`ip`- bzw. `oop`-Rolle), sonst 1. Attribute ohne Wert beim Spieler zählen nicht. `avg` ist der Mittelwert dieser Platzwerte, auf eine Nachkommastelle gerundet. `band` (aus dem ungerundeten Mittelwert): gut ab 13, mittel ab 11, sonst schwach (dieselben Schwellen wie die bisherige Teamanweisungs-Karte). `causers`: besetzte relevante Plätze mit Platzwert unter 11, aufsteigend, höchstens drei; `weak` sind die Bereichsattribute des Spielers unter 11, aufsteigend.

- [ ] **Step 1: Branch anlegen**

```bash
git checkout -b teil-3-taktik
```

- [ ] **Step 2: Failing tests schreiben** (`tests/js/taktik.test.mjs`, ESM, `node:test` und `node:assert/strict`, lädt `../../cotrainer/ui/taktik.js` per `createRequire`)

```js
const ROLES = {cb:{name:'Innenverteidiger',ph:'both',pos:['DC'],key:['Mar','Tck','Pos']},
  bpcb:{name:'Spielaufbauender IV',ph:'ip',pos:['DC'],key:['Pas','Vis','Dec']},
  pcm:{name:'Pressing-Achter',ph:'oop',pos:['MC'],key:['Wor','Sta','Tck']},
  cm:{name:'Zentraler Mittelfeldspieler',ph:'both',pos:['MC'],key:['Pas','Dec','Wor']}};
const pl = (id, a) => ({id, n:'S'+id, a});
const all = v => Object.fromEntries(['OtB','Tea','Dec','Ant','Pas','Vis','Tec','Fir','Cmp','Dri','Fla','Pos','Cnt','Pac','Acc','Wor','Sta','Agg','Tck'].map(k=>[k,v]));

test('AREAS hat die acht FM27-Bereiche in fester Reihenfolge', () => {
  assert.deepEqual(T.AREAS.map(x=>x.name), ['Formation mit Ball','Passstil','Spielaufbau','Chancen kreieren',
    'Formation ohne Ball','Pressinglinie','Pressingintensität','Pressingfalle']);
});
test('Schwellen: 13 gut, 11 mittel, darunter schwach', () => {
  const lu = v => [{i:0,pos:'MC',ip:'cm',oop:'pcm',player:pl(1,all(v))}];
  const band = (v,k) => T.areaRatings(lu(v), ROLES).find(x=>x.key===k).band;
  assert.equal(band(13,'intens'),'gut'); assert.equal(band(11,'intens'),'mittel'); assert.equal(band(10.9,'intens'),'schwach');
});
test('Rollen-Schlüsselattribute zählen doppelt', () => {
  // pcm (oop) hat Wor und Sta als key: (2*20 + 2*20 + 5 + 5) / 6 = 15
  const a = {...all(5), Wor:20, Sta:20};
  const r = T.areaRatings([{i:0,pos:'MC',ip:'cm',oop:'pcm',player:pl(1,a)}], ROLES).find(x=>x.key==='intens');
  assert.equal(r.avg, 15);
});
test('Verursacher: Plätze unter 11, aufsteigend, höchstens drei, mit schwachen Attributen', () => {
  const lu = [[1,8],[2,9],[3,10],[4,7],[5,15]].map(([id,v],i)=>({i,pos:'DC',ip:'cb',oop:'cb',player:pl(id,all(v))}));
  const r = T.areaRatings(lu, ROLES).find(x=>x.key==='linie');
  assert.deepEqual(r.causers.map(c=>c.id), [4,1,2]);
  assert.deepEqual(r.causers[0].weak.map(x=>x[0]).sort(), ['Acc','Ant','Pac','Pos']);
  assert.equal(r.causers[0].pos, 'DC'); assert.equal(r.causers[0].role, 'Innenverteidiger'); assert.equal(r.causers[0].i, 3);
});
test('Leere Plätze zählen nicht; ohne besetzten Platz ist der Bereich nicht bewertbar', () => {
  const r = T.areaRatings([{i:0,pos:'GK',ip:'cb',oop:'cb',player:null}], ROLES);
  assert.ok(r.every(x => x.band === null && x.avg === null && x.causers.length === 0));
});
test('Unbekannte Rollen-ID: alle Gewichte 1, kein Fehler', () => {
  const r = T.areaRatings([{i:0,pos:'MC',ip:'gibtsnicht',oop:'gibtsnicht',player:pl(1,all(12))}], ROLES);
  assert.equal(r.find(x=>x.key==='intens').avg, 12);
});
test('Attribute ohne Wert zählen nicht', () => {
  const r = T.areaRatings([{i:0,pos:'MC',ip:'cm',oop:'pcm',player:pl(1,{Wor:14,Sta:14})}], ROLES);
  assert.equal(r.find(x=>x.key==='intens').avg, 14);
});
```

`tests/test_taktik_js.py`: ein Test `test_taktik_js`, der `node --test tests/js/` per `subprocess.run` mit `cwd` = Repo-Wurzel ausführt und `returncode == 0` prüft (Ausgabe bei Fehler in die Assertion). `pytest.mark.skipif(shutil.which('node') is None, reason='Node.js fehlt')`.

- [ ] **Step 3: Test laufen lassen, Fehlschlag prüfen**

Run: `.venv\Scripts\python -m pytest tests/test_taktik_js.py -q`
Expected: FAIL (Datei `taktik.js` fehlt)

- [ ] **Step 4: `cotrainer/ui/taktik.js` schreiben**

Aufbau: `(function(root){ ... const api={AREAS, areaRatings}; if(typeof module!=='undefined'&&module.exports)module.exports=api; else root.TAKTIK=api; })(this);` Kein DOM, keine Globals außer `TAKTIK`. Weitere Funktionen hängen Task 2 und 3 an `api` an.

- [ ] **Step 5: Einbinden**
  - `index.html`: `<script src="taktik.js"></script>` vor dem großen Script-Block.
  - `build.ps1`: `--add-data 'cotrainer/ui/taktik.js;cotrainer/ui'` neben dem bestehenden `index.html`-Eintrag. Kommentar „Nur index.html wird eingepackt“ entsprechend anpassen.

- [ ] **Step 6: Tests laufen lassen**

Run: `.venv\Scripts\python -m pytest tests -q -m "not save"`
Expected: alle grün, inklusive `test_taktik_js`

- [ ] **Step 7: Commit**

```bash
git add cotrainer/ui/taktik.js cotrainer/ui/index.html build.ps1 tests/js/taktik.test.mjs tests/test_taktik_js.py
git commit -m "Taktik: acht Bereiche mit Einschätzung und Verursachern (taktik.js)"
```

---

### Task 2: Abhilfe und der neue Reiter „Taktik“

**Files:**
- Modify: `cotrainer/ui/taktik.js`
- Modify: `cotrainer/ui/index.html` (`SECTIONS`, `PICKS`, `vTaktik`, `instrCard` entfernen)
- Test: `tests/js/taktik.test.mjs`

**Interfaces:**
- Consumes: `TAKTIK.AREAS`, `TAKTIK.areaRatings` (Task 1).
- Produces: `helpFor(area, causer, player, slot, roles, names?) -> [{kind, text, role?}]`
  - `kind` ∈ `'rolle' | 'training' | 'transfer'`.
  - `area` ist ein Eintrag aus `areaRatings`; `slot` = `{i, pos, ip, oop}`; `player` = `{id, n, a}`.
- Produces in `index.html`: `lineup(an) -> [{i, pos, ip, oop, player}]` aus `an.sl` und `an.assign` (`player` = `an.assign[i]?.p || null`); `areas(an)` = `TAKTIK.areaRatings(lineup(an), ROLES)`. Task 3 und 4 benutzen beide.

Regeln für `helpFor` (Reihenfolge der Rückgabe wie hier):
1. **Rolle:** Kandidaten sind alle Rollen, deren `pos` die Position des Platzes enthält und deren `ph` die Phase des Bereichs oder `'both'` ist, ohne die aktuelle Rolle. Für jeden Kandidaten zählt der Mittelwert des Spielers über die `key`-Attribute des Kandidaten. Liegt der beste Kandidat mindestens 1,0 über dem Mittelwert der aktuellen Rolle, dann `{kind:'rolle', role:<id>, text:'Rolle „<neu>“ statt „<alt>“ – passt besser zu seinen Stärken'}`. Sonst kein Eintrag.
2. **Training:** immer `{kind:'training', text:'Trainingseinheit „<Bereichsname>“ einplanen; individueller Trainingsfokus auf <schwächstes Attribut auf Deutsch>'}`. Der deutsche Attributname kommt über einen optionalen Parameter `names` (Objekt Kürzel → Name, in `index.html` ist das `AN`); ohne `names` wird das Kürzel verwendet.
3. **Transfer:** immer `{kind:'transfer', text:'Transfervorschläge für diese Position ansehen'}`.

- [ ] **Step 1: Failing tests** in `tests/js/taktik.test.mjs`

```js
test('helpFor schlägt eine besser passende Rolle derselben Phase vor', () => {
  const R2 = {...ROLES, scm:{name:'Abschirmender Achter',ph:'oop',pos:['MC'],key:['Pos','Dec','Mar']}};
  const a = {...all(8), Pos:16, Dec:16, Mar:16};
  const slot = {i:0,pos:'MC',ip:'cm',oop:'pcm'};
  const area = T.areaRatings([{...slot,player:pl(1,a)}], R2).find(x=>x.key==='intens');
  const h = T.helpFor(area, area.causers[0], pl(1,a), slot, R2, {Wor:'Laufbereitschaft'});
  assert.deepEqual(h.map(x=>x.kind), ['rolle','training','transfer']);
  assert.equal(h[0].role, 'scm');
  assert.equal(h[0].text, 'Rolle „Abschirmender Achter“ statt „Pressing-Achter“ – passt besser zu seinen Stärken');
});
test('helpFor ohne bessere Rolle: nur Training und Transfer', () => {
  const slot = {i:0,pos:'MC',ip:'cm',oop:'pcm'};
  const area = T.areaRatings([{...slot,player:pl(1,all(8))}], ROLES).find(x=>x.key==='intens');
  const h = T.helpFor(area, area.causers[0], pl(1,all(8)), slot, ROLES);
  assert.deepEqual(h.map(x=>x.kind), ['training','transfer']);
  assert.match(h[0].text, /^Trainingseinheit „Pressingintensität“ einplanen; individueller Trainingsfokus auf /);
});
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen** (`node --test tests/js/`, Expected: `helpFor is not a function`)

- [ ] **Step 3: `helpFor` implementieren**, an `api` anhängen.

- [ ] **Step 4: Reiter umbauen** in `index.html`
  - `SECTIONS`: Bezeichnung `'Taktik'` statt `'Trainer & Taktik'`; Kommentar über `vTaktik` ebenso.
  - `PICKS`: `['taktik','Nur Taktik','Schwachstellen, Trainer, Spielstile']`; im Eintrag „Alles“ den Text auf „Kader, Transfers, Taktik, Training, Kaderliste“.
  - `vTaktik` neu, Reihenfolge der Karten:
    1. **„Deine Taktik“**: der bisherige Kopf (Formation, Spielstil, Gewicht mit Ball, Herkunftshinweis) plus eine Tabelle Position (`PDE`) · Rolle mit Ball · Rolle gegen den Ball · Spieler (aus `lineup(an)`, leerer Platz „–“).
    2. **„Taktische Bereiche“**: eine Zeile je Bereich mit Name, `avg` (eine Nachkommastelle, „–“ bei null) und einer Pille: gut `pill g` „gut“, mittel `pill` „mittel“, schwach `pill b` „schwach“, null `pill` „nicht bewertbar“. Unter jeder schwachen Zeile die Verursacher: Name (klickbar → `openPlayer(id)`), Position, Rolle, schwache Attribute als „Ecken 8, …“ mit deutschen Namen aus `AN`. Darunter die `helpFor`-Einträge als Liste. Ein Rollenvorschlag hat den Knopf „Übernehmen“, der wie die bestehende Rollenwahl `S.roles[S.formation][i]` setzt (Phase des Bereichs), `WCACHE.clear()`, `save()`, `render()`. Der Transfereintrag hat den Knopf „Ansehen“, der `S.f.pos=String(i)`, `save()`, `showSection('transfer')` ausführt. Fußnote: „Einschätzung aus den Attributen deiner Startelf in den Rollen der Taktik (1–20; Schlüsselattribute der Rolle zählen doppelt). Gut ab 13, mittel ab 11.“
    3. **„Trainer“**: Platzhalter-Karte, die Task 3 füllt (vorerst der bisherige Inhalt der Liste `tips` ohne Fit-Kreis).
    4. **„Diese Spielstile passen besser zu deinem Kader“**: die bisherige Karte „Taktik-Empfehlung“ mit neuer Überschrift.
  - `instrCard` und ihr Aufruf entfallen; `INSTR`, `instrList` und `styleMods` bleiben (Entwicklerhilfe mit `config.json`).
  - Der Fit-Kreis „Trainer ↔ Taktik“ entfällt (er beruhte auf `c.style` aus `config.json`).

- [ ] **Step 5: Tests laufen lassen**

Run: `.venv\Scripts\python -m pytest tests -q -m "not save"`
Expected: alle grün

- [ ] **Step 6: Im Browser prüfen** (Vorgehen laut `CLAUDE.md`, Ravenna-`dev-data.json`, Konsole fehlerfrei). Erwartet: acht Zeilen, mindestens eine mit Pille, ein Klick auf „Übernehmen“ ändert die Rolle in der Taktiktabelle, „Ansehen“ springt zu den Transfervorschlägen mit gesetzter Position.

- [ ] **Step 7: Commit**

```bash
git add cotrainer/ui/taktik.js cotrainer/ui/index.html tests/js/taktik.test.mjs
git commit -m "Reiter Taktik: Bereiche, Verursacher und Abhilfe"
```

---

### Task 3: Trainerbewertungen als Textstufen und Führungsstil pro Karriere

**Files:**
- Modify: `cotrainer/ui/taktik.js`
- Modify: `cotrainer/ui/index.html` (Karte „Trainer“ in `vTaktik`, `load()` für `S.lead`)
- Test: `tests/js/taktik.test.mjs`

**Interfaces:**
- Consumes: `areaRatings` (Task 1), `areas(an)` (Task 2).
- Produces:
  - `LEADERSHIP`: `{training:[{key,name,desc,tendency,sure}], mental:[…]}` in der Reihenfolge der Karten im Spiel; `LEAD_MAX = {training:3, mental:2}`.
  - `cleanLead(sel) -> {training:[key], mental:[key]}`: entfernt unbekannte Schlüssel und Doppelte, schneidet auf `LEAD_MAX` ab; `sel` darf `undefined` sein.
  - `coachHints(coaching, rated) -> [text]`: `coaching` = `{Bewertungsname: Textstufe}`, `rated` = Ergebnis von `areaRatings`.
  - `leadHints(sel, ctx) -> [{kind, text}]`: `sel` wie von `cleanLead`, `ctx` = `{family, styleKey, avgAge}`, `kind` ∈ `'konflikt' | 'passt' | 'hinweis'`.

`LEADERSHIP` (Kartenname, Beschreibung wie im Spiel gekürzt, Tendenz; `sure:false` = Zuordnung nach dem Sinn, vom Nutzer zu bestätigen):

| Gruppe | key | Karte | Tendenz | sure |
|---|---|---|---|---|
| training | `offensive` | Offensive | Spielt offensiven Fußball | true |
| training | `defensiv` | Defensiv | Spielt soliden Defensivfußball | true |
| training | `entwickler` | Entwickler | Entwickelt Nachwuchsspieler | true |
| training | `energisch` | Energisch | Spielt dynamischen Fußball | true |
| training | `entertainer` | Entertainer | Spielt unterhaltsamen Fußball | true |
| training | `pragmatiker` | Pragmatiker | Spielt vertikalen Fußball | false |
| training | `spezialist` | Spezialist | Spezialist | true |
| training | `laptop` | Laptop-Trainer | Holt das Optimum aus Standardsituationen heraus | false |
| training | `taktiker` | Taktiker | Taktiktüftler | false |
| mental | `erfolgshungrig` | Erfolgshungrig | Sehr ambitioniert | false |
| mental | `diszipliniert` | Diszipliniert | Absoluter Disziplinfanatiker | false |
| mental | `belastbar` | Belastbar | Geborener Führungsspieler | false |
| mental | `ueberzeugend` | Überzeugend | Leidenschaftlicher Motivator | false |
| mental | `inspirierend` | Inspirierend | Inspiriert andere | false |
| mental | `gut` | Gut | Allseits bekannter Erfolgstyp | false |

Beschreibungen (`desc`, aus den Screenshots): Offensive „Attraktiver Offensivfußball.“, Defensiv „Die Null muss stehen.“, Entwickler „Junge Talente fördern.“, Energisch „Gegner mit flottem Tempo-Fußball überrennen.“, Entertainer „Ansehnlicher, packender Fußball für die Fans.“, Pragmatiker „Der schnellste und einfachste Weg zum Sieg.“, Spezialist „Fokus auf Torwarttraining und Fitness.“, Laptop-Trainer „Ballbesitzorientiert und bei Standards effektiv.“, Taktiker „Kleinste taktische Details.“, Erfolgshungrig „Zielstrebig, will alles selbst kontrollieren.“, Diszipliniert „Disziplin und hohe Standards.“, Belastbar „Steht nach Rückschlägen sofort wieder auf.“, Überzeugend „Reißt Menschen mit.“, Inspirierend „Starke, präsente Führungspersönlichkeit.“, Gut „Passt sich jeder Liga und jedem Land an.“

`coachHints`: Für jeden Bereich mit `band === 'schwach'` und jede Bewertung in seinem `coach`, deren Stufe „Sehr schlecht“ oder „Schlecht“ ist: `'„<Bereich>“ ist schwach, und deine Trainerbewertung <Bewertung> ist „<Stufe>“ – einen Co-Trainer mit Stärke in <Bewertung> diese Einheit leiten lassen.'` Jede Kombination nur einmal; leere `coaching` → `[]`.

`leadHints` (hängt am Kartenschlüssel, nicht am Tendenztext; Reihenfolge der Ausgabe wie in der Tabelle):

| Karte | Bedingung | kind | text |
|---|---|---|---|
| `defensiv` | `family==='pressing'` oder `styleKey==='vertical_tikitaka'` | konflikt | „Hohes Pressing passt nicht zu deinem Ruf als Defensivtrainer – Spieler lassen sich davon schwerer überzeugen.“ |
| `offensive` | `family==='counter'` | konflikt | „Konterfußball aus tiefem Block passt nicht zu deinem offensiven Ruf.“ |
| `offensive` | `family` ∈ possession, pressing, wide | passt | „Dein offensiver Ruf passt zum Spielstil – das hilft beim Überzeugen der Spieler.“ |
| `energisch` | `styleKey==='tikitaka'` | konflikt | „Geduldiges Tiki-Taka passt nicht zu deinem Ruf für flotten Tempo-Fußball.“ |
| `energisch` | `family` ∈ pressing, counter, direct oder `styleKey==='vertical_tikitaka'` | passt | „Dein Ruf für Tempo-Fußball passt zum Spielstil.“ |
| `laptop` | `family` ∈ counter, direct | konflikt | „Als Laptop-Trainer stehst du für Ballbesitz – dein Spielstil verzichtet darauf.“ |
| `pragmatiker` | `styleKey==='tikitaka'` | konflikt | „Geduldiges Tiki-Taka passt nicht zu deinem Ruf, auf dem schnellsten Weg zum Sieg zu spielen.“ |
| `entwickler` | `avgAge > 27` | hinweis | „Deine Startelf ist im Schnitt <avgAge, eine Nachkommastelle> Jahre alt – mehr junge Spieler einbauen passt zu deinem Ruf.“ |
| `taktiker` | immer | passt | „Mehrere Taktiken für verschiedene Gegner einüben (Trainingseinheit „Geheimtraining“) passt zu deinem Ruf.“ |

- [ ] **Step 1: Failing tests**

```js
test('coachHints: schwacher Bereich plus schwache Bewertung', () => {
  const rated = [{key:'intens',name:'Pressingintensität',band:'schwach',coach:['Fitness','Defensive']},
                 {key:'pass',name:'Passstil',band:'gut',coach:['Ballbesitz']}];
  const h = T.coachHints({Fitness:'Schlecht',Defensive:'Gut',Ballbesitz:'Sehr schlecht'}, rated);
  assert.deepEqual(h, ['„Pressingintensität“ ist schwach, und deine Trainerbewertung Fitness ist „Schlecht“ – einen Co-Trainer mit Stärke in Fitness diese Einheit leiten lassen.']);
  assert.deepEqual(T.coachHints({}, rated), []);
});
test('LEADERSHIP: 9 Trainings- und 6 Mentalkarten, Grenzen 3 und 2', () => {
  assert.equal(T.LEADERSHIP.training.length, 9); assert.equal(T.LEADERSHIP.mental.length, 6);
  assert.deepEqual(T.LEAD_MAX, {training:3, mental:2});
  assert.equal(T.LEADERSHIP.training.find(c=>c.key==='defensiv').tendency, 'Spielt soliden Defensivfußball');
});
test('cleanLead: unbekannte und überzählige Karten fallen weg', () => {
  assert.deepEqual(T.cleanLead(undefined), {training:[], mental:[]});
  assert.deepEqual(T.cleanLead({training:['offensive','gibtsnicht','offensive','entwickler','energisch','taktiker'], mental:['gut','belastbar','diszipliniert']}),
    {training:['offensive','entwickler','energisch'], mental:['gut','belastbar']});
});
test('leadHints: Konflikt, Passung, Alter', () => {
  const sel = t => ({training:t, mental:[]});
  assert.deepEqual(T.leadHints(sel(['defensiv']), {family:'possession',styleKey:'vertical_tikitaka',avgAge:25}).map(x=>x.kind), ['konflikt']);
  assert.deepEqual(T.leadHints(sel(['offensive']), {family:'counter',styleKey:'counter',avgAge:25}).map(x=>x.kind), ['konflikt']);
  const y = T.leadHints(sel(['entwickler']), {family:'possession',styleKey:'tikitaka',avgAge:28.44});
  assert.equal(y[0].text, 'Deine Startelf ist im Schnitt 28,4 Jahre alt – mehr junge Spieler einbauen passt zu deinem Ruf.');
  assert.deepEqual(T.leadHints(sel([]), {family:'pressing',styleKey:'gegenpress',avgAge:30}), []);
});
```

- [ ] **Step 2: Fehlschlag prüfen** (`node --test tests/js/`)

- [ ] **Step 3: Implementieren** (`LEADERSHIP`, `LEAD_MAX`, `cleanLead`, `coachHints`, `leadHints` an `api`). Zahlen im Text mit Komma (`toLocaleString('de-DE',{maximumFractionDigits:1, minimumFractionDigits:1})`).

- [ ] **Step 4: Karte „Trainer“ in `vTaktik`**
  - Zwei Spalten mit allen Bewertungen aus `DATA.coach.coaching` und `DATA.coach.mental`: Name und Textstufe als Pille (Sehr schlecht/Schlecht `pill b`, Durchschnitt `pill`, Gut `pill a`, Sehr gut/Herausragend/Elite `pill g`). Keine Zahlen.
  - Darunter `coachHints(...)` als Liste. Ohne Bewertungen entfallen Tabelle und Hinweise (Spec 8.4); an ihrer Stelle steht nur „Im Spielstand wurden keine Trainerbewertungen gefunden.“
  - **Führungsstil:** Überschrift „Dein Führungsstil (wie unter „Ihr Stil“ im Spiel)“, zwei Gruppen „Training (3 wählen)“ und „Mentales (2 wählen)“. Jede Karte als anklickbares Kästchen mit Name, `desc` und der Tendenz klein darunter (bei `sure:false` mit dem Zusatz „(Zuordnung vermutet)“); gewählt mit Akzentrand. Klick schaltet um; ist die Gruppe schon voll, ersetzt der Klick die zuerst gewählte Karte der Gruppe. Gespeichert in `S.lead`, `save()`, `render()`. `load()` setzt `S.lead = TAKTIK.cleanLead(s.lead)`.
  - Darunter die Tendenzen der gewählten Karten als Pillen („Tendenzen im Profil“) und `leadHints(S.lead, {family: STYLES[S.style].family, styleKey: S.style, avgAge})` mit `avgAge` = Durchschnittsalter der besetzten Startelfplätze; Konflikt mit `<span class="warn">Widerspruch:</span>`, Passung mit `<span class="good">Passt:</span>`, Hinweis ohne Präfix. Ohne Auswahl: „Wähle deinen Führungsstil wie im Spiel, dann prüft Co-Trainer, ob Taktik und Ruf zusammenpassen.“
  - Die bisherigen Einträge der alten Liste, die auf `c.style`, `c.preferred_system`, `c.tendencies` oder Tendenz-Regex beruhten, entfallen; die Hinweise zu Motivationsfähigkeit und Autorität (aus `c.mental`) bleiben.

- [ ] **Step 5: Tests laufen lassen** (`.venv\Scripts\python -m pytest tests -q -m "not save"`, alle grün)

- [ ] **Step 6: Im Browser prüfen**: 15 Bewertungen als Pillen (Ravenna); Karten wählen → Neuladen → bleibt gewählt; eine vierte Trainingskarte ersetzt die erste; „Defensiv“ bei Vertikalem Tiki-Taka zeigt „Widerspruch“. In der Konsole kein Fehler. Mit `DATA.coach={}` (im Entwicklermodus per Konsole gesetzt, dann `render()`) erscheint der Hinweistext ohne Fehler.

- [ ] **Step 7: Commit**

```bash
git add cotrainer/ui/taktik.js cotrainer/ui/index.html tests/js/taktik.test.mjs
git commit -m "Taktik: Trainerbewertungen als Textstufen, Führungsstil pro Karriere"
```

---

### Task 4: Schwache Bereiche steuern Training und Transfers; Abschluss

**Files:**
- Modify: `cotrainer/ui/index.html` (`vTraining`, `vTransfer`, `renderSugAus`, `renderSug`)
- Modify: `HANDOFF.md`, `CLAUDE.md`

**Interfaces:**
- Consumes: `areas(an)`, `lineup(an)` (Task 2).

- [ ] **Step 1: Training (Spec 7.4)**
  - In `vTraining`: `weak` = Namen der Bereiche mit `band==='schwach'`. Sortierung der Einheiten für mit/gegen den Ball: Feedback zuerst (wie bisher), dann schwache Bereiche, dann der Rest. Schwache Bereiche der jeweiligen Phase, die in `tvIP`/`tvOOP` fehlen, werden vorne eingefügt (ohne Doppelte).
  - In `sess(k)`: zusätzlich `<span class="pill b">Schwachstelle</span>`, wenn `k` in `weak` steht.
  - Im Text unter der Überschrift: „Schwache Taktikbereiche (<Liste>) sind vorgezogen.“, nur wenn `weak` nicht leer ist.

- [ ] **Step 2: Transfers (Spec 7.3 „Suchkriterium“)**
  - Neuer Filter in `vTransfer`, sichtbar wenn mindestens ein schwacher Bereich Verursacher hat: Checkbox „Nur Positionen mit Taktik-Schwachstellen“ (`S.f.weak`).
  - In `renderSugAus` und `renderSug`: Ist `S.f.weak` an, ist `idx` die Menge der Platzindizes `i` aller Verursacher schwacher Bereiche, geschnitten mit dem Positionsfilter, falls gesetzt. Ist die Schnittmenge leer: Meldung „Keine Schwachstellen-Position passt zum Positionsfilter.“ statt der Tabelle.
  - In `renderSugAus` ein zusätzlicher Grund, wenn der Spieler auf eine Verursacher-Position passt (Positionswert ≥ 15): „Spielt <PDE> – dort liegt die Schwachstelle „<Bereich>““. Er steht nach dem Grund zur schwächsten Position; es bleiben höchstens zwei Gründe. `rec` ändert sich nicht.

- [ ] **Step 3: Tests** (`.venv\Scripts\python -m pytest tests -q`, alle grün, inklusive der Spielstand-Tests; der Osijek-Test mit Kopie des Spielstands, falls das Spiel läuft)

- [ ] **Step 4: Im Browser prüfen** mit einem Skript im Scratchpad nach dem Muster der bisherigen Prüfskripte (headless Edge, Ravenna-Daten), Konsole fehlerfrei:
  - Training zeigt die Pille „Schwachstelle“ bei mindestens einer Einheit, wenn ein Bereich schwach ist.
  - „Nur Positionen mit Taktik-Schwachstellen“ reduziert die Zeilen auf passende Positionen; zusammen mit einem Positionsfilter ohne Schnittmenge erscheint die Meldung.
  - In Stufe „Aus“ erscheint der neue Grund, und die Reihenfolge der Zeilen ist mit und ohne Filter dieselbe (nur weniger Zeilen).

- [ ] **Step 5: Dokumentation**
  - `HANDOFF.md`: neuer Punkt 19 unter „Was bisher gemacht wurde“ (Teil 3: Reiter Taktik, `taktik.js`, Bereiche-Tabelle mit Rechenregel, Führungsstil pro Karriere, Verknüpfung mit Training und Transfers); unter „Nächste Schritte“ Teil 3 als erledigt; unter „Vom Nutzer zu bestätigen“: die Zuordnung Karte → Tendenz bei den Karten mit `sure:false`; ob der gewählte Führungsstil im Spielstand steht (dann könnte Co-Trainer ihn lesen); die Einschätzung der Bereiche mit dem Bildschirm „Taktische Effektivität“ im Spiel vergleichen.
  - `CLAUDE.md`: unter „Tests“ ergänzen, dass `tests/js/` Node.js braucht und ohne Node übersprungen wird; unter „Oberfläche“, dass die Taktiklogik in `cotrainer/ui/taktik.js` liegt.

- [ ] **Step 6: `.exe` bauen und starten**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1` (aus der Bash), dann `dist\Co-Trainer.exe` starten und den Reiter „Taktik“ öffnen: Er muss erscheinen (beweist, dass `taktik.js` gepackt ist).

- [ ] **Step 7: Commit**

```bash
git add cotrainer/ui/index.html HANDOFF.md CLAUDE.md
git commit -m "Taktik-Schwachstellen steuern Training und Transferfilter; Doku Teil 3"
```
