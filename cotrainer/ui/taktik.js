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
        if (!s.player || !area.pos.includes(s.pos)) continue;
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
          i: s.i, id: s.player.id, n: s.player.n, pos: s.pos, role: role ? role.name : '',
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
    const curId = slot[area.phase], cur = (roles || {})[curId];
    const curMean = mean(cur);
    let best = null, bestMean = null;
    for (const [id, r] of Object.entries(roles || {})) {
      if (id === curId || !r.pos.includes(slot.pos) || !(r.ph === area.phase || r.ph === 'both')) continue;
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

  const api = {AREAS, areaRatings, helpFor};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.TAKTIK = api;
})(this);
