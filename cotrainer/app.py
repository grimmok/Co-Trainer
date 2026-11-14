"""Programmfenster: zeigt cotrainer/ui/index.html in einem Edge-WebView2-Fenster (pywebview)."""
import os
import socket
import sys

from . import settings
from .api import Api

UI_PORT = 47127         # fester Port: die Oberfläche merkt sich ihren Zustand pro Adresse (localStorage)
WEBVIEW2_MISSING = ('Co-Trainer braucht die Microsoft-Edge-WebView2-Laufzeit. Sie ist bei Windows 10/11 normalerweise '
                    'vorhanden. Bitte über Windows Update oder von microsoft.com nachinstallieren.')
WEBVIEW2_CLIENTS = ('{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', '{2CD8A007-E189-409D-A2C8-9AF4EF3C72AA}',
                    '{0D50BFEC-CD6A-4F9A-964C-C7416E3ACB10}', '{65C35B14-6C1D-4122-AC46-7148CC9D6497}')


def ui_path():
    """Pfad zu ui/index.html – auch im gepackten Programm (PyInstaller entpackt nach sys._MEIPASS)."""
    if getattr(sys, 'frozen', False):
        base = os.path.join(sys._MEIPASS, 'cotrainer')
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'ui', 'index.html')


def webview2_installed():
    """Ist eine WebView2-Laufzeit eingetragen? Ohne sie würde pywebview auf den alten Internet Explorer ausweichen."""
    import winreg
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for node in (r'SOFTWARE\WOW6432Node', 'SOFTWARE'):
            for client in WEBVIEW2_CLIENTS:
                try:
                    with winreg.OpenKey(root, rf'{node}\Microsoft\EdgeUpdate\Clients\{client}') as key:
                        version = str(winreg.QueryValueEx(key, 'pv')[0])
                except OSError:
                    continue
                if version and version != '0.0.0.0':
                    return True
    return False


def message_box(text):
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, text, 'Co-Trainer', 0x10)


def _port():
    """UI_PORT, wenn er frei ist; sonst None (pywebview nimmt dann einen zufälligen Port)."""
    with socket.socket() as s:
        try:
            s.bind(('127.0.0.1', UI_PORT))
        except OSError:
            return None
    return UI_PORT


def main():
    if not webview2_installed():
        message_box(WEBVIEW2_MISSING)
        return
    import webview
    api = Api()
    try:
        api._window = webview.create_window('Co-Trainer', ui_path(), js_api=api, width=1280, height=860,
                                            min_size=(1000, 700), background_color='#0f1216')
        webview.start(private_mode=False, http_port=_port(),
                      storage_path=os.path.join(os.path.dirname(settings.settings_path()), 'webview'))
    except Exception:
        message_box(WEBVIEW2_MISSING)
