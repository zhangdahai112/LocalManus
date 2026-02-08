# Production Configuration Summary

## ✅ Configuration Complete

Your Next.js application has been configured for production deployment to:
- **Server**: 47.121.183.184
- **Backend Port**: 1243
- **Frontend Port**: 3000

## 📦 Files Created/Modified

### 1. **next.config.ts**
- ✅ Configured environment variables
- ✅ Set standalone output for Docker
- ✅ Disabled image optimization
- ✅ Added server actions allowed origins
- ✅ Webpack fallbacks configured

### 2. **.env.production**
```env
NEXT_PUBLIC_API_URL=http://47.121.183.184:1243
BACKEND_URL=http://47.121.183.184:1243
NODE_ENV=production
```

### 3. **.env.local.example**
Template for local development

### 4. **PRODUCTION_DEPLOYMENT.md**
Complete deployment guide with:
- Deployment steps
- Network architecture
- Troubleshooting guide
- Security checklist
- Performance optimization

### 5. **deploy-production.sh**
Automated deployment script

## 🚀 Quick Deployment

### Method 1: Using Deployment Script (Recommended)

```bash
# Make script executable
chmod +x deploy-production.sh

# Run deployment
./deploy-production.sh
```

### Method 2: Manual Docker Deployment

```bash
# 1. Ensure .env is configured
cd localmanus-backend
cp .env.example .env
# Edit .env with your API keys

# 2. Update docker-compose.yml ports
# backend: ports: - "1243:8000"

# 3. Build and deploy
docker-compose build
docker-compose up -d

# 4. Check status
docker-compose ps
```

### Method 3: Manual Deployment

#### Backend
```bash
cd localmanus-backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 1243
```

#### Frontend
```bash
cd localmanus-ui
npm install
npm run build
npm start
```

## 🌐 Access Points

After deployment:

- **Frontend**: http://47.121.183.184:3000
- **Backend API**: http://47.121.183.184:1243
- **API Documentation**: http://47.121.183.184:1243/docs
- **Health Check**: http://47.121.183.184:1243/api/health

## 🔧 Environment Variables

### Browser Context (Client-Side)
```
NEXT_PUBLIC_API_URL=http://47.121.183.184:1243
```

### SSR Context (Server-Side)
```
BACKEND_URL=http://backend:8000  (Docker)
BACKEND_URL=http://47.121.183.184:1243  (Manual)
```

## 🎯 How It Works

The `getApiBaseUrl()` utility automatically detects context:

```typescript
export const getApiBaseUrl = (): string => {
  // Browser → http://47.121.183.184:1243
  if (typeof window !== 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://47.121.183.184:1243';
  }
  
  // SSR → http://backend:8000 (Docker) or http://47.121.183.184:1243
  return process.env.BACKEND_URL || 'http://47.121.183.184:1243';
};
```

## 📋 Pre-Deployment Checklist

- [ ] Update `localmanus-backend/.env` with API keys
- [ ] Verify server firewall allows ports 3000 and 1243
- [ ] Ensure Docker and Docker Compose are installed
- [ ] Create data directories (done by script)
- [ ] Update CORS settings in backend if needed

## 🔍 Verification

### 1. Check Backend Health
```bash
curl http://47.121.183.184:1243/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "localmanus-backend",
  "timestamp": "..."
}
```

### 2. Check Frontend
```bash
curl http://47.121.183.184:3000
```
Should return HTML of home page.

### 3. Check Docker Services
```bash
docker-compose ps
```
Both services should show "Up (healthy)"

## 🐛 Troubleshooting

### Frontend Can't Reach Backend

1. **Check backend is running**:
   ```bash
   curl http://47.121.183.184:1243/api/health
   ```

2. **Check environment variables**:
   ```bash
   docker-compose exec ui env | grep API_URL
   ```

3. **Check logs**:
   ```bash
   docker-compose logs backend
   docker-compose logs ui
   ```

### Port Already in Use

```bash
# Find process
sudo lsof -i :1243
sudo lsof -i :3000

# Kill process
sudo kill -9 <PID>
```

### Permission Issues

```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/
```

## 📊 Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f ui
```

### Resource Usage
```bash
# Docker stats
docker stats

# System resources
htop
```

## 🔄 Updates

### Update Code
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Update Dependencies

**Backend**:
```bash
docker-compose exec backend pip install -r requirements.txt
docker-compose restart backend
```

**Frontend**:
```bash
docker-compose exec ui npm install
docker-compose restart ui
```

## 🔒 Security

### Firewall Configuration
```bash
# Allow required ports
sudo ufw allow 3000/tcp
sudo ufw allow 1243/tcp

# Check status
sudo ufw status
```

### Update CORS (if needed)

Edit `localmanus-backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://47.121.183.184:3000",
        "http://your-domain.com"
    ],
    # ...
)
```

## 📝 Next Steps

1. ✅ Configuration files created
2. 🔄 Run `./deploy-production.sh` or deploy manually
3. 🧪 Test all endpoints
4. 🔐 Configure HTTPS (optional but recommended)
5. 📈 Set up monitoring
6. 💾 Configure automated backups

## 📚 Documentation

For detailed information, see:
- **PRODUCTION_DEPLOYMENT.md** - Complete deployment guide
- **DOCKER_DEPLOYMENT.md** - Docker-specific documentation
- **README_DOCKER.md** - Quick start guide

## 🆘 Support

If you encounter issues:
1. Check logs: `docker-compose logs -f`
2. Verify configuration files
3. Test health endpoints
4. Review documentation
