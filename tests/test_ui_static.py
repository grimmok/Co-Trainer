"""Statische Prüfungen an cotrainer/ui/index.html (ohne Browser)."""
import re
from pathlib import Path

HTML = (Path(__file__).resolve().parent.parent / 'cotrainer' / 'ui' / 'index.html').read_text(encoding='utf-8')


def test_style_and_instruction_groups_exist_in_pg():
    # Osijek (Flügelspiel) brach ab: STYLES nutzte die Gruppe 'ST', PG kannte sie nicht (15.11.)
    pg = re.search(r'const PG=\{(.*?)\};', HTML).group(1)
    groups = set(re.findall(r'(\w+):\[', pg))
    used = set(re.findall(r"\['([A-Z]+)','[A-Za-z ]+',[.0-9]+\]", HTML))
    assert used, 'keine Stil-Modifikatoren gefunden'
    assert used <= groups, f'fehlende Positionsgruppen in PG: {sorted(used - groups)}'


def test_about_modal_has_no_external_links():
    # ein Link würde das Programmfenster wegnavigieren (keine Online-Funktionen)
    body = HTML[HTML.index('function openAbout'):]
    body = body[:body.index('\nfunction ')]
    assert 'href="http' not in body and "href='http" not in body and 'fmsave' in body


def test_dev_api_has_about():
    dev = HTML[HTML.index('async function devApi'):HTML.index('async function boot')]
    assert 'about:' in dev
