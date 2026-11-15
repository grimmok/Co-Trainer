# tests/test_nations.py
import pytest
from cotrainer import nations as N

def test_label_fallback():
    assert N.nation_label({776: ('Italien', 'ITA')}, 776) == ('ITA', 'Italien')
    assert N.nation_label({}, 999) == ('–', '')
    assert N.nation_label({}, None) == ('–', '')

def test_geo_without_table():
    assert N.nation_geo(b'\x00' * 1000) == {}

@pytest.mark.save
def test_geo_ravenna(ravenna_game_db):
    g = N.nation_geo(ravenna_game_db)
    assert g[776] == (2, 11)          # Italien: Europa, Südeuropa (vom Nutzer bestätigt)
    assert g[769] == (2, 25)          # Frankreich
    assert g[771] == (2, 4)           # Deutschland
    assert g[1657] == (5, 21)         # Uruguay
    assert len(g) == 251

@pytest.mark.save
def test_names_lang_db(lang_db_path):
    n = N.nation_names(lang_db_path)
    assert n[776] == ('Italien', 'ITA') and n[769] == ('Frankreich', 'FRA')
    assert n[771] == ('Deutschland', 'GER') and n[1657] == ('Uruguay', 'URU')
    assert len(n) >= 230
