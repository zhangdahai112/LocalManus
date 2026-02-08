# Docker Compose Configuration Summary

## ✅ What Has Been Added

### 1. Backend Service Configuration

**File**: `docker-compose.yml`

- **Container**: `localmanus-backend`
- **Port**: `8000:8000`
- **Build Context**: `./localmanus-backend/Dockerfile`
- **Environment Variables**: All LLM and agent configuration from `.env`
- **Persistent Volumes**:
  - `./data/db:/app/db` - SQLite database storage
  - `./data/uploads:/app/uploads` - User uploaded files
  - `.env` file mounted read-only
- **Health Check**: `/api/health` endpoint with retry logic
- **Network**: `localmanus-network` (bridge mode)

### 2. Frontend Service Configuration

**File**: `docker-compose.yml`

- **Container**: `localmanus-ui`
- **Port**: `3000:3000`
- **Build Context**: `./localmanus-ui/Dockerfile`
- **Environment**: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- **Dependency**: Waits for backend health check
- **Network**: `localmanus-network` (bridge mode)

### 3. Backend Dockerfile

**File**: `localmanus-backend/Dockerfile`

Features:
- **Base Image**: Python 3.11-slim (multi-stage build)
- **Dependencies**: Installed via pip from requirements.txt
- **Optimizations**: Layer caching for faster rebuilds
- **Security**: Non-root user, minimal attack surface
- **Health Check**: Built-in curl health monitoring
- **Port**: Exposes 8000
- **Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`

### 4. Supporting Files

**`.dockerignore`**: Excludes unnecessary files from build context
**`DOCKER_DEPLOYMENT.md`**: Complete deployment guide
**`.env.docker.example`**: Template for environment variables

### 5. Health Check Endpoint

**File**: `localmanus-backend/main.py`

Added `/api/health` endpoint:
```python
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "localmanus-backend",
        "timestamp": datetime.utcnow().isoformat()
    }
```

## 📁 Volume Mount Points

### Database Volume
- **Host**: `./data/db/`
- **Container**: `/app/db/`
- **Content**: SQLite database files
- **Purpose**: Persist user data, sessions, projects

### Uploads Volume
- **Host**: `./data/uploads/`
- **Container**: `/app/uploads/`
- **Structure**: `uploads/{user_id}/filename`
- **Purpose**: Persist user uploaded files with isolation

### Environment File
- **Host**: `./localmanus-backend/.env`
- **Container**: `/app/.env`
- **Mode**: Read-only
- **Purpose**: LLM API keys and configuration

## 🌐 Network Configuration

### Service Communication

```
Frontend (localhost:3000)
    ↓ HTTP requests
Backend (localhost:8000)
    ↓ File system
Volumes (./data/db, ./data/uploads)
```

### Address Consistency

✅ **Frontend → Backend**: Uses `http://localhost:8000` (configured via `NEXT_PUBLIC_API_URL`)
✅ **Docker Network**: Internal communication via `localmanus-network`
✅ **Host Access**: Both services accessible from host machine

## 🚀 Usage

### Start Services
```bash
docker-compose up -d
```

### Check Status
```bash
docker-compose ps
```

### View Logs
```bash
docker-compose logs -f
```

### Stop Services
```bash
docker-compose down
```

### Rebuild
```bash
docker-compose up -d --build
```

## 🔧 Configuration Checklist

Before deploying:

1. ✅ Copy `.env.docker.example` to `localmanus-backend/.env`
2. ✅ Set `OPENAI_API_KEY` in `.env`
3. ✅ Verify `MODEL_NAME` and `OPENAI_API_BASE`
4. ✅ Ensure `data/` directory exists (will be auto-created)
5. ✅ Run `docker-compose up -d`

## 📊 Resource Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 10GB free space

### Recommended
- **CPU**: 4 cores
- **RAM**: 8GB
- **Disk**: 50GB free space (for uploads)

## 🔒 Security Considerations

1. **Volume Permissions**: `data/` directory should have appropriate permissions
2. **Environment Variables**: Never commit `.env` to version control
3. **CORS**: Update `allow_origins` in production (not `["*"]`)
4. **API Keys**: Use environment variables, never hardcode
5. **Database**: SQLite file permissions set to user-only

## 📝 Next Steps

1. Configure reverse proxy (nginx/Caddy) for HTTPS
2. Set up automated backups for `data/` directory
3. Configure log rotation
4. Monitor disk usage for uploads
5. Set up CI/CD pipeline for automated deployments

## 🐛 Troubleshooting

### Backend won't start
```bash
docker-compose logs backend
# Check for missing .env or invalid configuration
```

### Frontend can't reach backend
```bash
# Verify backend is healthy
curl http://localhost:8000/api/health

# Check docker network
docker network inspect localmanus_localmanus-network
```

### Volume permission denied
```bash
# Fix ownership
sudo chown -R $USER:$USER data/
```

## 📚 Documentation

- Full guide: `DOCKER_DEPLOYMENT.md`
- API docs: http://localhost:8000/docs (when running)
- Frontend: http://localhost:3000
