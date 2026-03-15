# 🛠️ Tech Stack & Dependencies
> **Update Frequency:** When adding/removing dependencies or changing versions.

## Backend Stack

### Core Framework
| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115+ | Web framework |
| uvicorn[standard] | 0.27+ | ASGI server |
| pydantic | v2 | Data validation |
| pydantic-settings | 2.1+ | Configuration management |

### Database
| Package | Version | Purpose |
|---------|---------|---------|
| sqlmodel | 0.0.21+ | ORM (SQLAlchemy + Pydantic) |
| sqlalchemy | 2.0+ | SQL toolkit |
| asyncpg | 0.29+ | Async PostgreSQL driver |
| alembic | 1.13+ | Database migrations |
| psycopg2-binary | 2.9+ | Sync PostgreSQL driver (for Alembic) |

### Cache & Real-time
| Package | Version | Purpose |
|---------|---------|---------|
| redis | 5.0+ | Redis client + async support |
| websockets | 12.0+ | WebSocket support |
| aiohttp | 3.9+ | Async HTTP client (tools, browser)

### LLM Providers
| Package | Version | Purpose |
|---------|---------|---------|
| openai | 1.12+ | OpenAI SDK |
| anthropic | 0.17+ | Anthropic SDK |
| google-generativeai | 0.3+ | Google Gemini SDK |
| groq | 0.4+ | Groq SDK |
| tiktoken | 0.6+ | Token counting for OpenAI models |
| aiohttp | 3.9+ | Async HTTP for Ollama |
| httpx | 0.26+ | HTTP client for API calls |

### Tools & Execution
| Package | Version | Purpose |
|---------|---------|---------|
| beautifulsoup4 | 4.12+ | HTML parsing (browser tool) |
| lxml | 5.0+ | XML/HTML parsing backend |

### Utilities
| Package | Version | Purpose |
|---------|---------|---------|
| python-dotenv | 1.0+ | Environment variables |
| python-multipart | 0.0.9+ | Form data parsing |
| pyyaml | 6.0+ | YAML parsing |
| structlog | 24+ | Structured logging |
| tenacity | 8+ | Retry logic |
| passlib[bcrypt] | 1.7+ | Password hashing |
| python-jose[cryptography] | 3.3+ | JWT tokens |

## Frontend Stack

### Core Framework
| Package | Version | Purpose |
|---------|---------|---------|
| next | 14.1+ | React framework |
| react | ^18.2 | UI library |
| react-dom | ^18.2 | DOM renderer |
| typescript | ^5 | Type checking |

### Styling
| Package | Version | Purpose |
|---------|---------|---------|
| tailwindcss | ^3.3 | CSS framework |
| postcss | ^8 | CSS processing |
| autoprefixer | ^10 | CSS autoprefixing |
| clsx | ^2.1 | Class name utilities |
| tailwind-merge | ^2.2 | Tailwind class merging |

### UI Components
| Package | Version | Purpose |
|---------|---------|---------|
| lucide-react | ^0.323 | Icons |
| @radix-ui/* | latest | Headless UI primitives (via shadcn) |

### State Management
| Package | Version | Purpose |
|---------|---------|---------|
| zustand | ^4.5 | Global state |
| @tanstack/react-query | ^5 | Server state |

### Canvas & Visual
| Package | Version | Purpose |
|---------|---------|---------|
| konva | ^9.3 | 2D canvas library |
| react-konva | ^18.2 | React bindings for Konva |
| framer-motion | ^11 | Animations |

### Drag & Drop
| Package | Version | Purpose |
|---------|---------|---------|
| @dnd-kit/core | ^6 | Drag & drop primitives |
| @dnd-kit/sortable | ^8 | Sortable lists |
| @dnd-kit/utilities | ^3 | DnD utilities |

### Real-time
| Package | Version | Purpose |
|---------|---------|---------|
| socket.io-client | ^4.7 | WebSocket client (optional) |

## DevOps & Infrastructure

### Containerization
| Technology | Version | Purpose |
|------------|---------|---------|
| Docker | latest | Container runtime |
| docker-compose | latest | Multi-container orchestration |

### Services
| Service | Version | Purpose |
|---------|---------|---------|
| PostgreSQL | 16 | Primary database |
| Redis | 7 | Cache, queues, pub/sub |
| Nginx | 1.25+ | Reverse proxy |

## Environment Variables Required

```bash
# Database
POSTGRES_USER=qubot
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=qubot_db
DATABASE_URL=postgresql+asyncpg://qubot:secure_password@db:5432/qubot_db

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM Providers (references to env vars, not actual keys stored)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
GROQ_API_KEY=gsk_...
OLLAMA_HOST=http://localhost:11434  # For local models

# Admin
ADMIN_EMAIL=admin@qubot.local
ADMIN_PASSWORD=secure_admin_pass

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Version Constraints

- **Python**: 3.12+ (required for modern async features)
- **Node.js**: 20+ (for Next.js 14)
- **PostgreSQL**: 16+ (for JSONB and advanced features)
- **Redis**: 7+ (for Streams)

## Dependency Update Policy

1. **Patch versions**: Auto-update acceptable
2. **Minor versions**: Review changelog before updating
3. **Major versions**: Require testing in staging environment
4. **Security updates**: Apply within 7 days of release
