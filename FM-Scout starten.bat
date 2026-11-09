@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -c "import zstandard" 2>nul || python -m pip install --user zstandard
rem Ohne Angabe wird der zuletzt gespeicherte Spielstand genommen.
rem Bestimmten Spielstand verwenden: Pfad in config.json bei "save" eintragen.
python extract.py %*
if errorlevel 1 pause & exit /b 1
start "" "%~dp0FM-Scout.html"
