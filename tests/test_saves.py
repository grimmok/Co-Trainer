import os, time, pytest
from cotrainer import saves
from cotrainer.extract import SaveReadError


def _mk(folder, name, age):
    p = folder / name; p.write_bytes(b"x"); t = time.time() - age; os.utime(p, (t, t)); return p


def test_list_newest_first_without_backups(tmp_path):
    _mk(tmp_path, "alt.fm", 300); _mk(tmp_path, "neu.fm", 10)
    _mk(tmp_path, "last save overwrite backup.fm", 1); _mk(tmp_path, "Autosave 3.fm", 2); _mk(tmp_path, "notiz.txt", 1)
    assert [s.name for s in saves.list_saves(str(tmp_path))] == ["neu.fm", "alt.fm"]


def test_missing_folder_gives_empty_list(tmp_path):
    assert saves.list_saves(str(tmp_path / "gibt-es-nicht")) == []


def test_summary_of_garbage_raises(tmp_path):
    p = _mk(tmp_path, "kaputt.fm", 1)
    with pytest.raises(SaveReadError):
        saves.read_summary(str(p))


def test_default_dir_is_games_folder_with_newest_save(tmp_path, monkeypatch):
    for game, age in (("Football Manager 26", 50), ("Football Manager 2024", 500)):
        d = tmp_path / "Documents" / "Sports Interactive" / game / "games"; d.mkdir(parents=True)
        _mk(d, "a.fm", age)
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path))
    assert saves.default_saves_dir() == str(tmp_path / "Documents" / "Sports Interactive" / "Football Manager 26" / "games")


def test_default_dir_is_none_without_saves(tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path))
    assert saves.default_saves_dir() is None


@pytest.mark.save
def test_summary_ravenna_is_fast(ravenna_save):
    t = time.time(); s = saves.read_summary(ravenna_save)
    assert s["manager"] == "Haribaert Kachinski" and "Ravenna" in s["club"]
    assert s["game_date"][:4] == "2026"
    assert time.time() - t < 5
