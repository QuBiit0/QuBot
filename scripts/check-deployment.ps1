# ===========================================
# Qubot - Windows Deployment Diagnostic Script
# ===========================================
# Usage: .\scripts\check-deployment.ps1

param(
    [switch]$Fix,
    [switch]$Start
)

# Colors
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

function Write-Header($text) {
    Write-Host ""
    Write-Host "$Cyan===========================================$Reset"
    Write-Host "$Cyan$text$Reset"
    Write-Host "$Cyan===========================================$Reset"
}

function Write-Success($text) { Write-Host "$Green✓ $text$Reset" }
function Write-Warning($text) { Write-Host "$Yellow⚠ $text$Reset" }
function Write-Error($text) { Write-Host "$Red✗ $text$Reset" }
function Write-Info($text) { Write-Host "$Blueℹ $text$Reset" }

# ===========================================
# Main Diagnostic
# ===========================================
Write-Header "Qubot Deployment Diagnostic Tool"

$Issues = @()

# ===========================================
# Check 1: Docker Desktop
# ===========================================
Write-Host "`n[1/7] Checking Docker Desktop..."

$dockerPath = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerPath) {
    Write-Error "Docker is not installed or not in PATH"
    Write-Host ""
    Write-Host "Please install Docker Desktop:"
    Write-Host "https://docs.docker.com/desktop/install/windows-install/"
    exit 1
}
Write-Success "Docker CLI found"

# Check if Docker Desktop process is running
$dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
if (-not $dockerProcess) {
    Write-Error "Docker Desktop is not running"
    Write-Host ""
    Write-Host "Please start Docker Desktop:"
    Write-Host "  1. Open Docker Desktop from Start Menu"
    Write-Host "  2. Wait for the whale icon to stop animating"
    Write-Host "  3. Run this script again"
    $Issues += "Docker Desktop not running"
} else {
    Write-Success "Docker Desktop process is running"
}

# Check Docker daemon
Write-Host "  Checking Docker daemon..."
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker daemon is responding"
    } else {
        Write-Error "Docker daemon is not responding"
        Write-Host "  Docker Desktop might still be starting up..."
        $Issues += "Docker daemon not responding"
    }
} catch {
    Write-Error "Cannot connect to Docker daemon"
    $Issues += "Docker daemon connection failed"
}

# ===========================================
# Check 2: Docker Compose
# ===========================================
Write-Host "`n[2/7] Checking Docker Compose..."

try {
    $composeVersion = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker Compose v2 available"
        $script:DOCKER_COMPOSE = "docker compose"
    } else {
        throw "Docker Compose v2 not available"
    }
} catch {
    try {
        $composeVersion = docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker Compose v1 available"
            $script:DOCKER_COMPOSE = "docker-compose"
        } else {
            throw "Docker Compose not available"
        }
    } catch {
        Write-Error "Docker Compose not found"
        $Issues += "Docker Compose not installed"
    }
}

# ===========================================
# Check 3: Project Files
# ===========================================
Write-Host "`n[3/7] Checking Project Files..."

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

if (Test-Path "docker-compose.local.yml") {
    Write-Success "docker-compose.local.yml found"
} else {
    Write-Error "docker-compose.local.yml not found"
    Write-Host "Make sure you're running this script from the project root"
    $Issues += "docker-compose.local.yml missing"
}

if (Test-Path ".env") {
    Write-Success ".env file found"
} else {
    Write-Warning ".env file not found"
    if (Test-Path ".env.example") {
        Write-Info "Creating .env from .env.example..."
        Copy-Item ".env.example" ".env"
        Write-Success ".env created (please review it!)"
    } else {
        $Issues += ".env file missing"
    }
}

if (Test-Path "backend/Dockerfile") {
    Write-Success "Backend Dockerfile found"
} else {
    Write-Error "Backend Dockerfile not found"
    $Issues += "Backend Dockerfile missing"
}

if (Test-Path "frontend/Dockerfile") {
    Write-Success "Frontend Dockerfile found"
} else {
    Write-Error "Frontend Dockerfile not found"
    $Issues += "Frontend Dockerfile missing"
}

# ===========================================
# Check 4: Port Availability
# ===========================================
Write-Host "`n[4/7] Checking Port Availability..."

$ports = @(
    @{ Port = 5432; Name = "PostgreSQL" },
    @{ Port = 6379; Name = "Redis" },
    @{ Port = 8000; Name = "API" },
    @{ Port = 3000; Name = "Frontend" }
)

$PortConflicts = @()
foreach ($portInfo in $ports) {
    $port = $portInfo.Port
    $name = $portInfo.Name
    
    $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Warning "Port $port ($name) is already in use"
        $PortConflicts += $portInfo
    } else {
        Write-Success "Port $port ($name) is available"
    }
}

if ($PortConflicts.Count -gt 0) {
    $Issues += "Port conflicts detected"
}

# ===========================================
# Check 5: WSL2 (Windows specific)
# ===========================================
Write-Host "`n[5/7] Checking WSL2..."

try {
    $wslInfo = wsl --status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "WSL2 is available"
    } else {
        Write-Warning "WSL2 might not be properly configured"
        Write-Host "  Docker Desktop might be using Hyper-V backend"
    }
} catch {
    Write-Warning "Cannot check WSL2 status"
}

# ===========================================
# Check 6: Container Status
# ===========================================
Write-Host "`n[6/7] Checking Container Status..."

try {
    $containers = docker ps -a --filter "name=qubot" --format "{{.Names}}|{{.Status}}|{{.State}}"
    if ($containers) {
        Write-Success "Qubot containers found:"
        foreach ($container in $containers) {
            $parts = $container -split "\|"
            Write-Host "  - $($parts[0]): $($parts[1])"
        }
        
        # Check running containers
        $running = docker ps --filter "name=qubot" --format "{{.Names}}"
        if ($running) {
            Write-Success "$($running.Count) container(s) running"
        } else {
            Write-Warning "No containers are currently running"
            Write-Host "  Run: .\scripts\deploy-local.sh"
            $Issues += "Containers not running"
        }
    } else {
        Write-Warning "No Qubot containers found"
        Write-Host "  The application hasn't been deployed yet"
        $Issues += "No containers found"
    }
} catch {
    Write-Warning "Cannot check container status"
}

# ===========================================
# Check 7: Service Health
# ===========================================
Write-Host "`n[7/7] Checking Service Health..."

# Check API
$apiHealthy = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health/ready" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Success "API is healthy (http://localhost:8000)"
        $apiHealthy = $true
    }
} catch {
    Write-Warning "API is not responding at http://localhost:8000/api/v1/health/ready"
    if (-not ($Issues -contains "API not responding")) {
        $Issues += "API not responding"
    }
}

# Check Frontend
$frontendHealthy = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 307) {
        Write-Success "Frontend is healthy (http://localhost:3000)"
        $frontendHealthy = $true
    }
} catch {
    Write-Warning "Frontend is not responding at http://localhost:3000"
    if (-not ($Issues -contains "Frontend not responding")) {
        $Issues += "Frontend not responding"
    }
}

# ===========================================
# Summary
# ===========================================
Write-Header "Diagnostic Summary"

if ($Issues.Count -eq 0) {
    Write-Success "All checks passed! Your deployment looks good."
    Write-Host ""
    Write-Host "Access your application:"
    Write-Host "  • API:      http://localhost:8000"
    Write-Host "  • Frontend: http://localhost:3000"
    Write-Host "  • API Docs: http://localhost:8000/docs"
} else {
    Write-Warning "Found $($Issues.Count) issue(s):"
    foreach ($issue in $Issues) {
        Write-Host "  • $issue"
    }
    
    Write-Host ""
    Write-Info "Recommendations:"
    
    if ($Issues -contains "Docker Desktop not running") {
        Write-Host ""
        Write-Host "  1. Start Docker Desktop:"
        Write-Host "     • Press Windows key, type 'Docker Desktop'"
        Write-Host "     • Click on Docker Desktop to open it"
        Write-Host "     • Wait for the whale icon to stop animating (about 30-60 seconds)"
        Write-Host "     • Run this diagnostic again"
    }
    
    if ($Issues -contains "Port conflicts detected") {
        Write-Host ""
        Write-Host "  2. Fix port conflicts:"
        Write-Host "     Some required ports (5432, 6379, 8000, 3000) are already in use."
        Write-Host "     You might have:"
        Write-Host "     • PostgreSQL running locally - Stop the Windows service"
        Write-Host "     • Redis running locally - Stop the Windows service"
        Write-Host "     • Another instance running - Run: docker-compose down"
    }
    
    if ($Issues -contains "Containers not running" -or $Issues -contains "No containers found") {
        Write-Host ""
        Write-Host "  3. Deploy the application:"
        Write-Host "     • Git Bash:   ./scripts/deploy-local.sh"
        Write-Host "     • PowerShell: docker compose -f docker-compose.local.yml up --build"
    }
}

Write-Host ""
Write-Header "Quick Commands"
Write-Host "Start:     .\scripts\deploy-local.sh"
Write-Host "Logs:      docker compose -f docker-compose.local.yml logs -f"
Write-Host "Stop:      docker compose -f docker-compose.local.yml down"
Write-Host "Clean:     docker compose -f docker-compose.local.yml down -v"
Write-Host "Diagnostic:.\scripts\check-deployment.ps1"
Write-Host ""

# ===========================================
# Auto-fix (if requested)
# ===========================================
if ($Fix -and $Issues.Count -gt 0) {
    Write-Header "Attempting Auto-Fix"
    
    if ($Issues -contains "Containers not running" -or $Issues -contains "No containers found") {
        Write-Info "Starting deployment..."
        & "$PSScriptRoot\deploy-local.sh"
    }
}

# ===========================================
# Start (if requested)
# ===========================================
if ($Start) {
    Write-Header "Starting Deployment"
    & "$PSScriptRoot\deploy-local.sh"
}
