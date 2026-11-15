@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Please install Python first.
  pause
  exit /b 1
)
if not exist venv\Scripts\activate.bat python -m venv venv
call venv\Scripts\activate.bat
echo.
echo === Installing packages, please wait ===
pip install -r requirements.txt
echo.
echo === Creating database tables ===
alembic upgrade head
echo.
echo === Starting backend. Open http://127.0.0.1:8000/docs in your browser ===
echo === Keep this window open. Press Ctrl+C to stop. ===
uvicorn app.main:app --reload
pause
