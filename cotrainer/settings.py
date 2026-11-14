"""Programmeinstellungen des Nutzers in %APPDATA%\\Co-Trainer\\settings.json."""
import json
import os
from dataclasses import asdict, dataclass

THEMES = {'dark', 'light'}
INFO_LEVELS = {'aus', 'scoutbericht', 'werte'}


@dataclass
class Settings:
    saves_dir: str | None = None            # Spielstand-Ordner
    game_dir: str | None = None             # Spielinstallation (für die Sprachdatenbank)
    theme: str = 'dark'
    info_level: str = 'aus'                 # Informationsstufe der Transfervorschläge (ab Teil 2 benutzt)
    skip_spoiler_warning: bool = False      # „Nicht mehr fragen“ (ab Teil 2 benutzt)


def settings_path():
    base = os.environ.get('APPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
    return os.path.join(base, 'Co-Trainer', 'settings.json')


def load(path=None):
    """Fehlende oder beschädigte Datei ergibt Standardwerte; unbekannte Schlüssel und falsche Werte werden verworfen."""
    try:
        with open(path or settings_path(), encoding='utf-8') as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return Settings()
    if not isinstance(raw, dict):
        return Settings()
    s = Settings()
    for name in ('saves_dir', 'game_dir'):
        if isinstance(raw.get(name), str) and raw[name]:
            setattr(s, name, raw[name])
    if raw.get('theme') in THEMES:
        s.theme = raw['theme']
    if raw.get('info_level') in INFO_LEVELS:
        s.info_level = raw['info_level']
    if isinstance(raw.get('skip_spoiler_warning'), bool):
        s.skip_spoiler_warning = raw['skip_spoiler_warning']
    return s


def save(s, path=None):
    path = path or settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(asdict(s), f, ensure_ascii=False, indent=2)
