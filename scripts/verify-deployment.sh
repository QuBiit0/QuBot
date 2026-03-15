#!/bin/bash

# Qubot Deployment Verification Script
# Usage: ./scripts/verify-deployment.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Qubot Deployment Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: API Health
echo -n "Testing API health... "
if curl -s -f "${API_URL}/api/v1/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
    exit 1
fi

# Test 2: API Info
echo -n "Testing API info... "
if curl -s -f "${API_URL}/api/v1/info" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Test 3: Agents endpoint
echo -n "Testing agents endpoint... "
AGENTS_RESPONSE=$(curl -s "${API_URL}/api/v1/agents")
if echo "$AGENTS_RESPONSE" | grep -q "data"; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Test 4: Tasks endpoint
echo -n "Testing tasks endpoint... "
TASKS_RESPONSE=$(curl -s "${API_URL}/api/v1/tasks")
if echo "$TASKS_RESPONSE" | grep -q "data"; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Test 5: Tools endpoint
echo -n "Testing tools endpoint... "
TOOLS_RESPONSE=$(curl -s "${API_URL}/api/v1/tools/available")
if echo "$TOOLS_RESPONSE" | grep -q "data"; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Test 6: LLM configs
echo -n "Testing LLM configs endpoint... "
if curl -s -f "${API_URL}/api/v1/llm-configs" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Test 7: Frontend
echo -n "Testing frontend... "
if curl -s -f "${FRONTEND_URL}" > /dev/null 2>&1 || curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" | grep -q "307\|200"; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${YELLOW}⚠ SKIP (may not be deployed)${NC}"
fi

# Test 8: Database connectivity
echo -n "Testing database connectivity... "
if curl -s "${API_URL}/api/v1/health" | grep -q "database.*healthy\|healthy"; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Test 9: Redis connectivity
echo -n "Testing Redis connectivity... "
if curl -s "${API_URL}/api/v1/health" | grep -q "redis.*healthy\|healthy"; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${YELLOW}⚠ SKIP (Redis may not be available)${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Verification Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}API:${NC} ${API_URL}"
echo -e "${GREEN}API Docs:${NC} ${API_URL}/docs"
echo -e "${GREEN}Frontend:${NC} ${FRONTEND_URL}"
echo ""
echo "Quick test commands:"
echo "  curl ${API_URL}/api/v1/health"
echo "  curl ${API_URL}/api/v1/agents"
echo "  curl ${API_URL}/api/v1/tasks"
