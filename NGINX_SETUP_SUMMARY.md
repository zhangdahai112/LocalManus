# Nginx Configuration Summary

## What Was Done

Added Nginx reverse proxy to the LocalManus docker-compose setup for unified API routing and SSR support.

## Files Created/Modified

### Created Files (7)

1. **`nginx/nginx.conf`** (69 lines)
   - Development configuration
   - Port: 80
   - Basic routing and rate limiting

2. **`nginx/nginx.prod.conf`** (110 lines)
   - Production configuration
   - Port: 1243 via docker-compose.prod.yml
   - Advanced features: gzip, security headers, optimized caching
   - Rate limits: 20 req/s API, 5 req/m login

3. **`nginx/README.md`** (155 lines)
   - Comprehensive nginx documentation
   - Architecture diagrams
   - Configuration examples
   - Troubleshooting guide

4. **`docker-compose.prod.yml`** (26 lines)
   - Production overrides
   - Nginx port mapping to 1243
   - Production environment variables

5. **`deploy-with-nginx.sh`** (185 lines)
   - Linux/Mac deployment script
   - Interactive mode selection
   - Health checks

6. **`deploy-with-nginx.bat`** (180 lines)
   - Windows deployment script
   - Same features as shell script

7. **`NGINX_QUICKSTART.md`** (280 lines)
   - Quick start guide
   - Migration instructions
   - Common troubleshooting

### Modified Files (1)

1. **`docker-compose.yml`**
   - Added nginx service with health checks
   - Changed backend to `expose` instead of `ports`
   - Changed ui to `expose` instead of `ports`
   - Updated NEXT_PUBLIC_API_URL to point to nginx

## Architecture

```
Client Browser
    ↓
Nginx (localhost:80 or 47.121.183.184:1243)
    ↓
    ├─→ /api/*  → Backend (FastAPI on internal port 8000)
    └─→ /*      → Frontend (Next.js SSR on internal port 3000)
```

## Key Features

### Routing
- `/api/*` → Backend service
- `/health` → Backend health check
- `/_next/static/*` → Frontend static assets (cached 365 days)
- `/*` → Frontend SSR

### Security
- Rate limiting on API endpoints
- Stricter rate limiting on login endpoints
- Security headers (XSS, frame options, content type)
- Connection limiting

### Performance
- Gzip compression
- Static asset caching
- Keepalive connections to backend/frontend
- Proxy buffering disabled for streaming

### Reliability
- Health checks for all services
- Automatic restart on failure
- Proper startup order (nginx waits for backend health)

## Usage

### Development Mode
```bash
docker-compose up -d
```
Access: `http://localhost`

### Production Mode
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
Access: `http://47.121.183.184:1243`

### Using Deployment Scripts
```bash
# Linux/Mac
./deploy-with-nginx.sh

# Windows
deploy-with-nginx.bat
```

## Environment Variables

### Before (Direct Access)
```env
# Frontend needed to know backend port
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### After (Via Nginx)
```env
# Frontend just uses nginx (no port needed for :80)
NEXT_PUBLIC_API_URL=http://localhost

# SSR still uses internal Docker network
BACKEND_URL=http://backend:8000
```

## Benefits

1. **Unified Entry Point**: Single URL for all services
2. **Production Ready**: Rate limiting, security headers, compression
3. **Scalable**: Ready for load balancing and multiple backends
4. **Secure**: Rate limits protect against abuse
5. **Fast**: Caching and compression reduce bandwidth
6. **Maintainable**: Centralized routing configuration

## Migration from Previous Setup

### What Changed
- **Before**: Backend on port 8000, Frontend on port 3000
- **After**: Everything through nginx on port 80 (dev) or 1243 (prod)

### What Stayed the Same
- All API endpoints (same paths)
- Frontend routes (same paths)
- Backend code (no changes)
- Frontend code (already uses getApiBaseUrl())

### Migration Steps
1. Pull latest code
2. Run `docker-compose down` (stop old setup)
3. Run `./deploy-with-nginx.sh` (start new setup)
4. Update bookmarks from `:8000` to nginx port

## Configuration Files Explained

| File | Port | Use Case |
|------|------|----------|
| `nginx.conf` | 80 | Local development |
| `nginx.prod.conf` | 1243 | Production deployment |
| `docker-compose.yml` | 80 | Base configuration |
| `docker-compose.prod.yml` | 1243 | Production overrides |

## Customization

### Change Ports
Edit `docker-compose.prod.yml`:
```yaml
nginx:
  ports:
    - "YOUR_PORT:80"
```

### Adjust Rate Limits
Edit `nginx/nginx.prod.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=YOUR_RATE;
```

### Add HTTPS
1. Mount SSL certs in nginx container
2. Update nginx config to listen on 443
3. Add SSL certificate paths

## Testing

### Health Checks
```bash
curl http://localhost/health
```

### API Test
```bash
curl http://localhost/api/health
```

### Frontend Test
```bash
curl http://localhost/
```

### View Logs
```bash
docker logs localmanus-nginx
docker logs localmanus-backend
docker logs localmanus-ui
```

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| 502 Bad Gateway | Backend not running | Check `docker ps` and `docker logs localmanus-backend` |
| 429 Too Many Requests | Rate limit hit | Wait or increase limit in nginx config |
| 504 Gateway Timeout | Backend slow | Check backend logs, increase timeout |

## Next Steps

1. ✅ Configuration complete
2. ⏭️ Test deployment: `./deploy-with-nginx.sh`
3. ⏭️ Verify all endpoints work
4. ⏭️ Deploy to production server
5. ⏭️ Monitor logs for issues

## Resources

- Detailed documentation: `nginx/README.md`
- Quick start guide: `NGINX_QUICKSTART.md`
- Production deployment: `PRODUCTION_DEPLOYMENT.md`
- Docker compose reference: `docker-compose.yml`

---

**Summary**: Nginx now handles all routing, providing a production-ready setup with security, performance, and scalability features built in.
