@echo off
echo Starting Cart Recovery AI Backend...
echo.

echo Activating virtual environment...
call "%~dp0\.venv\Scripts\activate.bat"

cd /d "%~dp0\backend"

echo Installing/updating dependencies...
pip install -r requirements.txt

echo.
echo Starting FastAPI server...
echo Backend will be available at: http://localhost:8000
echo Admin Dashboard: http://localhost:8000/admin
echo API Documentation: http://localhost:8000/docs
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
