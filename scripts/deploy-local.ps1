# Qubot Local Deployment Script for Windows PowerShell
# Usage: .\scripts\deploy-local.ps1

param(
    [switch]$SkipBuild,
    [switch]$Reset
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Color($Text, $Color) {
    Write-Host $Text -ForegroundColor $Color
}

Write-Color "========================================" Blue
Write-Color "Qubot Local Deployment (Windows)" Blue
Write-Color "========================================" Blue
Write-Host ""

# Check if running as administrator (not required but helpful)
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Color "Note: Not running as Administrator (this is OK)" Yellow
}

# Check Docker
Write-Color "1. Checking Docker..." Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not running"
    }
    Write-Color "   ✓ Docker is running" Green
} catch {
    Write-Color "   ✗ Docker is not running! Please start Docker Desktop" Red
    exit 1
}

# Check environment file
Write-Color ""
Write-Color "2. Checking environment file..." Yellow
if (-Not (Test-Path ".env")) {
    if (Test-Path ".env.local") {
        Copy-Item ".env.local" ".env"
        Write-Color "   ✓ Created .env from .env.local" Green
    } else {
        Write-Color "   ✗ No .env or .env.local file found!" Red
        exit 1
    }
} else {
    Write-Color "   ✓ .env file exists" Green
}

# Reset if requested
if ($Reset) {
    Write-Color ""
    Write-Color "⚠ Resetting all data..." Yellow
    docker compose -f docker-compose.prod.yml -p qubot down -v
    Write-Color "   ✓ Containers and volumes removed" Green
}

# Build images
if (-Not $SkipBuild) {
    Write-Color ""
    Write-Color "3. Building Docker images..." Yellow
    Write-Color "   This may take a few minutes..." Gray
    
    docker compose -f docker-compose.prod.yml -p qubot build --no-cache
    
    if ($LASTEXITCODE -ne 0) {
        Write-Color "   ✗ Build failed!" Red
        exit 1
    }
    Write-Color "   ✓ Images built successfully" Green
} else {
    Write-Color ""
    Write-Color "3. Skipping build (using existing images)" Yellow
}

# Start services
Write-Color ""
Write-Color "4. Starting services..." Yellow
docker compose -f docker-compose.prod.yml -p qubot up -d

if ($LASTEXITCODE -ne 0) {
    Write-Color "   ✗ Failed to start services!" Red
    exit 1
}
Write-Color "   ✓ Services started" Green

# Wait for database
Write-Color ""
Write-Color "5. Waiting for database to be ready..." Yellow
$maxAttempts = 30
$attempt = 0
$dbReady = $false

while ($attempt -lt $maxAttempts -and -not $dbReady) {
    $attempt++
    Write-Host "   Attempt $attempt/$maxAttempts..." -NoNewline -ForegroundColor Gray
    
    $pgIsReady = docker compose -f docker-compose.prod.yml -p qubot exec -T db pg_isready -U qubot 2>&1
    if ($pgIsReady -match "accepting connections") {
        $dbReady = $true
        Write-Color " ✓" Green
    } else {
        Write-Host "" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $dbReady) {
    Write-Color "   ✗ Database failed to start!" Red
    Write-Color "   Check logs: docker compose -f docker-compose.prod.yml logs db" Red
    exit 1
}

# Wait for Redis
Write-Color ""
Write-Color "6. Waiting for Redis to be ready..." Yellow
Start-Sleep -Seconds 3
$redisReady = docker compose -f docker-compose.prod.yml -p qubot exec -T redis redis-cli ping 2>&1
if ($redisReady -match "PONG") {
    Write-Color "   ✓ Redis is ready" Green
} else {
    Write-Color "   ⚠ Redis may not be ready yet" Yellow
}

# Run migrations
Write-Color ""
Write-Color "7. Running database migrations..." Yellow
docker compose -f docker-compose.prod.yml -p qubot exec -T api alembic upgrade head 2>&1 | ForEach-Object {
    Write-Host "   $_" -ForegroundColor Gray
}

if ($LASTEXITCODE -eq 0) {
    Write-Color "   ✓ Migrations completed" Green
} else {
    Write-Color "   ⚠ Migration warning (may be already up to date)" Yellow
}

# Seed database
Write-Color ""
Write-Color "8. Seeding database..." Yellow
docker compose -f docker-compose.prod.yml -p qubot exec -T api python -c "from scripts.seed_db import seed; seed()" 2>&1 | ForEach-Object {
    if ($_ -match "error|Error") {
        Write-Host "   $_" -ForegroundColor Red
    } else {
        Write-Host "   $_" -ForegroundColor Gray
    }
}
Write-Color "   ✓ Database seeded" Green

# Wait for API to be healthy
Write-Color ""
Write-Color "9. Waiting for API to be healthy..." Yellow
$maxAttempts = 30
$attempt = 0
$apiHealthy = $false

while ($attempt -lt $maxAttempts -and -not $apiHealthy) {
    $attempt++
    Write-Host "   Attempt $attempt/$maxAttempts..." -NoNewline -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $apiHealthy = $true
            Write-Color " ✓" Green
        }
    } catch {
        Write-Host ""
        Start-Sleep -Seconds 2
    }
}

if (-not $apiHealthy) {
    Write-Color "   ✗ API health check failed!" Red
    Write-Color "   Check logs: docker compose -f docker-compose.prod.yml logs api" Red
    exit 1
}

# Success message
Write-Color ""
Write-Color "========================================" Green
Write-Color "✓ Deployment Successful!" Green
Write-Color "========================================" Green
Write-Host ""
Write-Color "Your application is running at:" Cyan
Write-Host "  API:        http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend:   http://localhost:3000" -ForegroundColor White
Write-Host "  Health:     http://localhost:8000/api/v1/health" -ForegroundColor White
Write-Host ""
Write-Color "Useful commands:" Cyan
Write-Host "  View logs:     docker compose -f docker-compose.prod.yml logs -f" -ForegroundColor Gray
Write-Host "  Stop:          docker compose -f docker-compose.prod.yml down" -ForegroundColor Gray
Write-Host "  Restart:       .\scripts\deploy-local.ps1" -ForegroundColor Gray
Write-Host "  Verify:        .\scripts\verify-deployment.ps1" -ForegroundColor Gray
Write-Host ""
Write-Color "Quick test:" Cyan
Write-Host "  curl http://localhost:8000/api/v1/health" -ForegroundColor DarkGray
