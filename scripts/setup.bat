@echo off
echo ========================================================
echo CampusOps · Setting up Virtual Environment and Packages
echo ========================================================

REM 1. Set up backend venv
echo [1/3] Creating Python Virtual Environment (backend\venv)...
python -m venv backend\venv

echo [2/3] Installing Backend Dependencies into venv...
call backend\venv\Scripts\pip install -r backend\requirements.txt

REM 2. Install frontend packages
echo [3/3] Installing Frontend Node Modules...
cd frontend
call npm install
cd ..

echo.
echo ========================================================
echo Setup complete! Run scripts\seed-database.bat or start.bat
echo ========================================================
pause

