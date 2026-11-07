@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -m venv .venv
  if errorlevel 1 goto error
)
if not exist ".env" copy ".env.example" ".env" >nul
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
".venv\Scripts\python.exe" scripts\check_environment.py
if errorlevel 1 goto error
echo Starting TRAVESÍA. Keep this window open while the app is running.
".venv\Scripts\python.exe" app.py
goto end
:error
echo.
echo Setup did not complete. Check the Python installation and internet connection, then read START_HERE.txt. The first run must download Flask/Werkzeug from PyPI.
:end
pause
endlocal
