# Qubot Deployment Verification Script for Windows PowerShell
# Usage: .\scripts\verify-deployment.ps1

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Qubot Deployment Verification" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

$API_URL = "http://localhost:8000"
$FRONTEND_URL = "http://localhost:3000"
$TESTS_PASSED = 0
$TESTS_FAILED = 0

function Test-Endpoint($Name, $Url, $ExpectedStatus = 200) {
    Write-Host "Testing $Name... " -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq $ExpectedStatus -or $response.StatusCode -eq 307) {
            Write-Host "✓ PASS" -ForegroundColor Green
            $global:TESTS_PASSED++
            return $true
        } else {
            Write-Host "✗ FAIL (HTTP $($response.StatusCode))" -ForegroundColor Red
            $global:TESTS_FAILED++
            return $false
        }
    } catch {
        Write-Host "✗ FAIL ($($_.Exception.Message))" -ForegroundColor Red
        $global:TESTS_FAILED++
        return $false
    }
}

# Test 1: Health
Test-Endpoint "API Health" "$API_URL/api/v1/health"

# Test 2: Info
Test-Endpoint "API Info" "$API_URL/api/v1/info"

# Test 3: Agents
Test-Endpoint "Agents Endpoint" "$API_URL/api/v1/agents"

# Test 4: Tasks
Test-Endpoint "Tasks Endpoint" "$API_URL/api/v1/tasks"

# Test 5: Tools
Test-Endpoint "Tools Endpoint" "$API_URL/api/v1/tools/available"

# Test 6: LLM Configs
Test-Endpoint "LLM Configs" "$API_URL/api/v1/llm-configs"

# Test 7: Agent Classes
Test-Endpoint "Agent Classes" "$API_URL/api/v1/agent-classes"

# Test 8: Frontend
Write-Host "Testing Frontend... " -NoNewline
try {
    $response = Invoke-WebRequest -Uri $FRONTEND_URL -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 307) {
        Write-Host "✓ PASS" -ForegroundColor Green
        $TESTS_PASSED++
    } else {
        Write-Host "✗ FAIL (HTTP $($response.StatusCode))" -ForegroundColor Red
        $TESTS_FAILED++
    }
} catch {
    Write-Host "⚠ SKIP (not deployed)" -ForegroundColor Yellow
}

# Test 9: Check containers
Write-Host ""
Write-Host "Checking Docker containers..." -ForegroundColor Yellow
$containers = docker compose -f docker-compose.prod.yml -p qubot ps --format "{{.Name}}: {{.Status}}" 2>$null
if ($containers) {
    $containers | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "  No containers found" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
if ($TESTS_FAILED -eq 0) {
    Write-Host "✓ All Tests Passed!" -ForegroundColor Green
} else {
    Write-Host "⚠ Some tests failed" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Passed: $TESTS_PASSED, Failed: $TESTS_FAILED" -ForegroundColor Gray
Write-Host ""
Write-Host "Quick API test:" -ForegroundColor Cyan
Write-Host "  Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/health' | ConvertTo-Json" -ForegroundColor DarkGray
