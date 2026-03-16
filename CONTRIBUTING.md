# Contributing to Qubot

## Development Setup

### Prerequisites
- Python 3.12+
- Node.js 22+
- Docker & Docker Compose
- PostgreSQL 16 (or use Docker)
- Redis 7 (or use Docker)

### Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd Qubot

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install --include=dev

# Start infrastructure
docker compose up db redis -d

# Run backend
cd ../backend
uvicorn app.main:app --reload --port 8000

# Run frontend (another terminal)
cd ../frontend
npm run dev
```

## Code Quality

### Backend (Python)
```bash
cd backend
ruff check .        # Lint
ruff format .       # Format
pytest              # Test
```

### Frontend (TypeScript)
```bash
cd frontend
npx eslint .        # Lint
npx prettier --check .  # Format check
npx tsc --noEmit    # Type check
```

## Git Workflow

### Branch Naming
- `feat/description` — New features
- `fix/description` — Bug fixes
- `refactor/description` — Code refactoring
- `docs/description` — Documentation

### Commit Messages
Format: `type(scope): description`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Examples:
```
feat(agents): add agent status transition validation
fix(auth): handle expired refresh tokens correctly
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for system design.

### Backend Layers
```
Routers (HTTP) → Services (Business Logic) → Repositories (Data Access)
```

### Key Rules
- Type hints on all public functions
- Pydantic schemas for all API inputs/outputs
- No business logic in routers
- No credentials in code — use environment variables
