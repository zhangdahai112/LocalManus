@echo off
REM Production Deployment Script for LocalManus (Windows)
REM Server: 47.121.183.184
REM Backend Port: 1243
REM Frontend Port: 3000

echo.
echo ================================
echo LocalManus Production Deployment
echo ================================
echo.

REM Configuration
set BACKEND_PORT=1243
set FRONTEND_PORT=3000
set API_BASE_URL=http://47.121.183.184:%BACKEND_PORT%

REM Check Docker installation
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

echo [OK] Docker and Docker Compose are installed
echo.

REM Create data directories
echo [INFO] Creating data directories...
if not exist "data\db" mkdir "data\db"
if not exist "data\uploads" mkdir "data\uploads"
echo [OK] Data directories created
echo.

REM Check if .env exists
if not exist "localmanus-backend\.env" (
    echo [WARNING] Backend .env file not found!
    echo Creating from template...
    
    (
        echo MODEL_NAME=gpt-4
        echo OPENAI_API_KEY=your_api_key_here
        echo OPENAI_API_BASE=https://api.openai.com/v1
        echo AGENT_MEMORY_LIMIT=40
        echo UPLOAD_SIZE_LIMIT=10485760
        echo DATABASE_URL=sqlite:///./db/localmanus.db
    ) > localmanus-backend\.env
    
    echo [OK] Created localmanus-backend\.env
    echo [IMPORTANT] Edit localmanus-backend\.env with your API keys!
    echo.
    pause
)

REM Create production environment file for frontend
echo [INFO] Creating frontend production environment...
(
    echo NEXT_PUBLIC_API_URL=%API_BASE_URL%
    echo BACKEND_URL=%API_BASE_URL%
    echo NODE_ENV=production
) > localmanus-ui\.env.production
echo [OK] Frontend environment configured
echo.

REM Build Docker images
echo [INFO] Building Docker images...
docker-compose build --no-cache

echo.
echo [INFO] Starting services...
docker-compose up -d

echo.
echo [INFO] Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check service status
echo.
echo [INFO] Service Status:
docker-compose ps

echo.
echo [INFO] Health Checks:
echo.

REM Check backend health
echo | set /p="Backend: "
curl -f -s "http://localhost:%BACKEND_PORT%/api/health" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Healthy
) else (
    echo [ERROR] Not responding
)

REM Check frontend
echo | set /p="Frontend: "
curl -f -s "http://localhost:%FRONTEND_PORT%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Running
) else (
    echo [ERROR] Not responding
)

echo.
echo ================================
echo [OK] Deployment Complete!
echo ================================
echo.
echo Access your application:
echo   Frontend: http://47.121.183.184:%FRONTEND_PORT%
echo   Backend:  http://47.121.183.184:%BACKEND_PORT%
echo   API Docs: http://47.121.183.184:%BACKEND_PORT%/docs
echo.
echo Useful commands:
echo   View logs:    docker-compose logs -f
echo   Stop:         docker-compose down
echo   Restart:      docker-compose restart
echo   Status:       docker-compose ps
echo.
echo For detailed deployment info, see: PRODUCTION_DEPLOYMENT.md
echo.
pause
