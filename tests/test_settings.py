from cotrainer import settings as st


def test_roundtrip(tmp_path):
    p = str(tmp_path / "a" / "settings.json")
    st.save(st.Settings(saves_dir=r"C:\x", theme="light"), p)
    s = st.load(p)
    assert s.saves_dir == r"C:\x" and s.theme == "light" and s.info_level == "aus"


def test_missing_file_gives_defaults(tmp_path):
    assert st.load(str(tmp_path / "nix.json")) == st.Settings()


def test_corrupt_file_gives_defaults(tmp_path):      # Review Focus 5
    p = tmp_path / "settings.json"; p.write_text("{kaputt", encoding="utf-8")
    assert st.load(str(p)) == st.Settings()


def test_invalid_values_fall_back(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text('{"theme": "lila", "info_level": "alles", "fremd": 1}', encoding="utf-8")
    s = st.load(str(p))
    assert s.theme == "dark" and s.info_level == "aus"


def test_wrong_types_fall_back(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text('{"saves_dir": 5, "game_dir": ["x"], "skip_spoiler_warning": "ja"}', encoding="utf-8")
    assert st.load(str(p)) == st.Settings()


def test_file_that_is_not_an_object_gives_defaults(tmp_path):
    p = tmp_path / "settings.json"; p.write_text("[1, 2]", encoding="utf-8")
    assert st.load(str(p)) == st.Settings()


def test_path_is_under_appdata(monkeypatch):
    monkeypatch.setenv("APPDATA", r"C:\Users\x\AppData\Roaming")
    assert st.settings_path() == r"C:\Users\x\AppData\Roaming\Co-Trainer\settings.json"
