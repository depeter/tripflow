# Tripflow Production Deployment Guide

## Overview

Tripflow uses a **Docker-based deployment** system that builds images on the target server and uses volume mounts for data persistence.

## Architecture

- **7 Docker containers** orchestrated with Docker Compose:
  - `tripflow-postgres` - PostgreSQL 14 with PostGIS
  - `tripflow-qdrant` - Vector database for AI recommendations
  - `tripflow-redis` - Cache and Celery broker
  - `tripflow-api` - FastAPI backend
  - `tripflow-celery-worker` - Background task processor
  - `tripflow-celery-beat` - Task scheduler
  - `tripflow-frontend` - React app served by nginx

- **Data persistence** via volume mounts to `/home/peter/tripflow-data/`
  - Database files survive container rebuilds
  - No data loss on redeployment

## Deployment Process

### Single Command Deployment

```bash
cd /home/peter/work/tripflow
./deploy.sh
```

This automated script:
1. Transfers source files to scraparr server
2. Builds Docker images ON the server (avoids local disk space issues)
3. Stops all old processes and containers
4. Starts fresh containers with new code
5. Runs health checks
6. Cleans up old artifacts
7. Tests external access

### What Gets Deployed

**On Scraparr Server (192.168.1.149):**
- Frontend: http://192.168.1.149:3002
- Backend API: http://192.168.1.149:3002/api/*
- API Docs: http://192.168.1.149:3002/docs
- Health Check: http://192.168.1.149:3002/health

**Port Allocations:**
- 3002: Frontend (nginx)
- 5433: PostgreSQL
- 6333-6334: Qdrant
- 6379: Redis
- Backend runs inside container on port 8000 (proxied by nginx)

## Key Files

### Production Configuration

**docker-compose.production.yml**
- Defines all 7 services
- Volume mounts: `/home/peter/tripflow-data/{postgres,qdrant,redis}`
- Network: `tripflow-network`
- Health checks for all services
- Restart policy: `unless-stopped`

**frontend/nginx.conf**
- Serves React static files
- Proxies `/api/*` to backend container
- Proxies `/health` and `/docs` to backend
- Gzip compression
- Cache headers for static assets

**deploy.sh**
- Automated deployment script
- Builds images on server (NOT locally)
- Handles cleanup and health checks
- No manual steps required

## Important: Do NOT Use These Approaches

❌ **WRONG: Building images locally and transferring**
- Causes disk space issues (development machine has limited space)
- Large image files to transfer

❌ **WRONG: Manual uvicorn/http.server processes**
- Not managed by Docker
- Don't restart automatically
- Conflict with container ports

❌ **WRONG: Deploying without volume mounts**
- Database resets on every deployment
- Data loss

❌ **WRONG: Using docker save/load**
- Unnecessary complexity
- Takes more time
- Uses more disk space

## Correct Deployment Pattern

✅ **Build on server, not locally**
```bash
# In deploy.sh on scraparr server
cd /home/peter/tripflow-build
docker build -t tripflow-api:latest ./backend
docker build -t tripflow-frontend:latest ./frontend
```

✅ **Use volume mounts for data**
```yaml
volumes:
  - /home/peter/tripflow-data/postgres:/var/lib/postgresql/data
```

✅ **Single docker-compose file**
```bash
docker compose -f docker-compose.production.yml up -d
```

✅ **nginx proxy in frontend container**
```nginx
location /api/ {
    proxy_pass http://tripflow-api:8000/api/;
}
```

## Management Commands

### View Logs
```bash
# All services
ssh peter@scraparr 'docker compose -f /home/peter/docker-compose.production.yml logs -f'

# Specific service
ssh peter@scraparr 'docker logs -f tripflow-api'
ssh peter@scraparr 'docker logs -f tripflow-frontend'
```

### Restart Services
```bash
# All services
ssh peter@scraparr 'docker compose -f /home/peter/docker-compose.production.yml restart'

# Specific service
ssh peter@scraparr 'docker restart tripflow-api'
```

### Stop All Services
```bash
ssh peter@scraparr 'docker compose -f /home/peter/docker-compose.production.yml down'
```

### Start Services
```bash
ssh peter@scraparr 'docker compose -f /home/peter/docker-compose.production.yml up -d'
```

### Check Status
```bash
ssh peter@scraparr 'docker compose -f /home/peter/docker-compose.production.yml ps'
```

## Data Persistence

Data is stored in `/home/peter/tripflow-data/` on scraparr server:
- `postgres/` - PostgreSQL database files
- `qdrant/` - Vector database
- `redis/` - Redis persistence

**These directories persist across deployments** - containers can be rebuilt without data loss.

## Troubleshooting

### Frontend Not Accessible
```bash
# Check nginx logs
ssh peter@scraparr 'docker logs tripflow-frontend'

# Test from inside server
ssh peter@scraparr 'curl http://localhost:80'
```

### Backend Not Responding
```bash
# Check API logs
ssh peter@scraparr 'docker logs tripflow-api'

# Check if container is running
ssh peter@scraparr 'docker ps | grep tripflow-api'

# Test health endpoint
ssh peter@scraparr 'docker exec tripflow-api curl http://localhost:8000/health'
```

### Database Connection Issues
```bash
# Check postgres is running
ssh peter@scraparr 'docker ps | grep tripflow-postgres'

# Check database logs
ssh peter@scraparr 'docker logs tripflow-postgres'

# Connect to database
ssh peter@scraparr 'docker exec -it tripflow-postgres psql -U postgres -d tripflow'
```

### Port Conflicts
If you see "port already allocated":
```bash
# Find what's using the port
ssh peter@scraparr 'ss -tlnp | grep <PORT>'

# Stop the conflicting service
ssh peter@scraparr 'docker stop <container_name>'
```

## Deployment Checklist

Before running `./deploy.sh`:
- [ ] All code changes committed locally
- [ ] Tests passing locally
- [ ] No pending migrations
- [ ] Frontend builds successfully (`npm run build` in frontend/)
- [ ] Backend requirements.txt up to date

After deployment:
- [ ] Frontend loads at http://192.168.1.149:3002
- [ ] Health check returns healthy: http://192.168.1.149:3002/health
- [ ] API docs accessible: http://192.168.1.149:3002/docs
- [ ] Database data persisted (check for existing records)
- [ ] Check logs for errors

## Common Issues and Solutions

### Issue: Build fails with "No space left on device"
**Solution:** Clean up Docker on the build server
```bash
ssh peter@scraparr 'docker system prune -af --volumes'
ssh peter@scraparr 'docker builder prune -af'
```

### Issue: Containers keep restarting
**Solution:** Check logs for the failing container
```bash
ssh peter@scraparr 'docker logs <container_name>'
```

### Issue: Database schema changes not applied
**Solution:** Run migrations inside the API container
```bash
ssh peter@scraparr 'docker exec tripflow-api alembic upgrade head'
```

### Issue: Frontend shows old version
**Solution:** Hard refresh browser (Ctrl+Shift+R) or clear browser cache

## Production vs Development

**Development (Local):**
- Uses `docker-compose.yml`
- Volume mounts to local source code for hot-reload
- Debug mode enabled
- Ports: 3000 (frontend), 8000 (backend)

**Production (Scraparr):**
- Uses `docker-compose.production.yml`
- No source code mounts (built into images)
- Debug mode disabled
- Ports: 3002 (nginx serving both frontend and API)
- Data persisted to `/home/peter/tripflow-data/`

## Future Improvements

- [ ] Add automated health monitoring
- [ ] Set up log rotation
- [ ] Add database backup automation
- [ ] Configure SSL/HTTPS with Let's Encrypt
- [ ] Add CI/CD pipeline for automated deployments
- [ ] Set up monitoring/alerting (Prometheus + Grafana)

## Last Updated

2025-11-17 - Initial deployment system established
