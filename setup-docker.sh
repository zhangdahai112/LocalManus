#!/bin/bash

# LocalManus Docker Setup Script
# This script prepares the environment for Docker deployment

set -e

echo "🚀 LocalManus Docker Setup"
echo "=========================="
echo ""

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/db
mkdir -p data/uploads

echo "✅ Data directories created:"
echo "   - data/db (for SQLite database)"
echo "   - data/uploads (for user files)"
echo ""

# Check if .env exists
if [ ! -f "localmanus-backend/.env" ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Creating .env from template..."
    
    if [ -f ".env.docker.example" ]; then
        cp .env.docker.example localmanus-backend/.env
        echo "✅ Created localmanus-backend/.env from .env.docker.example"
        echo ""
        echo "⚠️  IMPORTANT: Edit localmanus-backend/.env and set your API keys!"
        echo "   Required: OPENAI_API_KEY"
    else
        echo "❌ Error: .env.docker.example template not found"
        exit 1
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🐳 Docker environment ready!"
echo ""
echo "Next steps:"
echo "1. Edit localmanus-backend/.env with your API keys"
echo "2. Run: docker-compose up -d"
echo "3. Access frontend at: http://localhost:3000"
echo "4. Access backend at: http://localhost:8000"
echo ""
echo "For more info, see DOCKER_DEPLOYMENT.md"
