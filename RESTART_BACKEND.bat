@echo off
echo.
echo ========================================
echo  Restarting Research Agent Backend
echo ========================================
echo.
echo This will:
echo  1. Stop the current backend server
echo  2. Activate the virtual environment
echo  3. Start uvicorn with hot reload
echo.
echo Press Ctrl+C to stop the server when needed.
echo.

cd backend
call venv\Scripts\activate.bat
uvicorn main:app --reload --port 8000
