# Documentation Templates — Technical Writer

> Templates reutilizables para documentación técnica.

## 1. README Template

```markdown
# {Project Name}

{Badge: Build Status} {Badge: License} {Badge: Version}

> {One-line description of the project}

## 🚀 Quick Start

### Prerequisites
- Node.js >= 18
- Docker & Docker Compose

### Installation

\`\`\`bash
git clone {repo-url}
cd {project-name}
cp .env.example .env
docker compose up -d
\`\`\`

### Development

\`\`\`bash
npm install
npm run dev
\`\`\`

## 📁 Project Structure

\`\`\`
src/
├── api/           # API endpoints
├── services/      # Business logic
├── models/        # Data models
└── utils/         # Helpers
\`\`\`

## 🔧 Configuration

| Variable | Description | Default |
|----------|-----------|---------|
| `PORT` | Server port | 3000 |
| `DATABASE_URL` | DB connection string | - |

## 📚 Documentation

- [API Reference](docs/api.md)
- [Architecture](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)

## 📝 License

MIT © {Author}
```

## 2. API Endpoint Documentation

```markdown
## `POST /api/v1/users`

Create a new user.

### Headers

| Header | Value | Required |
|--------|-------|----------|
| Authorization | Bearer {token} | ✅ |
| Content-Type | application/json | ✅ |

### Request Body

\`\`\`json
{
  "email": "user@example.com",
  "name": "John Doe",
  "role": "admin"
}
\`\`\`

### Response `201 Created`

\`\`\`json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "admin",
  "created_at": "2024-01-21T10:30:00Z"
}
\`\`\`

### Error Responses

| Status | Description |
|--------|-----------|
| 400 | Invalid request body |
| 409 | Email already exists |
| 401 | Unauthorized |
```

## 3. ADR (Architecture Decision Record)

```markdown
# ADR-{NUMBER}: {Title}

**Status:** Proposed | Accepted | Deprecated | Superseded
**Date:** YYYY-MM-DD
**Decision Makers:** {names}

## Context

{What is the issue? Why do we need to make a decision?}

## Decision

{What is the change we're proposing/deciding?}

## Alternatives Considered

### Option A: {Name}
- **Pros:** ...
- **Cons:** ...

### Option B: {Name}
- **Pros:** ...
- **Cons:** ...

## Consequences

### Positive
- {Benefit 1}
- {Benefit 2}

### Negative
- {Tradeoff 1}
- {Tradeoff 2}

### Risks
- {Risk 1}: Mitigation: {how to mitigate}
```

## 4. Changelog Entry

```markdown
## [1.2.0] - 2024-01-21

### Added
- User profile editing (name, avatar, bio)
- Password reset via email
- API rate limiting (100 req/min)

### Changed
- Improved login page loading speed by 40%
- Updated dependency: fastapi 0.114 → 0.115

### Fixed
- Fixed: Login returns 500 on invalid email format (#42)
- Fixed: Profile image upload fails for PNG > 5MB (#38)

### Security
- Patched XSS vulnerability in user bio field
```

## 5. Onboarding Guide

```markdown
# Developer Onboarding Guide

## Day 1: Setup

### 1. Clone & Run
\`\`\`bash
git clone {repo}
cd {project}
cp .env.example .env
docker compose up -d
\`\`\`

### 2. Verify
- [ ] API running at http://localhost:8000/docs
- [ ] Frontend at http://localhost:3000
- [ ] Database connected

### 3. Create your first branch
\`\`\`bash
git checkout -b feature/your-name-onboarding
\`\`\`

## Day 2: Architecture
- Read `docs/architecture.md`
- Review the data model in `docs/data-model.md`
- Pair with a team member on a small ticket

## Day 3: First Contribution
- Pick a `good-first-issue` from the backlog
- Implement, test, submit PR
```

## Writing Style Guide

### Reglas de Oro

| ✅ Hacer | ❌ No Hacer |
|---------|------------|
| Voz activa: "Ejecuta el comando" | Voz pasiva: "El comando es ejecutado" |
| Oraciones cortas | Párrafos interminables |
| Ejemplos concretos | Descripciones abstractas |
| Bullet points para listas | Párrafos con listas inline |
| Verbos imperativos | "Deberías considerar..." |
| Títulos descriptivos | "Sección 3.2.1" |
