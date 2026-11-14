"""Spielstand mit der Bibliothek fmsave lesen und ins interne Format des Co-Trainers umwandeln."""
import warnings
from dataclasses import dataclass, field

import fmsave

from .extract import ATTR_KEYS, POS_KEYS, CUP_WORDS, GBP_TO_EUR, log

# fmsave-Feldnamen in der Reihenfolge von ATTR_KEYS (ohne Füße, die kommen hinter 'technique')
_ATTR_FIELDS = [
    'crossing', 'dribbling', 'finishing', 'heading', 'long_shots', 'marking', 'off_the_ball', 'passing',
    'penalty_taking', 'tackling', 'vision', 'handling', 'aerial_reach', 'command_of_area', 'communication',
    'kicking', 'throwing', 'anticipation', 'decisions', 'one_on_ones', 'positioning', 'reflexes', 'first_touch',
    'technique', 'flair', 'corners', 'teamwork', 'work_rate', 'long_throws', 'eccentricity', 'rushing_out',
    'punching', 'acceleration', 'free_kick_taking', 'strength', 'stamina', 'pace', 'jumping_reach', 'leadership',
    'dirtiness', 'balance', 'bravery', 'consistency', 'aggression', 'agility', 'important_matches',
    'injury_proneness', 'versatility', 'natural_fitness', 'determination', 'composure', 'concentration']
_POS_FIELDS = [k.lower() if k != 'ST' else 'stc' for k in POS_KEYS]
_PERS_FIELDS = ['adaptability', 'ambition', 'loyalty', 'pressure', 'professionalism', 'sportsmanship',
                'temperament', 'controversy']


# strict=True würde NK Osijek ablehnen (GateCheckError „clubs: status_confirmation=0.86, erwartet 0.95“); der eigene Leser
# findet dort keinen Kader. Deshalb läuft fmsave nicht strikt, und jede Warnung außer UnknownBuildWarning wird geloggt.
STRICT = False


@dataclass
class FmsData:
    players: dict = field(default_factory=dict)
    contracts: dict = field(default_factory=dict)
    clubs: dict = field(default_factory=dict)
    comps: dict = field(default_factory=dict)
    own_club: int = 0


def _val(obj, name, default):
    v = getattr(obj, name, None) if obj is not None else None
    return default if v is None else v


def player_record(p):
    """fmsave-Spieler -> Spielerdatensatz wie in extract._analyse; None ohne Geburtsdatum."""
    if p.birth_date is None:
        return None
    attrs = []
    for f in _ATTR_FIELDS:
        attrs.append(_val(p.attributes, f, 1) * 5)
        if f == 'technique':
            attrs += [_val(p, 'left_foot', 1) * 5, _val(p, 'right_foot', 1) * 5]
    ca = _val(p.ability, 'current', 0)
    pa = _val(p.ability, 'potential', 0)
    if pa <= 0:
        pa = ca
    pers = None
    if p.personality is not None:
        pers = [getattr(p.personality, f, None) for f in _PERS_FIELDS]
        if not all(isinstance(x, int) and 1 <= x <= 20 for x in pers):
            pers = None
    return dict(id=p.uid, name=(p.name or '').strip() or f'#{p.uid}', dob=p.birth_date, club=p.club_uid or 0,
                first=(getattr(p, 'first_name', None) or '').strip(), last=(getattr(p, 'last_name', None) or '').strip(),
                loan_parent=getattr(p, 'loan_parent_club_uid', None),
                ca=ca, pa=pa, pos=[_val(p.positions, f, 1) for f in _POS_FIELDS], attrs=attrs, pers=pers,
                team_slot=p.team_slot)


assert len(ATTR_KEYS) == len(_ATTR_FIELDS) + 2


def comps_from_fixtures(fixtures, comp_db, cnames):
    """Ligen aus den Spielen mit mindestens einer ersten Mannschaft: je Wettbewerb die beteiligten Vereine."""
    teams = {}
    for f in fixtures:
        # mindestens eine erste Mannschaft: so fallen reine Nachwuchsligen weg, B-Mannschaften in Seniorenligen bleiben
        if 0 in (f.home_team_slot, f.away_team_slot) and f.home_club_uid is not None \
                and f.away_club_uid is not None:
            teams.setdefault(f.competition_id, set()).update((f.home_club_uid, f.away_club_uid))
    comps = {}
    for cid, ts in teams.items():
        long_, short = cnames.get(comp_db.get(cid), (f'Wettbewerb {cid}',) * 2)
        if len(ts) < 6 or CUP_WORDS.search(long_):
            continue
        comps[cid] = dict(name=short, long=long_, teams=sorted(ts))
    return comps


def contract_record(c):
    """Vertrag: Wochengehalt von GBP nach EUR, Ende als ISO-Text."""
    return dict(wage_week=None if c.wage is None else round(c.wage * GBP_TO_EUR),
                end=c.end.isoformat() if c.end else None)


def pick_own_club(managed, club_name):
    """Eigener Verein nach dem Namen aus der Spielstand-Übersicht; ohne Treffer None (Rückfall auf den eigenen Leser)."""
    for m in managed:
        if club_name in (m.club_name, m.club_short_name):
            return m.club_uid
    return None


def read(path, cnames, club_name):
    """Spielstand mit fmsave lesen; bei jedem Fehler None (der Aufrufer nimmt dann den eigenen Leser)."""
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            with fmsave.open(path, strict=STRICT) as s:
                own = pick_own_club(s.managed_clubs(), club_name)
                if own is None:
                    log('fmsave: kein eigener Verein')
                    return None
                players, contracts = {}, {}
                for p in s.players():
                    r = player_record(p)
                    if r is None:
                        continue
                    players[p.uid] = r
                    if p.contract is not None:
                        contracts[p.uid] = contract_record(p.contract)
                clubs = {c.uid: dict(name=c.name, short=c.short_name or c.name) for c in s.clubs()}
                comp_db = {c.id: c.database_id for c in s.competitions()}
                comps = comps_from_fixtures(s.fixtures(), comp_db, cnames)
        for w in caught:                       # der unbekannte Build gehört bei FM27 dazu; alles andere melden
            if not issubclass(w.category, fmsave.UnknownBuildWarning):
                log('fmsave Warnung:', w.category.__name__, str(w.message)[:200])
        log('fmsave:', len(players), len(clubs), len(comps), 'eigener Verein', own)
        return FmsData(players, contracts, clubs, comps, own)
    except Exception as e:
        log('fmsave nicht nutzbar:', type(e).__name__, str(e)[:200])
        return None
