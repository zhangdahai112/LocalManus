# Nginx Reverse Proxy Configuration

## Architecture

```
Client Browser
    ↓
Nginx (Port 80/1243)
    ↓
    ├─→ /api/* → Backend (FastAPI on port 8000)
    └─→ /* → Frontend (Next.js SSR on port 3000)
```

## Configuration Files

- **`nginx.conf`**: Development configuration (port 80)
- **`nginx.prod.conf`**: Production configuration with optimizations (port 1243)

## Key Features

### API Routing
- All `/api/*` requests are forwarded to the backend service
- Rate limiting: 20 requests/second (burst: 50)
- Login endpoint: 5 requests/minute (burst: 3)
- Streaming support with buffering disabled
- 300s timeout for long-running operations

### Static Assets
- Next.js static files (`/_next/static/`) cached for 365 days
- Image optimization cached for 7 days
- Gzip compression enabled

### Security
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection enabled
- Connection limiting: 10 concurrent connections per IP

### Health Checks
- Nginx health: `http://localhost/health`
- Backend health: `http://localhost:8000/api/health`

## Usage

### Development (Port 80)
```bash
docker-compose up -d
```

Access: `http://localhost`

### Production (Port 1243)
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Access: `http://47.121.183.184:1243`

## Environment Variables

### Frontend (Browser Context)
- `NEXT_PUBLIC_API_URL`: Points to nginx (e.g., `http://localhost` or `http://47.121.183.184:1243`)

### Frontend (SSR Context)
- `BACKEND_URL`: Direct backend access via Docker network (`http://backend:8000`)

## URL Flow Examples

### API Request (Browser → Backend)
```
Browser: http://localhost/api/auth/login
    ↓
Nginx: proxy_pass http://backend/api/auth/login
    ↓
Backend: FastAPI receives /api/auth/login
```

### Page Request (Browser → SSR)
```
Browser: http://localhost/projects
    ↓
Nginx: proxy_pass http://frontend/projects
    ↓
Next.js SSR: Renders /projects page
    ↓ (SSR makes API call)
Next.js SSR: fetch('http://backend:8000/api/projects')
    ↓
Backend: Returns data
    ↓
Next.js SSR: Returns rendered HTML
    ↓
Browser: Receives HTML
```

## Logs

View nginx logs:
```bash
# Access logs
docker exec localmanus-nginx tail -f /var/log/nginx/access.log

# Error logs
docker exec localmanus-nginx tail -f /var/log/nginx/error.log
```

## Customization

### Change Rate Limits
Edit `nginx.conf` or `nginx.prod.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;
```

### Change Upload Size
```nginx
client_max_body_size 10M;
```

### Add HTTPS
Mount SSL certificates and update configuration:
```yaml
volumes:
  - ./nginx/ssl:/etc/nginx/ssl:ro
```

```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
}
```

## Troubleshooting

### 502 Bad Gateway
- Check if backend/frontend containers are running: `docker ps`
- Check logs: `docker logs localmanus-nginx`
- Verify health checks: `curl http://localhost/health`

### Rate Limiting (429 Too Many Requests)
- Adjust rate limit zones in nginx configuration
- Increase burst size for specific endpoints

### Timeout Errors (504 Gateway Timeout)
- Increase `proxy_read_timeout` for long operations
- Check backend performance

## Performance Tuning

- **Worker connections**: Adjust based on expected load
- **Keepalive connections**: Improves performance for persistent connections
- **Gzip compression**: Reduces bandwidth usage
- **Cache settings**: Optimize cache durations for your use case
