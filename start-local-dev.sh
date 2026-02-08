#!/bin/bash

# Local Development Start Script
# Starts backend and frontend in local dev mode

set -e

echo "=================================="
echo "LocalManus - Local Dev Mode"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -d "localmanus-backend" ] || [ ! -d "localmanus-ui" ]; then
    echo "❌ Error: Must run from LocalManus root directory"
    exit 1
fi

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Backend setup
echo "📦 Setting up backend..."
cd localmanus-backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found in backend"
    echo "Creating from template..."
    cat > .env <<EOF
MODEL_NAME=gpt-4
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=http://localhost:11434/v1
AGENT_MEMORY_LIMIT=40
UPLOAD_SIZE_LIMIT=10485760
DATABASE_URL=sqlite:///./db/localmanus.db
EOF
    echo "✅ Created .env file"
    echo "⚠️  Please edit localmanus-backend/.env with your API keys"
    read -p "Press Enter after updating .env file..."
fi

echo "Installing/updating backend dependencies..."
pip install -q -r requirements.txt

echo "✅ Backend setup complete"
echo ""

# Frontend setup
echo "📦 Setting up frontend..."
cd ../localmanus-ui

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (this may take a while)..."
    npm install
else
    echo "Frontend dependencies already installed"
fi

if [ ! -f ".env.local" ]; then
    echo "⚠️  No .env.local file found"
    echo "Creating with local development defaults..."
    cat > .env.local <<EOF
# Local Development Environment
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
NODE_ENV=development
EOF
    echo "✅ Created .env.local file"
fi

echo "✅ Frontend setup complete"
echo ""

# Start services
echo "=================================="
echo "🚀 Starting Services"
echo "=================================="
echo ""
echo "Starting backend on http://localhost:8000"
echo "Starting frontend on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

cd ../localmanus-backend

# Start backend in background
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend in foreground
cd ../localmanus-ui
npm run dev &
FRONTEND_PID=$!

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Keep script running
wait $FRONTEND_PID

# Cleanup
kill $BACKEND_PID 2>/dev/null
echo ""
echo "✅ Services stopped"
