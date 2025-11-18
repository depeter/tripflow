# TripFlow Docker Deployment Guide

This guide covers deploying TripFlow to the Scraparr server using Docker containers.

## Architecture

The production deployment uses Docker Compose with the following services:

- **tripflow-frontend** - React app served by nginx (port 3001)
  - Built using multi-stage Docker build
  - nginx serves static files and proxies API requests
  - Production build optimized for performance

- **tripflow-api** - FastAPI backend (internal port 8000)
  - Accessed through nginx reverse proxy at `/api/*`
  - Handles all business logic and database operations

- **tripflow-postgres** - PostgreSQL 14 with PostGIS (port 5433)
  - Persistent data storage for locations, trips, users
  - Schema: `tripflow`

- **tripflow-qdrant** - Vector database (ports 6333, 6334)
  - Semantic search for AI recommendations
  - Collection: `locations`

- **tripflow-redis** - Redis cache (port 6379)
  - Celery task queue backend

- **tripflow-celery-worker** - Celery worker
  - Background tasks (data sync, ETL)

- **tripflow-celery-beat** - Celery scheduler
  - Periodic task scheduling

## Network Configuration

All services run on a shared Docker network `tripflow-network` with the following external access:

- Frontend: http://192.168.1.149:3001
- API (through nginx): http://192.168.1.149:3001/api/v1
- API Docs: http://192.168.1.149:3001/docs
- PostgreSQL: localhost:5433 (from host only)
- Qdrant: localhost:6333, localhost:6334 (from host only)
- Redis: localhost:6379 (from host only)

## Deployment

### Quick Deploy

From your development machine:

```bash
cd /home/peter/work/tripflow
./deploy-docker-to-scraparr.sh
```

This script will:
1. Upload all necessary files to scraparr server
2. Build Docker images on the server
3. Start all containers with docker-compose
4. Run health checks
5. Display access URLs and useful commands

### Manual Deploy

If you prefer manual deployment:

```bash
# 1. Upload files
scp -r backend frontend docker-compose.production.yml migrations peter@scraparr:/home/peter/tripflow/

# 2. SSH to server
ssh peter@scraparr

# 3. Navigate to project
cd /home/peter/tripflow

# 4. Start containers
docker compose -f docker-compose.production.yml up -d --build

# 5. Check status
docker compose -f docker-compose.production.yml ps
```

## Configuration

### Environment Variables

Production environment variables are configured in `docker-compose.production.yml`:

**Backend:**
- `DATABASE_URL` - PostgreSQL connection (internal Docker network)
- `QDRANT_HOST=qdrant` - Qdrant service name
- `REDIS_URL=redis://redis:6379/0` - Redis service name
- `SECRET_KEY` - JWT signing key (override with environment variable)
- `DEBUG=False` - Production mode

**Frontend:**
- `REACT_APP_API_BASE_URL=` - Empty = use relative paths
- nginx proxies `/api/*` to backend service

### Volumes

Persistent data is stored in Docker volumes:

- `tripflow_postgres_data` - Database files
- `tripflow_qdrant_data` - Vector database storage
- `tripflow_redis_data` - Redis persistence

## Management Commands

### View Logs

```bash
# All services
ssh peter@scraparr 'cd /home/peter/tripflow && docker compose -f docker-compose.production.yml logs -f'

# Specific service
ssh peter@scraparr 'docker logs -f tripflow-api'
ssh peter@scraparr 'docker logs -f tripflow-frontend'
ssh peter@scraparr 'docker logs -f tripflow-postgres'
```

### Restart Services

```bash
# All services
ssh peter@scraparr 'cd /home/peter/tripflow && docker compose -f docker-compose.production.yml restart'

# Specific service
ssh peter@scraparr 'docker restart tripflow-api'
```

### Stop/Start Services

```bash
# Stop all
ssh peter@scraparr 'cd /home/peter/tripflow && docker compose -f docker-compose.production.yml down'

# Start all
ssh peter@scraparr 'cd /home/peter/tripflow && docker compose -f docker-compose.production.yml up -d'

# Rebuild and restart specific service
ssh peter@scraparr 'cd /home/peter/tripflow && docker compose -f docker-compose.production.yml up -d --build api'
```

### Database Access

```bash
# Connect to PostgreSQL
ssh peter@scraparr 'docker exec -it tripflow-postgres psql -U postgres -d tripflow'

# Run SQL file
ssh peter@scraparr 'docker exec -i tripflow-postgres psql -U postgres -d tripflow < /home/peter/tripflow/migrations/migration.sql'

# Backup database
ssh peter@scraparr 'docker exec tripflow-postgres pg_dump -U postgres tripflow > tripflow_backup.sql'
```

### Container Shell Access

```bash
# Backend container
ssh peter@scraparr 'docker exec -it tripflow-api /bin/bash'

# PostgreSQL container
ssh peter@scraparr 'docker exec -it tripflow-postgres /bin/bash'

# Frontend container
ssh peter@scraparr 'docker exec -it tripflow-frontend /bin/sh'
```

## Health Checks

All critical services have health checks configured:

- **Frontend**: nginx responds on port 80
- **Backend**: `/health` endpoint returns healthy status
- **PostgreSQL**: `pg_isready` check
- **Redis**: `redis-cli ping`

View health status:

```bash
ssh peter@scraparr 'cd /home/peter/tripflow && docker compose -f docker-compose.production.yml ps'
```

## Troubleshooting

### Frontend shows blank page

1. Check frontend container logs:
   ```bash
   ssh peter@scraparr 'docker logs tripflow-frontend'
   ```

2. Verify nginx is running:
   ```bash
   ssh peter@scraparr 'docker exec tripflow-frontend nginx -t'
   ```

3. Check if build succeeded:
   ```bash
   ssh peter@scraparr 'docker exec tripflow-frontend ls -la /usr/share/nginx/html'
   ```

### API requests fail (CORS errors)

1. Check nginx proxy configuration:
   ```bash
   ssh peter@scraparr 'docker exec tripflow-frontend cat /etc/nginx/conf.d/default.conf'
   ```

2. Verify backend is reachable from frontend container:
   ```bash
   ssh peter@scraparr 'docker exec tripflow-frontend wget -O- http://tripflow-api:8000/health'
   ```

3. Check CORS configuration in backend:
   ```bash
   ssh peter@scraparr 'docker logs tripflow-api | grep CORS'
   ```

### Database connection errors

1. Check PostgreSQL is running:
   ```bash
   ssh peter@scraparr 'docker exec tripflow-postgres pg_isready -U postgres'
   ```

2. Verify database exists:
   ```bash
   ssh peter@scraparr 'docker exec tripflow-postgres psql -U postgres -c "\l"'
   ```

3. Check connection from backend:
   ```bash
   ssh peter@scraparr 'docker exec tripflow-api python -c "from app.core.database import engine; print(engine)"'
   ```

### Container won't start

1. Check Docker logs:
   ```bash
   ssh peter@scraparr 'docker logs tripflow-api'
   ```

2. Verify dependencies started:
   ```bash
   ssh peter@scraparr 'docker compose -f docker-compose.production.yml ps'
   ```

3. Check resource usage:
   ```bash
   ssh peter@scraparr 'docker stats --no-stream'
   ```

### Out of disk space

1. Check disk usage:
   ```bash
   ssh peter@scraparr 'df -h'
   ```

2. Clean up unused images/containers:
   ```bash
   ssh peter@scraparr 'docker system prune -a'
   ```

3. Check volume sizes:
   ```bash
   ssh peter@scraparr 'docker system df -v'
   ```

## Updating the Application

### Update Backend Code

```bash
cd /home/peter/work/tripflow
# Make code changes...
./deploy-docker-to-scraparr.sh  # Redeploy
```

Or update only backend:

```bash
scp -r backend peter@scraparr:/home/peter/tripflow/
ssh peter@scraparr 'cd /home/peter/tripflow && docker compose -f docker-compose.production.yml up -d --build api'
```

### Update Frontend Code

```bash
cd /home/peter/work/tripflow
# Make code changes...
./deploy-docker-to-scraparr.sh  # Redeploy
```

Or update only frontend:

```bash
scp -r frontend peter@scraparr:/home/peter/tripflow/
ssh peter@scraparr 'cd /home/peter/tripflow && docker compose -f docker-compose.production.yml up -d --build frontend'
```

### Database Migrations

```bash
# Upload migration file
scp migrations/new_migration.sql peter@scraparr:/home/peter/tripflow/migrations/

# Run migration
ssh peter@scraparr 'docker exec -i tripflow-postgres psql -U postgres -d tripflow < /home/peter/tripflow/migrations/new_migration.sql'
```

## Monitoring

### Check Service Status

```bash
ssh peter@scraparr 'cd /home/peter/tripflow && docker compose -f docker-compose.production.yml ps'
```

### Resource Usage

```bash
ssh peter@scraparr 'docker stats'
```

### Network Connectivity

```bash
# Check which networks containers are on
ssh peter@scraparr 'docker network inspect tripflow-network'

# Test inter-container connectivity
ssh peter@scraparr 'docker exec tripflow-frontend ping tripflow-api'
```

## Security Considerations

**Production Checklist:**

- [ ] Change `SECRET_KEY` in docker-compose.production.yml
- [ ] Set `DEBUG=False` (already done)
- [ ] Configure CORS origins properly
- [ ] Use strong database passwords
- [ ] Enable HTTPS with reverse proxy (nginx on host)
- [ ] Set up firewall rules (limit port 3001 access)
- [ ] Regular security updates (`docker compose pull`)
- [ ] Backup database regularly
- [ ] Monitor logs for suspicious activity
- [ ] Implement rate limiting
- [ ] Enable Docker security scanning

## Backup and Restore

### Backup

```bash
# Database
ssh peter@scraparr 'docker exec tripflow-postgres pg_dump -U postgres tripflow > /tmp/tripflow_backup_$(date +%Y%m%d).sql'

# Qdrant data
ssh peter@scraparr 'docker exec tripflow-qdrant tar czf /tmp/qdrant_backup.tar.gz /qdrant/storage'

# Copy backups locally
scp peter@scraparr:/tmp/tripflow_backup_*.sql /home/peter/backups/
```

### Restore

```bash
# Restore database
scp /home/peter/backups/tripflow_backup.sql peter@scraparr:/tmp/
ssh peter@scraparr 'docker exec -i tripflow-postgres psql -U postgres -d tripflow < /tmp/tripflow_backup.sql'
```

## Performance Optimization

### Frontend

- Static assets cached for 1 year (in nginx.conf)
- Gzip compression enabled
- Production build minified and optimized

### Backend

- Gunicorn workers (configure in Dockerfile)
- Connection pooling for database
- Redis caching for frequent queries

### Database

```bash
# Check database performance
ssh peter@scraparr 'docker exec tripflow-postgres psql -U postgres -d tripflow -c "SELECT * FROM pg_stat_activity;"'

# Analyze tables
ssh peter@scraparr 'docker exec tripflow-postgres psql -U postgres -d tripflow -c "VACUUM ANALYZE;"'
```

## Next Steps

1. **Enable HTTPS**: Set up nginx reverse proxy on host with SSL
2. **Monitoring**: Add Prometheus + Grafana for metrics
3. **Logging**: Centralized logging with ELK stack
4. **Backups**: Automated daily backups with retention policy
5. **CI/CD**: GitHub Actions for automated deployments
6. **Load Balancing**: Multiple backend replicas if needed
7. **CDN**: Serve static assets from CDN

## Support

For issues or questions:
- Check logs first
- Review this documentation
- Inspect container health and network connectivity
- Test each service individually
