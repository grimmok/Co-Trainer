import datetime

import pytest
from cotrainer import extract


@pytest.mark.save
def test_analyse_ravenna(ravenna_data):
    m = ravenna_data["meta"]
    assert m["manager"] == "Haribaert Kachinski"
    assert m["club"] == "Ravenna Football Club 1913"
    assert m["scout_area"] == 4 and m["scout_area_name"] == "Eigenes Land"
    assert m["finances"]["transfer_budget"] == 604815
    assert m["finances"]["wage_budget_week"] == 98362
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


def test_result_without_own_squad_is_a_clear_error():
    # z. B. Nationaltrainer oder Spielstand mit zwei Managern: der Leser findet keinen eigenen Kader
    with pytest.raises(extract.SaveReadError, match="kein Kader des eigenen Vereins"):
        extract.require_squad([], "Südkorea.fm")
    assert extract.require_squad([{"id": 1}], "x.fm") is None


@pytest.mark.save
def test_two_manager_save_reports_missing_squad(ravenna_save):
    import os
    path = os.path.join(os.path.dirname(ravenna_save), "Trainertest .fm")
    if not os.path.isfile(path):
        pytest.skip("Trainertest .fm fehlt")
    with pytest.raises(extract.SaveReadError, match="kein Kader des eigenen Vereins"):
        extract.analyse(path)


def test_coach_with_empty_manager_name_is_not_searched():
    assert extract.read_coach(b"\x00" * 5000, "") is None


def _readable(monkeypatch, result):
    monkeypatch.setattr(extract, "read_frames", lambda p: ([b""], [0]))
    monkeypatch.setattr(extract, "directory", lambda f, o: {s: 0 for s in extract.REQUIRED_SECTIONS})
    monkeypatch.setattr(extract, "_analyse", result)


def test_error_in_analysis_is_not_reported_as_unreadable_save(monkeypatch):
    def broken(*a): raise KeyError("rolle")
    _readable(monkeypatch, broken)
    with pytest.raises(KeyError):
        extract.analyse("x.fm")


def test_every_result_passes_the_guard(monkeypatch):
    from cotrainer.guard import HiddenValueError
    _readable(monkeypatch, lambda *a: {"squad": [{"ca": 150}]})
    with pytest.raises(HiddenValueError):
        extract.analyse("x.fm")


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
    assert extract.find_club_record(db, 'nk osijek', 'NK Osijek') is None


def _budget_block(wage_budget=None, payroll=45680, pad=37):
    import struct
    b = b'\x01' + struct.pack('<iii', 1000000, 900000, 800000) + b'\x00' + struct.pack('<iii', 1, 2, payroll)
    if wage_budget is not None:
        b += b'\x00' * pad + struct.pack('<i', wage_budget)    # Blockstart + 63
    return b'\x00' * 10 + b


def test_club_finances_wage_budget_is_read_at_block_start_plus_63():
    d = _budget_block(wage_budget=43339) + b'\x00' * 20
    f = extract.club_finances(extract.DB(d), {'end': 0})
    assert f['wage_budget_week'] == round(43339 * extract.GBP_TO_EUR)
    assert f['wage_payroll_week'] == round(45680 * extract.GBP_TO_EUR)
    assert f['transfer_budget'] == round(900000 * extract.GBP_TO_EUR)


def test_club_finances_wage_budget_falls_back_to_payroll(capsys):
    for tail in (None, 0, 10 ** 8):                      # Daten zu kurz, Wert <= 0, Wert >= 1e8
        d = _budget_block(wage_budget=tail) + (b'' if tail is None else b'\x00' * 20)
        f = extract.club_finances(extract.DB(d), {'end': 0})
        assert 'Rückfall' in capsys.readouterr().out
        assert f['wage_budget_week'] == f['wage_payroll_week'] == round(45680 * extract.GBP_TO_EUR)


def test_map_ratings_by_name_and_birthdate():
    d1, d2 = datetime.date(2000, 1, 1), datetime.date(1999, 2, 2)
    old = {101: {'name': 'Nicolas Viola', 'dob': d1}, 102: {'name': 'Ohne Treffer', 'dob': d2}}
    new = {7: {'name': 'nicolas viola ', 'dob': d1}, 8: {'name': 'Anders Geschrieben', 'dob': d2}}
    assert extract.map_ratings({101: (6.8, 7.1), 102: (6.0, 6.2)}, old, new) == {7: (6.8, 7.1)}


def test_map_ratings_uses_first_and_last_name_for_common_names():
    d = datetime.date(1995, 3, 3)
    old = {101: {'name': 'Otávio Edmilson da Silva Monteiro', 'dob': d}}
    new = {7: {'name': 'Otávio', 'first': 'Otávio Edmilson', 'last': 'da Silva  Monteiro', 'dob': d}}
    assert extract.map_ratings({101: (6.8, 7.1)}, old, new) == {7: (6.8, 7.1)}


def test_squad_and_pool_scope_depend_on_source():
    me = 5
    first = dict(club=me, team_slot=0, loan_parent=None)
    reserve = dict(club=me, team_slot=1, loan_parent=None)
    loaned_out = dict(club=9, team_slot=0, loan_parent=me)
    other = dict(club=9, team_slot=0, loan_parent=None)
    assert [extract.in_squad(p, me, True) for p in (first, reserve, other)] == [True, False, False]
    assert extract.in_squad(reserve, me, False) is True          # eigener Leser: kein team_slot
    assert [extract.in_pool_scope(p, me, True) for p in (first, loaned_out, other)] == [False, False, True]
    assert extract.in_pool_scope(loaned_out, me, False) is True


def test_read_scout_area_variants():
    def area(b):
        return extract.read_scout_area({0: bytes(20) + b + bytes(20)}, {'humans': 0})
    date = bytes.fromhex('b41aea07 01006c07')
    assert area(bytes.fromhex('3300 04 01000000 2000 0100') + date) == 4      # Ravenna
    assert area(bytes.fromhex('3300 07 07000000 2000 0500') + date) == 7      # Osijek (15.11.): 05 statt 01
    assert area(bytes.fromhex('3300 01 00000000 0000 0000') + date) is None   # kein „20 00“
    assert area(bytes.fromhex('3300 03 01000000 2000 0100 b41a 0000')) is None  # kein Jahr 2000–2047
    assert extract.read_scout_area({}, {}) is None


@pytest.mark.save
def test_osijek_reads_first_team_from_fmsave(osijek_save):
    data = extract.analyse(osijek_save)
    m = data["meta"]
    assert m["source"] == "fmsave" and m["club"] == "NK Osijek" and m["manager"] == "Ivan Kurasic"
    assert m["league"] == "First League" and len(m["rivals"]) == 9
    assert 20 <= len(data["squad"]) <= 30 and len(data["pool"]) > 1000
    f = m["finances"]                                                # per Screenshot bestätigt (14.11.)
    assert f["wage_budget_week"] == 50451 and f["transfer_budget"] == 499998
    # Der Kontostand ändert sich, wenn der Nutzer weiterspielt (Screenshots: 14.11. 6.713.387, 15.11. 6,82 Mio. =
    # gelesen 6.824.841)
    assert isinstance(f["balance"], int) and f["balance"] > 0
    assert m["scout_area"] == 7 and m["scout_filter"] == 7          # Weltweit (Bytes 15.11., Screenshot passt)
    assert f["wage_payroll_week"] == 45680              # Gehaltskosten gesamt laut Screenshot


@pytest.mark.save
def test_ravenna_reads_first_team_from_fmsave(ravenna_data):
    m = ravenna_data["meta"]
    assert m["source"] == "fmsave" and m["league"] == "Serie C/B"
    assert 24 <= len(ravenna_data["squad"]) <= 28                    # 27 in der ersten Mannschaft
    assert sum(1 for p in ravenna_data["squad"] if p.get("tr")) >= 23  # Bewertungen zugeordnet (gemessen: 23)
    assert len(m["rivals"]) == 18


# ---------------------------------------------------------------- Ligastufe und Scoutinggebiet
X = extract


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


def test_weaker_league_compares_groups():
    clubs = {1: dict(nat=776, rep=4500), 2: dict(nat=776, rep=4500), 3: dict(nat=776, rep=4200),
             4: dict(nat=776, rep=3000), 5: dict(nat=776, rep=4268), 6: dict(nat=769, rep=4000)}
    ll = {1: dict(name='Serie C/B', teams=[1, 2]), 2: dict(name='Serie C/A', teams=[3]),
          3: dict(name='Serie D/A', teams=[4]), 4: dict(name='Eccellenza', teams=[5]),
          5: dict(name='3. Liga', teams=[6])}
    g = X.league_groups(ll, clubs)
    assert g[1] == g[2] == (776, 'Serie C', 4400)    # eigene Gruppe: Mittel aller Staffeln
    assert X.weaker_league(g, 1, 2) is False         # gleiche Gruppe, obwohl die Staffel C/A schwächer ist
    assert X.weaker_league(g, 1, 3) is True          # 3000 gegen 4400
    assert X.weaker_league(g, 1, 4) is False         # 4268 = 97 % der eigenen Gruppe
    assert X.weaker_league(g, 1, 5) is True          # anderes Land, gleiche Regel: 4000 < 0,95 × 4400
    assert X.weaker_league(g, 1, None) is False      # Verein ohne Liga
    assert X.weaker_league(g, None, 3) is False      # eigene Liga unbekannt


def test_weaker_league_for_club_without_league():
    clubs = {1: dict(nat=776, rep=4500), 2: dict(nat=776, rep=4300)}
    g = X.league_groups({1: dict(name='Serie C/B', teams=[1, 2])}, clubs)      # Gruppenmittel 4400
    assert X.weaker_league(g, 1, None, dict(nat=776, rep=3500)) is True        # Serie-D-Verein: 3500 < 4180
    assert X.weaker_league(g, 1, None, dict(nat=776, rep=4300)) is False       # 98 % des Mittels
    assert X.weaker_league(g, 1, None, dict(nat=769, rep=1000)) is False       # anderes Land
    assert X.weaker_league(g, 1, None, dict(nat=776, rep=0)) is False          # ohne Reputation
    assert X.weaker_league(g, 1, None, dict(nat=776)) is False
    assert X.weaker_league(g, 1, None, {}) is False
    assert X.weaker_league(g, None, None, dict(nat=776, rep=1000)) is False    # eigene Liga unbekannt


def test_scout_context_needs_own_league_for_league_areas():
    tiers = {22: (776, 1), 23: (776, 2), 24: (776, 3), 30: (769, 1)}
    comps = {22: dict(teams=[1]), 23: dict(teams=[2]), 24: dict(teams=[3]), 30: dict(teams=[4])}
    geo = {776: (2, 11)}
    for area in (2, 3):
        ctx, note = X.scout_context(area, 776, None, tiers, comps, geo, {})
        assert ctx is None and note == X.SCOUT_NOTE_MISSING
    ctx, note = X.scout_context(3, 776, 23, tiers, comps, geo, {})
    assert note is None and ctx.league_teams == {2} and ctx.adjacent_teams == {1, 2, 3}
    ctx, note = X.scout_context(4, 776, None, tiers, comps, geo, {})
    assert note is None and ctx.area == 4
    assert X.scout_context(5, 769, 30, tiers, comps, geo, {}) == (None, X.SCOUT_NOTE_MISSING)   # keine Geodaten
    assert X.scout_context(None, 776, 22, tiers, comps, geo, {}) == (None, X.SCOUT_NOTE_MISSING)


def test_own_league_includes_all_staffeln():
    # Spiel (Screenshot 15.11.): „Serie C – Umfasst Spieler in unserer Liga“ = alle drei Staffeln
    tiers = {21: (776, 2), 31: (776, 3), 32: (776, 3), 33: (776, 3), 40: (769, 3)}
    comps = {21: dict(teams=[1]), 31: dict(teams=[2]), 32: dict(teams=[3]), 33: dict(teams=[4]),
             40: dict(teams=[5])}
    ctx, note = X.scout_context(2, 776, 32, tiers, comps, {776: (2, 11)}, {})
    assert note is None and ctx.league_teams == {2, 3, 4}


def test_willingness_uses_club_reputation():
    cm = {1: dict(rep=4300), 2: dict(rep=7100), 3: dict(rep=4000), 4: dict(rep=0), 5: dict()}
    assert X.club_rep_diff(2, 1, cm) == 56                       # Serie A gegen Serie C
    assert X.club_rep_diff(4, 1, cm) == X.club_rep_diff(5, 1, cm) == X.club_rep_diff(9, 1, cm) == 0
    assert X.club_rep_diff(2, 4, cm) == 0                        # eigene Reputation unbekannt: neutral
    assert X.club_rep_diff(0, 1, cm) == X.FREE_AGENT_DIFF

    def will(club, free=False):
        return X.willingness_score(X.club_rep_diff(club, 1, cm), free, 2.0, 26)
    assert will(2) < will(4) < will(3)                           # größerer Verein → geringere Chance
    assert will(4) == will(5) == will(1)                         # unbekannt = gleich groß
    assert will(0, free=True) > will(3)


def test_vis_selection_ignores_ca_and_pa():
    import random
    rnd = random.Random(7)
    area = [dict(id=i, club=i % 30, nat=776 if i % 3 else 769, age=16 + i % 20, ca=rnd.randint(40, 160),
                 pa=rnd.randint(60, 190), attrs=[rnd.randint(1, 100) for _ in range(54)]) for i in range(400)]
    will = {pl['id']: rnd.randint(2, 97) for pl in area}
    con = {pl['id']: dict(end=None if pl['id'] % 9 == 0 else f'202{pl["id"] % 5 + 6}-06-30') for pl in area}
    rep = {c: rnd.randint(0, 5000) for c in range(1, 30)}
    club_map = {c: dict(nat=776 if c % 4 else 769, rep=rep[c]) for c in range(1, 30)}
    league_of = {c: 100 + c % 6 for c in range(1, 30) if c % 5}
    near = {101, 102, 103}

    def rel(pl):
        return X.pool_relevance(pl, club_map, 776, near, league_of)

    def run():
        out = X.select_pool(area, will, con, rep, lambda pl: 80 <= pl['ca'] <= 130, lambda pl: -pl['ca'],
                            relevance=rel, my_rep=2500, vis_ok=lambda pl: pl['club'] != 0 or pl['age'] >= 18,
                            vis_n=250, quality_n=80)
        return [pl['id'] for pl, v in out if v], [pl['id'] for pl, v in out if not v]
    vis1, qual1 = run()
    cas, pas = [pl['ca'] for pl in area], [pl['pa'] for pl in area]
    rnd.shuffle(cas); rnd.shuffle(pas)
    for pl, ca, pa in zip(area, cas, pas):
        pl['ca'], pl['pa'] = ca, pa
        rnd.shuffle(pl['attrs'])
    vis2, qual2 = run()
    assert len(vis1) == 250 and vis1 == vis2                      # Auswahl und Reihenfolge gleich
    assert qual1 != qual2 and not set(vis1) & set(qual1)          # Qualitätsteil darf sich ändern, keine Doppelten
    byid = {pl['id']: pl for pl in area}
    keys = [(rel(byid[i]), -(will[i] // 10)) for i in vis1]
    assert keys == sorted(keys)                                   # Nähe, dann Wechselchance-Stufe
    assert len({k[0] for k in keys}) > 1


def test_vis_order_within_band_by_reputation_gap():
    area = [dict(id=1, club=5), dict(id=2, club=6), dict(id=3, club=0), dict(id=4, club=6), dict(id=5, club=7),
            dict(id=6, club=8)]
    will = {1: 91, 2: 95, 3: 97, 4: 95, 5: 80, 6: 93}
    con = {1: dict(end='2027-06-30'), 2: dict(end='2028-06-30'), 4: dict(end='2026-12-31'), 5: dict(end=None)}
    rep = {5: 3000, 6: 4500, 7: 4300, 8: 5300}
    out = X.select_pool(area, will, con, rep, lambda pl: False, lambda pl: 0, my_rep=4300)
    # Stufe 90er: Verein 6 (Abstand 200) vor Verein 8 (1000) vor Verein 5 (1300) vor vereinslos (ohne Reputation);
    # bei gleichem Verein entscheidet das Vertragsende; Stufe 80er (trotz Abstand 0) zuletzt
    assert [pl['id'] for pl, v in out] == [4, 2, 6, 1, 3, 5] and all(v for _, v in out)


def test_vis_relevance_before_willingness_band():
    # Serie-B-Verein (Liga Stufe ± 1) vor Verein ohne Liga und vor fremdem Land, alle in derselben Wechselchance-Stufe
    club_map = {1: dict(nat=776, rep=4300), 10: dict(nat=776, rep=5200), 11: dict(nat=776, rep=4300),
                12: dict(nat=769, rep=4300), 13: dict(nat=776, rep=7000)}
    league_of = {1: 103, 10: 102, 13: 101}            # 11 und 12 ohne spielbare Liga
    near = {102, 103, 104}
    area = [dict(id=1, club=11, nat=776), dict(id=2, club=10, nat=776), dict(id=3, club=12, nat=776),
            dict(id=4, club=0, nat=776), dict(id=5, club=0, nat=769), dict(id=6, club=13, nat=776),
            dict(id=7, club=10, nat=776)]
    will = {1: 75, 2: 72, 3: 79, 4: 97, 5: 97, 6: 70, 7: 55}
    rep = {c: v['rep'] for c, v in club_map.items()}

    def rel(pl):
        return X.pool_relevance(pl, club_map, 776, near, league_of)
    assert [rel(pl) for pl in area] == [1, 0, 2, 1, 2, 2, 0]
    out = X.select_pool(area, will, {}, rep, lambda pl: False, lambda pl: 0, relevance=rel, my_rep=4300)
    order = [pl['id'] for pl, _ in out]
    assert order.index(2) < order.index(1)            # Serie B vor Verein ohne Liga, gleiche Stufe 70er
    assert order == [2, 7, 4, 1, 5, 3, 6]
    # vis_ok schließt aus (z. B. Vereinslose unter 18)
    out = X.select_pool(area, will, {}, rep, lambda pl: False, lambda pl: 0, relevance=rel, my_rep=4300,
                        vis_ok=lambda pl: pl['club'] != 0)
    assert 4 not in [pl['id'] for pl, _ in out] and 5 not in [pl['id'] for pl, _ in out]


def test_own_reader_willingness_ignores_ca():
    # Eigener Leser: kein Vereinsabstand aus Stärke; CA/PA/Attribute ändern die Wechselchance nicht
    base = dict(id=1, club=5, pers=[10, 15, 12] + [10] * 5)
    cm = {5: dict(), 1: dict()}
    outs = set()
    for ca in (40, 90, 150, 199):
        pl = dict(base, ca=ca, pa=ca + 10, attrs=[ca % 100] * 54)
        outs.add(X.player_willingness(pl, 1, cm, False, 2.0, 26))
    assert len(outs) == 1
    assert X.club_diff(5, 1, cm, False) == 0 and X.club_diff(0, 1, cm, False) == X.FREE_AGENT_DIFF
    assert X.player_willingness(dict(base, club=1), 1, cm, False, 2.0, 26) is None


def test_willingness_ignores_personality():
    # Ehrgeiz und Loyalität sieht man im Spiel ohne Scouting nicht → keine Wirkung auf die Wechselchance
    cm = {1: dict(rep=4300), 2: dict(rep=7100), 3: dict(rep=3000)}
    for club in (2, 3, 0):
        outs = {X.player_willingness(dict(id=1, club=club, pers=pers), 1, cm, True, 2.0, 26)
                for pers in ([10] * 8, [1, 20, 20] + [10] * 5, [20, 1, 1] + [1] * 5, None)}
        assert len(outs) == 1


def test_rep_diff_cap_for_small_clubs():
    cm = {1: dict(rep=4300), 2: dict(rep=1000), 3: dict(rep=4100)}
    assert X.club_diff(2, 1, cm, True) == X.REP_DIFF_MIN == -4
    assert X.club_diff(3, 1, cm, True) == -4
    assert X.club_diff(0, 1, cm, True) == X.FREE_AGENT_DIFF


def test_has_lower_tier():
    tiers = {22: (776, 1), 23: (776, 2), 24: (776, 3), 30: (769, 1)}
    assert X.has_lower_tier(tiers, 23) is True
    assert X.has_lower_tier(tiers, 24) is False
    assert X.has_lower_tier(tiers, 30) is False
    assert X.has_lower_tier(tiers, None) is False


@pytest.mark.save
def test_ravenna_scout_area(ravenna_data):
    m = ravenna_data['meta']
    assert m['scout_filter'] == m['scout_area'] and m['nat'] == 'ITA'
    pool = ravenna_data['pool']
    assert pool and all(p['nat'] != '–' for p in pool[:200])
    assert any(p['vis'] for p in pool) and sum(p['vis'] for p in pool) <= X.VIS_POOL
    assert len(pool) <= 8000
    assert all(isinstance(p['weaker_league'], bool) and isinstance(p['near_league'], bool) for p in pool)
    vis = [p for p in pool if p['vis']]
    assert any(p['lg'] == 'Serie BKT' for p in vis) and any(p['weaker_league'] for p in vis)
    assert not any(not p['club'] and p['age'] < 18 for p in vis)
