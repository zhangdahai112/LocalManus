#!/bin/bash

# Production Deployment Script for LocalManus with Nginx
# Server: 47.121.183.184
# Port: 1243 (via Nginx)

set -e

echo "=================================="
echo "LocalManus Production Deployment"
echo "with Nginx Reverse Proxy"
echo "=================================="
echo ""

# Configuration
NGINX_PORT=1243
API_BASE_URL="http://47.121.183.184:$NGINX_PORT"

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
mkdir -p nginx
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
BACKEND_URL=http://backend:8000
NODE_ENV=production
EOF
echo "✅ Frontend environment configured"
echo ""

# Choose deployment mode
echo "Select deployment mode:"
echo "  1) Development (port 80, nginx.conf)"
echo "  2) Production (port 1243, nginx.prod.conf)"
read -p "Enter choice [1-2]: " mode

if [ "$mode" == "2" ]; then
    echo "🚀 Using production configuration..."
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
    NGINX_CONFIG="nginx.prod.conf"
else
    echo "🔧 Using development configuration..."
    COMPOSE_FILES="-f docker-compose.yml"
    NGINX_CONFIG="nginx.conf"
fi

# Verify nginx config exists
if [ ! -f "nginx/$NGINX_CONFIG" ]; then
    echo "❌ Nginx configuration not found: nginx/$NGINX_CONFIG"
    exit 1
fi

echo ""

# Build and deploy
echo "🔨 Building Docker images..."
docker-compose $COMPOSE_FILES build --no-cache

echo ""
echo "🚀 Starting services..."
docker-compose $COMPOSE_FILES up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose $COMPOSE_FILES ps

echo ""
echo "🔍 Health Checks:"
echo ""

# Determine the port to check
if [ "$mode" == "2" ]; then
    CHECK_PORT=$NGINX_PORT
else
    CHECK_PORT=80
fi

# Check nginx health
echo -n "Nginx: "
if curl -f -s "http://localhost:$CHECK_PORT/health" > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Not responding"
    echo "   Check logs: docker logs localmanus-nginx"
fi

# Check frontend via nginx
echo -n "Frontend (via Nginx): "
if curl -f -s "http://localhost:$CHECK_PORT/" > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

# Check backend via nginx
echo -n "Backend (via Nginx): "
if curl -f -s "http://localhost:$CHECK_PORT/api/health" > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

echo ""
echo "=================================="
echo "✅ Deployment Complete!"
echo "=================================="
echo ""

if [ "$mode" == "2" ]; then
    echo "Access your application:"
    echo "  Application: http://47.121.183.184:$NGINX_PORT"
    echo "  API Docs:    http://47.121.183.184:$NGINX_PORT/api/docs"
    echo "  Health:      http://47.121.183.184:$NGINX_PORT/health"
else
    echo "Access your application:"
    echo "  Application: http://localhost"
    echo "  API Docs:    http://localhost/api/docs"
    echo "  Health:      http://localhost/health"
fi

echo ""
echo "Architecture:"
echo "  Browser → Nginx → Backend (FastAPI)"
echo "          ↘ Nginx → Frontend (Next.js SSR)"
echo ""
echo "Useful commands:"
echo "  View logs:       docker-compose $COMPOSE_FILES logs -f"
echo "  Nginx logs:      docker logs localmanus-nginx"
echo "  Stop:            docker-compose $COMPOSE_FILES down"
echo "  Restart:         docker-compose $COMPOSE_FILES restart"
echo "  Status:          docker-compose $COMPOSE_FILES ps"
echo ""
echo "For detailed info, see: nginx/README.md"
