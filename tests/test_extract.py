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


@pytest.mark.save
def test_osijek_reads_first_team_from_fmsave(osijek_save):
    data = extract.analyse(osijek_save)
    m = data["meta"]
    assert m["source"] == "fmsave" and m["club"] == "NK Osijek" and m["manager"] == "Ivan Kurasic"
    assert m["league"] == "First League" and len(m["rivals"]) == 9
    assert 20 <= len(data["squad"]) <= 30 and len(data["pool"]) > 1000
    f = m["finances"]                                                # per Screenshot bestätigt (14.11.)
    assert f["wage_budget_week"] == 50451 and f["transfer_budget"] == 499998 and f["balance"] == 6713387
    assert f["wage_payroll_week"] == 45680              # Gehaltskosten gesamt laut Screenshot


@pytest.mark.save
def test_ravenna_reads_first_team_from_fmsave(ravenna_data):
    m = ravenna_data["meta"]
    assert m["source"] == "fmsave" and m["league"] == "Serie C/B"
    assert 24 <= len(ravenna_data["squad"]) <= 28                    # 27 in der ersten Mannschaft
    assert sum(1 for p in ravenna_data["squad"] if p.get("tr")) >= 23  # Bewertungen zugeordnet (gemessen: 23)
    assert len(m["rivals"]) == 18
