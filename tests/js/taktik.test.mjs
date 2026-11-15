import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const T = createRequire(import.meta.url)('../../cotrainer/ui/taktik.js');

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
