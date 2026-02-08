# Docker Deployment Guide

## Overview

This Docker Compose setup includes:
- **Backend**: FastAPI application with AI agent system
- **Frontend**: Next.js UI application
- **Persistent Volumes**: Database and file uploads
- **Networking**: Internal bridge network for service communication

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                           │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Frontend   │ ──────► │   Backend    │                 │
│  │   (Next.js)  │         │  (FastAPI)   │                 │
│  │  Port: 3000  │         │  Port: 8000  │                 │
│  └──────────────┘         └──────┬───────┘                 │
│                                   │                          │
│                          ┌────────▼────────┐                │
│                          │  Persistent     │                │
│                          │  Volumes        │                │
│                          │  - db/          │                │
│                          │  - uploads/     │                │
│                          └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. Docker installed (version 20.10+)
2. Docker Compose installed (version 2.0+)
3. `.env` file configured in `localmanus-backend/` (see `.env.example`)

## Quick Start

### 1. Configure Environment Variables

Create `.env` file in `localmanus-backend/`:

```bash
cd localmanus-backend
cp .env.example .env
# Edit .env with your API keys and configuration
```

Required variables:
```env
MODEL_NAME=gpt-4
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
AGENT_MEMORY_LIMIT=40
UPLOAD_SIZE_LIMIT=10485760
```

### 2. Build and Start Services

```bash
# From the root directory (LocalManus/)
docker-compose up -d
```

This will:
- Build both frontend and backend images
- Create persistent volumes for database and uploads
- Start services with automatic restart
- Set up health checks

### 3. Verify Services

Check service status:
```bash
docker-compose ps
```

Expected output:
```
NAME                 STATUS              PORTS
localmanus-backend   Up (healthy)        0.0.0.0:8000->8000/tcp
localmanus-ui        Up                  0.0.0.0:3000->3000/tcp
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Volume Management

### Persistent Data Locations

All persistent data is stored in the `data/` directory:

```
LocalManus/
├── data/
│   ├── db/              # SQLite database files
│   └── uploads/         # User uploaded files (organized by user_id)
├── docker-compose.yml
└── ...
```

### Backup Data

```bash
# Backup database
cp -r data/db data/db-backup-$(date +%Y%m%d)

# Backup uploads
cp -r data/uploads data/uploads-backup-$(date +%Y%m%d)
```

### Restore Data

```bash
# Stop services
docker-compose down

# Restore from backup
cp -r data/db-backup-YYYYMMDD data/db
cp -r data/uploads-backup-YYYYMMDD data/uploads

# Start services
docker-compose up -d
```

## Service Management

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f ui
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services

```bash
# Stop (keeps volumes)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop and remove everything including volumes (⚠️ DATA LOSS)
docker-compose down -v
```

### Rebuild Services

```bash
# Rebuild after code changes
docker-compose build

# Rebuild and restart
docker-compose up -d --build
```

## Troubleshooting

### Backend Health Check Failing

```bash
# Check backend logs
docker-compose logs backend

# Check health status
docker inspect --format='{{json .State.Health}}' localmanus-backend
```

### Frontend Cannot Connect to Backend

1. Check backend is healthy: `docker-compose ps`
2. Verify network: `docker network inspect localmanus_localmanus-network`
3. Check NEXT_PUBLIC_API_URL in docker-compose.yml matches backend URL

### Database Issues

```bash
# Enter backend container
docker-compose exec backend bash

# Check database file
ls -la db/
sqlite3 db/localmanus.db ".tables"
```

### Permission Issues with Volumes

```bash
# Fix ownership
sudo chown -R $USER:$USER data/
```

## Development Mode

For development with hot reload:

```bash
# Backend with volume mount for code
docker-compose -f docker-compose.dev.yml up

# Or run locally
cd localmanus-backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Production Deployment

### Security Checklist

- [ ] Change default passwords
- [ ] Use strong API keys
- [ ] Configure CORS properly (not `allow_origins=["*"]`)
- [ ] Enable HTTPS with reverse proxy (nginx/Caddy)
- [ ] Set up database backups
- [ ] Monitor disk space for uploads
- [ ] Configure log rotation

### Recommended Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # For SSE streaming
        proxy_buffering off;
        proxy_cache off;
    }
}
```

## Monitoring

### Check Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

### Database Size

```bash
docker-compose exec backend du -sh db/
```

### Upload Directory Size

```bash
docker-compose exec backend du -sh uploads/
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| MODEL_NAME | LLM model name | gpt-4 |
| OPENAI_API_KEY | OpenAI API key | (required) |
| OPENAI_API_BASE | API base URL | http://localhost:11434/v1 |
| AGENT_MEMORY_LIMIT | Max conversation rounds | 40 |
| UPLOAD_SIZE_LIMIT | Max file upload size (bytes) | 10485760 (10MB) |
| DATABASE_URL | Database connection string | sqlite:///./db/localmanus.db |

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review documentation in `docs/`
- Check API health: `curl http://localhost:8000/api/health`
