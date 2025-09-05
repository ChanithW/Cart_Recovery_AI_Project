@echo off
echo ============================================
echo    Cart Recovery AI - Complete Setup
echo ============================================
echo.

echo This script will start both backend and frontend servers.
echo Make sure you have:
echo   - Python 3.8+ installed
echo   - Node.js 16+ installed  
echo   - MySQL 8.0+ running
echo   - OpenRouter API key configured
echo.

pause

echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d %~dp0 && start_backend.bat"

echo Waiting 10 seconds for backend to start...
timeout /t 10 /nobreak >nul

echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd /d %~dp0 && start_frontend.bat"

echo.
echo ============================================
echo        Servers Starting...
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo Admin:    http://localhost:8000/admin
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit this window...
pause >nul
