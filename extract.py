"""FM-Scout: liest einen Football-Manager-27-Spielstand (.fm) und erzeugt die Analyse-Seite.

Aufruf:  python extract.py [Pfad\\zum\\Spielstand.fm | Nummer]
         python extract.py --list      (Spielstände mit Nummer auflisten)
Ohne Angabe wird der zuletzt gespeicherte Spielstand verwendet (Sicherungen ausgenommen).
FMS_ROLES=1 gibt die Rollen-Fingerabdrücke aller Taktiken aus (für den Rollentest).
Der Spielstand wird nur gelesen, nie verändert.
"""
import array, bisect, datetime, glob, json, math, os, re, struct, sys, time
from collections import Counter, defaultdict

try:
    import zstandard
except ImportError:
    sys.exit('Bitte zuerst installieren:  python -m pip install zstandard')

HERE = os.path.dirname(os.path.abspath(__file__))
GBP_TO_EUR = 1.1641          # FM speichert Geld intern in Pfund
MAGIC = b'\x28\xb5\x2f\xfd'

ATTR_KEYS = ['Cro', 'Dri', 'Fin', 'Hea', 'Lon', 'Mar', 'OtB', 'Pas', 'Pen', 'Tck', 'Vis', 'Han', 'Aer', 'Cmd', 'Com',
             'Kic', 'Thr', 'Ant', 'Dec', 'One', 'Pos', 'Ref', 'Fir', 'Tec', 'LFoot', 'RFoot', 'Fla', 'Cor', 'Tea', 'Wor',
             'LTh', 'Ecc', 'TRO', 'Pun', 'Acc', 'Fre', 'Str', 'Sta', 'Pac', 'Jum', 'Ldr', 'Dirt', 'Bal', 'Bra', 'Cons',
             'Agg', 'Agi', 'ImpM', 'InjPr', 'Vers', 'Nat', 'Det', 'Cmp', 'Cnt']
HIDDEN = {'Cons', 'Dirt', 'ImpM', 'InjPr', 'Vers'}
POS_KEYS = ['GK', 'SW', 'DL', 'DC', 'DR', 'DM', 'ML', 'MC', 'MR', 'AML', 'AMC', 'AMR', 'ST', 'WBL', 'WBR']


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ---------------------------------------------------------------- Dateien finden
SKIP_SAVE = re.compile(r'backup|auto ?save|autosave', re.I)


def list_saves():
    """Eigene Spielstände, neueste zuerst. Sicherungen (z. B. 'last save overwrite backup.fm') werden ausgelassen."""
    docs = os.path.join(os.path.expanduser('~'), 'Documents', 'Sports Interactive')
    cands = glob.glob(os.path.join(docs, 'Football Manager*', 'games', '*.fm'))
    cands = [c for c in cands if not SKIP_SAVE.search(os.path.basename(c))]
    return sorted(cands, key=os.path.getmtime, reverse=True)


def find_save(arg):
    if arg and not arg.isdigit():
        if not os.path.exists(arg):
            sys.exit(f'Spielstand nicht gefunden: {arg}')
        return arg
    cands = list_saves()
    if not cands:
        sys.exit('Kein Spielstand gefunden. Bitte Pfad angeben: python extract.py "...\\Spielstand.fm"')
    k = int(arg) if arg else 1          # Nummer aus "python extract.py --list"
    if not 1 <= k <= len(cands):
        sys.exit(f'Es gibt nur {len(cands)} Spielstände (siehe python extract.py --list).')
    return cands[k - 1]


def print_saves():
    for k, c in enumerate(list_saves(), 1):
        t = time.strftime('%d.%m.%Y %H:%M', time.localtime(os.path.getmtime(c)))
        print(f'{k:3}  {t}  {os.path.basename(c)}')


def find_lang_db(cfg):
    if cfg.get('lang_db') and os.path.exists(cfg['lang_db']):
        return cfg['lang_db']
    roots = []
    for drv in 'CDEFGHIJ':
        for sub in (r'SteamLibrary\steamapps\common', r'Steam\steamapps\common',
                    r'Program Files (x86)\Steam\steamapps\common', r'Program Files\Steam\steamapps\common'):
            roots.append(f'{drv}:\\{sub}')
    for r in roots:
        for game in ('Football Manager 27', 'Football Manager 2027'):
            dbs = glob.glob(os.path.join(r, game, 'shared', 'data', 'database', 'db', '*', '*_fm', 'lang_db.dat'))
            if dbs:
                return max(dbs, key=lambda p: os.path.basename(os.path.dirname(os.path.dirname(p))))
    return None


# ---------------------------------------------------------------- fmf-Container
def read_frames(path):
    data = open(path, 'rb').read()
    dz = zstandard.ZstdDecompressor()
    frames, offs = [], []
    pos = data.find(MAGIC)
    while pos != -1:
        obj = dz.decompressobj()
        raw = obj.decompress(data[pos:])
        used = len(data) - pos - len(obj.unused_data)
        frames.append(raw); offs.append(pos)
        pos = data.find(MAGIC, pos + used)
    return frames, offs


def directory(frames, offs):
    """Letzter Block = Inhaltsverzeichnis: Name -> Blockindex."""
    idx = {o: i for i, o in enumerate(offs)}
    names = {}
    for m in re.finditer(rb'([\x01-\x60])\x00\x00\x00([a-z0-9_]{3,96})\x04\x00\x00\x00\.dat', frames[-1]):
        if len(m.group(2)) != m.group(1)[0]:
            continue
        off = struct.unpack('<Q', frames[-1][m.end():m.end() + 8])[0]
        i = idx.get(off + 26)
        if i is not None:
            names[m.group(2).decode()] = i
    return names


# ---------------------------------------------------------------- Sprachdatenbank (Wettbewerbsnamen)
def comp_names(lang_path):
    if not lang_path:
        return {}
    data = open(lang_path, 'rb').read()
    dz = zstandard.ZstdDecompressor()
    rec = re.compile(rb'(.{4})([\x02-\x60])\x00\x00\x00([^\xff\x00]{2,96})\xff([\x01-\x60])\x00\x00\x00([^\xff\x00]{1,96})\xff', re.S)
    pos, n = data.find(MAGIC), 0
    best = {}
    while pos != -1 and n < 12:
        obj = dz.decompressobj(); raw = obj.decompress(data[pos:])
        used = len(data) - pos - len(obj.unused_data)
        found = {}
        for m in rec.finditer(raw):
            if len(m.group(3)) != m.group(2)[0] or len(m.group(5)) != m.group(4)[0]:
                continue
            try:
                found[struct.unpack('<I', m.group(1))[0]] = (m.group(3).decode('utf-8'), m.group(5).decode('utf-8'))
            except UnicodeDecodeError:
                pass
        if b'Serie A\xff' in raw and len(found) > len(best):
            best = found
        pos = data.find(MAGIC, pos + used); n += 1
    return best


# ---------------------------------------------------------------- Hauptdatenbank
class DB:
    def __init__(self, d):
        self.d = d

    def u16(self, o): return struct.unpack_from('<H', self.d, o)[0]
    def u32(self, o): return struct.unpack_from('<I', self.d, o)[0]
    def i32(self, o): return struct.unpack_from('<i', self.d, o)[0]
    def i64(self, o): return struct.unpack_from('<q', self.d, o)[0]

    def date(self, o):
        dd, y = self.u16(o) & 0x1ff, self.u16(o + 2)
        if 1900 < y < 2100 and 1 <= dd <= 366:
            return datetime.date(y, 1, 1) + datetime.timedelta(days=dd - 1)
        return None


def name_tables(db):
    d = db.d
    lo, hi = int(len(d) * 0.15), int(len(d) * 0.70)
    tables = []
    i = lo
    while i < hi:
        nid = db.u32(i); ln = db.u32(i + 4)
        if 0 < ln < 80 and i + 8 + ln + 8 < len(d) and db.u32(i + 8 + ln) == nid + 1 and 0 < db.u32(i + 12 + ln) < 80:
            tab = {}
            while True:
                nid = db.u32(i); ln = db.u32(i + 4)
                if not 0 < ln < 80:
                    break
                try:
                    tab[nid] = d[i + 8:i + 8 + ln].decode('utf-8')
                except UnicodeDecodeError:
                    break
                i += 8 + ln
                if db.u32(i) != nid + 1:
                    break
            if len(tab) > 1000:
                tables.append(tab)
                if len(tables) >= 3:
                    break
        i += 1
    # Vor- und Nachnamen = die zwei größten Tabellen, in Dateireihenfolge
    big = sorted(sorted(range(len(tables)), key=lambda k: -len(tables[k]))[:2])
    return [tables[k] for k in big]  # [Vornamen, Nachnamen]


def player_blocks(db):
    pat = re.compile(rb'\x00(?=[\x01-\x14]{15}[\x01-\x64]{54})')
    out = []
    for m in pat.finditer(db.d):
        p = m.start() + 1
        if 20 in db.d[p:p + 15]:
            out.append(p)
    return out


HDR = re.compile(rb'\x00{9}(.{4})\x00(.{4})\x00\xff\xff\xff\xff\x00{5}(..)(..)', re.S)


def clubs(db):
    """Vereinsdatensätze: 'Name'/'Kurzname'-Paar, rund 2000 Bytes später die Markierung 03 Vereins-ID."""
    d = db.d
    hi = int(len(d) * 0.10)
    res = []
    pair = re.compile(rb'([\x02-\x40])\x00\x00\x00([^\x00-\x1f]{2,64}?)([\x02-\x30])\x00\x00\x00([^\x00-\x1f]{2,48}?)(?=[\x00-\x03])', re.S)
    for m in pair.finditer(d, 0, hi):
        if len(m.group(2)) != m.group(1)[0] or len(m.group(4)) != m.group(3)[0]:
            continue
        try:
            res.append(dict(name=m.group(2).decode('utf-8'), short=m.group(4).decode('utf-8'), end=m.end()))
        except UnicodeDecodeError:
            continue
    ends = [c['end'] for c in res]
    byid = {}
    # Markierung "ff <Vereins-ID> 00×6 04 1d" ca. 2,3-2,9 KB nach dem Namen
    for m in re.finditer(rb'\xff(.{4})\x00{6}\x04\x1d', d[:hi], re.S):
        a = struct.unpack('<I', m.group(1))[0]
        if not 0 < a < 300000 or a in byid:
            continue
        k = bisect.bisect_left(ends, m.start()) - 1
        if k < 0 or m.start() - res[k]['end'] > 5000 or 'id' in res[k]:
            continue
        res[k]['id'] = a
        byid[a] = res[k]
    # Kontostand liegt 193 Bytes vor der Markierung "03 <Vereins-ID>"
    for c in byid.values():
        i = d.find(b'\x03' + struct.pack('<I', c['id']), c['end'], c['end'] + 5000)
        if i > 0 and struct.unpack_from('<I', d, i + 9)[0] == struct.unpack_from('<I', d, i + 5)[0] + 1:
            c['idpos'] = i
    return byid


def club_finances(db, c):
    """Budgetblock kurz nach dem Kurznamen: 01 Start Aktuell Garantiert 00 x y Gehaltsbudget/Woche (alles £)."""
    e = c['end']
    pat = re.compile(rb'\x01(.{4})(.{4})(.{4})\x00(.{4})(.{4})(.{4})', re.S)
    f = {}
    for m in pat.finditer(db.d, e, e + 120):
        a, b, g, _, _, w = (struct.unpack('<i', m.group(k))[0] for k in range(1, 7))
        if 0 <= a < 2e9 and 0 <= b < 2e9 and 0 <= g < 2e9 and 0 < w < 1e8 and (a == 0 or 0.3 < b / a < 3):
            f = dict(start_budget=a, transfer_budget=b, next_season_min=g, wage_budget_week=w)
            break
    # Kontostand (i32, £): "ff 00 <Kontostand> xxxx 01 00 6c 07 ×3 00×5" im Vereinsdatensatz
    m = re.compile(rb'\xff\x00(.{4}).{4}(?:\x01\x00\x6c\x07){3}\x00{5}', re.S).search(db.d, e, e + 4000)
    if m:
        f['balance'] = struct.unpack('<i', m.group(1))[0]
    return {k: round(v * GBP_TO_EUR) for k, v in f.items()}


def contracts(db, bpid, hstarts):
    """Vertragskopf direkt vor jeder Person: Datum 00 Personen-ID Vereins-ID 00×4 Wochengehalt(£).
    Der Attributblock des Spielers steht 500-3000 Bytes davor und trägt die ID (Personen-ID - 1).
    Gültig nur, wenn 60-140 Bytes nach dem Vertragskopf ein Personenkopf folgt."""
    pat = re.compile(rb'..[\x6c-\x7f]\x07\x00(.{4})(.{4})\x00\x00\x00\x00(.{4})', re.S)
    res = {}
    for m in pat.finditer(db.d):
        pid = struct.unpack('<I', m.group(1))[0]
        if pid in res or (pid - 1) not in bpid:
            continue
        if not 300 <= m.start() - bpid[pid - 1] <= 4000:
            continue
        club = struct.unpack('<I', m.group(2))[0]
        k = bisect.bisect_left(hstarts, m.start())
        if k >= len(hstarts) or not 60 <= hstarts[k] - m.start() <= 140:
            continue
        wage = struct.unpack('<I', m.group(3))[0]
        if wage > 3_000_000:
            continue
        i = m.start()
        j = db.d.rfind(b'\xff' * 8, i - 140, i)
        end = db.date(j + 8) if j > 0 else None
        res[pid] = dict(club=club, wage_week=round(wage * GBP_TO_EUR), end=end.isoformat() if end else None, hk=k)
    return res


def competitions(frames, names, cnames):
    """Teamlisten der Ligen: Zeilen mit Abstand 443 Bytes, beginnend mit Vereins-ID 00 ff×6."""
    row = re.compile(rb'(.{4})\x00\xff\xff\xff\xff\xff\xff', re.S)
    comps = {}
    for nm, i in names.items():
        if not nm.startswith('comp_') or not nm[5:].isdigit():
            continue
        b = frames[i]
        hits = [(m.start(), struct.unpack('<I', m.group(1))[0]) for m in row.finditer(b)]
        # längste Folge von Tabellenzeilen mit gleichem Abstand (Zeilengröße je nach Liga verschieden)
        best = []
        for a in range(len(hits)):
            for b2 in range(a + 1, min(a + 4, len(hits))):
                step = hits[b2][0] - hits[a][0]
                if not 200 <= step <= 2000:
                    continue
                run = [hits[a], hits[b2]]
                pos = set(o for o, _ in hits)
                nxt = hits[b2][0] + step
                lookup = dict(hits)
                while nxt in lookup:
                    run.append((nxt, lookup[nxt])); nxt += step
                if len(run) > len(best):
                    best = run
            if len(best) >= 24:
                break
        if len(best) >= 6:
            cid = int(nm[5:])
            long_, short = cnames.get(cid, (nm, nm))
            comps[cid] = dict(name=short, long=long_, teams=[c for _, c in best])
    return comps


CUP_WORDS = re.compile(r'cup|coppa|pokal|copa|coupe|trophy|taça|beker|kupa|puchar|champions|europa|conference|'
                       r'libertadores|sudamericana|super|shield|play-?off|qualif|friendly|youth|u1\d|u2\d|reserve|'
                       r'trofeo|supercopa|charity|vase|community', re.I)


def training(frames, names):
    t = frames[names['training_man']]
    rat = {}
    o = t.find(b'\x01\x02\x00\x00\x00')
    if o > 8:
        o -= 8
        n = struct.unpack_from('<I', t, o)[0]; o += 4
        for _ in range(min(n, 500)):
            pid = struct.unpack_from('<I', t, o)[0]
            if t[o + 4:o + 9] != b'\x01\x02\x00\x00\x00':
                break
            a, b = struct.unpack_from('<ff', t, o + 9)
            rat[pid] = [round(a, 2), round(b, 2)]
            o += 17
    weeks = []
    pat = re.compile(rb'\x0b(..)([\xe8-\xef]\x07)\x01((?:\x04.{6}\x00){7})(.{4})', re.S)
    plan, prev = None, None
    for m in pat.finditer(t):
        ln = struct.unpack('<I', m.group(4))[0]
        if ln > 80:
            continue
        s = t[m.end():m.end() + ln].decode('utf-8', 'replace')
        dd = struct.unpack('<H', m.group(1))[0] & 0x1ff; yr = struct.unpack('<H', m.group(2))[0]
        dt = datetime.date(yr, 1, 1) + datetime.timedelta(days=dd - 1)
        if prev is None or dt <= prev:
            plan = []; weeks.append(plan)
        prev = dt
        plan.append([dt.isoformat(), s])
    return rat, weeks


# ---------------------------------------------------------------- Eigene Taktik (tactics_man)
# Positions-Bits im Taktik-Slot
POS_BITS = {0x1: 'GK', 0x2: 'SW', 0x4: 'DR', 0x8: 'DL', 0x10: 'DC', 0x20: 'WBR', 0x40: 'WBL', 0x80: 'DM',
            0x100: 'MR', 0x200: 'ML', 0x400: 'MC', 0x800: 'AMR', 0x1000: 'AML', 0x2000: 'AMC', 0x4000: 'ST'}
# Grundkoordinaten (x, y) fürs Spielfeld; Nebenfeld 0x20 = rechts, 0x10 = links
POS_XY = {'GK': (50, 93), 'SW': (50, 85), 'DR': (86, 72), 'DL': (14, 72), 'DC': (50, 77), 'WBR': (88, 55),
          'WBL': (12, 55), 'DM': (50, 61), 'MR': (85, 44), 'ML': (15, 44), 'MC': (50, 47), 'AMR': (85, 30),
          'AML': (15, 30), 'AMC': (50, 31), 'ST': (50, 11)}
SIDE_DX = {'DC': 14, 'DM': 13, 'MC': 20, 'AMC': 13, 'ST': 13}
# Rollen-Fingerabdruck: (Phase, Rollengruppen-Bit, Bitfolge der Unterblöcke) -> (Rolle, Kürzel, FM27-Name)
# Abgeglichen mit der Taktik aus den Screenshots (u. a. ST: Halbraumstürmer / Mittelstürmer).
ROLE_FP = {
    ('ip', 0, ((12,), (44, 54))): ('bpgk', 'BTW', 'Ballspielender Torwart'),
    ('ip', 2, ((3,), (38,), (44,), (52,), (53,))): ('ifb', 'IAV', 'Inverser Außenverteidiger'),
    ('ip', 1, ((24,), (53, 56))): ('bpcb', 'SpIV', 'Spielaufbauender Innenverteidiger'),
    ('ip', 1, ((24,), (33, 53))): ('cb', 'IV', 'Innenverteidiger'),
    ('ip', 4, ((5,), (7,), (15,), (39,), (47, 54))): ('dlp', 'TSm', 'Tiefer Spielmacher'),
    ('ip', 5, ((7,), (16,), (46,), (47,), (57,), (54,))): ('mp', 'Spm', 'Spielmacher'),
    ('ip', 5, ((9,), (16,), (17,), (32,), (47,), (56,), (55,))): ('fr', 'F', 'Freie Rolle'),
    ('ip', 6, ((7,), (10,), (17,), (27,), (45,), (49,), (55,))): ('wf', 'AS', 'Außenstürmer'),
    ('ip', 6, ((7,), (10,), (27,), (39, 54))): ('w', 'FL', 'Flügelspieler'),
    ('ip', 10, ((11,), (31,), (55, 63))): ('hsf', 'HRS', 'Halbraumstürmer'),
    ('oop', 0, ((1,), (32, 54))): ('gk', 'TW', 'Torwart'),
    ('oop', 9, ((10,), (42, 54))): ('pfb', 'PrAV', 'Pressender Außenverteidiger'),
    ('oop', 9, ((11,), (43, 53))): ('hfb', 'AbAV', 'Abwartender Außenverteidiger'),
    ('oop', 3, ((35, 53),)): ('cb', 'IV', 'Innenverteidiger'),
    ('oop', 15, ((18,), (50, 53))): ('dm', 'DM', 'Defensiver Mittelfeldspieler'),
    ('oop', 15, ((20,), (47, 53))): ('sdm', 'As6', 'Abschirmender Sechser'),
    ('oop', 20, ((27,), (43,), (53,))): ('tcf', 'MaMS', 'Mitarbeitender Mittelstürmer'),
    ('oop', 35, ((38,), (54,))): ('twm', 'ÄMF', 'Äußerer Mittelfeldspieler'),
    ('oop', 42, ((43,), (54,))): ('cfo', 'MS', 'Mittelstürmer'),
}
# Stil-Code im Taktikkopf -> Schlüssel in STYLES (app.html). Weitere Codes erst nach Bestätigung eintragen.
STYLE_CODES = {'TREV': 'vertical_tikitaka', 'EGEG': 'gegenpress'}
# Ersatzrolle, wenn ein Fingerabdruck (noch) unbekannt ist
ROLE_DEFAULT = {'GK': ('gk', 'gk'), 'SW': ('cb', 'cb'), 'DC': ('cb', 'cb'), 'DR': ('fb', 'fb'), 'DL': ('fb', 'fb'),
                'WBR': ('wb', 'wb'), 'WBL': ('wb', 'wb'), 'DM': ('dm', 'dm'), 'MC': ('cm', 'cm'),
                'MR': ('wm', 'twm'), 'ML': ('wm', 'twm'), 'AMC': ('am', 'tam'), 'AMR': ('w', 'tw'),
                'AML': ('w', 'tw'), 'ST': ('cf', 'cfo')}


def _bits(v):
    return tuple(k for k in range(64) if v >> k & 1)


def _tactic_entry(t, p):
    """Ein Slot-Eintrag: 44 00 02 | Position u16 | Seite u16 | 00 01 01 | n u32 | Gruppe u64 | n × Unterblock."""
    if t[p:p + 3] != b'\x44\x00\x02' or t[p + 7:p + 10] != b'\x00\x01\x01':
        return None
    pos, side = struct.unpack_from('<HH', t, p + 3)
    n = struct.unpack_from('<I', t, p + 10)[0]
    if n > 20:
        return None
    grp = struct.unpack_from('<Q', t, p + 14)[0]
    q, subs = p + 22, []
    for _ in range(n):
        if t[q:q + 3] != b'\x02\x02\x02' or t[q + 11] != 0xff:
            return None
        subs.append(_bits(struct.unpack_from('<Q', t, q + 16)[0])); q += 24
    return dict(pos=POS_BITS.get(pos), side=side, grp=_bits(grp), subs=tuple(subs), end=q)


def read_tactics(frames, names):
    """Eigene (benannte) Taktiken des Managers mit Positionen und Rollen mit/gegen den Ball."""
    if 'tactics_man' not in names:
        return []
    t = frames[names['tactics_man']]
    out = []
    for m in re.finditer(rb'\x22\x44\x00\x1b\x00\x00\x00([\x00\x02])(.)\x00\x00\x00', t, re.S):
        ln = m.group(2)[0]
        name = t[m.end():m.end() + ln].decode('utf-8', 'replace').strip()
        p = t.find(b'\x44\x00\x02', m.end() + ln, m.end() + ln + 200)
        # Kopf zwischen Name und erstem Slot: ~16 Byte Einstellungen (noch nicht dekodiert),
        # dann "ff len u32 Stilname Code4", z. B. "Gegenpressing" + "EGEG", "Vertikales Tiki-Taka" + "TREV"
        style_name = style_code = None
        if p != -1:
            sm = re.search(rb'\xff([\x02-\x40])\x00\x00\x00', t[m.end() + ln:p])
            if sm:
                s0 = m.end() + ln + sm.end()
                sl = sm.group(1)[0]
                if s0 + sl + 4 == p:
                    style_name = t[s0:s0 + sl].decode('utf-8', 'replace')
                    style_code = t[s0 + sl:p].decode('latin-1')
        ents = []
        while p != -1 and len(ents) < 22:
            e = _tactic_entry(t, p)
            if not e:
                break
            ents.append(e)
            p = t.find(b'\x44\x00\x02', e['end'], e['end'] + 16)
        if len(ents) != 22 or not all(e['pos'] for e in ents):
            continue
        slots, unknown = [], 0
        dbg = os.environ.get('FMS_ROLES')
        if dbg:
            kind = 'aktiv' if m.group(1) == b'\x02' else 'eigene'
            print(f'\nTaktik "{name}" ({kind})')
        for i in range(0, 22, 2):
            a, b = ents[i], ents[i + 1]
            k_ip = ('ip', a['grp'][0] if a['grp'] else -1, a['subs'])
            k_oop = ('oop', b['grp'][0] if b['grp'] else -1, b['subs'])
            ip, oop = ROLE_FP.get(k_ip), ROLE_FP.get(k_oop)
            unknown += (ip is None) + (oop is None)
            if dbg:
                side = {0x20: ' rechts', 0x10: ' links'}.get(a['side'], '')
                for kk, r, ph in ((k_ip, ip, 'mit Ball'), (k_oop, oop, 'gegen Ball')):
                    print(f'  {a["pos"] + side:12} {ph:11} {r[2] if r else "UNBEKANNT":34} {kk!r}')
            d_ip, d_oop = ROLE_DEFAULT.get(a['pos'], ('cm', 'cm'))
            x, y = POS_XY[a['pos']]
            dx = SIDE_DX.get(a['pos'], 0)
            x += dx if a['side'] == 0x20 else -dx if a['side'] == 0x10 else 0
            slots.append([a['pos'], x, y, ip[0] if ip else d_ip, oop[0] if oop else d_oop,
                          ip[1] if ip else '?', oop[1] if oop else '?', b['pos']])
        out.append(dict(name=name, active=m.group(1) == b'\x02', slots=slots, unknown=unknown,
                        style_name=style_name, style_code=style_code))
    return out


# ---------------------------------------------------------------- Bewertungen (CA/PA bleiben intern)
# (Schwelle, Nominativ, "zu ..."-Form)
LEVELS = [(185, 'Weltklassespieler', 'zu einem Weltklassespieler'),
          (170, 'Spieler der internationalen Spitzenklasse', 'zu einem Spieler der internationalen Spitzenklasse'),
          (155, 'Stammspieler einer europäischen Top-Liga', 'zu einem Stammspieler einer europäischen Top-Liga'),
          (140, 'solider Spieler einer Top-Liga', 'zu einem soliden Spieler einer Top-Liga'),
          (125, 'guter Erstliga-Spieler', 'zu einem guten Erstliga-Spieler'),
          (112, 'guter Zweitliga-Spieler', 'zu einem guten Zweitliga-Spieler'),
          (100, 'solider Zweitliga- bzw. guter Drittliga-Spieler', 'zu einem soliden Zweitliga- bzw. guten Drittliga-Spieler'),
          (88, 'guter Drittliga-Spieler', 'zu einem guten Drittliga-Spieler'),
          (75, 'solider Drittliga-Spieler', 'zu einem soliden Drittliga-Spieler'),
          (0, 'Spieler für untere Ligen', 'zu einem Spieler für untere Ligen')]


def level(x):
    for t, nom, dat in LEVELS:
        if x >= t:
            return nom, dat
    return LEVELS[-1][1:]


def level_text(x):
    return level(x)[0]


def potential_text(ca, pa, age):
    if pa <= 0:
        pa = ca
    gap = pa - ca
    if age >= 29 or gap < 5:
        return f'Am Leistungsmaximum – {level(ca)[0]}'
    if pa >= 185:
        return 'Möglicher Weltklassespieler'
    if pa < 75:
        return 'Wird voraussichtlich kein Profi-Niveau erreichen'
    lead = 'deutlich weiter ' if gap >= 30 else ''
    return f'Kann sich {lead}{level(pa)[1]} entwickeln'


def est_value(ca, pa, age, years_left, lg_factor):
    base = 2200 * math.exp((ca - 50) / 12.5)
    if age <= 21:
        base *= 1 + max(0, pa - ca) / 60
    elif age >= 30:
        base *= max(0.15, 1 - (age - 29) * 0.15)
    if years_left is not None:
        base *= 0.45 if years_left < 0.6 else 0.75 if years_left < 1.2 else 1.0
    return int(round(base * lg_factor, -3))


# ---------------------------------------------------------------- Hauptprogramm
def main():
    cfg_path = os.path.join(HERE, 'config.json')
    cfg = json.load(open(cfg_path, encoding='utf-8')) if os.path.exists(cfg_path) else {}
    if len(sys.argv) > 1 and sys.argv[1] in ('--list', '-l'):
        print_saves()
        return
    save = find_save(sys.argv[1] if len(sys.argv) > 1 else cfg.get('save'))
    log('Spielstand:', save)
    frames, offs = read_frames(save)
    names = directory(frames, offs)
    db = DB(frames[names['game_db']])
    log('Datenbank', len(db.d) // 1_000_000, 'MB')

    summary = frames[names['save_game_summary']]
    manager, game_date, club_name = '', None, ''
    for m in re.finditer(rb'([\x02-\x40])\x00\x00\x00([^\x00-\x1f]{2,64}?)([\x02-\x40])\x00\x00\x00([^\x00-\x1f]{2,64}?)(.{4})(..)([\xe8-\xef]\x07)', summary, re.S):
        if len(m.group(2)) == m.group(1)[0] and len(m.group(4)) == m.group(3)[0]:
            manager = m.group(2).decode('utf-8', 'replace')
            club_name = m.group(4).decode('utf-8', 'replace')
            dd, yy = struct.unpack('<H', m.group(6))[0] & 0x1ff, struct.unpack('<H', m.group(7))[0]
            game_date = datetime.date(yy, 1, 1) + datetime.timedelta(days=dd - 1)
    game_date = game_date or datetime.date.today()
    log('Manager', manager, 'Datum', game_date)

    tabs = name_tables(db)
    F, L = (tabs + [{}, {}])[:2]
    log('Namen', len(F), len(L))

    blocks = player_blocks(db)
    log('Spielerblöcke', len(blocks))
    # Personenköpfe: Vorname-ID 00 Nachname-ID 00 ff×4 00 len [voller Name] Geburtsdatum
    hstarts, hinfo = [], []
    d = db.d
    for m in re.finditer(rb'\x00\xff\xff\xff\xff\x00', d):
        o = m.start()
        if o < 9 or d[o - 5] != 0:
            continue
        first, last = db.u32(o - 9), db.u32(o - 4)
        if first not in F or last not in L:
            continue
        ln = db.u32(o + 6)
        if ln > 120:
            continue
        dpos = o + 10 + ln
        dob = db.date(dpos)
        if not dob:
            continue
        full = d[o + 10:o + 10 + ln].decode('utf-8', 'replace') if ln else ''
        hstarts.append(o - 9)
        hinfo.append((first, last, dob, dpos, full))
    log('Personen', len(hstarts))
    bset = sorted(blocks)

    club_map = clubs(db)
    log('Vereine', len(club_map))
    lang = find_lang_db(cfg)
    cnames = comp_names(lang)
    log('Wettbewerbsnamen', len(cnames), lang or '(nicht gefunden)')
    comps = competitions(frames, names, cnames)

    bpid = {db.u32(p - 43): p for p in blocks}
    con = contracts(db, bpid, hstarts)
    log('Verträge', len(con))
    players = {}
    for pid, c in con.items():
        p = bpid[pid - 1]
        first, last, dob, dpos, full = hinfo[c['hk']]
        pers = list(db.d[dpos + 22:dpos + 30])
        if not all(1 <= x <= 20 for x in pers):
            pers = None
        attrs = list(db.d[p + 15:p + 69])
        players[pid] = dict(
            id=pid, name=(F.get(first, '') + ' ' + L.get(last, '')).strip() or f'#{pid}',
            dob=dob, club=c['club'], ca=db.u16(p - 24), pa=db.u16(p - 22),
            pos=list(db.d[p:p + 15]), attrs=attrs, pers=pers)
    log('Spieler zugeordnet', len(players))
    if os.environ.get('FMS_DEBUG'):
        for pl in players.values():
            if any(s in pl['name'] for s in os.environ['FMS_DEBUG'].split(',')):
                print('DEBUG', pl['name'], pl['dob'], pl['club'], 'CA', pl['ca'], 'PA', pl['pa'], pl['pos'],
                      [round(x / 5) for x in pl['attrs']])
    rat, weeks = training(frames, names)

    # menschlicher Verein = Verein der meisten Spieler in der Trainingsbewertung
    cc = Counter(players[p]['club'] for p in rat if p in players)
    my_id = cc.most_common(1)[0][0] if cc else None
    if my_id is None or club_map.get(my_id, {}).get('short') != club_name:
        # Vereinsname aus der Spielstand-Übersicht; bei Namensgleichheit den Verein mit den meisten Spielern nehmen
        npl = Counter(pl['club'] for pl in players.values())
        cands = [cid for cid, c in club_map.items() if club_name in (c['short'], c['name'])]
        if cands:
            my_id = max(cands, key=lambda c: npl.get(c, 0))
    my = club_map.get(my_id, {'name': '?', 'short': '?'})
    log('Eigener Verein', my.get('name'), my_id)

    # Stärken: Vereine (Top-16 CA) und Ligen
    by_club = defaultdict(list)
    for pl in players.values():
        by_club[pl['club']].append(pl['ca'])
    club_str = {c: sum(sorted(v, reverse=True)[:16]) / min(16, len(v)) for c, v in by_club.items() if len(v) >= 11}
    league_of = {}
    league_list = {}
    for cid, c in comps.items():
        if CUP_WORDS.search(c['long']):
            continue
        teams = [t for t in c['teams'] if t in club_str]
        if len(teams) < 6:
            continue
        s = sum(club_str[t] for t in teams) / len(teams)
        league_list[cid] = dict(name=c['name'], long=c['long'], strength=s, teams=teams)
        for t in teams:
            if t not in league_of or len(league_list[league_of[t]]['teams']) > len(teams):
                league_of[t] = cid
    my_league = league_list.get(league_of.get(my_id), {})
    my_str = club_str.get(my_id, 90)
    lg_str = my_league.get('strength', my_str)
    log('Liga', my_league.get('name'), 'Stärke', round(lg_str, 1))

    fin = club_finances(db, my) if 'end' in my else {}
    ccfg = cfg.get('clubs', {})
    club_cfg = ccfg.get(my.get('short'), ccfg.get(my.get('name'), {}))
    log('Finanzen', fin)

    def age_of(dob):
        return game_date.year - dob.year - ((game_date.month, game_date.day) < (dob.month, dob.day))

    def years_left(pid):
        c = con.get(pid)
        if not c or not c['end']:
            return None
        return (datetime.date.fromisoformat(c['end']) - game_date).days / 365.25

    def willingness(pl):
        """0-100: wie wahrscheinlich ein Wechsel zu uns ist (Schätzung, nutzt versteckte Werte nur intern)."""
        if pl['club'] == my_id:
            return None
        free = pl['club'] == 0
        own = club_str.get(pl['club'], 50 if free else my_str + 5)   # unbekannter Verein: neutral
        diff = own - my_str                       # >0: sein Verein ist stärker
        score = 75 - diff * 1.6
        lvl_gap = pl['ca'] - my_str                # Spieler deutlich besser als unser Niveau
        if lvl_gap > 10:
            score -= (lvl_gap - 10) * 1.2
        p = pl['pers'] or [10] * 8
        ambition, loyalty = p[1], p[3]
        if diff > 0:
            score -= (ambition - 10) * 1.5
        score -= (loyalty - 10) * 1.0
        yl = years_left(pl['id'])
        if yl is not None:
            score += 12 if yl < 0.6 else 5 if yl < 1.2 else -4 if yl > 3 else 0
        if free:                                     # vereinslos
            score += 10
        age = age_of(pl['dob'])
        if age >= 31:
            score += 6
        return max(2, min(97, round(score)))

    def out_player(pl, mine):
        age = age_of(pl['dob'])
        c = con.get(pl['id'], {})
        club = club_map.get(pl['club'], {})
        lid = league_of.get(pl['club'])
        lgf = 0.6 + (league_list[lid]['strength'] / max(lg_str, 1)) * 0.4 if lid else 0.8
        yl = years_left(pl['id'])
        a = pl['attrs']
        attrs = {k: max(1, min(20, int(a[i] / 5 + 0.5))) for i, k in enumerate(ATTR_KEYS) if k not in HIDDEN}
        r = dict(id=pl['id'], n=pl['name'], age=age, pos=pl['pos'], a=attrs,
                 club=club.get('short') or club.get('name') or '', lg=(league_list[lid]['name'] if lid else ''),
                 wage=c.get('wage_week'), end=c.get('end'),
                 pot=potential_text(pl['ca'], pl['pa'], age), lvl=level_text(pl['ca']),
                 val=est_value(pl['ca'], pl['pa'], age, yl, lgf))
        if mine:
            r['tr'] = rat.get(pl['id'])
        else:
            r['will'] = willingness(pl)
            r['q'] = round(pl['ca'] - my_str)      # nur relative Einordnung, keine CA
        return r

    squad = [out_player(pl, True) for pl in players.values() if pl['club'] == my_id]
    # Pool: Spieler, die für das eigene Niveau realistisch interessant sind
    lo, hi = my_str - 15, my_str + 35
    cand = [pl for pl in players.values() if pl['club'] != my_id and 16 <= age_of(pl['dob']) <= 35
            and (lo <= pl['ca'] <= hi or (age_of(pl['dob']) <= 21 and pl['pa'] >= my_str + 10 and pl['ca'] >= lo - 25))]
    for pl in cand:
        pl['_w'] = willingness(pl)
    # realistische Kandidaten zuerst: Wechselbereitschaft × Qualität
    cand.sort(key=lambda pl: -(pl['_w'] * (pl['ca'] - lo + 10)))
    pool = [out_player(pl, False) for pl in cand[:cfg.get('pool_size', 6000)]]
    for p in pool:
        q = p.pop('q')
        p['rel'] = 'deutlich stärker' if q > 25 else 'stärker' if q > 10 else 'ähnlich' if q > -5 else 'schwächer'
    log('Kader', len(squad), 'Pool', len(pool))

    # Taktik: Positionen + Rollen aus dem Spielstand, Anweisungen/Feedback aus config.json
    tactic = dict(club_cfg.get('tactic', {}))
    saved = read_tactics(frames, names)
    if saved:
        st = next((x for x in saved if x['active']), saved[0])
        tactic.update(name=st['name'], slots=st['slots'], source='Spielstand', unknown_roles=st['unknown'],
                      saved=list(dict.fromkeys(x['name'] for x in saved)))
        if st['style_name']:
            tactic['style_name'] = st['style_name']
            if st['style_code'] in STYLE_CODES:
                tactic['style'] = STYLE_CODES[st['style_code']]
        log('Taktik aus Spielstand:', st['name'], '| Stil:', st['style_name'], st['style_code'],
            '| unbekannte Rollen:', st['unknown'])
    elif tactic.get('slots'):
        tactic['source'] = 'config.json'
        log('Keine eigene Taktik im Spielstand – nutze config.json')

    data = dict(
        meta=dict(manager=manager, date=game_date.isoformat(), club=my.get('name'), club_short=my.get('short'),
                  league=my_league.get('name', ''), league_long=my_league.get('long', ''),
                  finances=fin, save=os.path.basename(save), created=datetime.datetime.now().isoformat(timespec='minutes'),
                  rivals=[club_map.get(t, {}).get('short', '') for t in my_league.get('teams', []) if t != my_id]),
        coach=club_cfg.get('coach', {}), tactic=tactic,
        squad=squad, pool=pool, training=dict(weeks=weeks),
    )
    tpl = open(os.path.join(HERE, 'app.html'), encoding='utf-8-sig').read()
    out = os.path.join(HERE, 'FM-Scout.html')
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    open(out, 'w', encoding='utf-8').write(tpl.replace('/*__DATA__*/null', js))
    log('Fertig:', out)


if __name__ == '__main__':
    main()



