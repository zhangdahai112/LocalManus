#!/bin/bash

# Production Deployment Script for LocalManus
# Server: 47.121.183.184
# Backend Port: 1243
# Frontend Port: 3000

set -e

echo "================================"
echo "LocalManus Production Deployment"
echo "================================"
echo ""

# Configuration
BACKEND_PORT=1243
FRONTEND_PORT=3000
API_BASE_URL="http://47.121.183.184:$BACKEND_PORT"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Please don't run as root"
   exit 1
fi

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/db
mkdir -p data/uploads
echo "✅ Data directories created"
echo ""

# Check if .env exists
if [ ! -f "localmanus-backend/.env" ]; then
    echo "⚠️  Backend .env file not found!"
    echo "Creating from template..."
    
    cat > localmanus-backend/.env <<EOF
MODEL_NAME=gpt-4
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
AGENT_MEMORY_LIMIT=40
UPLOAD_SIZE_LIMIT=10485760
DATABASE_URL=sqlite:///./db/localmanus.db
EOF
    
    echo "✅ Created localmanus-backend/.env"
    echo "⚠️  IMPORTANT: Edit localmanus-backend/.env with your API keys!"
    echo ""
    read -p "Press Enter after updating the .env file..."
fi

# Create production environment file for frontend
echo "📝 Creating frontend production environment..."
cat > localmanus-ui/.env.production <<EOF
NEXT_PUBLIC_API_URL=$API_BASE_URL
BACKEND_URL=$API_BASE_URL
NODE_ENV=production
EOF
echo "✅ Frontend environment configured"
echo ""

# Update docker-compose.yml for production
echo "🐳 Updating Docker Compose configuration..."
cat > docker-compose.yml <<EOF
services:
  # Backend service
  backend:
    build:
      context: ./localmanus-backend
      dockerfile: Dockerfile
    container_name: localmanus-backend
    ports:
      - "$BACKEND_PORT:8000"
    environment:
      - MODEL_NAME=\${MODEL_NAME:-gpt-4}
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - OPENAI_API_BASE=\${OPENAI_API_BASE:-https://api.openai.com/v1}
      - AGENT_MEMORY_LIMIT=\${AGENT_MEMORY_LIMIT:-40}
      - UPLOAD_SIZE_LIMIT=\${UPLOAD_SIZE_LIMIT:-10485760}
      - DATABASE_URL=sqlite:///./db/localmanus.db
    volumes:
      - ./data/db:/app/db
      - ./data/uploads:/app/uploads
      - ./localmanus-backend/.env:/app/.env:ro
    restart: unless-stopped
    networks:
      - localmanus-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Frontend service
  ui:
    build:
      context: ./localmanus-ui
      dockerfile: Dockerfile
    container_name: localmanus-ui
    ports:
      - "$FRONTEND_PORT:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=$API_BASE_URL
      - BACKEND_URL=http://backend:8000
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - localmanus-network

volumes:
  db_data:
    driver: local
  uploads_data:
    driver: local

networks:
  localmanus-network:
    driver: bridge
EOF
echo "✅ Docker Compose updated"
echo ""

# Build and deploy
echo "🔨 Building Docker images..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🔍 Health Checks:"
echo ""

# Check backend health
echo -n "Backend: "
if curl -f -s "http://localhost:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Not responding"
fi

# Check frontend
echo -n "Frontend: "
if curl -f -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

echo ""
echo "================================"
echo "✅ Deployment Complete!"
echo "================================"
echo ""
echo "Access your application:"
echo "  Frontend: http://47.121.183.184:$FRONTEND_PORT"
echo "  Backend:  http://47.121.183.184:$BACKEND_PORT"
echo "  API Docs: http://47.121.183.184:$BACKEND_PORT/docs"
echo ""
echo "Useful commands:"
echo "  View logs:    docker-compose logs -f"
echo "  Stop:         docker-compose down"
echo "  Restart:      docker-compose restart"
echo "  Status:       docker-compose ps"
echo ""
echo "For detailed deployment info, see: PRODUCTION_DEPLOYMENT.md"
