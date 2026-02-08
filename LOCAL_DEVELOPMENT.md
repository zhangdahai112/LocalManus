# Local Development Guide

This guide covers how to run LocalManus in local development mode with hot reload and direct backend access.

## Development Modes

LocalManus supports three development modes:

1. **Local Dev Mode** - Direct local backend (no Docker)
2. **Docker Dev Mode** - Docker Compose with nginx
3. **Production Mode** - Optimized production build

## 1. Local Dev Mode (Recommended for Development)

Run backend and frontend directly on your machine for fastest development iteration.

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd localmanus-backend

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Create .env file (first time only)
# Copy from .env.example and configure
cp .env.example .env
# Edit .env with your settings

# Run backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd localmanus-ui

# Install dependencies (first time only)
npm install

# Create .env.local (first time only)
# This file is already created with local defaults
# Check e:\LocalManus\localmanus-ui\.env.local

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### Environment Configuration

**Backend (`.env`):**
```env
MODEL_NAME=gpt-4
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=http://localhost:11434/v1  # or your LLM endpoint
AGENT_MEMORY_LIMIT=40
UPLOAD_SIZE_LIMIT=10485760
DATABASE_URL=sqlite:///./db/localmanus.db
```

**Frontend (`.env.local`):**
```env
# Public API URL (accessible from browser)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Internal API URL (for SSR)
BACKEND_URL=http://localhost:8000

# Node environment
NODE_ENV=development
```

### Development Workflow

1. Start backend: `uvicorn main:app --reload`
2. Start frontend: `npm run dev`
3. Access app: `http://localhost:3000`
4. Make changes - both have hot reload!

### Advantages

✅ Fast hot reload on both backend and frontend  
✅ Direct debugging with breakpoints  
✅ No Docker overhead  
✅ Easy to test API changes  
✅ Full IDE support  

## 2. Docker Dev Mode

Run everything in Docker with nginx proxy.

### Setup

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access:** `http://localhost` (via nginx)

### Environment Configuration

Uses `.env.development` for frontend:
```env
NEXT_PUBLIC_API_URL=http://localhost
BACKEND_URL=http://backend:8000
NODE_ENV=development
```

### Advantages

✅ Production-like environment  
✅ Tests nginx configuration  
✅ Isolated from local system  
✅ Easy to share setup  

### Disadvantages

❌ Slower iteration (rebuild on changes)  
❌ Harder to debug  
❌ More resource intensive  

## 3. Production Mode

Optimized build for deployment.

```bash
# Using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or using deployment script
./deploy-with-nginx.sh  # Linux/Mac
deploy-with-nginx.bat   # Windows
```

**Access:** `http://47.121.183.184:1243`

## API Endpoint Reference

### Local Dev Mode
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

### Docker Dev Mode
- Application: `http://localhost` (via nginx)
- API Docs: `http://localhost/api/docs`
- Health Check: `http://localhost/health`

### Production Mode
- Application: `http://47.121.183.184:1243`
- API Docs: `http://47.121.183.184:1243/api/docs`
- Health Check: `http://47.121.183.184:1243/health`

## Environment Files

| File | Mode | Committed | Purpose |
|------|------|-----------|---------|
| `.env.local` | Local Dev | ❌ No | Personal local dev settings |
| `.env.development` | Docker Dev | ✅ Yes | Docker development defaults |
| `.env.production` | Production | ✅ Yes | Production configuration |
| `.env.local.example` | Template | ✅ Yes | Example for local dev |

## Switching Between Modes

### From Local Dev to Docker Dev

```bash
# Stop local servers (Ctrl+C)

# Start Docker
docker-compose up -d
```

### From Docker Dev to Local Dev

```bash
# Stop Docker
docker-compose down

# Start local servers
cd localmanus-backend && uvicorn main:app --reload
cd localmanus-ui && npm run dev
```

### From Dev to Production

```bash
# Stop dev services
docker-compose down  # or Ctrl+C on local servers

# Deploy production
./deploy-with-nginx.sh
```

## Common Development Tasks

### Install New Backend Dependency

```bash
cd localmanus-backend
pip install package-name
pip freeze > requirements.txt
```

### Install New Frontend Dependency

```bash
cd localmanus-ui
npm install package-name
```

### Reset Database

```bash
# Local dev
rm -rf localmanus-backend/db/localmanus.db

# Docker
docker-compose down -v
rm -rf data/db/*
docker-compose up -d
```

### View Logs

```bash
# Local dev
# Check terminal where servers are running

# Docker dev
docker-compose logs -f

# Specific service
docker logs -f localmanus-backend
docker logs -f localmanus-ui
docker logs -f localmanus-nginx
```

### Run Tests

```bash
# Backend tests
cd localmanus-backend
pytest

# Frontend tests
cd localmanus-ui
npm test
```

### Build Frontend

```bash
cd localmanus-ui

# Clean previous build
rm -rf .next

# Build
npm run build

# Test production build locally
npm start
```

## Troubleshooting

### Port Already in Use

**Backend (port 8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Frontend (port 3000):**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

### Cannot Connect to Backend

1. Check backend is running: `curl http://localhost:8000/api/health`
2. Check `.env.local` has correct URL: `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Check CORS settings in `main.py`

### Hot Reload Not Working

**Frontend:**
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

**Backend:**
- Make sure using `--reload` flag
- Check file is saved
- Restart uvicorn

### Import Errors

**Backend:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**Frontend:**
```bash
# Reinstall dependencies
rm -rf node_modules
npm install
```

### Environment Variables Not Loading

1. Restart dev server after changing `.env.local`
2. Check file name is exactly `.env.local`
3. Check syntax (no quotes around values usually)
4. For NEXT_PUBLIC_* vars, need rebuild

## Best Practices

### Local Development

1. **Use `.env.local`** for personal settings (not committed)
2. **Keep backend running** in one terminal
3. **Keep frontend running** in another terminal
4. **Use hot reload** - don't restart unless needed
5. **Check console** for errors in browser and terminal

### Code Changes

1. **Backend changes** - Hot reload automatic with `--reload`
2. **Frontend changes** - Hot reload automatic
3. **Config changes** - May need restart
4. **Dependency changes** - Need reinstall

### Git Workflow

1. **Don't commit** `.env.local`
2. **Do commit** `.env.development`, `.env.production`
3. **Update** `.env.local.example` if adding new vars
4. **Test** in Docker dev mode before pushing

## Performance Tips

### Local Dev

- Use local LLM (Ollama) to avoid API rate limits
- Keep only necessary services running
- Use fast SSD for node_modules and venv

### Docker Dev

- Use named volumes for better performance
- Don't use `--no-cache` unless needed
- Keep images updated: `docker-compose pull`

## Quick Reference

### Start Local Dev
```bash
# Terminal 1 - Backend
cd localmanus-backend && source venv/bin/activate && uvicorn main:app --reload

# Terminal 2 - Frontend
cd localmanus-ui && npm run dev
```

### Start Docker Dev
```bash
docker-compose up -d && docker-compose logs -f
```

### Stop Everything
```bash
# Local: Ctrl+C in each terminal
# Docker: docker-compose down
```

### Check Status
```bash
# Local
curl http://localhost:8000/api/health
curl http://localhost:3000

# Docker
docker-compose ps
curl http://localhost/health
```

---

**Recommended Setup for Active Development:**

Use **Local Dev Mode** for:
- Fast iteration
- Debugging
- API development
- Frontend development

Use **Docker Dev Mode** for:
- Testing deployment
- Nginx configuration
- Integration testing
- Before pushing to production

Use **Production Mode** for:
- Final testing
- Deployment
- Performance testing
