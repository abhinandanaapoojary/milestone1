@echo off
cd /d "%~dp0frontend"
where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found. Please install Node.js LTS from nodejs.org first.
  pause
  exit /b 1
)
if not exist node_modules call npm install
echo.
echo === Starting frontend. Open http://localhost:5173 in your browser ===
echo === Keep this window open. Press Ctrl+C to stop. ===
call npm run dev
pause
