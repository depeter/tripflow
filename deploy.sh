#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 TripFlow Production Deployment Script${NC}"
echo "=========================================="

# Configuration
SERVER="peter@scraparr"
SERVER_IP="192.168.1.149"
WORK_DIR="/home/peter/work/tripflow"

# Create SSH password helper
cat > /tmp/scraparr_pass.sh << 'EOF'
#!/bin/sh
echo "nomansland"
EOF
chmod +x /tmp/scraparr_pass.sh

# Step 1: Transfer source files to server
echo -e "\n${YELLOW}📤 Step 1: Transferring source files to scraparr server...${NC}"

SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  ssh $SERVER "mkdir -p /home/peter/tripflow-build"

# Transfer backend
echo "Transferring backend..."
SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  scp -r $WORK_DIR/backend/app \
         $WORK_DIR/backend/requirements.txt \
         $WORK_DIR/backend/Dockerfile \
         $SERVER:/home/peter/tripflow-build/backend/

# Transfer frontend
echo "Transferring frontend..."
SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  scp -r $WORK_DIR/frontend/src \
         $WORK_DIR/frontend/public \
         $WORK_DIR/frontend/package.json \
         $WORK_DIR/frontend/package-lock.json \
         $WORK_DIR/frontend/Dockerfile \
         $WORK_DIR/frontend/nginx.conf \
         $WORK_DIR/frontend/next.config.mjs \
         $WORK_DIR/frontend/tsconfig.json \
         $WORK_DIR/frontend/tailwind.config.ts \
         $WORK_DIR/frontend/postcss.config.mjs \
         $SERVER:/home/peter/tripflow-build/frontend/

# Transfer docker-compose
echo "Transferring docker-compose.production.yml..."
SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  scp $WORK_DIR/docker-compose.production.yml \
      $SERVER:/home/peter/

# Step 2: Build and deploy on server
echo -e "\n${YELLOW}🔧 Step 2: Building and deploying on scraparr server...${NC}"

SSH_ASKPASS=/tmp/scraparr_pass.sh DISPLAY=:0 SSH_ASKPASS_REQUIRE=force \
  ssh $SERVER bash << 'REMOTE_SCRIPT'
set -e

echo "=== Cleaning up old processes and containers ==="

# Kill all python http.server processes
ps aux | grep 'python3.*http.server' | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true

# Kill all uvicorn processes not in containers
ps aux | grep 'uvicorn' | grep -v docker | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true

# Stop ALL existing containers
echo "Stopping all Tripflow containers..."
cd /home/peter
docker compose -f docker-compose.production.yml down 2>/dev/null || true

# Remove containers from old deployments
docker ps -a | grep -E 'tripflow-docker|tripflow-backend|tripflow-new' | awk '{print $1}' | xargs -r docker stop 2>/dev/null || true
docker ps -a | grep -E 'tripflow-docker|tripflow-backend|tripflow-new' | awk '{print $1}' | xargs -r docker rm 2>/dev/null || true

echo "=== Building Docker images ==="
cd /home/peter/tripflow-build

echo "Building backend image..."
cd backend
docker build -t tripflow-api:latest .

echo "Building frontend image..."
cd ../frontend
docker build -t tripflow-frontend:latest .

echo "=== Creating data directories (if needed) ==="
mkdir -p /home/peter/tripflow-data/postgres 2>/dev/null || true
mkdir -p /home/peter/tripflow-data/qdrant 2>/dev/null || true
mkdir -p /home/peter/tripflow-data/redis 2>/dev/null || true

echo "=== Starting services ==="
cd /home/peter
docker compose -f docker-compose.production.yml up -d

echo "=== Waiting for services to be ready ==="
sleep 15

echo "=== Checking container status ==="
docker compose -f docker-compose.production.yml ps

echo "=== Running health checks ==="

# Check backend health
if docker exec tripflow-api curl -f http://localhost:8000/health 2>/dev/null; then
    echo "✅ Backend API is healthy"
else
    echo "⚠️  Backend API health check failed"
    echo "Backend logs:"
    docker logs tripflow-api --tail 30
fi

# Check frontend
if docker exec tripflow-frontend wget -q -O- http://localhost:80 2>/dev/null | grep -q 'html'; then
    echo "✅ Frontend is serving content"
else
    echo "⚠️  Frontend check failed"
    echo "Frontend logs:"
    docker logs tripflow-frontend --tail 30
fi

# Check database
if docker exec tripflow-postgres pg_isready -U postgres -d tripflow >/dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL not ready"
fi

# Check Qdrant
if docker exec tripflow-qdrant wget -q -O- http://localhost:6333/healthz 2>/dev/null; then
    echo "✅ Qdrant is ready"
else
    echo "⚠️  Qdrant not ready"
fi

# Check Redis
if docker exec tripflow-redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis not ready"
fi

echo "=== Cleanup build directory and old containers ==="
# Clean up build directory
rm -rf /home/peter/tripflow-build

# Remove old deployment directories (keep the data!)
rm -rf /home/peter/tripflow-docker 2>/dev/null || true
rm -rf /home/peter/tripflow-backend 2>/dev/null || true
rm -rf /home/peter/tripflow-new 2>/dev/null || true

# Prune unused Docker resources
docker system prune -f

echo "=== Deployment complete! ==="
REMOTE_SCRIPT

# Step 3: Test external access
echo -e "\n${YELLOW}🧪 Step 3: Testing external access...${NC}"

sleep 3

# Test frontend
if timeout 5 curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP:3002 | grep -q "200"; then
    echo -e "${GREEN}✅ Frontend accessible at http://$SERVER_IP:3002${NC}"
else
    echo -e "${RED}⚠️  Frontend not accessible externally${NC}"
fi

# Test backend health through nginx proxy
if timeout 5 curl -s http://$SERVER_IP:3002/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend API accessible through nginx proxy${NC}"
else
    echo -e "${RED}⚠️  Backend API not accessible through proxy${NC}"
fi

echo -e "\n${GREEN}=========================================="
echo "🎉 Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "📍 Access TripFlow:"
echo "   Application: http://$SERVER_IP:3002"
echo "   API Docs: http://$SERVER_IP:3002/docs"
echo "   Health Check: http://$SERVER_IP:3002/health"
echo ""
echo "🐳 Docker Management:"
echo "   View logs: ssh $SERVER 'docker compose -f /home/peter/docker-compose.production.yml logs -f'"
echo "   Restart: ssh $SERVER 'docker compose -f /home/peter/docker-compose.production.yml restart'"
echo "   Stop: ssh $SERVER 'docker compose -f /home/peter/docker-compose.production.yml down'"
echo "   Status: ssh $SERVER 'docker compose -f /home/peter/docker-compose.production.yml ps'"
echo ""
echo "💾 Data Location (persists across deployments):"
echo "   /home/peter/tripflow-data/postgres - Database files"
echo "   /home/peter/tripflow-data/qdrant - Vector DB"
echo "   /home/peter/tripflow-data/redis - Cache"
echo ""
