"""Länder: Kontinent und Region aus game_db, deutsche Namen und Kürzel aus lang_db.dat.

Schlüssel ist überall die Datenbank-Nr. des Landes (dieselbe in jedem Spielstand), nicht die
Zeile der Nationentabelle.
Kontinent: 0 Afrika, 1 Asien, 2 Europa, 3 Nord-/Mittelamerika, 4 Ozeanien, 5 Südamerika, 255 keiner.
Region: Nummer aus der Nationentabelle (z. B. 11 = Südeuropa), siehe HANDOFF „Kontinent und Region je Land“.
"""
import struct

import zstandard

from .extract import MAGIC, log

_GEO_STEP = 8           # 9. Schritt der Nationentabelle: 24 feste Bytes, Kontinent = Byte 1, Region = u32 ab Byte 5
_U32 = struct.Struct('<I')
_HEADER = struct.Struct('<III')


def _step_start(game_db, record_start, scan, stop):
    """Beginn des Schritts `stop` im Datensatz ab `record_start` (Ablauf wie fmsave `_closing_header_at`)."""
    pos = record_start + 1
    for count_struct, lead, strings, tail in scan.steps[:stop]:
        if count_struct is None:
            entries = 1
        else:
            entries = count_struct.unpack_from(game_db, pos)[0]
            pos += count_struct.size
        if not strings:
            pos += entries * (lead + tail)
        else:
            for _ in range(entries):
                pos += lead
                for _ in range(strings):
                    pos += 4 + _U32.unpack_from(game_db, pos)[0]
                pos += tail
    return pos


def nation_geo(game_db):
    """Datenbank-Nr. → (Kontinent, Region); {}, wenn die Nationentabelle nicht genau einmal gefunden wird."""
    try:
        from fmsave._layouts.fm27_27_0_0 import NATION_TABLE
        from fmsave.readers.nations import _closing_header_at, _nation_scan, _walk_table
        scan = _nation_scan(NATION_TABLE)
    except Exception as e:          # fmsave fehlt oder hat andere Interna
        log('Nationentabelle: fmsave nicht nutzbar:', e)
        return {}
    step = scan.steps[_GEO_STEP] if len(scan.steps) > _GEO_STEP else None
    if step is None or step[0] is not None or step[1] < 9 or step[2]:
        log('Nationentabelle: unerwarteter Aufbau des 9. Schritts')
        return {}
    starts = []
    m = scan.search.search(game_db)
    while m is not None:
        records = m.start() + scan.records_offset
        if _walk_table(game_db, records, scan) is not None:
            starts.append(records)
        m = scan.search.search(game_db, m.start() + 1)
    if len(starts) != 1:
        log(f'Nationentabelle: {len(starts)} ablaufbare Tabellen statt einer')
        return {}
    geo, pos, n = {}, starts[0], len(game_db)
    try:
        for _ in range(scan.row_count):
            end = _closing_header_at(game_db, pos, scan, n)
            g = _step_start(game_db, pos, scan, _GEO_STEP)
            _row, db_id, _third = _HEADER.unpack_from(game_db, end)
            geo[db_id] = (game_db[g + 1], _U32.unpack_from(game_db, g + 5)[0])
            pos = end + _HEADER.size
    except (struct.error, IndexError) as e:
        log('Nationentabelle: Zeile nicht lesbar:', e)
        return {}
    return geo


def _parse_names(raw):
    """Länderliste eines lang_db-Frames: Kopf (12 Bytes, Anzahl bei 8), dann je Land
    Nr.(4) len Name Flag len Kurzname Flag len Kürzel len Adjektiv Flag. None, wenn der Frame anders aussieht."""
    if len(raw) < 12:
        return None
    count = _U32.unpack_from(raw, 8)[0]
    if not 0 < count <= 5000:
        return None
    out, p = {}, 12

    def text(p):
        k = _U32.unpack_from(raw, p)[0]
        if k > 200 or p + 4 + k > len(raw):
            raise ValueError
        return raw[p + 4:p + 4 + k].decode('utf-8'), p + 4 + k

    try:
        for _ in range(count):
            db_id = _U32.unpack_from(raw, p)[0]
            name, p = text(p + 4)
            _short, p = text(p + 1)
            code, p = text(p + 1)
            _adj, p = text(p)
            p += 1
            out[db_id] = (name, code)
    except (ValueError, struct.error, UnicodeDecodeError):
        return None
    return out if p == len(raw) else None


def nation_names(lang_path):
    """Datenbank-Nr. → (deutscher Name, Kürzel) aus lang_db.dat; {} ohne Datei oder ohne deutsche Länderliste."""
    if not lang_path:
        return {}
    try:
        with open(lang_path, 'rb') as f:
            data = f.read()
    except OSError as e:
        log('Ländernamen: lang_db.dat nicht lesbar:', e)
        return {}
    dz = zstandard.ZstdDecompressor()
    view = memoryview(data)             # kein Kopieren des Puffers je Frame
    pos = data.find(MAGIC)
    while pos != -1:
        obj = dz.decompressobj()
        try:
            raw = obj.decompress(view[pos:])
        except zstandard.ZstdError:
            pos = data.find(MAGIC, pos + 4)
            continue
        used = len(data) - pos - len(obj.unused_data)
        if b'\x07\x00\x00\x00Italien' in raw and b'\x0b\x00\x00\x00Deutschland' in raw:
            names = _parse_names(raw)
            if names and names.get(776, ('',))[0] == 'Italien' and names.get(771, ('',))[0] == 'Deutschland':
                return names
        pos = data.find(MAGIC, pos + used)
    log('Ländernamen: deutsche Länderliste in lang_db.dat nicht gefunden')
    return {}


def nation_label(names, db_id):
    """(Kürzel, Name) eines Landes; fehlt der Eintrag: ('–', ''). Ohne Kürzel steht '–' davor."""
    entry = names.get(db_id) if db_id is not None else None
    if not entry:
        return ('–', '')
    name, code = entry
    return (code or '–', name)
