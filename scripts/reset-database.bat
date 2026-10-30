@echo off
echo ========================================================
echo CampusOps · Resetting Database to Baseline State
echo ========================================================

call backend\venv\Scripts\python backend\app\database\seed\seed.py

echo.
echo Baseline university state restored cleanly!
pause

