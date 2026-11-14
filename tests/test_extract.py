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
