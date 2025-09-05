@echo off
echo Starting Cart Recovery AI Frontend...
echo.

cd /d "%~dp0\frontend"

echo Installing/updating dependencies...
npm install

echo.
echo Starting React development server...
echo Frontend will be available at: http://localhost:3000
echo.

npm start
