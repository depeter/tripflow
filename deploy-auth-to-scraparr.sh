#!/bin/bash
set -e

echo "🚀 Deploying TripFlow Auth Backend to Scraparr Server..."

# Configuration
SERVER="peter@192.168.1.149"
REMOTE_DIR="/home/peter/tripflow-backend"
PASSWORD="nomansland"

echo "📦 Creating deployment package..."

# Change to tripflow directory
cd /home/peter/work/tripflow

# Create temporary deployment directory
DEPLOY_DIR="/tmp/tripflow-deploy-$$"
mkdir -p "$DEPLOY_DIR"

# Copy backend files
cp -r backend/* "$DEPLOY_DIR/"

# Create .env file for scraparr
cat > "$DEPLOY_DIR/.env" << 'EOF'
# TripFlow Backend Environment Variables

APP_NAME=TripFlow
DEBUG=True

# Database - Tripflow DB on localhost (same server)
DATABASE_URL=postgresql://tripflow:tripflow@localhost:5435/tripflow

# Qdrant Vector Database (local)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis (local)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Sync
SYNC_ENABLED=True

# Source databases - Scraparr database
SOURCE_DB_PARK4NIGHT=postgresql://scraparr:scraparr@localhost:5434/scraparr
SOURCE_DB_CAMPERCONTACT=
SOURCE_DB_LOCAL_SITES=

# Security
SECRET_KEY=tripflow-production-secret-key-change-this-in-real-production

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://192.168.1.149:3000","http://scraparr:3000"]

# Authentication
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF

# Create startup script
cat > "$DEPLOY_DIR/start.sh" << 'EOF'
#!/bin/bash
cd /home/peter/tripflow-backend

# Activate venv
source venv/bin/activate

# Start uvicorn
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
EOF

chmod +x "$DEPLOY_DIR/start.sh"

echo "📤 Uploading to scraparr server..."

# Create remote directory
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" "mkdir -p $REMOTE_DIR"

# Upload files
sshpass -p "$PASSWORD" rsync -avz --delete \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  "$DEPLOY_DIR/" "$SERVER:$REMOTE_DIR/"

echo "🔧 Setting up Python environment on scraparr..."

sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" << 'ENDSSH'
cd /home/peter/tripflow-backend

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate

# Install/upgrade dependencies
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy asyncpg psycopg2-binary python-jose[cryptography] passlib[bcrypt] python-multipart authlib httpx pydantic-settings email-validator

echo "✅ Python environment ready"
ENDSSH

echo "🔄 Stopping old backend if running..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" "pkill -f 'uvicorn app.main:app' || true"

sleep 2

echo "🚀 Starting backend..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" "cd /home/peter/tripflow-backend && nohup ./start.sh > backend.log 2>&1 &"

sleep 5

echo "✅ Testing backend..."
if curl -s http://192.168.1.149:8001/health | grep -q "healthy"; then
    echo "✅ Backend is healthy!"
    echo ""
    echo "🎉 Deployment complete!"
    echo ""
    echo "📍 API Base URL: http://192.168.1.149:8001"
    echo "📖 API Docs: http://192.168.1.149:8001/docs"
    echo ""
    echo "🧪 Test login:"
    echo "curl -X POST http://192.168.1.149:8001/api/v1/auth/login \\"
    echo "  -H 'Content-Type: application/x-www-form-urlencoded' \\"
    echo "  -d 'username=admin@tripflow.com&password=admin123'"
else
    echo "⚠️  Backend may not be running. Check logs:"
    echo "ssh peter@192.168.1.149 'tail -50 /home/peter/tripflow-backend/backend.log'"
fi

# Cleanup
rm -rf "$DEPLOY_DIR"
