#!/bin/bash
set -e

# Update and install prerequisites
apt-get update
apt-get install -y ca-certificates curl gnupg

# Add Docker's official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker and Docker Compose plugin
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Add the default ubuntu user to the docker group
usermod -aG docker ubuntu

# Create application directory
mkdir -p /home/ubuntu/cloud-operations-reasoning-agent
mkdir -p /home/ubuntu/.cora
chown -R ubuntu:ubuntu /home/ubuntu/cloud-operations-reasoning-agent
chown -R ubuntu:ubuntu /home/ubuntu/.cora

echo "=========================================="
echo "Ubuntu EC2 Setup Complete!"
echo "Docker and Docker Compose are installed."
echo "You can now SCP your .env and docker-compose.yml to:"
echo "  /home/ubuntu/cloud-operations-reasoning-agent/"
echo "Then run: docker compose up -d"
echo "=========================================="
