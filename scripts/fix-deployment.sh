#!/bin/bash
# ===========================================
# Qubot - Deployment Fix Script
# ===========================================
# Usage: ./scripts/fix-deployment.sh
# Fixes common deployment issues automatically

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Use docker compose (new) or docker-compose (old)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

print_header() {
    echo ""
    echo -e "${CYAN}===========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===========================================${NC}"
}

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

# ===========================================
# Check Docker
# ===========================================
print_header "🔧 Deployment Fix Tool"

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running"
    echo ""
    echo "Please start Docker Desktop first!"
    echo ""
    echo "Windows:"
    echo "  1. Press Windows key"
    echo "  2. Type 'Docker Desktop'"
    echo "  3. Click to open it"
    echo "  4. Wait for the whale icon to stop animating"
    echo ""
    exit 1
fi

print_success "Docker is running"

# ===========================================
# Fix Steps
# ===========================================

# Step 1: Stop all running containers
echo ""
print_info "Step 1: Stopping all containers..."
$DOCKER_COMPOSE -f docker-compose.local.yml down --remove-orphans 2>/dev/null || true
print_success "Containers stopped"

# Step 2: Clean up Docker system
echo ""
print_info "Step 2: Cleaning up Docker system..."
docker system prune -f 2>/dev/null || true
docker volume prune -f 2>/dev/null || true
print_success "Docker system cleaned"

# Step 3: Check port conflicts
echo ""
print_info "Step 3: Checking for port conflicts..."

PORTS=("5432" "6379" "8000" "3000")
for port in "${PORTS[@]}"; do
    # Try to find and kill processes using these ports
    if command -v lsof &> /dev/null; then
        PIDS=$(lsof -ti :$port 2>/dev/null || true)
        if [ -n "$PIDS" ]; then
            print_warning "Port $port is in use by PID(s): $PIDS"
            read -p "Kill these processes? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kill -9 $PIDS 2>/dev/null || true
                print_success "Processes killed"
            fi
        fi
    fi
done

# Step 4: Rebuild images
echo ""
print_info "Step 4: Rebuilding Docker images..."
$DOCKER_COMPOSE -f docker-compose.local.yml build --no-cache
print_success "Images rebuilt"

# Step 5: Start services
echo ""
print_info "Step 5: Starting services..."
$DOCKER_COMPOSE -f docker-compose.local.yml up -d
print_success "Services started"

# Step 6: Wait for health checks
echo ""
print_info "Step 6: Waiting for services to be healthy..."
echo "This may take up to 60 seconds..."

sleep 10

for i in {1..12}; do
    echo -ne "\r  Checking... ($i/12)"
    
    # Check if API is responding
    if curl -s http://localhost:8000/api/v1/health/ready &> /dev/null; then
        echo ""
        print_success "API is healthy!"
        break
    fi
    
    sleep 5
done

echo ""

# ===========================================
# Summary
# ===========================================
print_header "🎉 Fix Complete!"

echo ""
echo -e "${CYAN}Status Check:${NC}"

# Check containers
CONTAINERS=$($DOCKER_COMPOSE -f docker-compose.local.yml ps -q)
if [ -n "$CONTAINERS" ]; then
    print_success "$($DOCKER_COMPOSE -f docker-compose.local.yml ps -q | wc -l) containers running"
    $DOCKER_COMPOSE -f docker-compose.local.yml ps
else
    print_error "No containers running"
fi

echo ""
echo -e "${CYAN}Access Points:${NC}"
echo "  • API:       http://localhost:8000"
echo "  • Frontend:  http://localhost:3000"
echo "  • API Docs:  http://localhost:8000/docs"
echo ""

echo -e "${CYAN}Useful Commands:${NC}"
echo "  View logs:   $DOCKER_COMPOSE -f docker-compose.local.yml logs -f"
echo "  Stop:        $DOCKER_COMPOSE -f docker-compose.local.yml down"
echo "  Restart:     $DOCKER_COMPOSE -f docker-compose.local.yml restart"
echo ""

print_info "If you're still having issues, run: ./scripts/check-deployment.sh"
