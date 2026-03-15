# Qubot Diagnostic Script for Windows PowerShell
# Run: .\scripts\diagnose.ps1

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Qubot Deployment Diagnostics" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Check 1: Docker
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
$dockerVersion = docker version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Docker is installed" -ForegroundColor Green
    docker version --format '{{.Server.Version}}' 2>$null | ForEach-Object { Write-Host "   Version: $_" -ForegroundColor Gray }
} else {
    Write-Host "   ✗ Docker is not running or not installed" -ForegroundColor Red
    Write-Host "   Please start Docker Desktop" -ForegroundColor Red
    exit 1
}

# Check 2: Docker Compose
Write-Host ""
Write-Host "2. Checking Docker Compose..." -ForegroundColor Yellow
$composeVersion = docker compose version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Docker Compose is available" -ForegroundColor Green
} else {
    Write-Host "   ✗ Docker Compose not found" -ForegroundColor Red
    exit 1
}

# Check 3: Environment file
Write-Host ""
Write-Host "3. Checking environment file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   ✓ .env file exists" -ForegroundColor Green
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "SECRET_KEY=.*your-.*-production" -or $envContent -match "SECRET_KEY=.*local-development") {
        Write-Host "   ⚠ Using default SECRET_KEY - change this for production!" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✗ .env file not found" -ForegroundColor Red
    Write-Host "   Creating from .env.local..." -ForegroundColor Yellow
    if (Test-Path ".env.local") {
        Copy-Item ".env.local" ".env"
        Write-Host "   ✓ Created .env from .env.local" -ForegroundColor Green
    } else {
        Write-Host "   ✗ .env.local not found either" -ForegroundColor Red
    }
}

# Check 4: Docker Compose file
Write-Host ""
Write-Host "4. Checking Docker Compose file..." -ForegroundColor Yellow
if (Test-Path "docker-compose.prod.yml") {
    Write-Host "   ✓ docker-compose.prod.yml exists" -ForegroundColor Green
} else {
    Write-Host "   ✗ docker-compose.prod.yml not found" -ForegroundColor Red
    exit 1
}

# Check 5: Running containers
Write-Host ""
Write-Host "5. Checking running containers..." -ForegroundColor Yellow
$containers = docker compose -f docker-compose.prod.yml -p qubot ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}" 2>$null
if ($containers) {
    Write-Host "   Current containers:" -ForegroundColor Gray
    $containers | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "   No containers running" -ForegroundColor Yellow
}

# Check 6: Check specific services
Write-Host ""
Write-Host "6. Testing services..." -ForegroundColor Yellow

# Test API
Write-Host "   Testing API on port 8000..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✓ API is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "   ✗ API not responding (this is normal if not deployed yet)" -ForegroundColor Yellow
}

# Check 7: Port availability
Write-Host ""
Write-Host "7. Checking port availability..." -ForegroundColor Yellow
$ports = @(8000, 3000, 5432, 6379)
foreach ($port in $ports) {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Host "   Port $port : ✓ In use" -ForegroundColor Green
    } else {
        Write-Host "   Port $port : ✗ Available (not in use)" -ForegroundColor Gray
    }
}

# Check 8: Disk space
Write-Host ""
Write-Host "8. Checking disk space..." -ForegroundColor Yellow
docker system df

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Diagnostics Complete" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run deployment: .\scripts\deploy-local.ps1" -ForegroundColor White
Write-Host "  2. Or manually: docker compose -f docker-compose.prod.yml up -d" -ForegroundColor White
Write-Host "  3. Check logs: docker compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
Write-Host ""
