# 🐳 LocalManus Docker Deployment

Complete containerized deployment for LocalManus AI Agent System.

## 📦 What's Included

- **Backend Service**: FastAPI + AgentScope AI agents
- **Frontend Service**: Next.js web interface
- **Persistent Storage**: Database + File uploads
- **Health Monitoring**: Automatic health checks
- **Network Isolation**: Internal Docker network

## 🎯 Quick Start

### 1. Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space

### 2. Setup

**Linux/Mac**:
```bash
chmod +x setup-docker.sh
./setup-docker.sh
```

**Windows**:
```cmd
setup-docker.bat
```

### 3. Configure

Edit `localmanus-backend/.env`:
```env
OPENAI_API_KEY=your_actual_api_key_here
MODEL_NAME=gpt-4
OPENAI_API_BASE=https://api.openai.com/v1
```

### 4. Deploy

```bash
docker-compose up -d
```

### 5. Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
LocalManus/
├── docker-compose.yml          # Service orchestration
├── data/                       # Persistent storage (auto-created)
│   ├── db/                    # SQLite database
│   └── uploads/               # User files
├── localmanus-backend/
│   ├── Dockerfile             # Backend container config
│   ├── .dockerignore          # Build exclusions
│   ├── .env                   # Configuration (create this!)
│   └── ...
├── localmanus-ui/
│   ├── Dockerfile             # Frontend container config
│   └── ...
├── setup-docker.sh            # Linux/Mac setup script
├── setup-docker.bat           # Windows setup script
└── DOCKER_DEPLOYMENT.md       # Full documentation
```

## 🔧 Service Configuration

### Backend (Port 8000)

**Volumes**:
- `./data/db:/app/db` - Database persistence
- `./data/uploads:/app/uploads` - File uploads
- `.env:/app/.env:ro` - Environment config

**Environment**:
- Model configuration from `.env`
- Database path
- Upload limits

**Health Check**:
- Endpoint: `/api/health`
- Interval: 30s
- Retries: 3

### Frontend (Port 3000)

**Depends On**: Backend health check passes

**Environment**:
- `NEXT_PUBLIC_API_URL=http://localhost:8000`

**Network**: Connected to backend via Docker network

## 🚀 Common Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View status
docker-compose ps
```

### Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f ui

# Last 100 lines
docker-compose logs --tail=100
```

### Rebuild

```bash
# After code changes
docker-compose build

# Rebuild and restart
docker-compose up -d --build

# Force rebuild (no cache)
docker-compose build --no-cache
```

### Maintenance

```bash
# Shell into backend
docker-compose exec backend bash

# Shell into frontend
docker-compose exec ui sh

# View resource usage
docker stats
```

## 💾 Data Management

### Backup

```bash
# Backup everything
tar -czf localmanus-backup-$(date +%Y%m%d).tar.gz data/

# Backup database only
cp -r data/db data/db-backup-$(date +%Y%m%d)

# Backup uploads only
cp -r data/uploads data/uploads-backup-$(date +%Y%m%d)
```

### Restore

```bash
# Stop services first
docker-compose down

# Restore from backup
tar -xzf localmanus-backup-YYYYMMDD.tar.gz

# Start services
docker-compose up -d
```

### Clean Up

```bash
# Remove stopped containers
docker-compose down

# Remove volumes (⚠️ DATA LOSS)
docker-compose down -v

# Clean up Docker system
docker system prune -a
```

## 🔍 Troubleshooting

### Backend Health Check Fails

```bash
# Check logs
docker-compose logs backend

# Check health directly
curl http://localhost:8000/api/health

# Inspect container
docker inspect localmanus-backend
```

### Frontend Can't Connect

1. Verify backend is healthy:
   ```bash
   docker-compose ps
   ```

2. Check API URL configuration:
   ```bash
   docker-compose exec ui env | grep API_URL
   ```

3. Test backend from frontend container:
   ```bash
   docker-compose exec ui wget -O- http://backend:8000/api/health
   ```

### Database Locked

```bash
# Check for stale processes
docker-compose ps

# Restart backend
docker-compose restart backend
```

### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Check data directory
du -sh data/

# Clean up unused images
docker image prune -a
```

### Permission Denied on Volumes

```bash
# Fix ownership (Linux/Mac)
sudo chown -R $USER:$USER data/

# Check permissions
ls -la data/
```

## 🔒 Security Best Practices

### 1. Environment Variables
- ✅ Never commit `.env` files
- ✅ Use strong, unique API keys
- ✅ Rotate secrets regularly

### 2. Network Security
- ✅ Update CORS origins (not `["*"]`)
- ✅ Use reverse proxy with HTTPS
- ✅ Configure firewall rules

### 3. File Permissions
- ✅ Restrict `data/` directory access
- ✅ Run containers as non-root (already configured)
- ✅ Validate uploaded files

### 4. Database Security
- ✅ Regular backups
- ✅ Encrypt sensitive data
- ✅ Monitor database size

## 📊 Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend availability
curl http://localhost:3000

# Container health status
docker inspect --format='{{.State.Health.Status}}' localmanus-backend
```

### Resource Usage

```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Data directory size
du -sh data/
```

### Logs Analysis

```bash
# Error logs
docker-compose logs | grep -i error

# Recent activity
docker-compose logs --since 1h

# Save logs to file
docker-compose logs > logs-$(date +%Y%m%d).txt
```

## 🌐 Production Deployment

### Recommended Setup

```
Internet
   ↓
[Nginx/Caddy] (HTTPS, SSL)
   ↓
[Docker Network]
   ├── Frontend (localhost:3000)
   └── Backend (localhost:8000)
        ↓
   [Persistent Volumes]
```

### Nginx Example

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_buffering off;  # Important for SSE streaming
        proxy_cache off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Automated Backups

```bash
# Add to crontab: daily backups at 2 AM
0 2 * * * cd /path/to/LocalManus && tar -czf backup-$(date +\%Y\%m\%d).tar.gz data/
```

## 📚 Additional Resources

- **Full Guide**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- **Setup Summary**: [DOCKER_SETUP_SUMMARY.md](DOCKER_SETUP_SUMMARY.md)
- **API Documentation**: http://localhost:8000/docs (when running)

## 🆘 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify configuration: Check `.env` file
3. Test health: `curl http://localhost:8000/api/health`
4. Review documentation: `DOCKER_DEPLOYMENT.md`

## 📝 License

See main project LICENSE file.
