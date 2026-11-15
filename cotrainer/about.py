"""Lizenzhinweise für das Fenster „Über Co-Trainer“ (THIRD_PARTY_LICENSES.txt, erzeugt von tools/third_party.py)."""
import os
import sys

NOTICES = 'THIRD_PARTY_LICENSES.txt'


def notices_path():
    """Gepackt liegt die Datei im Entpackordner von PyInstaller, sonst im Projektordner über dem Paket."""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, NOTICES)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), NOTICES)


def notices_text(path=None):
    """Inhalt der Lizenzliste oder None, wenn die Datei fehlt."""
    try:
        with open(path or notices_path(), encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return None
