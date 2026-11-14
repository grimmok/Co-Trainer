from types import SimpleNamespace as NS
import datetime, pytest
from cotrainer import fms, extract

ATTR_NAMES = [  # fmsave-Reihenfolge (52 Felder)
    'crossing','dribbling','finishing','heading','long_shots','marking','off_the_ball','passing','penalty_taking',
    'tackling','vision','handling','aerial_reach','command_of_area','communication','kicking','throwing','anticipation',
    'decisions','one_on_ones','positioning','reflexes','first_touch','technique','flair','corners','teamwork',
    'work_rate','long_throws','eccentricity','rushing_out','punching','acceleration','free_kick_taking','strength',
    'stamina','pace','jumping_reach','leadership','dirtiness','balance','bravery','consistency','aggression','agility',
    'important_matches','injury_proneness','versatility','natural_fitness','determination','composure','concentration']
POS_NAMES = ['gk','sw','dl','dc','dr','dm','ml','mc','mr','aml','amc','amr','stc','wbl','wbr']

def player(**kw):
    base = dict(uid=7, name='Max Muster', birth_date=datetime.date(2000, 5, 1), club_uid=11, team_slot=0,
                ability=NS(current=120, potential=140),
                attributes=NS(**{n: (i % 20) + 1 for i, n in enumerate(ATTR_NAMES)}),
                positions=NS(**{n: 20 if n == 'stc' else 1 for n in POS_NAMES}),
                personality=NS(adaptability=1, ambition=2, loyalty=3, pressure=4, professionalism=5,
                               sportsmanship=6, temperament=7, controversy=8),
                left_foot=6, right_foot=20,
                contract=NS(wage=4008, end=datetime.date(2027, 6, 30)))
    base.update(kw); return NS(**base)

def test_player_record_maps_attributes_feet_positions_personality():
    r = fms.player_record(player())
    assert len(r['attrs']) == len(extract.ATTR_KEYS) == 54
    assert r['attrs'][extract.ATTR_KEYS.index('Cro')] == 5          # 1 × 5
    assert r['attrs'][extract.ATTR_KEYS.index('Tec')] == 4 * 5
    assert r['attrs'][extract.ATTR_KEYS.index('LFoot')] == 30 and r['attrs'][extract.ATTR_KEYS.index('RFoot')] == 100
    assert r['attrs'][extract.ATTR_KEYS.index('Fla')] == 5 * 5
    assert r['pos'][extract.POS_KEYS.index('ST')] == 20 and len(r['pos']) == 15
    assert r['pers'] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert (r['id'], r['club'], r['ca'], r['pa'], r['team_slot']) == (7, 11, 120, 140, 0)

def test_player_record_edge_cases():
    assert fms.player_record(player(birth_date=None)) is None
    assert fms.player_record(player(club_uid=None))['club'] == 0
    assert fms.player_record(player(ability=NS(current=90, potential=None)))['pa'] == 90
    assert fms.player_record(player(ability=NS(current=90, potential=-75)))['pa'] == 90
    assert fms.player_record(player(personality=None))['pers'] is None

def test_comps_from_fixtures_uses_first_team_league_matches():
    fx = [NS(competition_id=5, home_club_uid=a, away_club_uid=b, home_team_slot=0, away_team_slot=0)
          for a, b in [(1, 2), (3, 4), (5, 6), (1, 3), (2, 4), (6, 5)]]
    fx += [NS(competition_id=5, home_club_uid=7, away_club_uid=1, home_team_slot=1, away_team_slot=0)]  # B-Team (Stammverein 7) zählt nicht
    fx += [NS(competition_id=9, home_club_uid=1, away_club_uid=2, home_team_slot=1, away_team_slot=1)]  # U-Mannschaft
    c = fms.comps_from_fixtures(fx, {5: 4312, 9: 99}, {4312: ('Italian Serie C/B', 'Serie C/B')})
    assert c == {5: {'name': 'Serie C/B', 'long': 'Italian Serie C/B', 'teams': [1, 2, 3, 4, 5, 6]}}

def test_pick_own_club_prefers_summary_name():
    m = [NS(club_uid=1, club_name='A', club_short_name='A'), NS(club_uid=2, club_name='NK Osijek', club_short_name='Osijek')]
    assert fms.pick_own_club(m, 'Osijek') == 2 and fms.pick_own_club(m, 'X') is None and fms.pick_own_club([], 'X') is None

def test_read_returns_none_when_fmsave_fails(monkeypatch):
    def boom(path, **kw): raise RuntimeError('summary does not fit')
    monkeypatch.setattr(fms.fmsave, 'open', boom)
    assert fms.read('x.fm', {}, 'X') is None

def test_read_returns_none_without_managed_club(monkeypatch):
    class Save:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def managed_clubs(self): return []
    monkeypatch.setattr(fms.fmsave, 'open', lambda path, **kw: Save())
    assert fms.read('x.fm', {}, 'X') is None

def test_contract_record_converts_wage_to_eur():
    assert fms.contract_record(NS(wage=4008, end=datetime.date(2027, 6, 30))) == {'wage_week': 4666, 'end': '2027-06-30'}
    assert fms.contract_record(NS(wage=None, end=None)) == {'wage_week': None, 'end': None}


def test_every_hidden_attribute_lands_at_its_own_index():
    vals = {n: i + 1 for i, n in enumerate(ATTR_NAMES)}          # jedes Feld ein eigener Wert 1..52
    pl = player(attributes=NS(**vals), left_foot=3, right_foot=4)
    r = fms.player_record(pl)
    expect = {'Cons': 'consistency', 'Dirt': 'dirtiness', 'ImpM': 'important_matches',
              'InjPr': 'injury_proneness', 'Vers': 'versatility'}
    assert set(expect) == extract.HIDDEN
    for key, name in expect.items():
        assert r['attrs'][extract.ATTR_KEYS.index(key)] == vals[name] * 5, key
    # jeder Wert genau einmal (kein Feld doppelt oder verschoben), dazu die beiden Füße
    assert sorted(r['attrs']) == sorted([v * 5 for v in vals.values()] + [15, 20])


def test_player_record_carries_names_and_loan_parent():
    r = fms.player_record(player(name='Otávio', first_name=' Otávio ', last_name='Edmilson', loan_parent_club_uid=11))
    assert (r['name'], r['first'], r['last'], r['loan_parent']) == ('Otávio', 'Otávio', 'Edmilson', 11)
    r = fms.player_record(player())
    assert r['first'] == '' and r['loan_parent'] is None


def test_read_passes_strict_setting_and_ignores_only_unknown_build(monkeypatch):
    import warnings
    seen = {}
    class Save:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def managed_clubs(self):
            warnings.warn('build', fms.fmsave.UnknownBuildWarning)
            return []
    def fake_open(path, **kw): seen.update(kw); return Save()
    monkeypatch.setattr(fms.fmsave, 'open', fake_open)
    assert fms.read('x.fm', {}, 'X') is None and seen == {'strict': fms.STRICT}
