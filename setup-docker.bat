@echo off
REM LocalManus Docker Setup Script (Windows)
REM This script prepares the environment for Docker deployment

echo.
echo ================================
echo LocalManus Docker Setup
echo ================================
echo.

REM Create data directories
echo Creating data directories...
if not exist "data\db" mkdir "data\db"
if not exist "data\uploads" mkdir "data\uploads"

echo [OK] Data directories created:
echo    - data\db (for SQLite database)
echo    - data\uploads (for user files)
echo.

REM Check if .env exists
if not exist "localmanus-backend\.env" (
    echo [WARNING] .env file not found!
    echo.
    echo Creating .env from template...
    
    if exist ".env.docker.example" (
        copy ".env.docker.example" "localmanus-backend\.env"
        echo [OK] Created localmanus-backend\.env from .env.docker.example
        echo.
        echo [IMPORTANT] Edit localmanus-backend\.env and set your API keys!
        echo    Required: OPENAI_API_KEY
    ) else (
        echo [ERROR] .env.docker.example template not found
        exit /b 1
    )
) else (
    echo [OK] .env file already exists
)

echo.
echo ================================
echo Docker environment ready!
echo ================================
echo.
echo Next steps:
echo 1. Edit localmanus-backend\.env with your API keys
echo 2. Run: docker-compose up -d
echo 3. Access frontend at: http://localhost:3000
echo 4. Access backend at: http://localhost:8000
echo.
echo For more info, see DOCKER_DEPLOYMENT.md
echo.
pause
