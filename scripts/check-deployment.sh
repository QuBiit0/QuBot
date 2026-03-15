#!/bin/bash
# ===========================================
# Qubot - Deployment Diagnostic Script
# ===========================================
# Usage: ./scripts/check-deployment.sh

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

echo -e "${CYAN}===========================================${NC}"
echo -e "${CYAN}  Qubot Deployment Diagnostic Tool${NC}"
echo -e "${CYAN}===========================================${NC}"
echo ""

# ===========================================
# Check 1: Docker Installation
# ===========================================
echo -e "${BLUE}[1/7]${NC} Checking Docker Installation..."

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "  ${GREEN}✓${NC} Docker installed: $DOCKER_VERSION"
else
    echo -e "  ${RED}✗${NC} Docker not found in PATH"
    echo ""
    echo "  Please install Docker Desktop:"
    echo "  https://docs.docker.com/get-started/get-docker/"
    exit 1
fi

# ===========================================
# Check 2: Docker Daemon
# ===========================================
echo -e "${BLUE}[2/7]${NC} Checking Docker Daemon..."

if docker info &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker daemon is running"
else
    echo -e "  ${RED}✗${NC} Docker daemon is not running"
    echo ""
    echo -e "  ${YELLOW}Please start Docker Desktop:${NC}"
    echo "  • Windows: Open Docker Desktop from Start Menu"
    echo "  • macOS: Open Docker Desktop from Applications"
    echo "  • Linux: sudo systemctl start docker"
    exit 1
fi

# ===========================================
# Check 3: Docker Compose
# ===========================================
echo -e "${BLUE}[3/7]${NC} Checking Docker Compose..."

if $DOCKER_COMPOSE version &> /dev/null; then
    COMPOSE_VERSION=$($DOCKER_COMPOSE version --short)
    echo -e "  ${GREEN}✓${NC} Docker Compose available: $COMPOSE_VERSION"
else
    echo -e "  ${RED}✗${NC} Docker Compose not found"
    exit 1
fi

# ===========================================
# Check 4: Project Files
# ===========================================
echo -e "${BLUE}[4/7]${NC} Checking Project Files..."

if [ -f "docker-compose.local.yml" ]; then
    echo -e "  ${GREEN}✓${NC} docker-compose.local.yml found"
else
    echo -e "  ${RED}✗${NC} docker-compose.local.yml not found"
    echo "  Make sure you're running this from the project root"
    exit 1
fi

if [ -f ".env" ]; then
    echo -e "  ${GREEN}✓${NC} .env file found"
else
    echo -e "  ${YELLOW}⚠${NC} .env file not found"
    if [ -f ".env.example" ]; then
        echo "  Creating .env from .env.example..."
        cp .env.example .env
        echo -e "  ${GREEN}✓${NC} .env created (please review it!)"
    fi
fi

# ===========================================
# Check 5: Port Availability
# ===========================================
echo -e "${BLUE}[5/7]${NC} Checking Port Availability..."

PORTS=("5432:PostgreSQL" "6379:Redis" "8000:API" "3000:Frontend")
for port_info in "${PORTS[@]}"; do
    port=$(echo $port_info | cut -d: -f1)
    name=$(echo $port_info | cut -d: -f2)
    
    # Cross-platform port check
    PORT_IN_USE=false
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            PORT_IN_USE=true
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -an 2>/dev/null | grep -q "0.0.0.0:$port "; then
            PORT_IN_USE=true
        fi
    elif command -v ss &> /dev/null; then
        if ss -tln 2>/dev/null | grep -q ":$port "; then
            PORT_IN_USE=true
        fi
    fi
    
    if [ "$PORT_IN_USE" = true ]; then
        echo -e "  ${YELLOW}⚠${NC} Port $port ($name) is already in use"
    else
        echo -e "  ${GREEN}✓${NC} Port $port ($name) is available"
    fi
done

# ===========================================
# Check 6: Container Status
# ===========================================
echo -e "${BLUE}[6/7]${NC} Checking Container Status..."

if $DOCKER_COMPOSE -f docker-compose.local.yml ps &> /dev/null; then
    CONTAINERS=$($DOCKER_COMPOSE -f docker-compose.local.yml ps -q)
    if [ -z "$CONTAINERS" ]; then
        echo -e "  ${YELLOW}⚠${NC} No containers are running"
        echo ""
        echo "  To start the application:"
        echo "    ./scripts/deploy-local.sh"
    else
        echo -e "  ${GREEN}✓${NC} Containers found:"
        $DOCKER_COMPOSE -f docker-compose.local.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.State}}" 2>/dev/null || \
        $DOCKER_COMPOSE -f docker-compose.local.yml ps
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Could not check container status"
fi

# ===========================================
# Check 7: Service Health
# ===========================================
echo -e "${BLUE}[7/7]${NC} Checking Service Health..."

# Check API health
if curl -s http://localhost:8000/api/v1/health/ready &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} API is responding (http://localhost:8000)"
else
    echo -e "  ${YELLOW}⚠${NC} API is not responding"
fi

# Check Frontend
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200\|307"; then
    echo -e "  ${GREEN}✓${NC} Frontend is responding (http://localhost:3000)"
else
    echo -e "  ${YELLOW}⚠${NC} Frontend is not responding"
fi

echo ""
echo -e "${CYAN}===========================================${NC}"
echo -e "${CYAN}  Diagnostic Complete${NC}"
echo -e "${CYAN}===========================================${NC}"
echo ""

# ===========================================
# Recommendations
# ===========================================
echo -e "${CYAN}Quick Commands:${NC}"
echo "  Start:     ./scripts/deploy-local.sh"
echo "  Logs:      $DOCKER_COMPOSE -f docker-compose.local.yml logs -f"
echo "  Stop:      $DOCKER_COMPOSE -f docker-compose.local.yml down"
echo "  Clean:     $DOCKER_COMPOSE -f docker-compose.local.yml down -v"
echo ""
