@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (start "" "http://127.0.0.1:8765" & py -3 app.py & goto :end)
where python >nul 2>&1
if %errorlevel%==0 (start "" "http://127.0.0.1:8765" & python app.py & goto :end)
echo Python 3 is needed. Install from https://www.python.org/downloads/windows/
pause
:end
