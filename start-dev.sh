#!/bin/bash

echo "🚀 Starting SpeakFlow Development Environment"

# Start Backend
echo "📡 Starting backend server..."
cd Server
python -m venv venv 2>/dev/null || echo "Virtual environment exists"
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || echo "Manual activation required"
pip install -r requirements.txt
export OPENAI_API_KEY=sk-demo-key
export TRELLO_ENABLED=false
export WHATSAPP_ENABLED=false
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Frontend
echo "🎨 Starting frontend..."
cd ../Client
npm install
npm run dev &
FRONTEND_PID=$!

echo "✅ SpeakFlow is running!"
echo "📡 Backend: http://localhost:8000"
echo "🎨 Frontend: http://localhost:5173"
echo "📚 API Docs: http://localhost:8000/docs"

# Wait for user interrupt
trap "echo 'Stopping SpeakFlow...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
