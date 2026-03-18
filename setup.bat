@echo off
title CricketArb - One-Click Setup
color 0A
echo.
echo  ====================================================
echo     CricketArb - Cricket Betting Hedge System
echo     One-Click Setup for New Users
echo  ====================================================
echo.

:: Check prerequisites
echo [1/8] Checking prerequisites...
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo  ERROR: Python not found! Install Python 3.11+ from https://www.python.org
    echo  Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo   Python: %%i

where node >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo  ERROR: Node.js not found! Install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
for /f "tokens=1" %%i in ('node --version 2^>^&1') do echo   Node.js: %%i

where docker >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo  ERROR: Docker not found! Install Docker Desktop from https://www.docker.com
    pause
    exit /b 1
)
echo   Docker: installed
echo.
echo  All prerequisites found!
echo.

:: Start Docker containers
echo [2/8] Starting PostgreSQL + Redis (Docker)...
echo.
cd /d "g:\sonu\CricketArb"
docker-compose up -d
if %errorlevel% neq 0 (
    color 0C
    echo  ERROR: Docker failed to start. Is Docker Desktop running?
    echo  Start Docker Desktop and try again.
    pause
    exit /b 1
)
echo.
echo  PostgreSQL (port 5433) + Redis (port 6380) started!
echo.

:: Wait for containers to be ready
echo  Waiting 5 seconds for containers to initialize...
timeout /t 5 /nobreak >nul

:: Backend setup
echo [3/8] Setting up Python backend...
echo.
cd /d "g:\sonu\CricketArb\backend"

if not exist "venv" (
    echo  Creating virtual environment...
    python -m venv venv
)

echo  Activating virtual environment...
call venv\Scripts\activate.bat

echo  Installing Python dependencies (this may take a minute)...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    color 0C
    echo  ERROR: pip install failed. Check the error above.
    pause
    exit /b 1
)

echo  Installing email-validator (required by Pydantic)...
pip install email-validator --quiet

echo  Installing Playwright browser (for scraping mode)...
playwright install chromium 2>nul

echo.
echo  Python dependencies installed!
echo.

:: Database migration
echo [4/8] Setting up database...
echo.
cd /d "g:\sonu\CricketArb\backend"
call venv\Scripts\activate.bat

:: Check if alembic versions folder has any files
dir /b "alembic\versions\*.py" >nul 2>&1
if %errorlevel% neq 0 (
    echo  Generating initial migration...
    alembic revision --autogenerate -m "initial tables"
)

echo  Applying database migrations...
alembic upgrade head
if %errorlevel% neq 0 (
    color 0C
    echo  ERROR: Database migration failed. Check PostgreSQL is running.
    pause
    exit /b 1
)

echo  Seeding bookmakers...
python seed_bookmakers.py
echo.
echo  Database ready! (7 tables created, 5 bookmakers seeded)
echo.

:: Frontend setup
echo [5/8] Setting up React frontend...
echo.
cd /d "g:\sonu\CricketArb\frontend"

echo  Installing Node.js dependencies (this may take a minute)...
call npm install --silent
if %errorlevel% neq 0 (
    color 0C
    echo  ERROR: npm install failed. Check the error above.
    pause
    exit /b 1
)
echo.
echo  Frontend dependencies installed!
echo.

:: Summary
echo [6/8] Setup complete!
echo.
echo  ====================================================
echo     SETUP DONE! Here's how to start CricketArb:
echo  ====================================================
echo.
echo  You need 4 terminals open. Run these commands:
echo.
echo  TERMINAL 1 - Backend Server:
echo    cd g:\sonu\CricketArb\backend
echo    venv\Scripts\activate
echo    python main.py
echo.
echo  TERMINAL 2 - Celery Worker:
echo    cd g:\sonu\CricketArb\backend
echo    venv\Scripts\activate
echo    celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
echo.
echo  TERMINAL 3 - Celery Beat (Scheduler):
echo    cd g:\sonu\CricketArb\backend
echo    venv\Scripts\activate
echo    celery -A app.tasks.celery_app beat --loglevel=info
echo.
echo  TERMINAL 4 - Frontend:
echo    cd g:\sonu\CricketArb\frontend
echo    npm run dev
echo.
echo  Then open: http://localhost:5173
echo  Register an account, login, and you're ready!
echo.
echo  ====================================================
echo     OPTIONAL: Chrome Extension (Auto-Capture)
echo  ====================================================
echo.
echo  1. Open Chrome ^> go to chrome://extensions/
echo  2. Enable "Developer mode" (top right toggle)
echo  3. Click "Load unpacked"
echo  4. Select folder: g:\sonu\CricketArb\extension\
echo  5. Extension icon appears in toolbar
echo.
echo  ====================================================
echo     TIP: Use start.bat to launch everything at once!
echo  ====================================================
echo.

:: Ask to create start.bat
echo [7/8] Creating start.bat (launches all 3 services at once)...
echo.

:: Create start.bat
cd /d "g:\sonu\CricketArb"
(
echo @echo off
echo title CricketArb - Running
echo color 0A
echo echo.
echo echo  Starting CricketArb...
echo echo.
echo.
echo :: Start Docker if not running
echo docker-compose up -d 2^>nul
echo.
echo :: Start Backend
echo echo  Starting Backend Server...
echo start "CricketArb Backend" cmd /k "cd /d g:\sonu\CricketArb\backend && call venv\Scripts\activate.bat && python main.py"
echo.
echo :: Wait for backend to start
echo timeout /t 3 /nobreak ^>nul
echo.
echo :: Start Celery
echo echo  Starting Celery Worker...
echo start "CricketArb Celery" cmd /k "cd /d g:\sonu\CricketArb\backend && call venv\Scripts\activate.bat && celery -A app.tasks.celery_app worker --loglevel=info --pool=solo"
echo.
echo :: Start Frontend
echo echo  Starting Frontend...
echo start "CricketArb Frontend" cmd /k "cd /d g:\sonu\CricketArb\frontend && npm run dev"
echo.
echo :: Wait and open browser
echo timeout /t 5 /nobreak ^>nul
echo start http://localhost:5173
echo.
echo echo.
echo echo  ====================================================
echo echo     CricketArb is running!
echo echo     Dashboard: http://localhost:5173
echo echo     API Docs:  http://localhost:8000/docs
echo echo     Health:    http://localhost:8000/health
echo echo  ====================================================
echo echo.
echo echo  Close this window or press Ctrl+C to stop.
echo pause
) > start.bat

echo  start.bat created!
echo.

:: Create stop.bat
echo [8/8] Creating stop.bat (stops all services)...
(
echo @echo off
echo title CricketArb - Stopping
echo echo.
echo echo  Stopping CricketArb...
echo echo.
echo taskkill /fi "WINDOWTITLE eq CricketArb Backend*" /f 2^>nul
echo taskkill /fi "WINDOWTITLE eq CricketArb Celery*" /f 2^>nul
echo taskkill /fi "WINDOWTITLE eq CricketArb Frontend*" /f 2^>nul
echo cd /d g:\sonu\CricketArb
echo docker-compose down
echo echo.
echo echo  All services stopped.
echo pause
) > stop.bat

echo  stop.bat created!
echo.
echo  ====================================================
echo     ALL DONE!
echo.
echo     setup.bat  - You just ran this (one-time setup^)
echo     start.bat  - Double-click to START all services
echo     stop.bat   - Double-click to STOP all services
echo  ====================================================
echo.
pause
