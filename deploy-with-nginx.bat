@echo off
REM Production Deployment Script for LocalManus with Nginx
REM Server: 47.121.183.184
REM Port: 1243 (via Nginx)

echo ==================================
echo LocalManus Production Deployment
echo with Nginx Reverse Proxy
echo ==================================
echo.

set NGINX_PORT=1243
set API_BASE_URL=http://47.121.183.184:%NGINX_PORT%

REM Check Docker installation
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose are installed
echo.

REM Create data directories
echo 📁 Creating data directories...
if not exist data\db mkdir data\db
if not exist data\uploads mkdir data\uploads
if not exist nginx mkdir nginx
echo ✅ Data directories created
echo.

REM Check if .env exists
if not exist localmanus-backend\.env (
    echo ⚠️  Backend .env file not found!
    echo Creating from template...
    
    (
        echo MODEL_NAME=gpt-4
        echo OPENAI_API_KEY=your_api_key_here
        echo OPENAI_API_BASE=https://api.openai.com/v1
        echo AGENT_MEMORY_LIMIT=40
        echo UPLOAD_SIZE_LIMIT=10485760
        echo DATABASE_URL=sqlite:///./db/localmanus.db
    ) > localmanus-backend\.env
    
    echo ✅ Created localmanus-backend\.env
    echo ⚠️  IMPORTANT: Edit localmanus-backend\.env with your API keys!
    echo.
    pause
)

REM Create production environment file for frontend
echo 📝 Creating frontend production environment...
(
    echo NEXT_PUBLIC_API_URL=%API_BASE_URL%
    echo BACKEND_URL=http://backend:8000
    echo NODE_ENV=production
) > localmanus-ui\.env.production
echo ✅ Frontend environment configured
echo.

REM Choose deployment mode
echo Select deployment mode:
echo   1^) Development ^(port 80, nginx.conf^)
echo   2^) Production ^(port 1243, nginx.prod.conf^)
set /p mode="Enter choice [1-2]: "

if "%mode%"=="2" (
    echo 🚀 Using production configuration...
    set COMPOSE_FILES=-f docker-compose.yml -f docker-compose.prod.yml
    set NGINX_CONFIG=nginx.prod.conf
    set CHECK_PORT=%NGINX_PORT%
) else (
    echo 🔧 Using development configuration...
    set COMPOSE_FILES=-f docker-compose.yml
    set NGINX_CONFIG=nginx.conf
    set CHECK_PORT=80
)

REM Verify nginx config exists
if not exist nginx\%NGINX_CONFIG% (
    echo ❌ Nginx configuration not found: nginx\%NGINX_CONFIG%
    pause
    exit /b 1
)

echo.

REM Build and deploy
echo 🔨 Building Docker images...
docker-compose %COMPOSE_FILES% build --no-cache

echo.
echo 🚀 Starting services...
docker-compose %COMPOSE_FILES% up -d

echo.
echo ⏳ Waiting for services to start...
timeout /t 15 /nobreak >nul

REM Check service status
echo.
echo 📊 Service Status:
docker-compose %COMPOSE_FILES% ps

echo.
echo 🔍 Health Checks:
echo.

REM Check nginx health
echo Nginx:
curl -f -s http://localhost:%CHECK_PORT%/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   ✅ Healthy
) else (
    echo   ❌ Not responding
    echo   Check logs: docker logs localmanus-nginx
)

REM Check frontend via nginx
echo Frontend ^(via Nginx^):
curl -f -s http://localhost:%CHECK_PORT%/ >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   ✅ Running
) else (
    echo   ❌ Not responding
)

REM Check backend via nginx
echo Backend ^(via Nginx^):
curl -f -s http://localhost:%CHECK_PORT%/api/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   ✅ Running
) else (
    echo   ❌ Not responding
)

echo.
echo ==================================
echo ✅ Deployment Complete!
echo ==================================
echo.

if "%mode%"=="2" (
    echo Access your application:
    echo   Application: http://47.121.183.184:%NGINX_PORT%
    echo   API Docs:    http://47.121.183.184:%NGINX_PORT%/api/docs
    echo   Health:      http://47.121.183.184:%NGINX_PORT%/health
) else (
    echo Access your application:
    echo   Application: http://localhost
    echo   API Docs:    http://localhost/api/docs
    echo   Health:      http://localhost/health
)

echo.
echo Architecture:
echo   Browser → Nginx → Backend ^(FastAPI^)
echo           ↘ Nginx → Frontend ^(Next.js SSR^)
echo.
echo Useful commands:
echo   View logs:       docker-compose %COMPOSE_FILES% logs -f
echo   Nginx logs:      docker logs localmanus-nginx
echo   Stop:            docker-compose %COMPOSE_FILES% down
echo   Restart:         docker-compose %COMPOSE_FILES% restart
echo   Status:          docker-compose %COMPOSE_FILES% ps
echo.
echo For detailed info, see: nginx\README.md
echo.
pause
