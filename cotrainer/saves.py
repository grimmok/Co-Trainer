"""Spielstand-Ordner finden, Spielstände auflisten und die Kurzinfo eines Spielstands lesen.

Alle Dateien werden nur zum Lesen geöffnet.
"""
import datetime
import glob
import os
import re
import struct
from dataclasses import dataclass

import zstandard

from . import extract

SKIP_SAVE = re.compile(r'backup|auto ?save', re.I)      # Sicherungen des Spiels
TAIL_BYTES = 4 * 1024 * 1024                            # das Inhaltsverzeichnis steht am Dateiende


@dataclass
class SaveInfo:
    path: str
    name: str
    saved: str          # letzte Änderung, ISO-Zeit


def list_saves(folder):
    """Spielstände (*.fm) eines Ordners, neueste zuerst, ohne Sicherungen. Fehlt der Ordner: leere Liste."""
    if not folder or not os.path.isdir(folder):
        return []
    found = []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if not name.lower().endswith('.fm') or SKIP_SAVE.search(name) or not os.path.isfile(path):
            continue
        found.append((os.path.getmtime(path), path, name))
    found.sort(reverse=True)
    return [SaveInfo(path=p, name=n, saved=datetime.datetime.fromtimestamp(t).isoformat(timespec='seconds'))
            for t, p, n in found]


def default_saves_dir():
    """Der games-Ordner unter Dokumente\\Sports Interactive\\Football Manager* mit dem jüngsten Spielstand."""
    docs = os.path.join(os.path.expanduser('~'), 'Documents', 'Sports Interactive')
    best, best_time = None, ''
    for folder in glob.glob(os.path.join(docs, 'Football Manager*', 'games')):
        found = list_saves(folder)
        if found and found[0].saved > best_time:
            best, best_time = folder, found[0].saved
    return best


def _last_frame(data):
    """Entpackt den letzten zstd-Frame in data, der das Inhaltsverzeichnis enthält; None, wenn keiner passt."""
    pos = data.rfind(extract.MAGIC)
    while pos != -1:
        try:
            raw = zstandard.ZstdDecompressor().decompressobj().decompress(data[pos:])
        except zstandard.ZstdError:
            raw = b''
        if b'save_game_summary' in raw:
            return raw
        pos = data.rfind(extract.MAGIC, 0, pos)
    return None


def read_summary(path):
    """Manager, Verein und Spieldatum (ISO) – liest nur Inhaltsverzeichnis und save_game_summary, nicht game_db."""
    error = extract.SaveReadError(f'Das ist kein lesbarer FM27-Spielstand: {os.path.basename(path)}')
    try:
        with open(path, 'rb') as f:
            size = f.seek(0, os.SEEK_END)
            f.seek(max(0, size - TAIL_BYTES))
            toc = _last_frame(f.read())
            if toc is None and size > TAIL_BYTES:
                f.seek(0)
                toc = _last_frame(f.read())
            if toc is None:
                raise error
            m = re.search(rb'\x11\x00\x00\x00save_game_summary\x04\x00\x00\x00\.dat(.{8})(.{8})', toc, re.S)
            if not m:
                raise error
            offset, comp = struct.unpack('<QQ', m.group(1) + m.group(2))
            if offset + 26 >= size:
                raise error
            f.seek(offset + 26)
            block = f.read(comp if 0 < comp <= 64 * 1024 * 1024 else TAIL_BYTES)
        raw = zstandard.ZstdDecompressor().decompressobj().decompress(block)
    except (OSError, zstandard.ZstdError, struct.error) as e:
        raise error from e
    s = extract.parse_summary(raw)
    if not s['manager'] or not s['game_date']:
        raise error
    return dict(manager=s['manager'], club=s['club'], game_date=s['game_date'].isoformat())
