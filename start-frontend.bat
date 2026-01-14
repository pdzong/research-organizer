@echo off
echo Starting Research Agent Frontend...
echo.

cd frontend

if not exist node_modules (
    echo Installing dependencies...
    npm install
)

echo.
echo Starting Vite dev server...
echo App will be available at http://localhost:5173
echo.
npm run dev
