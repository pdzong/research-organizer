#!/bin/bash
echo "Starting Research Agent Backend..."
echo

cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    C:\Users\krzys\AppData\Local\Programs\Python\Python313\python -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/updating dependencies..."
pip install -r requirements.txt

echo
echo "Starting FastAPI server..."
echo "API will be available at http://localhost:8000"
echo "API docs at http://localhost:8000/docs"
echo
uvicorn main:app --reload --port 8000
