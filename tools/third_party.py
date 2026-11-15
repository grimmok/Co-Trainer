"""Sammelt die Lizenztexte aller Pakete, die in Co-Trainer.exe gebündelt werden, plus Python.

Aufruf (aus dem Projektordner, mit der Entwicklungsumgebung): .venv\\Scripts\\python tools\\third_party.py
Schreibt THIRD_PARTY_LICENSES.txt; build.ps1 ruft das vor dem Bauen auf und packt die Datei mit ein.
"""
import importlib.metadata as md
import os
import platform
import re
import sys

from packaging.markers import Marker

RULE = '=' * 70
HEAD = ('Co-Trainer – Lizenzen der mitgelieferten Software\n\n'
        'Co-Trainer selbst steht unter der MIT-Lizenz (siehe LICENSE).\n'
        'Die Datei Co-Trainer.exe enthält außerdem die folgende Software.\n')
LICENSE_FILE = re.compile(r'(^|/)(LICEN[CS]E|COPYING|NOTICE)[^/]*$', re.I)


def _norm(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def runtime_dists(root='cotrainer'):
    """Transitive Laufzeitabhängigkeiten von root (ohne root selbst), ohne Extras, jede einmal."""
    seen, out, todo = set(), [], [root]
    while todo:
        name = todo.pop(0)
        key = _norm(name)
        if key in seen:
            continue
        seen.add(key)
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            continue
        if key != _norm(root):
            out.append(dist)
        for req in dist.requires or []:
            spec, _, marker = req.partition(';')
            if marker.strip() and not Marker(marker).evaluate({'extra': ''}):
                continue
            todo.append(re.split(r'[\s<>=!~\[(]', spec.strip(), maxsplit=1)[0])
    return out


def _license_files(dist):
    files = [f for f in dist.files or [] if '.dist-info/' in str(f).replace('\\', '/')]
    lic = [f for f in files if '/licenses/' in str(f).replace('\\', '/')]
    return lic or [f for f in files if LICENSE_FILE.search(str(f).replace('\\', '/'))]


def _project_url(dist):
    m = dist.metadata
    if m.get('Home-page'):
        return m['Home-page']
    urls = m.get_all('Project-URL') or []
    return urls[0].split(',', 1)[-1].strip() if urls else 'unbekannt'


def _metadata_license(dist):
    m = dist.metadata
    if m.get('License-Expression'):
        return m['License-Expression'].strip()
    if (m.get('License') or '').strip():
        return m['License'].strip().splitlines()[0][:60]
    cls = [c.split('::')[-1].strip() for c in m.get_all('Classifier') or [] if c.startswith('License ::')]
    return cls[0] if cls else None


def license_text(dist):
    """Lizenztext aus den Dateien des Pakets; ohne Datei ein Hinweis mit Lizenz laut Paketangaben und Projekt."""
    texts = [dist.locate_file(f).read_text(encoding='utf-8', errors='replace').strip() for f in _license_files(dist)]
    if texts:
        return '\n\n'.join(texts)
    return (f'Kein Lizenztext im Paket enthalten. Lizenz laut Paketangaben: {_metadata_license(dist) or "unbekannt"}. '
            f'Projekt: {_project_url(dist)}')


def license_name(dist):
    """Kurzname für den Blockkopf; schweigen die Paketangaben, wird der MIT-Wortlaut erkannt."""
    name = _metadata_license(dist)
    if name:
        return name
    return 'MIT' if 'Permission is hereby granted, free of charge' in license_text(dist) else 'unbekannt'


LICENSES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'licenses')
# Bibliotheken ohne eigenes Python-Paket, die trotzdem in der .exe stecken (Analysis-00.toc von PyInstaller):
# OpenSSL-DLLs und libffi-8.dll kommen mit Python, expat und libmpdec sind in pyexpat.pyd/_decimal.pyd eingebaut,
# das WebView2 SDK liegt in pywebview (webview/lib). Texte aus den Originalquellen, siehe tools/licenses.
NATIVE = [
    ('OpenSSL 3 (libcrypto-3-x64.dll, libssl-3-x64.dll) – Apache-2.0', 'apache-2.0.txt'),
    ('libffi (libffi-8.dll) – MIT', 'libffi.txt'),
    ('Expat (in pyexpat.pyd) – MIT', 'expat.txt'),
    ('libmpdec (in _decimal.pyd) – BSD-2-Clause', 'mpdecimal.txt'),
    ('Microsoft WebView2 SDK 1.0.3856.49 (in pywebview) – BSD-3-Clause', 'webview2-sdk.txt'),
]


def native_blocks():
    """(Titel, Text) für mitgelieferte Bibliotheken ohne Python-Paket, dazu PyInstaller (Laufzeit-Hooks, Apache-2.0)."""
    out = []
    for title, name in NATIVE:
        with open(os.path.join(LICENSES_DIR, name), encoding='utf-8') as fh:
            out.append((title, fh.read()))
    pyi = md.distribution('pyinstaller')
    out.append((f'PyInstaller {pyi.version} (Startprogramm und Laufzeit-Hooks) – GPL-2.0 mit Ausnahme / Apache-2.0',
                license_text(pyi)))
    return out


def _block(title, text):
    return f'{RULE}\n{title}\n{RULE}\n{text.strip()}\n'


def render(dists, python_version, python_license, extras=()):
    """Kopf, Python-Pakete (fmsave zuerst, Rest alphabetisch), Python, dann extras als (Titel, Text)."""
    first = [d for d in dists if _norm(d.metadata['Name']) == 'fmsave']
    rest = sorted((d for d in dists if d not in first), key=lambda d: d.metadata['Name'].lower())
    parts = [HEAD]
    for d in first + rest:
        parts.append(_block(f"{d.metadata['Name']} {d.version} – {license_name(d)}", license_text(d)))
    parts.append(_block(f'Python {python_version} – PSF-2.0', python_license))
    parts.extend(_block(title, text) for title, text in extras)
    return '\n'.join(parts)


def main(out='THIRD_PARTY_LICENSES.txt'):
    with open(os.path.join(sys.base_prefix, 'LICENSE.txt'), encoding='utf-8') as fh:
        py_license = fh.read()
    text = render(runtime_dists(), platform.python_version(), py_license, native_blocks())
    with open(out, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    print('Geschrieben:', out)


if __name__ == '__main__':
    main()
