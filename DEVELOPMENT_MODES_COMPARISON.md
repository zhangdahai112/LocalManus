# Development Modes Comparison

## Quick Reference Chart

| Feature | Local Dev Mode | Docker Dev Mode | Production Mode |
|---------|----------------|-----------------|-----------------|
| **Setup Time** | ⚡ Fast (30s) | 🔨 Medium (2-3 min) | 🏗️ Slow (5+ min) |
| **Hot Reload** | ✅ Yes (instant) | ❌ No (rebuild needed) | ❌ No |
| **Debugging** | ✅ Easy (breakpoints) | ⚠️ Harder (logs only) | ❌ Hard |
| **Resource Usage** | 💚 Low | 💛 Medium | 💚 Low |
| **Nginx Testing** | ❌ No | ✅ Yes | ✅ Yes |
| **Production-like** | ⚠️ Partial | ✅ Yes | ✅ Yes |
| **Internet Required** | ⚠️ API only | ❌ No (after build) | ❌ No (after build) |
| **Port** | 3000, 8000 | 80 | 1243 |
| **Best For** | 🎯 **Development** | 🧪 **Testing** | 🚀 **Deployment** |

## Detailed Comparison

### Local Dev Mode ⭐ (Recommended for Development)

```
┌─────────────────────────────────────┐
│  Your Machine                       │
│                                     │
│  ┌─────────────┐  ┌──────────────┐ │
│  │  Backend    │  │  Frontend    │ │
│  │  (Python)   │  │  (Next.js)   │ │
│  │  :8000      │  │  :3000       │ │
│  └─────────────┘  └──────────────┘ │
│                                     │
│  Direct process execution           │
│  No containerization                │
└─────────────────────────────────────┘
```

**When to Use:**
- ✅ Writing new features
- ✅ Debugging issues
- ✅ Testing API changes
- ✅ Frontend development
- ✅ Quick iterations

**Pros:**
- ⚡ Instant hot reload
- 🐛 Easy debugging with IDE
- 💻 Low resource usage
- 🔄 Fast startup/restart
- 📊 Direct access to logs

**Cons:**
- ❌ No nginx testing
- ❌ Different from production
- ⚠️ Manual dependency management
- ⚠️ Need to manage two processes

**Setup:**
```bash
./start-local-dev.sh  # Linux/Mac
start-local-dev.bat   # Windows
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

---

### Docker Dev Mode 🐳

```
┌─────────────────────────────────────┐
│  Docker Host                        │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Nginx Container (:80)       │  │
│  └────────┬──────────────┬──────┘  │
│           │              │          │
│  ┌────────▼────────┐ ┌──▼────────┐ │
│  │  Backend        │ │  Frontend  │ │
│  │  Container      │ │  Container │ │
│  │  (:8000)        │ │  (:3000)   │ │
│  └─────────────────┘ └────────────┘ │
│                                     │
│  Internal Docker network            │
│  Volume-mounted data                │
└─────────────────────────────────────┘
```

**When to Use:**
- ✅ Testing nginx configuration
- ✅ Integration testing
- ✅ Before pushing to production
- ✅ Testing Docker setup
- ✅ Reproducing production issues

**Pros:**
- 🎯 Production-like environment
- 🔒 Isolated containers
- 🌐 Tests nginx routing
- 📦 Consistent environment
- 🔄 Easy to reset (down/up)

**Cons:**
- ❌ No hot reload (rebuild needed)
- 🐌 Slower iteration
- 💾 More resource intensive
- 🐛 Harder to debug
- ⏱️ Longer startup time

**Setup:**
```bash
docker-compose up -d
docker-compose logs -f
```

**Access:**
- Application: http://localhost (via nginx)

---

### Production Mode 🚀

```
┌─────────────────────────────────────┐
│  Production Server                  │
│  (47.121.183.184)                   │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Nginx Container (:1243)     │  │
│  └────────┬──────────────┬──────┘  │
│           │              │          │
│  ┌────────▼────────┐ ┌──▼────────┐ │
│  │  Backend        │ │  Frontend  │ │
│  │  (optimized)    │ │  (built)   │ │
│  └─────────────────┘ └────────────┘ │
│                                     │
│  Rate limiting enabled              │
│  Gzip compression                   │
│  Security headers                   │
│  Production builds                  │
└─────────────────────────────────────┘
```

**When to Use:**
- ✅ Production deployment
- ✅ Performance testing
- ✅ Final integration testing
- ✅ Demo environment
- ✅ Security testing

**Pros:**
- ⚡ Optimized builds
- 🔒 Security features (rate limit, headers)
- 🗜️ Compression enabled
- 📊 Production monitoring
- 🎯 Real-world testing

**Cons:**
- ❌ No hot reload
- ❌ Hard to debug
- 🐌 Slow rebuild
- 💰 Server resources needed

**Setup:**
```bash
./deploy-with-nginx.sh
# Choose option 2 (Production)
```

**Access:**
- Application: http://47.121.183.184:1243

---

## Workflow Examples

### Feature Development

```
1. Local Dev Mode
   └─→ Code → Hot Reload → Test → Repeat
   
2. Docker Dev Mode
   └─→ Test nginx routing → Integration test
   
3. Production Mode
   └─→ Deploy → Verify
```

### Bug Fixing

```
1. Local Dev Mode (if reproducible locally)
   └─→ Debug with breakpoints → Fix → Test
   
2. Docker Dev Mode (if environment-specific)
   └─→ Check logs → Fix → Rebuild → Test
   
3. Production Mode (if production-only)
   └─→ Check logs → Hotfix → Deploy
```

### Testing Strategy

```
Unit Tests → Local Dev Mode
  ↓
Integration Tests → Docker Dev Mode
  ↓
E2E Tests → Production Mode (staging)
  ↓
Deployment → Production Mode (live)
```

---

## Switching Between Modes

### Local → Docker

```bash
# Stop local services (Ctrl+C)
# Start Docker
docker-compose up -d
```

### Docker → Local

```bash
# Stop Docker
docker-compose down

# Start local
./start-local-dev.sh
```

### Dev → Production

```bash
# Stop dev services
docker-compose down

# Deploy production
./deploy-with-nginx.sh
```

---

## Command Reference

### Local Dev Mode

```bash
# Start (automated)
./start-local-dev.sh              # Linux/Mac
start-local-dev.bat               # Windows

# Start (manual)
# Terminal 1
cd localmanus-backend
source venv/bin/activate
uvicorn main:app --reload

# Terminal 2
cd localmanus-ui
npm run dev

# Stop
Ctrl+C in each terminal
```

### Docker Dev Mode

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose build --no-cache
docker-compose up -d

# Reset everything
docker-compose down -v
rm -rf data/*
docker-compose up -d
```

### Production Mode

```bash
# Start
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or use script
./deploy-with-nginx.sh  # Choose option 2

# View logs
docker-compose logs -f localmanus-nginx

# Stop
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Update
git pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Resource Usage Comparison

### Local Dev Mode
```
CPU:    ~5-10% (both processes)
RAM:    ~500MB (Python + Node)
Disk:   ~200MB (venv + node_modules)
Startup: ~30s
```

### Docker Dev Mode
```
CPU:    ~10-15% (3 containers)
RAM:    ~1.5GB (nginx + backend + frontend)
Disk:   ~1GB (images + volumes)
Startup: ~2-3 min
```

### Production Mode
```
CPU:    ~5-10% (optimized builds)
RAM:    ~1GB (3 containers)
Disk:   ~800MB (optimized images)
Startup: ~5+ min (initial build)
```

---

## Recommendation by Use Case

| Use Case | Recommended Mode | Why |
|----------|-----------------|-----|
| Daily development | **Local Dev** | Fast iteration, easy debug |
| API testing | **Local Dev** | Direct access to /docs |
| Frontend work | **Local Dev** | Instant hot reload |
| Backend work | **Local Dev** | Python debugging |
| Nginx config | **Docker Dev** | Test routing rules |
| Integration test | **Docker Dev** | Full stack testing |
| Pre-deployment test | **Docker Dev** | Production-like env |
| Production deploy | **Production** | Live environment |
| Demo/staging | **Production** | Optimized builds |

---

## Summary

**Use Local Dev Mode** (⭐ Default) when:
- You're actively coding
- You need fast feedback
- You want to debug easily

**Use Docker Dev Mode** when:
- You're testing nginx
- You need consistent environment
- You're preparing for deployment

**Use Production Mode** when:
- You're deploying to servers
- You need production features
- You're performance testing

**Pro Tip**: Start with Local Dev Mode for development, test with Docker Dev Mode before pushing, and deploy with Production Mode. This workflow gives you the best of all worlds! 🎯
