"""Lizenzliste der mitgelieferten Software (tools/third_party.py, THIRD_PARTY_LICENSES.txt)."""
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location('third_party', ROOT / 'tools' / 'third_party.py')
tp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tp)


def norm(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def test_runtime_dists_closure():
    names = {norm(d.metadata['Name']) for d in tp.runtime_dists()}
    assert {'fmsave', 'pywebview', 'zstandard', 'backports-zstd', 'pythonnet', 'bottle', 'proxy-tools'} <= names
    assert not names & {'cotrainer', 'pytest', 'pyinstaller', 'packaging'}


def test_license_text_falls_back_to_metadata():
    # proxy_tools 0.1.0 liefert keinen Lizenztext mit
    d = next(d for d in tp.runtime_dists() if norm(d.metadata['Name']) == 'proxy-tools')
    t = tp.license_text(d)
    assert t.startswith('Kein Lizenztext im Paket enthalten.') and 'MIT' in t and 'github.com/jtushman/proxy_tools' in t


def test_license_name_from_text_when_metadata_is_silent():
    # clr_loader nennt keine Lizenz in den Paketangaben, liefert aber den MIT-Text mit
    d = next(d for d in tp.runtime_dists() if norm(d.metadata['Name']) == 'clr-loader')
    assert tp.license_name(d) == 'MIT'


def test_render_order_and_blocks():
    t = tp.render(tp.runtime_dists(), '3.12.x', 'PSF LICENSE TEXT')
    ls = t.splitlines()
    rule = '=' * 70          # genaue Trennlinie; Lizenztexte (PSF) haben eigene ===-Unterstreichungen
    heads = [ls[i + 1] for i in range(len(ls) - 2) if ls[i] == rule and ls[i + 2] == rule]
    assert heads[0].startswith('fmsave 0.11.0 – MIT') and heads[-1].startswith('Python 3.12.x')
    assert heads[1:-1] == sorted(heads[1:-1], key=str.lower)
    assert 'Permission is hereby granted' in t and 'PSF LICENSE TEXT' in t
    assert not any(h.endswith('– unbekannt') for h in heads)


def test_checked_in_notices_match_installed_versions():
    t = (ROOT / 'THIRD_PARTY_LICENSES.txt').read_text(encoding='utf-8')
    for d in tp.runtime_dists():
        assert f"{d.metadata['Name']} {d.version} – " in t, d.metadata['Name']
    assert not re.search(r'Users\\[A-Za-z]', t)          # keine Pfade aus dem eigenen Rechner
