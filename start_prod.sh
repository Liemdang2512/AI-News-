#!/bin/bash

# Function to kill child processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

echo "🚀 Starting Fullstack App (Production Mode)..."

# Start Backend
echo "Starting Backend..."
cd backend
source venv/bin/activate
# Run with 4 workers for production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "Starting Frontend..."
cd frontend
# Ensure build exists or run it? 
# Assuming build is done, run start
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "✅ App is running!"
echo "👉 Frontend: http://localhost:3000"
echo "👉 Backend: http://localhost:8000"
echo ""
echo "📝 Logs are being written to backend.log and frontend.log"
echo "Press Ctrl+C to stop."

wait
