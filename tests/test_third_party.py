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


NATIVE_HEADS = ('OpenSSL 3', 'libffi', 'Expat', 'libmpdec', 'Microsoft WebView2 SDK 1.0.3856.49', 'PyInstaller')


def test_render_includes_native_libraries_and_pyinstaller():
    # Review: DLLs in der .exe (OpenSSL, libffi, WebView2 SDK, in Python eingebaut expat/libmpdec) und die
    # Laufzeit-Hooks von PyInstaller (Apache-2.0) brauchen ihren Lizenztext
    t = tp.render(tp.runtime_dists(), '3.12.x', 'PSF', tp.native_blocks())
    ls = t.splitlines()
    rule = '=' * 70
    heads = [ls[i + 1] for i in range(len(ls) - 2) if ls[i] == rule and ls[i + 2] == rule]
    i_py = next(i for i, h in enumerate(heads) if h.startswith('Python 3.12.x'))
    for name in NATIVE_HEADS:
        assert any(h.startswith(name) for h in heads[i_py + 1:]), name
    for title, text in tp.native_blocks():
        assert len(text) > 500 and ('Permission' in text or 'Redistribution' in text or 'Apache License' in text), title


def test_checked_in_notices_cover_native_libraries():
    t = (ROOT / 'THIRD_PARTY_LICENSES.txt').read_text(encoding='utf-8')
    for name in NATIVE_HEADS:
        assert '\n' + name in t, name


def test_build_excludes_build_time_modules():
    # cffi zieht über setuptools_ext setuptools und packaging in die .exe; zur Laufzeit braucht sie niemand
    ps = (ROOT / 'build.ps1').read_text(encoding='utf-8')
    for mod in ('setuptools', 'packaging', '_distutils_hack'):
        assert f'--exclude-module {mod}' in ps, mod
