#!/bin/bash
# ============================================================
# ADVERTORIAL PIPELINE — SCRIPT DE DÉPLOIEMENT VPS
# Lance ce script une seule fois sur ton VPS :
#   bash deploy.sh
# ============================================================

set -e

echo "🚀 Advertorial Pipeline — Deployment"
echo "======================================"

# ── CONFIG ──
APP_DIR="/root/advertorial-pipeline"
PUBLISH_DIR="/var/www/advertorials"
API_PORT=8000
DOMAIN="${1:-localhost}"  # Passe le domaine en argument si tu en as un

# ── 1. INSTALL DEPS ──
echo ""
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3-pip nginx

# ── 2. SETUP DIRECTORIES ──
echo ""
echo "📁 Setting up directories..."
mkdir -p "$PUBLISH_DIR"
mkdir -p "$APP_DIR/data/output"

# ── 3. INSTALL PYTHON DEPS ──
echo ""
echo "🐍 Installing Python dependencies..."
cd "$APP_DIR"
pip install --break-system-packages -q \
  anthropic>=0.40.0 \
  aiohttp>=3.9.0 \
  beautifulsoup4>=4.12.0 \
  lxml>=5.0.0 \
  pydantic>=2.5.0 \
  python-dotenv>=1.0.0 \
  pyyaml>=6.0.0 \
  fastapi>=0.115.0 \
  "uvicorn[standard]>=0.30.0"

# ── 4. CHECK .env ──
if [ ! -f "$APP_DIR/.env" ]; then
  echo ""
  echo "⚠️  No .env file found. Creating template..."
  cat > "$APP_DIR/.env" << 'ENVEOF'
ANTHROPIC_API_KEY=sk-ant-REPLACE-WITH-YOUR-KEY
ENVEOF
  echo "   → Edit $APP_DIR/.env with your real API key!"
  echo "   → Then re-run this script or restart the service."
fi

# ── 5. CONFIGURE NGINX ──
echo ""
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/advertorials << NGINXEOF
server {
    listen 80;
    server_name $DOMAIN;

    # Serve advertorial HTML pages
    location /articles/ {
        alias $PUBLISH_DIR/;
        try_files \$uri \$uri.html =404;
        add_header X-Content-Type-Options nosniff;
    }

    # Proxy API requests to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:$API_PORT/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_buffering off;  # Important for SSE streaming
    }

    # CORS headers for Lovable frontend
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";
}
NGINXEOF

# Enable site
ln -sf /etc/nginx/sites-available/advertorials /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
echo "   ✅ Nginx configured"

# ── 6. CREATE SYSTEMD SERVICE ──
echo ""
echo "⚙️  Creating systemd service..."
cat > /etc/systemd/system/advertorial-api.service << SVCEOF
[Unit]
Description=Advertorial Pipeline API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=/usr/local/bin/uvicorn api.routes:app --host 127.0.0.1 --port $API_PORT --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable advertorial-api
systemctl restart advertorial-api

echo "   ✅ Service created and started"

# ── 7. VERIFY ──
echo ""
echo "🔍 Verifying..."
sleep 2

if systemctl is-active --quiet advertorial-api; then
  echo "   ✅ API is running on port $API_PORT"
else
  echo "   ❌ API failed to start. Check: journalctl -u advertorial-api -n 50"
fi

if systemctl is-active --quiet nginx; then
  echo "   ✅ Nginx is running"
else
  echo "   ❌ Nginx failed. Check: nginx -t"
fi

# ── 8. SUMMARY ──
echo ""
echo "======================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "======================================"
echo ""
echo "  API:          http://127.0.0.1:$API_PORT"
echo "  Health check: curl http://127.0.0.1:$API_PORT/health"
echo "  Advertorials: http://$DOMAIN/articles/"
echo "  Nginx proxy:  http://$DOMAIN/api/"
echo ""
echo "  Pipeline dir: $APP_DIR"
echo "  HTML output:  $PUBLISH_DIR"
echo "  Logs:         journalctl -u advertorial-api -f"
echo ""
echo "  Next steps:"
echo "  1. Edit $APP_DIR/.env with your ANTHROPIC_API_KEY"
echo "  2. Set VITE_API_URL=http://$DOMAIN/api in Lovable"
echo "  3. Test: curl http://$DOMAIN/api/health"
echo ""
