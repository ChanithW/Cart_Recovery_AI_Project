@echo off
echo Starting Cart Recovery AI Backend...
echo.

cd /d "%~dp0\backend"

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing/updating dependencies...
pip install -r requirements.txt

echo.
echo Starting FastAPI server...
echo Backend will be available at: http://localhost:8000
echo Admin Dashboard: http://localhost:8000/admin
echo API Documentation: http://localhost:8000/docs
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
