@echo off
echo ========================================================
echo Starting CampusOps Unified Operations Platform
echo ========================================================

REM Start Backend FastAPI Server
echo Starting Backend API (FastAPI) on port 8000...
start "CampusOps Backend API" cmd /k "backend\venv\Scripts\python backend\run.py"

REM Start Frontend Vite Server
echo Starting Frontend (Vite React) on port 5173...
start "CampusOps Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo Platform is launching!
echo  - Frontend Web UI: http://localhost:5173
echo  - Backend API Docs: http://localhost:8000/docs
echo ========================================================
timeout /t 5
start http://localhost:5173

