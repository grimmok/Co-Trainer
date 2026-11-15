# Baut dist\Co-Trainer.exe (eine Datei, ohne Konsolenfenster).
# Voraussetzung: .venv mit den Entwickler-Abhängigkeiten, siehe CLAUDE.md.
# Aufruf: .\build.ps1          (mit -MitSpielstand laufen auch die langsamen Tests mit echtem Spielstand)
param([switch]$MitSpielstand)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Die Umgebung .venv fehlt: python -m uv venv --python 3.12 .venv; python -m uv pip install --python .venv -e ".[dev]"' }

if ($MitSpielstand) { & $python -m pytest tests -q } else { & $python -m pytest tests -q -m 'not save' }
if ($LASTEXITCODE -ne 0) { throw 'Tests fehlgeschlagen - es wird nichts gebaut.' }

# Lizenzen der mitgelieferten Pakete neu sammeln (THIRD_PARTY_LICENSES.txt, wird mit eingepackt)
& $python tools\third_party.py
if ($LASTEXITCODE -ne 0) { throw 'Lizenzliste konnte nicht erzeugt werden - es wird nichts gebaut.' }

# Eingepackt werden index.html, taktik.js und THIRD_PARTY_LICENSES.txt; dev-data.json und config.json bleiben draußen.
& $python -m PyInstaller --noconfirm --clean --onefile --windowed --name Co-Trainer `
    --collect-submodules fmsave --copy-metadata fmsave --collect-all backports.zstd `
    --exclude-module setuptools --exclude-module packaging --exclude-module _distutils_hack `
    --add-data 'cotrainer/ui/index.html;cotrainer/ui' --add-data 'cotrainer/ui/taktik.js;cotrainer/ui' --add-data 'THIRD_PARTY_LICENSES.txt;.' cotrainer/__main__.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller ist fehlgeschlagen.' }

$exe = Get-Item (Join-Path $PSScriptRoot 'dist\Co-Trainer.exe')
Write-Host ('Fertig: {0} ({1:N1} MB)' -f $exe.FullName, ($exe.Length / 1MB))
