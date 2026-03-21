# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-03-20

### Backend Fixes

#### Channels - All 17 channels now route to agent pipeline ✅
Fixed critical issue where 10 channels logged messages but never processed them through the agent orchestration pipeline.

**Channels rewritten to use proper `InboundMessage`/`OutboundMessage` pattern:**
- `line_channel.py` - Complete implementation with LINE API v2 (223 lines)
- `zalo_channel.py` - Full HMAC-SHA256 webhook verification
- `synology_chat_channel.py` - Complete webhook handling
- `feishu_channel.py` - Access token management and event handling
- `signal_channel.py` - Complete rewrite using signal-cli
- `teams_channel.py` - Bot Framework integration with OAuth2
- `googlechat_channel.py` - Google Cloud service account auth
- `imessage_channel.py` - BlueBubbles and AppleScript support
- `matrix_channel.py` - Matrix.org protocol with room management
- `mattermost_channel.py` - Mattermost API integration
- `irc_channel.py` - IRC webhook support
- `twitch_channel.py` - Twitch Events API integration
- `nostr_channel.py` - Nostr relay integration

**Key fix:** All channels now call `await self._process_message(msg, session)` in `handle_webhook()` to route messages through the OrchestratorService.

#### Plugin SDK - Fully Implemented ✅
- `backend/app/plugins/base.py` - BasePlugin, ChannelPlugin, ToolPlugin, IntegrationPlugin ABCs
- `backend/app/plugins/loader.py` - Filesystem-based plugin discovery with validation
- `backend/app/plugins/manager.py` - Full lifecycle management with hot-reload support
- `backend/app/plugins/examples/hello-world/` - Example plugin with manifest

#### SecretsManager - Fully Implemented ✅
- `retrieve_secret()` - Fetches and decrypts from PostgreSQL
- `list_secrets()` - Returns metadata without exposing values
- `delete_secret()` - Removes secret from database
- `update_secret()` - Updates value, description, tags
- `rotate_secret()` - Rotation with audit trail
- New `backend/app/models/secret.py` - SQLModel with Fernet encryption

#### Skill Execution Endpoint ✅
- `POST /skills/{skill_id}/execute` - Execute skills with code validation and timeout
- Integrated with existing `SkillExecutionService`

#### LSP Errors Fixed
- `tool_execution_service.py` - Loop detection method names corrected
- `base.py` (tools) - Schema type annotation fixed
- `browser_tool.py` - BeautifulSoup types fixed
- `seed_user.py` - AsyncSession usage corrected
- `script_execution_service.py` - SKILLS_PATH configuration fixed
- `tool.py` - Circular import resolved with TYPE_CHECKING

### Frontend Fixes

#### Clock Widget - Fixed ✅
- `OfficeSystem.tsx` - Changed from `toLocaleTimeString()` to explicit local timezone formatting
- Now shows `HH:MM:SS` in 24-hour format with user's local timezone

#### Navigation - Added Office button ✅
- `app/agents/[id]/page.tsx` - Breadcrumb now includes 🏠 Office link
- `app/agents/page.tsx` - Header includes "Office" home button

### System Verification
```
✅ Backend imports OK
✅ 31 tools registered
✅ 16 channel modules import
✅ 17 channels route to agent pipeline
✅ Plugin SDK functional
✅ SecretsManager with DB support
✅ Frontend builds (28 pages)
```

### New Files Created

#### Backend:
```
backend/app/models/secret.py              - Secret SQLModel
backend/app/plugins/base.py              - Plugin ABCs
backend/app/plugins/loader.py            - Plugin loader
backend/app/plugins/manager.py           - Lifecycle manager
backend/app/plugins/__init__.py          - Exports
backend/app/plugins/examples/hello-world/ - Example plugin
backend/app/api/endpoints/secrets.py      - Secrets API
backend/app/api/endpoints/voice.py       - Voice API
backend/app/api/endpoints/calendar.py    - Calendar API
```

#### Frontend:
```
frontend/app/secrets/page.tsx    - Secrets management UI
frontend/app/voice/page.tsx     - Voice assistant UI
frontend/app/calendar/page.tsx  - Calendar UI
frontend/app/skills/page.tsx    - Skills marketplace UI
frontend/app/nodes/page.tsx      - Agent nodes UI
frontend/app/webchat/page.tsx   - Web chat widget UI
```

#### Documentation:
```
docs/ANALYSIS-QUBOT-VS-OPENCLAW-VS-NANOBOT.md - Competitive analysis
```

---

## [0.1.0] - 2026-03-15

### Added
- FastAPI backend with 14 REST API routers
- PostgreSQL 16 database with 14 SQLModel tables and Alembic migrations
- Redis 7 integration for caching, task queues (Streams), and WebSocket pub/sub
- 5 LLM providers: OpenAI, Anthropic, Google, Groq, Ollama
- 6 tool implementations: HTTP, Shell, Browser, Filesystem, Scheduler
- Multi-agent orchestration with intelligent task assignment
- Background worker with Redis Streams consumer groups
- WebSocket real-time event system
- JWT authentication with refresh tokens
- Rate limiting and security middleware
- Next.js 15 frontend with Tailwind CSS and Shadcn/ui
- Kanban board with drag-and-drop (dnd-kit)
- Coworking office canvas (Konva.js)
- Agent creation wizard (6-step form)
- Zustand state management with TanStack Query
- Docker Compose orchestration (7 services)
- Kubernetes manifests
- Nginx reverse proxy configuration
- Prometheus metrics and Grafana dashboards
- Comprehensive documentation (22 docs)
