@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")
if not exist .venv\Scripts\python.exe (
  echo Creating Python virtual environment...
  %PY% -m venv .venv
  if errorlevel 1 (echo Could not create environment. Install Python 3.10+ and try again.& pause & exit /b 1)
)
echo Installing dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (echo Installation failed.& pause & exit /b 1)
start "" http://127.0.0.1:8000
echo TrialMirror starting at http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
