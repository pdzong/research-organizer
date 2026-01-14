#!/bin/bash
echo "Starting Research Agent Frontend..."
echo

cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo
echo "Starting Vite dev server..."
echo "App will be available at http://localhost:5173"
echo
npm run dev
