#!/bin/bash
set -e

###############################################################################
# CORA EC2 Deployment Script
# Copies config files and starts the Docker container on a remote Ubuntu EC2
###############################################################################

# Usage function
usage() {
    echo "Usage: $0 -i <ec2-ip> -k <key-path> [-d <remote-dir>]"
    echo ""
    echo "Options:"
    echo "  -i, --ip          Public IP of the EC2 instance"
    echo "  -k, --key         Path to the SSH private key (.pem)"
    echo "  -d, --dir         Remote directory (default: ~/cloud-operations-reasoning-agent)"
    echo "  -h, --help        Show this help message"
    echo ""
    exit 1
}

# Default values
REMOTE_DIR="~/cloud-operations-reasoning-agent"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--ip)
            EC2_IP="$2"
            shift 2
            ;;
        -k|--key)
            KEY_PATH="$2"
            shift 2
            ;;
        -d|--dir)
            REMOTE_DIR="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required inputs
if [ -z "$EC2_IP" ] || [ -z "$KEY_PATH" ]; then
    echo "Error: IP and Key path are required."
    usage
fi

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[1/3] Copying files to EC2...${NC}"
scp -i "$KEY_PATH" .env docker-compose.yml "ubuntu@$EC2_IP:$REMOTE_DIR/"

echo -e "${BLUE}[2/3] Starting Docker services on EC2...${NC}"
ssh -i "$KEY_PATH" "ubuntu@$EC2_IP" "cd $REMOTE_DIR && docker compose pull && docker compose up -d"

echo -e "${BLUE}[3/3] Verifying deployment...${NC}"
ssh -i "$KEY_PATH" "ubuntu@$EC2_IP" "docker compose ps"

echo -e "${GREEN}=========================================="
echo "Deployment successful!"
echo "API is available at: http://$EC2_IP/health"
echo "==========================================${NC}"
