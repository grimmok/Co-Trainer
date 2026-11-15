// Taktik-Logik ohne DOM: acht Bereiche (FM27-Trainingseinheiten) und ihre Einschätzung.
(function (root) {
  const FELD = ['DC', 'DL', 'DR', 'WBL', 'WBR', 'DM', 'MC', 'ML', 'MR', 'AMC', 'AML', 'AMR', 'ST', 'SW'];
  const AREAS = [
    {key: 'fmb', name: 'Formation mit Ball', phase: 'ip', pos: FELD, attrs: ['OtB', 'Tea', 'Dec', 'Ant'], coach: ['Taktik', 'Ballbesitz']},
    {key: 'pass', name: 'Passstil', phase: 'ip', pos: ['DC', 'DL', 'DR', 'WBL', 'WBR', 'DM', 'MC'], attrs: ['Pas', 'Vis', 'Tec', 'Fir'], coach: ['Ballbesitz', 'Techniken']},
    {key: 'aufbau', name: 'Spielaufbau', phase: 'ip', pos: ['GK', 'DC', 'DL', 'DR', 'WBL', 'WBR', 'DM'], attrs: ['Pas', 'Fir', 'Cmp', 'Dec'], coach: ['Ballbesitz', 'Taktik']},
    {key: 'chancen', name: 'Chancen kreieren', phase: 'ip', pos: ['MC', 'ML', 'MR', 'AMC', 'AML', 'AMR', 'ST'], attrs: ['Vis', 'Pas', 'Dri', 'Fla'], coach: ['Offensive', 'Techniken']},
    {key: 'fob', name: 'Formation ohne Ball', phase: 'oop', pos: FELD, attrs: ['Pos', 'Tea', 'Cnt', 'Dec'], coach: ['Defensive', 'Taktik']},
    {key: 'linie', name: 'Pressinglinie', phase: 'oop', pos: ['DC', 'DL', 'DR', 'WBL', 'WBR', 'DM'], attrs: ['Pac', 'Acc', 'Ant', 'Pos'], coach: ['Defensive', 'Fitness']},
    {key: 'intens', name: 'Pressingintensität', phase: 'oop', pos: FELD, attrs: ['Wor', 'Sta', 'Agg', 'Acc'], coach: ['Fitness', 'Defensive']},
    {key: 'falle', name: 'Pressingfalle', phase: 'oop', pos: ['DL', 'DR', 'WBL', 'WBR', 'ML', 'MR', 'AML', 'AMR', 'DM', 'MC'], attrs: ['Ant', 'Tck', 'Wor', 'Acc'], coach: ['Defensive', 'Taktik']},
  ];
  const GUT = 13, MITTEL = 11;

  // Gewichteter Mittelwert der Bereichsattribute eines Spielers; Schlüsselattribute der Rolle zählen doppelt.
  function slotValue(area, player, role) {
    const key = (role && role.key) || [];
    let sum = 0, w = 0;
    for (const k of area.attrs) {
      const v = player.a && player.a[k];
      if (v === undefined || v === null) continue;
      const g = key.includes(k) ? 2 : 1;
      sum += g * v; w += g;
    }
    return w ? sum / w : null;
  }

  function areaRatings(lineup, roles) {
    return AREAS.map(area => {
      const slots = [];
      for (const s of lineup) {
        const pos = area.phase === 'oop' ? (s.op || s.pos) : s.pos;
        if (!s.player || !area.pos.includes(pos)) continue;
        const role = (roles || {})[s[area.phase]];
        const val = slotValue(area, s.player, role);
        if (val === null) continue;
        slots.push({s, role, val});
      }
      const mean = slots.length ? slots.reduce((t, x) => t + x.val, 0) / slots.length : null;
      const band = mean === null ? null : mean >= GUT ? 'gut' : mean >= MITTEL ? 'mittel' : 'schwach';
      const causers = slots.filter(x => x.val < MITTEL)
        .sort((x, y) => x.val - y.val).slice(0, 3)
        .map(({s, role, val}) => ({
          i: s.i, id: s.player.id, n: s.player.n, pos: area.phase === 'oop' ? (s.op || s.pos) : s.pos, role: role ? role.name : '',
          avg: Math.round(val * 10) / 10,
          weak: area.attrs.filter(k => s.player.a[k] !== undefined && s.player.a[k] !== null && s.player.a[k] < MITTEL)
            .map(k => [k, s.player.a[k]]).sort((x, y) => x[1] - y[1]),
        }));
      return {key: area.key, name: area.name, phase: area.phase, coach: area.coach,
        avg: mean === null ? null : Math.round(mean * 10) / 10, band, causers};
    });
  }

  // Abhilfe für einen Verursacher: bessere Rolle, Training, Transfer (in dieser Reihenfolge).
  function helpFor(area, causer, player, slot, roles, names) {
    const out = [];
    const mean = (r) => {
      const v = ((r && r.key) || []).map(k => player.a && player.a[k]).filter(x => x !== undefined && x !== null);
      return v.length ? v.reduce((t, x) => t + x, 0) / v.length : null;
    };
    const slotPos = area.phase === 'oop' ? (slot.op || slot.pos) : slot.pos;
    const curId = slot[area.phase], cur = (roles || {})[curId];
    const curMean = mean(cur);
    let best = null, bestMean = null;
    for (const [id, r] of Object.entries(roles || {})) {
      if (id === curId || !r.pos.includes(slotPos) || !(r.ph === area.phase || r.ph === 'both')) continue;
      const m = mean(r);
      if (m !== null && (bestMean === null || m > bestMean)) { best = {id, r}; bestMean = m; }
    }
    if (best && curMean !== null && bestMean >= curMean + 1.0)
      out.push({kind: 'rolle', role: best.id, text: 'Rolle „' + best.r.name + '“ statt „' + (cur ? cur.name : curId) + '“ – passt besser zu seinen Stärken'});
    const attrs = AREAS.find(x => x.key === area.key).attrs;
    let weakest = causer && causer.weak && causer.weak[0] ? causer.weak[0][0] : null;
    if (!weakest) {
      const have = attrs.filter(k => player.a && player.a[k] !== undefined && player.a[k] !== null);
      weakest = have.sort((x, y) => player.a[x] - player.a[y])[0] || attrs[0];
    }
    out.push({kind: 'training', text: 'Trainingseinheit „' + area.name + '“ einplanen; individueller Trainingsfokus auf ' + ((names && names[weakest]) || weakest)});
    out.push({kind: 'transfer', text: 'Transfervorschläge für diese Position ansehen'});
    return out;
  }

  const C = (key, name, desc, tendency, sure) => ({key, name, desc, tendency, sure});
  const LEADERSHIP = {
    training: [
      C('offensive', 'Offensive', 'Attraktiver Offensivfußball.', 'Spielt offensiven Fußball', true),
      C('defensiv', 'Defensiv', 'Die Null muss stehen.', 'Spielt soliden Defensivfußball', true),
      C('entwickler', 'Entwickler', 'Junge Talente fördern.', 'Entwickelt Nachwuchsspieler', true),
      C('energisch', 'Energisch', 'Gegner mit flottem Tempo-Fußball überrennen.', 'Spielt dynamischen Fußball', true),
      C('entertainer', 'Entertainer', 'Ansehnlicher, packender Fußball für die Fans.', 'Spielt unterhaltsamen Fußball', true),
      C('pragmatiker', 'Pragmatiker', 'Der schnellste und einfachste Weg zum Sieg.', 'Spielt vertikalen Fußball', false),
      C('spezialist', 'Spezialist', 'Fokus auf Torwarttraining und Fitness.', 'Spezialist', true),
      C('laptop', 'Laptop-Trainer', 'Ballbesitzorientiert und bei Standards effektiv.', 'Holt das Optimum aus Standardsituationen heraus', false),
      C('taktiker', 'Taktiker', 'Kleinste taktische Details.', 'Taktiktüftler', false),
    ],
    mental: [
      C('erfolgshungrig', 'Erfolgshungrig', 'Zielstrebig, will alles selbst kontrollieren.', 'Sehr ambitioniert', false),
      C('diszipliniert', 'Diszipliniert', 'Disziplin und hohe Standards.', 'Absoluter Disziplinfanatiker', false),
      C('belastbar', 'Belastbar', 'Steht nach Rückschlägen sofort wieder auf.', 'Geborener Führungsspieler', false),
      C('ueberzeugend', 'Überzeugend', 'Reißt Menschen mit.', 'Leidenschaftlicher Motivator', false),
      C('inspirierend', 'Inspirierend', 'Starke, präsente Führungspersönlichkeit.', 'Inspiriert andere', false),
      C('gut', 'Gut', 'Passt sich jeder Liga und jedem Land an.', 'Allseits bekannter Erfolgstyp', false),
    ],
  };
  const LEAD_MAX = {training: 3, mental: 2};

  function cleanLead(sel) {
    const out = {};
    for (const g of Object.keys(LEAD_MAX)) {
      const ok = LEADERSHIP[g].map(c => c.key), seen = [];
      for (const k of (Array.isArray(sel && sel[g]) ? sel[g] : [])) if (ok.includes(k) && !seen.includes(k)) seen.push(k);
      out[g] = seen.slice(0, LEAD_MAX[g]);
    }
    return out;
  }

  // Baustellen: schwache Bereiche plus Bereiche mit Verursachern, die mindestens 0,3 unter dem Schnitt aller Bereiche liegen.
  function focusAreas(rated) {
    const list = (rated || []).filter(a => a.avg !== null && a.avg !== undefined);
    const mean = list.length ? list.reduce((t, a) => t + a.avg, 0) / list.length : 0;
    return list.filter(a => a.band === 'schwach' || ((a.causers || []).length > 0 && a.avg <= mean - 0.3 + 1e-9))
      .sort((x, y) => x.avg - y.avg).map(a => a.key);
  }

  function coachHints(coaching, rated, focusKeys) {
    const out = [], c = coaching || {};
    for (const a of rated || []) {
      if (focusKeys ? !focusKeys.includes(a.key) : a.band !== 'schwach') continue;
      for (const r of a.coach || []) {
        if (c[r] !== 'Sehr schlecht' && c[r] !== 'Schlecht') continue;
        const t = '„' + a.name + '“ ist ' + (focusKeys ? 'eine Baustelle' : 'schwach') + ', und deine Trainerbewertung ' + r + ' ist „' + c[r] + '“ – einen Co-Trainer mit Stärke in ' + r + ' diese Einheit leiten lassen.';
        if (!out.includes(t)) out.push(t);
      }
    }
    return out;
  }

  const TACTIC_NEEDS = {
    possession: ['Ballbesitz', 'Techniken', 'Taktik', 'Fitness'],
    pressing: ['Fitness', 'Defensive', 'Taktik'],
    counter: ['Offensive', 'Fitness', 'Defensive'],
    wide: ['Offensive', 'Techniken', 'Fitness'],
    direct: ['Fitness', 'Standardsituationen', 'Offensive'],
  };
  const CA_ALIAS = {Athletik: 'Fitness', Fitness: 'Athletik', Standards: 'Standardsituationen', Standardsituationen: 'Standards'};
  function tacticCoachGaps(coaching, family) {
    const c = coaching || {}, out = [];
    for (const n of TACTIC_NEEDS[family] || []) {
      const v = c[n] !== undefined ? c[n] : c[CA_ALIAS[n]];
      if (v === 'Sehr schlecht' || v === 'Schlecht') out.push([n, v]);
    }
    return out;
  }

  function leadHints(sel, ctx) {
    const s = cleanLead(sel), has = k => s.training.includes(k) || s.mental.includes(k);
    const fam = ctx && ctx.family, sk = ctx && ctx.styleKey, out = [];
    const add = (kind, text) => out.push({kind, text});
    if (has('defensiv') && (fam === 'pressing' || sk === 'vertical_tikitaka'))
      add('konflikt', 'Hohes Pressing passt nicht zu deinem Ruf als Defensivtrainer – Spieler lassen sich davon schwerer überzeugen.');
    if (has('offensive') && fam === 'counter') add('konflikt', 'Konterfußball aus tiefem Block passt nicht zu deinem offensiven Ruf.');
    if (has('offensive') && ['possession', 'pressing', 'wide'].includes(fam))
      add('passt', 'Dein offensiver Ruf passt zum Spielstil – das hilft beim Überzeugen der Spieler.');
    if (has('energisch') && sk === 'tikitaka') add('konflikt', 'Geduldiges Tiki-Taka passt nicht zu deinem Ruf für flotten Tempo-Fußball.');
    if (has('energisch') && (['pressing', 'counter', 'direct'].includes(fam) || sk === 'vertical_tikitaka'))
      add('passt', 'Dein Ruf für Tempo-Fußball passt zum Spielstil.');
    if (has('laptop') && ['counter', 'direct'].includes(fam))
      add('konflikt', 'Als Laptop-Trainer stehst du für Ballbesitz – dein Spielstil verzichtet darauf.');
    if (has('pragmatiker') && sk === 'tikitaka')
      add('konflikt', 'Geduldiges Tiki-Taka passt nicht zu deinem Ruf, auf dem schnellsten Weg zum Sieg zu spielen.');
    if (has('entwickler') && ctx && ctx.avgAge > 27)
      add('hinweis', 'Deine Startelf ist im Schnitt ' + ctx.avgAge.toLocaleString('de-DE', {maximumFractionDigits: 1, minimumFractionDigits: 1}) + ' Jahre alt – mehr junge Spieler einbauen passt zu deinem Ruf.');
    if (has('taktiker'))
      add('passt', 'Mehrere Taktiken für verschiedene Gegner einüben (Trainingseinheit „Geheimtraining“) passt zu deinem Ruf.');
    return out;
  }

  const api = {AREAS, areaRatings, helpFor, LEADERSHIP, LEAD_MAX, cleanLead, focusAreas, coachHints, tacticCoachGaps, leadHints};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.TAKTIK = api;
})(this);
