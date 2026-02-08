# Quick Start - Local Development Mode

Run LocalManus directly on your machine for fastest development iteration with hot reload.

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm

## Quick Start (Automated)

### Windows
```bash
start-local-dev.bat
```

### Linux/Mac
```bash
chmod +x start-local-dev.sh
./start-local-dev.sh
```

This script will:
1. ✅ Check prerequisites
2. ✅ Set up Python virtual environment
3. ✅ Install backend dependencies
4. ✅ Install frontend dependencies
5. ✅ Create environment files
6. ✅ Start both services

## Quick Start (Manual)

### 1. Backend

```bash
cd localmanus-backend

# Create virtual environment (first time)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies (first time)
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd localmanus-ui

# Install dependencies (first time)
npm install

# Run development server
npm run dev
```

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Environment Configuration

### Backend `.env`
Create `localmanus-backend/.env`:
```env
MODEL_NAME=gpt-4
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=http://localhost:11434/v1
AGENT_MEMORY_LIMIT=40
UPLOAD_SIZE_LIMIT=10485760
DATABASE_URL=sqlite:///./db/localmanus.db
```

### Frontend `.env.local`
Already created at `localmanus-ui/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
NODE_ENV=development
```

## Development Workflow

1. ✅ Start backend (one terminal)
2. ✅ Start frontend (another terminal)
3. ✅ Open http://localhost:3000
4. ✅ Make changes - hot reload works automatically!

## Stop Services

- Press `Ctrl+C` in each terminal window

## Advantages of Local Dev Mode

✅ **Fast Hot Reload** - Changes reflect immediately  
✅ **Easy Debugging** - Use IDE breakpoints  
✅ **No Docker Overhead** - Lower resource usage  
✅ **Direct Access** - Easy to inspect API responses  
✅ **Full IDE Support** - Autocomplete, type checking  

## Troubleshooting

### Port Already in Use

**Backend (port 8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Frontend (port 3000):**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

### Cannot Connect to Backend

1. Check backend is running: `curl http://localhost:8000/api/health`
2. Check `.env.local` has: `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Restart frontend after changing `.env.local`

### Module Not Found

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
npm install
```

### Hot Reload Not Working

**Frontend:**
```bash
rm -rf .next
npm run dev
```

**Backend:**
- Ensure using `--reload` flag
- Save the file
- Check for syntax errors

## Next Steps

- See [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) for comprehensive guide
- See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture
- See [NGINX_QUICKSTART.md](NGINX_QUICKSTART.md) for Docker deployment

## Comparison with Other Modes

| Feature | Local Dev | Docker Dev | Production |
|---------|-----------|------------|------------|
| Setup Time | Fast | Medium | Slow |
| Hot Reload | ✅ Yes | ❌ No | ❌ No |
| Debugging | ✅ Easy | ⚠️ Harder | ❌ Hard |
| Resource Usage | Low | Medium | Low |
| Nginx Testing | ❌ No | ✅ Yes | ✅ Yes |
| Production-like | ⚠️ Partial | ✅ Yes | ✅ Yes |
| **Best For** | **Development** | **Integration** | **Deployment** |

## Tips

1. **Keep terminals visible** - Watch for errors
2. **Use separate terminals** - One for backend, one for frontend
3. **Check console** - Browser console shows frontend errors
4. **Use API docs** - http://localhost:8000/docs for testing
5. **Restart on config changes** - Environment changes need restart

---

**Happy Coding! 🚀**

For detailed development guide, see: [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)
