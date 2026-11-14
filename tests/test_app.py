import os
import socket

import pytest
import webview

from cotrainer import app


def test_ui_path_exists():
    assert os.path.isfile(app.ui_path()) and app.ui_path().endswith(os.path.join("ui", "index.html"))


def test_ui_path_in_frozen_app(monkeypatch, tmp_path):
    (tmp_path / "cotrainer" / "ui").mkdir(parents=True); (tmp_path / "cotrainer" / "ui" / "index.html").write_text("x")
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path), raising=False); monkeypatch.setattr("sys.frozen", True, raising=False)
    assert app.ui_path() == str(tmp_path / "cotrainer" / "ui" / "index.html")


@pytest.fixture
def fake_gui(monkeypatch, tmp_path):
    """Kein echtes Fenster: zeichnet auf, womit pywebview aufgerufen würde."""
    seen = {"boxes": []}
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(app, "message_box", seen["boxes"].append)
    monkeypatch.setattr(app, "webview2_installed", lambda: True)
    monkeypatch.setattr(webview, "create_window", lambda *a, **k: seen.update(window=(a, k)) or "fenster")
    monkeypatch.setattr(webview, "start", lambda *a, **k: seen.update(start=k))
    return seen


def test_main_creates_window_with_persistent_storage(fake_gui, tmp_path):
    app.main()
    args, kw = fake_gui["window"]
    assert args[0] == "Co-Trainer" and args[1] == app.ui_path()
    assert (kw["width"], kw["height"], kw["min_size"]) == (1280, 860, (1000, 700))
    assert kw["js_api"]._window == "fenster"
    start = fake_gui["start"]
    assert start["private_mode"] is False and start["storage_path"] == str(tmp_path / "Co-Trainer" / "webview")
    assert start["http_port"] == app.UI_PORT          # fester Port: sonst vergisst die Oberfläche ihren Zustand
    assert fake_gui["boxes"] == []


def test_busy_port_falls_back_to_a_random_one(fake_gui):
    with socket.socket() as s:
        s.bind(("127.0.0.1", app.UI_PORT))
        app.main()
    assert fake_gui["start"]["http_port"] is None


def test_missing_webview2_shows_message_instead_of_window(fake_gui, monkeypatch):
    monkeypatch.setattr(app, "webview2_installed", lambda: False)
    app.main()
    assert "window" not in fake_gui and "WebView2-Laufzeit" in fake_gui["boxes"][0]


def test_start_failure_shows_message(fake_gui, monkeypatch):
    def boom(*a, **k): raise RuntimeError("kaputt")
    monkeypatch.setattr(webview, "start", boom)
    app.main()
    assert "WebView2-Laufzeit" in fake_gui["boxes"][0]
