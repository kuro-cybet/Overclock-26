@echo off
echo ========================================================
echo CampusOps · Seeding Synthetic University Dataset
echo ========================================================

call backend\venv\Scripts\python backend\app\database\seed\seed.py

echo.
echo Database seeded successfully!
pause

