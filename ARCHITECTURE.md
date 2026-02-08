# LocalManus Architecture with Nginx

## Complete System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Internet / Client Browser                   │
│                                                                      │
│  Development:  http://localhost                                      │
│  Production:   http://47.121.183.184:1243                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Host (Port Mapping)                       │
│                                                                      │
│  Development:  80 → Nginx Container:80                              │
│  Production:   1243 → Nginx Container:80                            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Nginx Container                             │
│                      (localmanus-nginx)                              │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    nginx.conf / nginx.prod.conf              │    │
│  │                                                              │    │
│  │  Request Routing:                                           │    │
│  │    • /api/*           → http://backend:8000                 │    │
│  │    • /health          → http://backend:8000/api/health      │    │
│  │    • /_next/static/*  → http://frontend:3000 (cached)       │    │
│  │    • /*               → http://frontend:3000 (SSR)          │    │
│  │                                                              │    │
│  │  Features:                                                   │    │
│  │    • Rate limiting (20 req/s API, 5 req/m login)            │    │
│  │    • Gzip compression                                        │    │
│  │    • Security headers                                        │    │
│  │    • Static asset caching                                    │    │
│  └────────────────────────────────────────────────────────────┘    │
│                               │                                      │
│                    ┌──────────┴──────────┐                          │
└────────────────────┼────────────────────┼──────────────────────────┘
                     │                     │
                     ▼                     ▼
        ┌────────────────────┐  ┌──────────────────────┐
        │  Backend Container  │  │  Frontend Container   │
        │ (localmanus-backend)│  │  (localmanus-ui)      │
        │                     │  │                       │
        │  FastAPI App        │  │  Next.js 16 + SSR     │
        │  Port: 8000         │  │  Port: 3000           │
        │  (internal only)    │  │  (internal only)      │
        │                     │  │                       │
        │  Endpoints:         │  │  Pages:               │
        │  • /api/auth/*      │  │  • / (home)           │
        │  • /api/projects/*  │  │  • /projects          │
        │  • /api/settings/*  │  │  • /settings          │
        │  • /api/skills/*    │  │  • /skills            │
        │  • /api/health      │  │                       │
        │  • /docs            │  │  SSR API Calls:       │
        │                     │  │  • Uses BACKEND_URL   │
        │  Database:          │  │  • http://backend:8000│
        │  • SQLite           │  │                       │
        │  • /app/db/         │  │  Browser API Calls:   │
        │                     │  │  • Uses NEXT_PUBLIC_  │
        │  File Storage:      │  │    API_URL            │
        │  • /app/uploads/    │  │  • Via Nginx          │
        └──────┬──────────────┘  └──────────────────────┘
               │                           
               ▼                           
    ┌──────────────────────┐             
    │   Docker Volumes     │             
    │                      │             
    │  • ./data/db         │             
    │  • ./data/uploads    │             
    └──────────────────────┘             


                    Docker Internal Network
                    (localmanus-network)
```

## Request Flow Examples

### 1. API Request: User Login

```
Browser
  │ POST http://localhost/api/auth/login
  │ Body: {username, password}
  ▼
Nginx
  │ Rate limit check (5 req/m)
  │ proxy_pass http://backend:8000/api/auth/login
  ▼
Backend (FastAPI)
  │ Authenticate user
  │ Generate JWT token
  │ Return: {access_token, user_info}
  ▼
Nginx
  │ Forward response
  ▼
Browser
  │ Store token in localStorage
  └─ Redirect to dashboard
```

### 2. SSR Page Load: Projects Page

```
Browser
  │ GET http://localhost/projects
  ▼
Nginx
  │ proxy_pass http://frontend:3000/projects
  ▼
Next.js Server (SSR)
  │ Server-side rendering starts
  │ Need project data...
  │
  │ fetch('http://backend:8000/api/projects')
  │ Note: Uses BACKEND_URL (internal network)
  ▼
Backend (FastAPI)
  │ Query database
  │ Return: [{id, name, ...}, ...]
  ▼
Next.js Server (SSR)
  │ Render HTML with data
  │ Return: Complete HTML page
  ▼
Nginx
  │ Forward HTML response
  ▼
Browser
  │ Display rendered page
  └─ Hydrate React components
```

### 3. Static Asset: Next.js JavaScript

```
Browser
  │ GET http://localhost/_next/static/chunks/main.js
  ▼
Nginx
  │ Check cache (365 day TTL)
  │ If cached → return from cache
  │ If not cached:
  │   proxy_pass http://frontend:3000/_next/static/chunks/main.js
  │   Cache response
  │   Add header: Cache-Control: public, immutable
  ▼
Browser
  │ Execute JavaScript
  └─ Cache locally
```

### 4. Streaming Response: AI Agent

```
Browser
  │ POST http://localhost/api/chat/stream
  │ Body: {message: "Hello"}
  ▼
Nginx
  │ Rate limit check (20 req/s + burst 50)
  │ proxy_pass http://backend:8000/api/chat/stream
  │ proxy_buffering off (for streaming)
  ▼
Backend (FastAPI)
  │ Initialize AI agent
  │ Stream tokens: "Hello" → "!" → " How" → " can" → ...
  │ Each token sent immediately
  ▼
Nginx
  │ Forward each chunk immediately (no buffering)
  ▼
Browser
  │ Display tokens in real-time
  └─ Update UI progressively
```

## Environment Variable Flow

### Browser Context (Client-Side)

```javascript
// In Browser JavaScript
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
// → "http://localhost" (dev)
// → "http://47.121.183.184:1243" (prod)

fetch(`${apiUrl}/api/projects`)
  ↓
  Goes through Nginx
```

### SSR Context (Server-Side)

```javascript
// In Next.js Server (SSR)
const apiUrl = process.env.BACKEND_URL;
// → "http://backend:8000" (always internal network)

fetch(`${apiUrl}/api/projects`)
  ↓
  Direct to backend via Docker network
  (bypasses Nginx)
```

### Utility Function (getApiBaseUrl)

```typescript
// app/utils/api.ts
export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    // Browser: use Nginx
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost';
  }
  // SSR: use internal network
  return process.env.BACKEND_URL || 'http://backend:8000';
};
```

## Container Communication

```
┌──────────────────────────────────────────────────┐
│         localmanus-network (Bridge)               │
│                                                   │
│  ┌────────────┐    ┌───────────┐    ┌─────────┐ │
│  │   nginx    │───▶│  backend  │    │   ui    │ │
│  │ :80        │    │ :8000     │◀───│ :3000   │ │
│  └────────────┘    └───────────┘    └─────────┘ │
│        │                                   │      │
│        │          SSR API Call             │      │
│        └───────────────────────────────────┘      │
│                                                   │
│  Service Discovery:                               │
│    • http://nginx:80                              │
│    • http://backend:8000                          │
│    • http://ui:3000                               │
└──────────────────────────────────────────────────┘
```

## Port Mapping

| Service | Internal Port | External Port (Dev) | External Port (Prod) |
|---------|--------------|--------------------|--------------------|
| Nginx   | 80           | 80                 | 1243               |
| Backend | 8000         | None (via nginx)   | None (via nginx)   |
| UI      | 3000         | None (via nginx)   | None (via nginx)   |

## Health Check Flow

```
Docker
  │ Every 30s
  ▼
Nginx Container
  │ wget http://localhost/health
  ▼
Nginx
  │ proxy_pass http://backend:8000/api/health
  ▼
Backend
  │ Check: database, file system
  │ Return: {"status": "healthy"}
  ▼
Docker
  │ Mark nginx as healthy
  └─ Allow traffic
```

## Deployment Modes

### Development Mode
```bash
docker-compose up -d
```
- Port: 80
- Config: nginx/nginx.conf
- URL: http://localhost
- Features: Basic routing, simple rate limits

### Production Mode
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
- Port: 1243
- Config: nginx/nginx.prod.conf
- URL: http://47.121.183.184:1243
- Features: Advanced security, caching, compression, stricter limits

## File Structure

```
e:\LocalManus\
├── nginx/
│   ├── nginx.conf           # Development config
│   ├── nginx.prod.conf      # Production config
│   └── README.md            # Nginx documentation
│
├── localmanus-backend/
│   ├── Dockerfile
│   ├── main.py
│   ├── core/
│   ├── agents/
│   └── .env
│
├── localmanus-ui/
│   ├── Dockerfile
│   ├── next.config.ts
│   ├── app/
│   ├── .env.production
│   └── .env.local
│
├── data/
│   ├── db/                  # SQLite database
│   └── uploads/             # User uploaded files
│
├── docker-compose.yml       # Base configuration
├── docker-compose.prod.yml  # Production overrides
│
├── deploy-with-nginx.sh     # Linux/Mac deployment
├── deploy-with-nginx.bat    # Windows deployment
│
├── NGINX_QUICKSTART.md      # Quick start guide
├── NGINX_SETUP_SUMMARY.md   # Setup summary
└── ARCHITECTURE.md          # This file
```

## Security Layers

```
1. Rate Limiting (Nginx)
   └─ Prevents brute force, DDoS

2. Security Headers (Nginx)
   └─ XSS, clickjacking protection

3. Connection Limiting (Nginx)
   └─ Max 10 concurrent per IP

4. JWT Authentication (Backend)
   └─ Verified on each request

5. User Isolation (Backend)
   └─ Files scoped to user_id

6. Docker Network Isolation
   └─ Backend/UI not directly accessible
```

## Monitoring Points

```
1. Nginx Access Logs
   └─ docker logs localmanus-nginx
   └─ /var/log/nginx/access.log

2. Nginx Error Logs
   └─ /var/log/nginx/error.log

3. Backend Logs
   └─ docker logs localmanus-backend

4. Frontend Logs
   └─ docker logs localmanus-ui

5. Health Checks
   └─ curl http://localhost/health

6. Container Stats
   └─ docker stats
```

---

This architecture provides:
- ✅ Single entry point (Nginx)
- ✅ Production-ready security
- ✅ Optimized performance
- ✅ Easy scaling path
- ✅ Clean separation of concerns
