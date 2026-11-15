import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js fehlt')
def test_taktik_js():
    r = subprocess.run(['node', '--test', 'tests/js/'], cwd=ROOT,
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stdout + r.stderr
