#!/bin/bash
set -e

###############################################################################
# CORA Docker Build & Push Script
# Builds and pushes both API and Client images to Docker Hub
###############################################################################

# Configuration
export DOCKER_DEFAULT_PLATFORM=linux/amd64
: ${DOCKER_HUB_USERNAME:=""}
: ${DOCKER_HUB_PASSWORD:=""}
: ${IMAGE_TAG:="latest"}

# Default image names (can be overridden)
: ${API_IMAGE_NAME:="cora-api"}
: ${CLIENT_IMAGE_NAME:="cora-client"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -u, --username    Docker Hub username"
    echo "  -p, --password    Docker Hub password OR Personal Access Token (PAT)"
    echo "  -t, --tag         Image tag (default: latest)"
    echo "  -a, --api-name    API image name (default: cora-api)"
    echo "  -c, --client-name Client image name (default: cora-client)"
    echo "  --skip-api        Skip building API image"
    echo "  --skip-client     Skip building Client image"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -u myuser -p my-pat-token"
    echo "  $0 -u myuser -p my-pat-token -t v1.0.0"
    echo "  $0 --skip-client -u myuser -p my-pat-token"
    echo ""
    echo "Environment Variables:"
    echo "  DOCKER_HUB_USERNAME - Docker Hub username"
    echo "  DOCKER_HUB_PASSWORD - Docker Hub password or PAT"
    echo "  IMAGE_TAG          - Image tag (default: latest)"
    echo "  API_IMAGE_NAME     - API image name (default: cora-api)"
    echo "  CLIENT_IMAGE_NAME  - Client image name (default: cora-client)"
    echo ""
    echo "Note: Use a Personal Access Token (PAT) instead of your password."
    echo "      Generate at: Docker Hub > Account Settings > Security > New Access Token"
}

# Parse arguments
SKIP_API=false
SKIP_CLIENT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--username)
            DOCKER_HUB_USERNAME="$2"
            shift 2
            ;;
        -p|--password)
            DOCKER_HUB_PASSWORD="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -a|--api-name)
            API_IMAGE_NAME="$2"
            shift 2
            ;;
        -c|--client-name)
            CLIENT_IMAGE_NAME="$2"
            shift 2
            ;;
        --skip-api)
            SKIP_API=true
            shift
            ;;
        --skip-client)
            SKIP_CLIENT=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate inputs
if [ -z "$DOCKER_HUB_USERNAME" ]; then
    log_error "Docker Hub username is required. Set DOCKER_HUB_USERNAME or use -u flag."
    exit 1
fi

if [ -z "$DOCKER_HUB_PASSWORD" ]; then
    log_error "Docker Hub password is required. Set DOCKER_HUB_PASSWORD or use -p flag."
    exit 1
fi

# Full image names
API_IMAGE="${DOCKER_HUB_USERNAME}/${API_IMAGE_NAME}:${IMAGE_TAG}"
CLIENT_IMAGE="${DOCKER_HUB_USERNAME}/${CLIENT_IMAGE_NAME}:${IMAGE_TAG}"

log_info "=========================================="
log_info "CORA Docker Build & Push"
log_info "=========================================="
log_info "API Image:   $API_IMAGE"
log_info "Client Image: $CLIENT_IMAGE"
log_info "Tag:         $IMAGE_TAG"
log_info ""

# Copy required files to build context (needed for Docker image)
log_info "Preparing build context..."
mkdir -p .docker_stage

# Copy Modal credentials if exists
if [ -f ~/.modal.toml ]; then
    log_info "Copying ~/.modal.toml to build context..."
    cp ~/.modal.toml .docker_stage/modal.toml
else
    log_warn "~/.modal.toml not found - Modal execution will not work"
    touch .docker_stage/modal.toml # Create empty to avoid Docker COPY failure
fi

# Copy config file if exists
if [ -f ~/.config/cora/config.yaml ]; then
    log_info "Copying ~/.config/cora/config.yaml to build context..."
    cp ~/.config/cora/config.yaml .docker_stage/config.yaml
else
    log_warn "~/.config/cora/config.yaml not found - LLM/Langfuse config will not work"
    touch .docker_stage/config.yaml # Create empty to avoid Docker COPY failure
fi

# Login to Docker Hub
log_info "Logging into Docker Hub..."
echo "$DOCKER_HUB_PASSWORD" | docker login -u "$DOCKER_HUB_USERNAME" --password-stdin

# Build and push API
if [ "$SKIP_API" = false ]; then
    log_info "=========================================="
    log_info "Building API image..."
    log_info "=========================================="
    
    docker build --platform linux/amd64 \
        -t "$API_IMAGE" \
        -t "${DOCKER_HUB_USERNAME}/${API_IMAGE_NAME}:latest" \
        .
    
    log_info "Pushing API image to Docker Hub..."
    docker push "$API_IMAGE"
    docker push "${DOCKER_HUB_USERNAME}/${API_IMAGE_NAME}:latest"
    
    log_info "API image pushed successfully!"
else
    log_warn "Skipping API image build"
fi

# Build and push Client
if [ "$SKIP_CLIENT" = false ]; then
    log_info "=========================================="
    log_info "Building Client image..."
    log_info "=========================================="
    
    docker build --platform linux/amd64 \
        -t "$CLIENT_IMAGE" \
        -t "${DOCKER_HUB_USERNAME}/${CLIENT_IMAGE_NAME}:latest" \
        -f client/Dockerfile \
        client/
    
    log_info "Pushing Client image to Docker Hub..."
    docker push "$CLIENT_IMAGE"
    docker push "${DOCKER_HUB_USERNAME}/${CLIENT_IMAGE_NAME}:latest"
    
    log_info "Client image pushed successfully!"
else
    log_warn "Skipping Client image build"
fi

# Logout from Docker Hub
docker logout

# Cleanup staging directory
rm -rf .docker_stage

log_info "=========================================="
log_info "All images built and pushed successfully!"
log_info "=========================================="
log_info ""
log_info "To deploy with CloudFormation, use:"
log_info "  --parameter-overrides \\"
if [ "$SKIP_API" = false ]; then
log_info "    DockerImageApi=${DOCKER_HUB_USERNAME}/${API_IMAGE_NAME}:${IMAGE_TAG} \\"
fi
if [ "$SKIP_CLIENT" = false ]; then
log_info "    DockerImageClient=${DOCKER_HUB_USERNAME}/${CLIENT_IMAGE_NAME}:${IMAGE_TAG} \\"
fi
log_info ""
