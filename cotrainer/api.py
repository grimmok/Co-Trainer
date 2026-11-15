"""Brücke zwischen Oberfläche und Python.

Die Oberfläche ruft die öffentlichen Methoden über window.pywebview.api auf. Alles, was mit einem Unterstrich
beginnt, bleibt für die Oberfläche unsichtbar (pywebview legt nur öffentliche Namen offen).
"""
import glob
import json
import os
import threading
from dataclasses import asdict

from . import __version__, extract, guard, saves, settings


def _lang_db_in(game_dir):
    """Sprachdatenbank unterhalb der Spielinstallation oder None."""
    found = glob.glob(os.path.join(game_dir, 'shared', 'data', 'database', 'db', '*', '*_fm', 'lang_db.dat'))
    return max(found) if found else None


class Api:
    def __init__(self, settings_file=None):
        self._settings_file = settings_file
        self._settings = settings.load(settings_file)
        self._window = None                 # wird von app.py gesetzt
        self._thread = None
        self._lock = threading.Lock()
        self._lang_db_cache = None

    # ------------------------------------------------------------ Zustand und Einstellungen
    def _save_settings(self):
        settings.save(self._settings, self._settings_file)

    def _lang_db(self):
        if self._lang_db_cache and os.path.exists(self._lang_db_cache):
            return self._lang_db_cache
        path = _lang_db_in(self._settings.game_dir) if self._settings.game_dir else None
        self._lang_db_cache = path or extract.find_lang_db({})
        return self._lang_db_cache

    def _saves(self, folder):
        return [asdict(s) for s in saves.list_saves(folder)]

    def get_state(self):
        remembered = self._settings.saves_dir
        state = dict(saves_dir=remembered, suggested_dir=saves.default_saves_dir(), theme=self._settings.theme,
                     info_level=self._settings.info_level, skip_spoiler_warning=self._settings.skip_spoiler_warning,
                     version=__version__, saves=[], lang_db_found=bool(self._lang_db()))
        if remembered and not os.path.isdir(remembered):
            state['saves_dir'] = None
            state['notice'] = 'Der gemerkte Spielstand-Ordner wurde nicht gefunden.'
        elif remembered:
            state['saves'] = self._saves(remembered)
        return state

    def set_saves_dir(self, path):
        if not path or not os.path.isdir(path):
            return dict(ok=False, error='Ordner nicht gefunden.')
        count = len(saves.list_saves(path))
        if not count:
            return dict(ok=False, error='In diesem Ordner liegen keine Spielstände (.fm).')
        self._settings.saves_dir = path
        self._save_settings()
        return dict(ok=True, count=count)

    def _browse(self):
        import webview
        picked = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        return dict(path=picked[0] if picked else None)

    def browse_saves_dir(self):
        return self._browse()

    def browse_game_dir(self):
        return self._browse()

    def list_saves(self):
        return dict(saves=self._saves(self._settings.saves_dir))

    def summary(self, path):
        try:
            return dict(ok=True, **saves.read_summary(path))
        except extract.SaveReadError as e:
            return dict(ok=False, error=str(e))

    def set_theme(self, theme):
        if theme not in settings.THEMES:
            return dict(ok=False, error='Unbekanntes Farbschema.')
        self._settings.theme = theme
        self._save_settings()
        return dict(ok=True)

    def set_info_level(self, level, skip_warning=None):
        """Informationsstufe der Transfervorschläge; skip_warning None lässt den gespeicherten Wert unverändert."""
        if level not in settings.INFO_LEVELS:
            return dict(ok=False, error='Unbekannte Informationsstufe.')
        self._settings.info_level = level
        if skip_warning is not None:
            self._settings.skip_spoiler_warning = bool(skip_warning)
        self._save_settings()
        return dict(ok=True)

    def set_title(self, title):
        """Fenstertitel, z. B. „Co-Trainer · Ravenna · Serie C/B“."""
        self._window.set_title(str(title)[:120])
        return dict(ok=True)

    def set_game_dir(self, path):
        if not path or not os.path.isdir(path) or not _lang_db_in(path):
            return dict(ok=False, error='In diesem Ordner wurde die Sprachdatenbank des Spiels nicht gefunden.')
        self._settings.game_dir = path
        self._lang_db_cache = None
        self._save_settings()
        return dict(ok=True)

    # ------------------------------------------------------------ Einlesen
    def analyse(self, path):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return dict(started=False, error='Es wird bereits ein Spielstand eingelesen.')
            self._thread = threading.Thread(target=self._run, args=(path,), daemon=True)
            self._thread.start()
        return dict(started=True)

    def _call(self, function, *args):
        self._window.evaluate_js(f'CT.{function}(' + ', '.join(json.dumps(a, ensure_ascii=False) for a in args) + ')')

    def _run(self, path):
        steps = extract.PROGRESS_STEPS

        def progress(text):
            index = steps.index(text) + 1 if text in steps else 0
            self._call('onProgress', index, len(steps), text)

        try:
            lang_db = self._lang_db()
            data = extract.analyse(path, cfg={'lang_db': lang_db} if lang_db else {}, progress=progress)
            guard.assert_public(data)
        except extract.SaveReadError as e:
            self._call('onError', str(e))
        except guard.HiddenValueError:
            self._call('onError', 'Interner Schutz hat ausgelöst – bitte melden.')
        except Exception as e:                                  # die Meldung selbst könnte Werte enthalten
            self._call('onError', f'Unerwarteter Fehler beim Einlesen: {type(e).__name__}')
        else:
            try:
                self._call('onResult', data)
            except Exception as e:                              # sonst bliebe die Seite beim Fortschritt stehen
                self._call('onError', f'Das Ergebnis konnte nicht angezeigt werden: {type(e).__name__}')

    def join(self, timeout=120):
        """Wartet auf das laufende Einlesen (für Tests)."""
        if self._thread:
            self._thread.join(timeout)
