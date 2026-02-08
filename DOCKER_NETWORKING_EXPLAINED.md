# Docker Networking Architecture Explanation

## Current Setup Analysis

### ✅ **Why `NEXT_PUBLIC_API_URL=http://localhost:8000` is CORRECT**

The current configuration works because:

1. **All API calls are client-side** (browser-based fetch)
2. **No server-side rendering (SSR) API calls**
3. **Ports are exposed to host machine**

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                   Host Machine                       │
│                                                      │
│  ┌──────────────┐        ┌──────────────┐          │
│  │   Browser    │        │              │          │
│  │  (User)      │        │   Docker     │          │
│  └──────┬───────┘        │   Network    │          │
│         │                │              │          │
│         │ http://localhost:3000         │          │
│         ▼                │              │          │
│  ┌──────────────┐        │  ┌────────┐ │          │
│  │  Port 3000   ├────────┼──► ui     │ │          │
│  └──────────────┘        │  └────────┘ │          │
│         │                │      │      │          │
│         │ http://localhost:8000 │      │          │
│         ▼                │      ▼      │          │
│  ┌──────────────┐        │  ┌────────┐ │          │
│  │  Port 8000   ├────────┼──► backend│ │          │
│  └──────────────┘        │  └────────┘ │          │
│                          │              │          │
└─────────────────────────────────────────────────────┘
```

## Request Flow

### Client-Side API Call (Current)

```javascript
// In browser (localmanus-ui/app/page.tsx)
fetch('http://localhost:8000/api/chat')

// Flow:
// 1. Browser makes request
// 2. Host machine OS routes to localhost:8000
// 3. Docker port mapping forwards to backend container
// 4. Backend responds
// ✅ WORKS PERFECTLY
```

### Server-Side API Call (If Implemented)

```javascript
// In Next.js server component or API route
fetch('http://localhost:8000/api/chat')

// Flow:
// 1. Next.js server (inside ui container) makes request
// 2. Container's localhost:8000 ← NOT THE BACKEND!
// 3. Request fails
// ❌ WOULD NOT WORK

// Solution: Use Docker service name
fetch('http://backend:8000/api/chat')

// Flow:
// 1. Next.js server (inside ui container) makes request
// 2. Docker network routes 'backend' to backend container
// 3. Backend responds
// ✅ WORKS
```

## When Configuration Needs to Change

### Scenario 1: Adding SSR/Server Components

If you add server-side API calls in Next.js:

```typescript
// app/dashboard/page.tsx (server component)
async function getData() {
  // ❌ WRONG in SSR
  const res = await fetch('http://localhost:8000/api/data');
  
  // ✅ CORRECT in SSR
  const apiUrl = process.env.INTERNAL_API_URL || 'http://backend:8000';
  const res = await fetch(`${apiUrl}/api/data`);
  
  return res.json();
}
```

**docker-compose.yml update needed**:
```yaml
ui:
  environment:
    - NEXT_PUBLIC_API_URL=http://localhost:8000  # For client
    - INTERNAL_API_URL=http://backend:8000       # For SSR
```

### Scenario 2: Production Deployment with Domain

When deploying to production with a domain:

```yaml
ui:
  environment:
    - NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

Browser requests go to your public domain.

### Scenario 3: Different Host Port

If backend runs on a different port:

```yaml
backend:
  ports:
    - "8080:8000"  # Host:Container

ui:
  environment:
    - NEXT_PUBLIC_API_URL=http://localhost:8080  # Updated!
```

## Current Implementation Verification

### ✅ Confirmed Client-Side Only

All API calls in the codebase are client-side:
- `app/page.tsx` - fetch in event handlers ✅
- `app/components/Omnibox.tsx` - fetch in event handlers ✅
- `app/components/UserStatus.tsx` - fetch in event handlers ✅
- `app/components/Sidebar.tsx` - fetch in useEffect ✅
- `app/projects/page.tsx` - fetch in event handlers ✅
- `app/settings/page.tsx` - fetch in event handlers ✅
- `app/skills/page.tsx` - fetch in event handlers ✅

No server components or API routes making backend calls.

## Best Practices

### For Development

```bash
# docker-compose.yml
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### For Production

```bash
# Use environment variable override
NEXT_PUBLIC_API_URL=https://api.production.com docker-compose up -d

# Or update docker-compose.prod.yml
NEXT_PUBLIC_API_URL=${API_URL:-https://api.production.com}
```

### For SSR Support (Future)

Create a utility function:

```typescript
// lib/api.ts
export function getApiUrl() {
  // Server-side: use Docker service name
  if (typeof window === 'undefined') {
    return process.env.INTERNAL_API_URL || 'http://backend:8000';
  }
  // Client-side: use public URL
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

// Usage
const response = await fetch(`${getApiUrl()}/api/chat`);
```

## Summary

| Context | URL | Reason |
|---------|-----|--------|
| **Browser → Backend** | `http://localhost:8000` | ✅ Exposed port on host |
| **ui container → Backend** | `http://backend:8000` | ✅ Docker service name |
| **Current App** | `http://localhost:8000` | ✅ All calls are client-side |

**Conclusion**: The current configuration is **CORRECT** for the current architecture where all API calls are client-side (browser-based). No changes needed unless SSR is added.
