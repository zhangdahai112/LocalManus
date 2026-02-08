# LocalManus Nginx Configuration Quick Start

## Overview

The application now uses **Nginx as a reverse proxy** to route requests:
- **API requests** (`/api/*`) → Backend (FastAPI)
- **All other requests** → Frontend (Next.js SSR)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Browser                       │
│                              ↓                               │
│                     http://localhost (port 80)               │
│                   or http://47.121.183.184:1243              │
└─────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                      Nginx Container                         │
│                                                              │
│  /api/*        →  Backend Container (port 8000)             │
│  /health       →  Backend Container (port 8000)             │
│  /*            →  Frontend Container (port 3000)            │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Development Mode (Port 80)

```bash
# Linux/Mac
./deploy-with-nginx.sh
# Choose option 1

# Windows
deploy-with-nginx.bat
# Choose option 1
```

**Access**: `http://localhost`

### Production Mode (Port 1243)

```bash
# Linux/Mac
./deploy-with-nginx.sh
# Choose option 2

# Windows
deploy-with-nginx.bat
# Choose option 2
```

**Access**: `http://47.121.183.184:1243`

## Manual Deployment

### Start Services

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Stop Services

```bash
# Development
docker-compose down

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
```

## Configuration Files

| File | Purpose | Port |
|------|---------|------|
| `nginx/nginx.conf` | Development config | 80 |
| `nginx/nginx.prod.conf` | Production config | 1243 |
| `docker-compose.yml` | Base config | 80 |
| `docker-compose.prod.yml` | Production override | 1243 |

## Key Changes from Previous Setup

### Before (Direct Access)
```
Browser → Backend (http://localhost:8000/api/*)
Browser → Frontend (http://localhost:3000)
```

### After (Via Nginx)
```
Browser → Nginx (http://localhost) → Backend (/api/*)
Browser → Nginx (http://localhost) → Frontend (/*)
```

## Environment Variables

### Frontend (Browser Context)
```env
NEXT_PUBLIC_API_URL=http://localhost          # Development
NEXT_PUBLIC_API_URL=http://47.121.183.184:1243  # Production
```

### Frontend (SSR Context)
```env
BACKEND_URL=http://backend:8000  # Always uses Docker internal network
```

## Benefits of Nginx

✅ **Single Entry Point**: Access everything via one URL
✅ **Rate Limiting**: Protect API from abuse (20 req/s, login 5 req/m)
✅ **Caching**: Static assets cached for performance
✅ **Security Headers**: XSS, frame options, content type protection
✅ **Load Balancing**: Ready for scaling (keepalive connections)
✅ **Compression**: Gzip enabled for bandwidth savings

## Troubleshooting

### 502 Bad Gateway
```bash
# Check if services are running
docker ps

# Check nginx logs
docker logs localmanus-nginx

# Check backend health
curl http://localhost/health
```

### 429 Too Many Requests
You've hit the rate limit. Wait a moment or adjust limits in `nginx/nginx.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;
```

### 504 Gateway Timeout
Backend is taking too long. Check backend logs:
```bash
docker logs localmanus-backend
```

Adjust timeout in nginx config:
```nginx
proxy_read_timeout 300s;
```

## Monitoring

### View All Logs
```bash
docker-compose logs -f
```

### View Specific Service Logs
```bash
docker logs -f localmanus-nginx
docker logs -f localmanus-backend
docker logs -f localmanus-ui
```

### Check Service Status
```bash
docker-compose ps
```

### Check Health
```bash
# Via nginx
curl http://localhost/health

# Direct backend (only in development)
curl http://localhost:8000/api/health
```

## Customization

### Change Nginx Port (Production)

Edit `docker-compose.prod.yml`:
```yaml
nginx:
  ports:
    - "1243:80"  # Change 1243 to desired port
```

### Enable HTTPS

1. Obtain SSL certificate
2. Mount certificate in nginx:
```yaml
volumes:
  - ./nginx/ssl:/etc/nginx/ssl:ro
```
3. Update `nginx.prod.conf`:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
}
```

### Adjust Rate Limits

Edit `nginx/nginx.prod.conf`:
```nginx
# API rate limit: 20 requests per second
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;

# Login rate limit: 5 requests per minute
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
```

## Migration Guide

### From Old Setup (No Nginx)

1. **Stop existing services**:
   ```bash
   docker-compose down
   ```

2. **Pull latest changes** (this already includes nginx)

3. **Deploy with nginx**:
   ```bash
   ./deploy-with-nginx.sh
   ```

4. **Update bookmarks**: Change from `http://localhost:8000` to `http://localhost`

### No Code Changes Required!

The frontend already uses `getApiBaseUrl()` which automatically works with nginx. No changes needed to your application code.

## Files Created

```
nginx/
├── nginx.conf              # Development config (port 80)
├── nginx.prod.conf         # Production config (port 1243)
└── README.md              # Detailed nginx documentation

docker-compose.yml          # Updated with nginx service
docker-compose.prod.yml     # Production overrides

deploy-with-nginx.sh        # Linux/Mac deployment script
deploy-with-nginx.bat       # Windows deployment script
```

## Next Steps

1. ✅ Review nginx configuration in `nginx/nginx.conf`
2. ✅ Test deployment: `./deploy-with-nginx.sh`
3. ✅ Access application: `http://localhost`
4. ✅ Check logs: `docker-compose logs -f`
5. ✅ Deploy to production when ready

## Support

For detailed nginx configuration options, see: `nginx/README.md`
For deployment details, see: `PRODUCTION_DEPLOYMENT.md`

---

**Quick Reference**:
- Development URL: `http://localhost`
- Production URL: `http://47.121.183.184:1243`
- Health Check: `http://localhost/health`
- API Docs: `http://localhost/api/docs`
