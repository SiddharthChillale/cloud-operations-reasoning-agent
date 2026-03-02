#!/bin/bash
set -e

###############################################################################
# CORA POC - EC2 User Data Script
# This script sets up Docker, Docker Compose, Cloudflare Tunnel, and CloudWatch
###############################################################################

# Configuration - Set these before launching or pass via user data
: ${DOCKER_IMAGE_API:="youruser/cora:latest"}
: ${DOCKER_IMAGE_CLIENT:="youruser/cora-client:latest"}
: ${CLOUDFLARE_TOKEN:=""}
: ${DOCKER_HUB_USERNAME:=""}
: ${DOCKER_HUB_ACCESS_TOKEN:=""}

echo "=========================================="
echo "CORA POC - Starting Setup"
echo "=========================================="

# Install Docker (AL2023 uses dnf)
echo "[1/6] Installing Docker..."
dnf install docker -y
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
echo "[2/6] Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install cloudflared
echo "[3/6] Installing cloudflared..."
curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Install AWS CloudWatch Agent
echo "[4/6] Installing CloudWatch Agent..."
yum install -y amazon-cloudwatch-agent

# Create app directory
echo "[5/6] Setting up application..."
mkdir -p /opt/cora
mkdir -p /var/log

# Create docker-compose.yml
cat > /opt/cora/docker-compose.yml << 'EOF'
version: '3.8'

services:
  api:
    image: ${DOCKER_IMAGE_API}
    container_name: cora-api
    ports:
      - "8000:8000"
    volumes:
      - cora-data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - cora-network

  client:
    image: ${DOCKER_IMAGE_CLIENT}
    container_name: cora-client
    command: sh -c "npm run build && npm run start"
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    restart: unless-stopped
    depends_on:
      api:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - cora-network

volumes:
  cora-data:
    driver: local

networks:
  cora-network:
    driver: bridge
EOF

# Create CloudWatch Agent config
mkdir -p /opt/aws/amazon-cloudwatch-agent/etc
cat > /opt/aws/amazon-cloudwatch-agent/etc/agent.json << 'EOF'
{
  "logs": {
    "force_flush_interval": 5,
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/cora-setup.log",
            "log_group_name": "/aws/ec2/cora-poc",
            "log_stream_name": "{instance_id}/setup",
            "retention_in_days": 7
          },
          {
            "file_path": "/var/log/cloudflared.log",
            "log_group_name": "/aws/ec2/cora-poc",
            "log_stream_name": "{instance_id}/cloudflared",
            "retention_in_days": 7
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch Agent
echo "Starting CloudWatch Agent..."
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/agent.json

# Start Docker containers
echo "[6/6] Starting Docker containers..."
cd /opt/cora

# Source .env file to get variables for docker login
if [ -f .env ]; then
    source .env
fi

# Login to Docker Hub if credentials provided
if [ -n "$DOCKER_HUB_USERNAME" ] && [ -n "$DOCKER_HUB_ACCESS_TOKEN" ]; then
    echo "Logging into Docker Hub..."
    echo "$DOCKER_HUB_ACCESS_TOKEN" | docker login -u "$DOCKER_HUB_USERNAME" --password-stdin
fi

docker-compose pull
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 15

# Start Cloudflare Tunnel
if [ -n "$CLOUDFLARE_TOKEN" ]; then
    echo "Starting Cloudflare Tunnel..."
    nohup cloudflared tunnel --url http://localhost:3000 --token "$CLOUDFLARE_TOKEN" > /var/log/cloudflared.log 2>&1 &
    echo "Cloudflare tunnel started. Check /var/log/cloudflared.log for URL."
else
    echo "WARNING: CLOUDFLARE_TOKEN not set. Skipping tunnel setup."
    echo "To enable tunnel, set CLOUDFLARE_TOKEN and run:"
    echo "  nohup cloudflared tunnel --url http://localhost:3000 --token '\$CLOUDFLARE_TOKEN' > /var/log/cloudflared.log 2>&1 &"
fi

echo "=========================================="
echo "CORA POC Setup Complete!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - FastAPI:  http://localhost:8000"
echo "  - Next.js:  http://localhost:3000"
echo ""
echo "Logs:"
echo "  - Setup:    /var/log/cora-setup.log"
echo "  - Cloudflare: /var/log/cloudflared.log"
echo "  - Docker:   docker logs cora-api (or cora-client)"
echo ""
echo "CloudWatch Logs:"
echo "  - Group: /aws/ec2/cora-poc"
echo ""
echo "To access from browser:"
echo "  1. If using Cloudflare: Check /var/log/cloudflared.log for your URL"
echo "  2. If no tunnel: Access via EC2 Public IP at http://<public-ip>:3000"
echo ""

# Log completion
echo "$(date): CORA POC setup complete" >> /var/log/cora-setup.log
