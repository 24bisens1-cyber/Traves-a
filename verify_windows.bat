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
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto error
".venv\Scripts\python.exe" scripts\check_environment.py --verification
if errorlevel 1 goto error
set CITYPULSEX_REQUIRE_FLASK_TESTS=1
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 goto error
node --test frontend/tests/*.test.cjs
if errorlevel 1 goto error
".venv\Scripts\python.exe" scripts/verify_glb_animation_browser.py
if errorlevel 1 goto error
".venv\Scripts\python.exe" scripts/verify_cinematic_refresh_browser.py
if errorlevel 1 goto error
".venv\Scripts\python.exe" scripts/verify_v7_character_postcards.py
if errorlevel 1 goto error
".venv\Scripts\python.exe" scripts/verify_booking_handoffs_browser.py
if errorlevel 1 goto error
".venv\Scripts\python.exe" scripts/verify_portal_run_browser.py
if errorlevel 1 goto error
".venv\Scripts\python.exe" scripts/verify_trip_pulseboard_browser.py
if errorlevel 1 goto error
echo.
echo TRAVESÍA verification completed successfully.
goto end
:error
echo.
echo Verification stopped. Check the error above. First setup requires internet access for PyPI and Playwright Chromium; full verification also needs Node.js 20 LTS or newer.
:end
pause
endlocal
