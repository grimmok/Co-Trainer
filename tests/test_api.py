import json, threading, pytest
from cotrainer import api as api_mod, extract


class FakeWindow:
    def __init__(self): self.calls = []
    def evaluate_js(self, js): self.calls.append(js)


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr(api_mod.saves, "default_saves_dir", lambda: None)   # unabhängig vom Rechner
    monkeypatch.setattr(extract, "find_lang_db", lambda cfg: cfg.get("lang_db"))
    a = api_mod.Api(settings_file=str(tmp_path / "settings.json")); a._window = FakeWindow(); return a


def test_state_reports_missing_remembered_folder(api, tmp_path):        # Review Focus 1
    assert api.set_saves_dir(str(tmp_path / "weg"))["ok"] is False
    (tmp_path / "g").mkdir(); (tmp_path / "g" / "a.fm").write_bytes(b"x")
    assert api.set_saves_dir(str(tmp_path / "g")) == {"ok": True, "count": 1}
    (tmp_path / "g" / "a.fm").unlink(); (tmp_path / "g").rmdir()
    s = api.get_state()
    assert s["saves_dir"] is None and "nicht gefunden" in s["notice"]


def test_state_lists_saves_of_remembered_folder(api, tmp_path):
    (tmp_path / "a.fm").write_bytes(b"x")
    api.set_saves_dir(str(tmp_path))
    s = api.get_state()
    assert s["saves_dir"] == str(tmp_path) and "notice" not in s
    assert [x["name"] for x in s["saves"]] == ["a.fm"] and s["theme"] == "dark" and s["version"]
    assert api.list_saves()["saves"] == s["saves"]


def test_settings_survive_a_restart(api, tmp_path):
    (tmp_path / "a.fm").write_bytes(b"x")
    api.set_saves_dir(str(tmp_path)); assert api.set_theme("light") == {"ok": True}
    again = api_mod.Api(settings_file=str(tmp_path / "settings.json")).get_state()
    assert again["saves_dir"] == str(tmp_path) and again["theme"] == "light"


def test_unknown_theme_is_rejected(api):
    assert api.set_theme("lila")["ok"] is False and api.get_state()["theme"] == "dark"


def test_game_dir_without_lang_db_is_rejected(api, tmp_path):
    assert api.set_game_dir(str(tmp_path))["ok"] is False
    assert api.get_state()["lang_db_found"] is False
    d = tmp_path / "shared" / "data" / "database" / "db" / "2700" / "2700_fm"; d.mkdir(parents=True); (d / "lang_db.dat").write_bytes(b"x")
    assert api.set_game_dir(str(tmp_path)) == {"ok": True}
    assert api.get_state()["lang_db_found"] is True


def test_game_dir_lang_db_is_passed_to_analyse(api, tmp_path, monkeypatch):
    d = tmp_path / "shared" / "data" / "database" / "db" / "2700" / "2700_fm"; d.mkdir(parents=True); (d / "lang_db.dat").write_bytes(b"x")
    api.set_game_dir(str(tmp_path))
    seen = {}
    monkeypatch.setattr(extract, "analyse", lambda p, cfg=None, progress=None: (seen.update(cfg or {}), {"squad": [], "pool": []})[1])
    api.analyse("x.fm"); api.join()
    assert seen["lang_db"] == str(d / "lang_db.dat")


def test_empty_folder_is_rejected(api, tmp_path):
    assert api.set_saves_dir(str(tmp_path))["error"] == "In diesem Ordner liegen keine Spielstände (.fm)."


def test_summary_of_unreadable_save_is_an_error_dict(api, tmp_path):
    (tmp_path / "kaputt.fm").write_bytes(b"x")
    r = api.summary(str(tmp_path / "kaputt.fm"))
    assert r["ok"] is False and "kein lesbarer FM27-Spielstand" in r["error"]


def test_analyse_reports_progress_then_result(api, monkeypatch):
    def fake(path, cfg=None, progress=None):
        for s in extract.PROGRESS_STEPS: progress(s)
        return {"meta": {"club": "X"}, "coach": {}, "squad": [], "pool": []}
    monkeypatch.setattr(extract, "analyse", fake)
    assert api.analyse("x.fm") == {"started": True}; api.join()
    calls = api._window.calls
    assert sum(c.startswith("CT.onProgress(") for c in calls) == len(extract.PROGRESS_STEPS)
    assert calls[-1].startswith("CT.onResult(") and json.loads(calls[-1][len("CT.onResult("):-1])["meta"]["club"] == "X"


def test_unreadable_save_reports_error(api, monkeypatch):                # Review Focus 2
    def fake(path, cfg=None, progress=None): raise extract.SaveReadError("Das ist kein lesbarer FM27-Spielstand: x.fm")
    monkeypatch.setattr(extract, "analyse", fake)
    api.analyse("x.fm"); api.join()
    assert api._window.calls[-1] == 'CT.onError("Das ist kein lesbarer FM27-Spielstand: x.fm")'


def test_unexpected_error_reports_type_and_allows_retry(api, monkeypatch):
    def fake(path, cfg=None, progress=None): raise ZeroDivisionError("geheim 150")
    monkeypatch.setattr(extract, "analyse", fake)
    api.analyse("x.fm"); api.join()
    assert api._window.calls[-1] == 'CT.onError("Unerwarteter Fehler beim Einlesen: ZeroDivisionError")'
    assert api.analyse("x.fm") == {"started": True}; api.join()


def test_hidden_value_never_reaches_window(api, monkeypatch):
    monkeypatch.setattr(extract, "analyse", lambda p, cfg=None, progress=None: {"squad": [{"ca": 150}]})
    api.analyse("x.fm"); api.join()
    assert all("150" not in c for c in api._window.calls) and api._window.calls[-1].startswith("CT.onError(")


def test_second_analyse_is_rejected_while_running(api, monkeypatch):    # Review Focus 4
    gate = threading.Event()
    monkeypatch.setattr(extract, "analyse", lambda p, cfg=None, progress=None: (gate.wait(5), {"squad": [], "pool": []})[1])
    assert api.analyse("x.fm")["started"] is True
    assert api.analyse("x.fm") == {"started": False, "error": "Es wird bereits ein Spielstand eingelesen."}
    gate.set(); api.join()
    assert sum(c.startswith("CT.onResult(") for c in api._window.calls) == 1


def test_set_title_changes_the_window_title(api):
    api._window.set_title = lambda t: api._window.calls.append("title:" + t)
    assert api.set_title("Co-Trainer · Ravenna · Serie C/B") == {"ok": True}
    assert api._window.calls[-1] == "title:Co-Trainer · Ravenna · Serie C/B"


def test_failed_result_delivery_reports_error_instead_of_hanging(api, monkeypatch):
    monkeypatch.setattr(extract, "analyse", lambda p, cfg=None, progress=None: {"squad": [], "pool": []})
    real = api._window.evaluate_js
    def flaky(js):
        if js.startswith("CT.onResult("): raise RuntimeError("Fenster")
        real(js)
    api._window.evaluate_js = flaky
    api.analyse("x.fm"); api.join()
    assert api._window.calls[-1] == 'CT.onError("Das Ergebnis konnte nicht angezeigt werden: RuntimeError")'
