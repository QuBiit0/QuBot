#!/bin/bash
# ===========================================
# Qubot - Local Deployment Script
# ===========================================
# Usage: ./scripts/deploy-local.sh [--clean] [--skip-build] [--logs]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Arguments
CLEAN=false
SKIP_BUILD=false
SHOW_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clean       Remove all volumes and rebuild from scratch"
            echo "  --skip-build  Skip building images (use existing)"
            echo "  --logs        Show logs after deployment"
            echo "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# ===========================================
# Helper Functions
# ===========================================
print_header() {
    echo ""
    echo -e "${CYAN}===========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ===========================================
# Pre-flight Checks
# ===========================================
print_header "🔍 Pre-flight Checks"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    echo ""
    echo "Please install Docker Desktop:"
    echo "  Windows: https://docs.docker.com/desktop/install/windows-install/"
    echo "  macOS:   https://docs.docker.com/desktop/install/mac-install/"
    echo "  Linux:   https://docs.docker.com/engine/install/"
    exit 1
fi
print_success "Docker CLI found"

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    echo ""
    echo -e "${YELLOW}Please start Docker Desktop first!${NC}"
    echo ""
    echo "Windows:"
    echo "  1. Open Docker Desktop from Start Menu"
    echo "  2. Wait for the whale icon to stop animating"
    echo "  3. Run this script again"
    echo ""
    exit 1
fi
print_success "Docker daemon is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "docker-compose is not installed"
    exit 1
fi

# Use docker compose (new) or docker-compose (old)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi
print_success "Docker Compose available: $DOCKER_COMPOSE"

# Check .env file
if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    if [ -f ".env.example" ]; then
        print_info "Creating .env from .env.example..."
        cp .env.example .env
        print_success ".env file created"
        print_warning "Please review and update .env with your settings!"
    else
        print_error ".env.example not found. Cannot create .env file."
        exit 1
    fi
else
    print_success ".env file found"
fi

# ===========================================
# Port Check
# ===========================================
print_header "🔌 Checking Ports"

PORTS=("5432" "6379" "8000" "3000")
PORT_NAMES=("PostgreSQL" "Redis" "API" "Frontend")
PORT_CONFLICTS=false

for i in "${!PORTS[@]}"; do
    port="${PORTS[$i]}"
    name="${PORT_NAMES[$i]}"
    
    # Check if port is in use (cross-platform)
    if command -v netstat &> /dev/null; then
        if netstat -an 2>/dev/null | grep -q ":$port "; then
            print_warning "Port $port ($name) appears to be in use"
            PORT_CONFLICTS=true
        fi
    elif command -v lsof &> /dev/null; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_warning "Port $port ($name) is already in use"
            PORT_CONFLICTS=true
        fi
    fi
done

if [ "$PORT_CONFLICTS" = true ]; then
    print_warning "Some ports are already in use. This might cause issues."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ===========================================
# Clean Up (if requested)
# ===========================================
if [ "$CLEAN" = true ]; then
    print_header "🧹 Cleaning Up"
    print_info "Stopping and removing containers..."
    $DOCKER_COMPOSE -f docker-compose.local.yml down -v --remove-orphans 2>/dev/null || true
    print_info "Removing unused images..."
    docker system prune -f 2>/dev/null || true
    print_success "Cleanup complete"
fi

# ===========================================
# Build & Deploy
# ===========================================
print_header "🏗️ Building & Deploying"

# Determine build flag
if [ "$SKIP_BUILD" = true ]; then
    BUILD_FLAG=""
    print_info "Skipping build (using existing images)"
else
    BUILD_FLAG="--build"
    print_info "Building images..."
fi

# Start services
print_info "Starting services..."
echo ""
$DOCKER_COMPOSE -f docker-compose.local.yml up -d $BUILD_FLAG

if [ $? -ne 0 ]; then
    print_error "Deployment failed!"
    echo ""
    echo "Common issues:"
    echo "  - Docker Desktop not running"
    echo "  - Port conflicts (PostgreSQL, Redis already running)"
    echo "  - Insufficient disk space"
    echo "  - Network issues"
    exit 1
fi

print_success "Services started successfully!"

# ===========================================
# Wait for Health Checks
# ===========================================
print_header "⏳ Waiting for Services"

wait_for_service() {
    local service=$1
    local max_attempts=$2
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local status=$($DOCKER_COMPOSE -f docker-compose.local.yml ps -q $service 2>/dev/null)
        if [ -z "$status" ]; then
            print_error "Service $service not found"
            return 1
        fi
        
        # Check health
        local health=$(docker inspect --format='{{.State.Health.Status}}' $service 2>/dev/null || echo "unknown")
        
        if [ "$health" = "healthy" ]; then
            print_success "$service is healthy"
            return 0
        elif [ "$health" = "unhealthy" ]; then
            print_warning "$service is unhealthy, retrying..."
        fi
        
        echo -ne "\r${BLUE}  Waiting for $service... ($attempt/$max_attempts)${NC}"
        sleep 3
        attempt=$((attempt + 1))
    done
    
    echo ""
    print_warning "$service may still be starting (check logs with --logs)"
    return 1
}

wait_for_service "qubot-db" 20
wait_for_service "qubot-redis" 15
wait_for_service "qubot-api" 30

# ===========================================
# Summary
# ===========================================
print_header "🎉 Deployment Complete!"

echo ""
echo -e "${CYAN}Services:${NC}"
echo "  📊 API:       http://localhost:8000"
echo "  🌐 Frontend:  http://localhost:3000"
echo "  💾 Database:  localhost:5432"
echo "  ⚡ Redis:     localhost:6379"

echo ""
echo -e "${CYAN}Documentation:${NC}"
echo "  • API Docs:    http://localhost:8000/docs"
echo "  • Health:      http://localhost:8000/api/v1/health/ready"
echo ""

echo -e "${CYAN}Commands:${NC}"
echo "  View logs:    $DOCKER_COMPOSE -f docker-compose.local.yml logs -f"
echo "  Stop:         $DOCKER_COMPOSE -f docker-compose.local.yml down"
echo "  Restart:      $DOCKER_COMPOSE -f docker-compose.local.yml restart"
echo "  Clean:        $DOCKER_COMPOSE -f docker-compose.local.yml down -v"
echo ""

if [ "$SHOW_LOGS" = true ]; then
    print_info "Showing logs (Ctrl+C to exit)..."
    $DOCKER_COMPOSE -f docker-compose.local.yml logs -f
fi
