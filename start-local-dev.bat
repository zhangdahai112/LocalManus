@echo off
REM Local Development Start Script
REM Starts backend and frontend in local dev mode

echo ==================================
echo LocalManus - Local Dev Mode
echo ==================================
echo.

REM Check if we're in the right directory
if not exist "localmanus-backend" (
    echo ❌ Error: Must run from LocalManus root directory
    pause
    exit /b 1
)

if not exist "localmanus-ui" (
    echo ❌ Error: Must run from LocalManus root directory
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python is not installed
    pause
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js is not installed
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed
echo.

REM Backend setup
echo 📦 Setting up backend...
cd localmanus-backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

if not exist ".env" (
    echo ⚠️  No .env file found in backend
    echo Creating from template...
    (
        echo MODEL_NAME=gpt-4
        echo OPENAI_API_KEY=your_api_key_here
        echo OPENAI_API_BASE=http://localhost:11434/v1
        echo AGENT_MEMORY_LIMIT=40
        echo UPLOAD_SIZE_LIMIT=10485760
        echo DATABASE_URL=sqlite:///./db/localmanus.db
    ) > .env
    echo ✅ Created .env file
    echo ⚠️  Please edit localmanus-backend\.env with your API keys
    pause
)

echo Installing/updating backend dependencies...
pip install -q -r requirements.txt

echo ✅ Backend setup complete
echo.

REM Frontend setup
echo 📦 Setting up frontend...
cd ..\localmanus-ui

if not exist "node_modules" (
    echo Installing frontend dependencies ^(this may take a while^)...
    call npm install
) else (
    echo Frontend dependencies already installed
)

if not exist ".env.local" (
    echo ⚠️  No .env.local file found
    echo Creating with local development defaults...
    (
        echo # Local Development Environment
        echo NEXT_PUBLIC_API_URL=http://localhost:8000
        echo BACKEND_URL=http://localhost:8000
        echo NODE_ENV=development
    ) > .env.local
    echo ✅ Created .env.local file
)

echo ✅ Frontend setup complete
echo.

REM Start services
echo ==================================
echo 🚀 Starting Services
echo ==================================
echo.
echo Starting backend on http://localhost:8000
echo Starting frontend on http://localhost:3000
echo.
echo Press Ctrl+C to stop all services
echo.
echo Opening new terminal windows for each service...
echo.

REM Start backend in new window
cd ..\localmanus-backend
start "LocalManus Backend" cmd /k "venv\Scripts\activate.bat && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
cd ..\localmanus-ui
start "LocalManus Frontend" cmd /k "npm run dev"

echo.
echo ✅ Services started in separate windows
echo.
echo Access your application:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo To stop services, close the terminal windows or press Ctrl+C in each
echo.

cd ..
pause
