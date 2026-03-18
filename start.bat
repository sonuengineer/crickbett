@echo off
title CricketArb - Running
color 0A
echo.
echo  Starting CricketArb...
echo.

:: Start Docker if not running
cd /d g:\sonu\CricketArb
docker-compose up -d 2>nul

:: Start Backend
echo  Starting Backend Server...
start "CricketArb Backend" cmd /k "cd /d g:\sonu\CricketArb\backend && call venv\Scripts\activate.bat && python main.py"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start Celery Worker (separate from beat on Windows)
echo  Starting Celery Worker...
start "CricketArb Worker" cmd /k "cd /d g:\sonu\CricketArb\backend && call venv\Scripts\activate.bat && celery -A app.tasks.celery_app worker --loglevel=info --pool=solo"

:: Start Celery Beat (scheduler - must be separate on Windows)
echo  Starting Celery Beat Scheduler...
start "CricketArb Beat" cmd /k "cd /d g:\sonu\CricketArb\backend && call venv\Scripts\activate.bat && celery -A app.tasks.celery_app beat --loglevel=info"

:: Start Frontend
echo  Starting Frontend...
start "CricketArb Frontend" cmd /k "cd /d g:\sonu\CricketArb\frontend && npm run dev"

:: Wait and open browser
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo.
echo  ====================================================
echo     CricketArb is running! (4 windows opened)
echo     Dashboard: http://localhost:5173
echo     API Docs:  http://localhost:8000/docs
echo     Health:    http://localhost:8000/health
echo  ====================================================
echo.
echo  Close this window or press Ctrl+C to stop.
pause
