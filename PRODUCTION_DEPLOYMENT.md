# Production Deployment Configuration

## Server Information

- **API Base URL**: `http://47.121.183.184:1243`
- **Frontend Port**: `3000`
- **Backend Port**: `1243`

## Configuration Files

### 1. Next.js Configuration (`next.config.ts`)

The configuration includes:
- ✅ **Environment variables** for API URLs
- ✅ **Standalone output** for Docker deployment
- ✅ **Image optimization** disabled for containerized deployment
- ✅ **Server Actions** with allowed origins
- ✅ **Webpack fallbacks** for module resolution

### 2. Environment Files

#### Production (`.env.production`)
```env
NEXT_PUBLIC_API_URL=http://47.121.183.184:1243
BACKEND_URL=http://47.121.183.184:1243
NODE_ENV=production
```

#### Local Development (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
NODE_ENV=development
```

## Deployment Steps

### Option 1: Docker Deployment (Recommended)

#### 1. Update docker-compose.yml

```yaml
services:
  backend:
    ports:
      - "1243:8000"  # Map backend to port 1243
    environment:
      - MODEL_NAME=${MODEL_NAME}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_API_BASE=${OPENAI_API_BASE}

  ui:
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://47.121.183.184:1243
      - BACKEND_URL=http://backend:8000  # Internal Docker network
```

#### 2. Build and Deploy

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Option 2: Manual Deployment

#### Backend

```bash
cd localmanus-backend

# Install dependencies
pip install -r requirements.txt

# Run with uvicorn on port 1243
uvicorn main:app --host 0.0.0.0 --port 1243
```

#### Frontend

```bash
cd localmanus-ui

# Install dependencies
npm install

# Build for production
npm run build

# Start production server
npm start
```

## API URL Configuration Strategy

### Browser Context (Client-Side)
- Uses `NEXT_PUBLIC_API_URL`
- Value: `http://47.121.183.184:1243`
- Accessible from user's browser

### SSR Context (Server-Side)
- Uses `BACKEND_URL`
- Value: `http://backend:8000` (Docker) or `http://47.121.183.184:1243` (manual)
- Accessible from Next.js server

### How It Works

The `getApiBaseUrl()` utility automatically detects the execution context:

```typescript
// localmanus-ui/app/utils/api.ts
export const getApiBaseUrl = (): string => {
  // Browser context
  if (typeof window !== 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://47.121.183.184:1243';
  }
  
  // Server context (SSR)
  return process.env.BACKEND_URL || 'http://47.121.183.184:1243';
};
```

## Network Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Internet                          │
│                                                      │
│  User Browser                                        │
│      ↓                                               │
│  http://47.121.183.184:3000 (Frontend)              │
│      ↓                                               │
│  http://47.121.183.184:1243 (Backend API)           │
│                                                      │
└─────────────────────────────────────────────────────┘

Docker Internal Network:
┌─────────────────────────────────────────────────────┐
│  ui container                                        │
│    - Port 3000 exposed to host                      │
│    - SSR calls: http://backend:8000                 │
│      ↓                                               │
│  backend container                                   │
│    - Port 8000 (internal)                           │
│    - Port 1243 (exposed to host)                    │
└─────────────────────────────────────────────────────┘
```

## Firewall Configuration

Ensure the following ports are open on the server:

```bash
# Allow frontend access
sudo ufw allow 3000/tcp

# Allow backend API access
sudo ufw allow 1243/tcp

# Check firewall status
sudo ufw status
```

## Nginx Reverse Proxy (Optional)

For production, consider using Nginx as a reverse proxy:

```nginx
# /etc/nginx/sites-available/localmanus
server {
    listen 80;
    server_name your-domain.com;

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
        proxy_pass http://localhost:1243;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # For SSE streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }
}
```

Enable and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/localmanus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Environment Variables Summary

| Variable | Browser | SSR | Docker | Manual |
|----------|---------|-----|--------|--------|
| `NEXT_PUBLIC_API_URL` | ✅ | ❌ | `http://47.121.183.184:1243` | `http://47.121.183.184:1243` |
| `BACKEND_URL` | ❌ | ✅ | `http://backend:8000` | `http://47.121.183.184:1243` |

## Troubleshooting

### Frontend Can't Reach Backend

1. **Check backend is running**:
   ```bash
   curl http://47.121.183.184:1243/api/health
   ```

2. **Check environment variables**:
   ```bash
   # In frontend container
   docker-compose exec ui env | grep API_URL
   ```

3. **Check CORS settings** in `localmanus-backend/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://47.121.183.184:3000"],  # Update this
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### SSR Calls Failing

1. **Docker deployment**: Ensure `BACKEND_URL=http://backend:8000`
2. **Manual deployment**: Ensure `BACKEND_URL=http://47.121.183.184:1243`

### Port Already in Use

```bash
# Find process using port 1243
sudo lsof -i :1243

# Kill process
sudo kill -9 <PID>
```

## Health Checks

### Backend Health
```bash
curl http://47.121.183.184:1243/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "localmanus-backend",
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### Frontend Health
```bash
curl http://47.121.183.184:3000
```

Should return the HTML of the home page.

## Monitoring

### Docker Logs
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

### Resource Usage
```bash
# Docker stats
docker stats

# System resources
htop
```

## Backup and Restore

### Backup
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz \
  localmanus-backend/.env \
  localmanus-ui/.env.production \
  docker-compose.yml
```

### Restore
```bash
# Stop services
docker-compose down

# Restore data
tar -xzf backup-YYYYMMDD.tar.gz

# Restore configuration
tar -xzf config-backup-YYYYMMDD.tar.gz

# Start services
docker-compose up -d
```

## Security Checklist

- [ ] Change default passwords
- [ ] Use strong API keys
- [ ] Configure firewall rules
- [ ] Set up HTTPS with SSL certificates
- [ ] Regular backups configured
- [ ] Update CORS origins to specific domains
- [ ] Monitor logs for suspicious activity
- [ ] Keep dependencies up to date

## Performance Optimization

### Frontend
- ✅ Standalone output for minimal Docker image
- ✅ Image optimization disabled (handled by CDN)
- ✅ React strict mode enabled

### Backend
- Consider using Gunicorn with multiple workers
- Enable Redis for caching
- Use a CDN for static assets

### Database
- Regular vacuum for SQLite
- Consider PostgreSQL for production

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify environment variables
3. Test health endpoints
4. Review DOCKER_DEPLOYMENT.md for general Docker issues
