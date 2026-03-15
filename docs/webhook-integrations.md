# Qubot — Webhook Integrations & Security

> **Module**: `backend/app/webhooks/`
> **Purpose**: Expose Qubot to external automation tools (n8n, Zapier, Make, custom apps) via authenticated HTTPS webhooks. Also documents all supported authentication mechanisms across the entire API.

---

## 1. Overview

Qubot exposes two categories of integration endpoints:

| Category | Path | Purpose |
|----------|------|---------|
| **Outbound webhooks** | Configured per event | Qubot calls YOUR URL when something happens |
| **Inbound webhooks** | `POST /webhooks/trigger/{slug}` | External tools trigger Qubot actions |
| **Generic API** | All `/api/v1/*` endpoints | Full programmatic access with auth |

---

## 2. Supported Authentication Methods

Qubot supports multiple auth mechanisms. Each can be used independently or combined.

### 2.1 JWT (Default — Web UI + API)

**Standard**: HS256 signed JSON Web Tokens

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

- **Obtain**: `POST /api/v1/auth/login` → returns `access_token` (60 min) + `refresh_token` (7 days)
- **Refresh**: `POST /api/v1/auth/refresh` → new `access_token`
- **Used by**: Web frontend, direct API consumers

```python
# backend/app/core/security.py
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config import settings

def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

def verify_token(token: str) -> str:
    """Returns subject (user_id) or raises HTTPException 401."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise ValueError("Not an access token")
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

---

### 2.2 API Keys (For n8n, Zapier, Make, automation tools)

Long-lived keys for machine-to-machine access. No expiry by default (or configurable expiry).

**Header format:**
```http
X-API-Key: qbt_live_abc123def456...
```

**Database table: `ApiKey`**
```python
class ApiKey(SQLModel, table=True):
    __tablename__ = "api_key"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str                        # Human label: "n8n Production", "Zapier"
    key_hash: str                    # bcrypt hash of the actual key
    key_prefix: str                  # First 8 chars for identification: "qbt_live"
    scopes: list[str] = Field(sa_column=Column(JSONB))  # ["tasks:read", "tasks:write", "agents:read"]
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
```

**API key scopes:**

| Scope | Access |
|-------|--------|
| `tasks:read` | GET tasks, task events |
| `tasks:write` | Create, update, delete tasks |
| `agents:read` | GET agents, status |
| `agents:write` | Update agents, status |
| `chat` | POST to /chat (orchestrator) |
| `webhooks:trigger` | Trigger inbound webhooks |
| `memory:read` | Read global + task memories |
| `memory:write` | Create/update global memories |
| `system:read` | Health + stats |
| `*` | All scopes (admin key) |

**Key generation:**
```python
import secrets

def generate_api_key() -> tuple[str, str]:
    """Returns (raw_key_to_show_once, hashed_key_to_store)."""
    raw = "qbt_live_" + secrets.token_urlsafe(32)
    hashed = bcrypt.hash(raw)
    return raw, hashed
```

**FastAPI dependency:**
```python
# backend/app/core/deps.py
async def require_api_key(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ApiKey:
    raw_key = request.headers.get("X-API-Key")
    if not raw_key:
        raise HTTPException(401, "Missing X-API-Key header")

    # Find by prefix (avoid full-table scan)
    prefix = raw_key[:8]
    key_record = await session.exec(
        select(ApiKey).where(ApiKey.key_prefix == prefix).where(ApiKey.is_active == True)
    ).first()

    if not key_record or not bcrypt.verify(raw_key, key_record.key_hash):
        raise HTTPException(401, "Invalid API key")

    if key_record.expires_at and key_record.expires_at < datetime.utcnow():
        raise HTTPException(401, "API key expired")

    # Update last_used_at (fire-and-forget, no await)
    key_record.last_used_at = datetime.utcnow()
    await session.commit()

    return key_record

def require_scope(scope: str):
    """Dependency factory: require a specific scope on the API key."""
    async def check(key: ApiKey = Depends(require_api_key)):
        if "*" not in key.scopes and scope not in key.scopes:
            raise HTTPException(403, f"API key missing required scope: {scope}")
        return key
    return check
```

---

### 2.3 OAuth 2.0 (Optional — for multi-user / third-party app integration)

For scenarios where external apps need delegated access on behalf of a Qubot user.

**Supported flows:**
- **Authorization Code** — for web apps / n8n OAuth2 credentials
- **Client Credentials** — for server-to-server (machine accounts)

**Tables:**
```python
class OAuthClient(SQLModel, table=True):
    __tablename__ = "oauth_client"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    client_id: str = Field(unique=True)
    client_secret_hash: str
    name: str
    redirect_uris: list[str] = Field(sa_column=Column(JSONB))
    allowed_scopes: list[str] = Field(sa_column=Column(JSONB))
    grant_types: list[str] = Field(sa_column=Column(JSONB))  # ["authorization_code", "refresh_token"]

class OAuthToken(SQLModel, table=True):
    __tablename__ = "oauth_token"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    client_id: str
    user_id: str
    access_token_hash: str
    refresh_token_hash: Optional[str] = None
    scopes: list[str] = Field(sa_column=Column(JSONB))
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Endpoints:**
```
GET  /oauth/authorize      — Authorization Code flow: redirect user to consent screen
POST /oauth/token          — Exchange code for tokens; refresh tokens
POST /oauth/revoke         — Revoke a token
GET  /oauth/userinfo       — Return authenticated user info
```

**Usage with n8n (OAuth2 Generic credential):**
1. Create OAuth Client in Qubot settings: `Authorization URL`, `Token URL`, `Client ID`, `Client Secret`
2. In n8n: add "Generic OAuth2" credential, fill in URLs and client credentials
3. n8n will redirect user for consent, then use Bearer access token on all requests

---

### 2.4 HMAC Webhook Signatures (For inbound webhooks from external services)

All inbound webhooks are signed so Qubot can verify the sender is legitimate.

```python
import hashlib, hmac, time

def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    timestamp: str,
    max_age_seconds: int = 300,
) -> bool:
    # Replay protection: reject if timestamp is older than 5 minutes
    if abs(time.time() - int(timestamp)) > max_age_seconds:
        return False
    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

Qubot includes this signature on all **outbound** webhook calls so the receiver can verify the request came from Qubot.

---

### 2.5 mTLS (Optional — enterprise environments)

For internal VPS networks where TLS client certificates are preferred over tokens. Configure at the Nginx level:

```nginx
# nginx/nginx.prod.conf
server {
    ssl_client_certificate /etc/ssl/qubot-ca.crt;
    ssl_verify_client optional;  # "on" to require, "optional" for mixed

    location /api/ {
        # Pass cert info to backend
        proxy_set_header X-Client-Cert $ssl_client_s_dn;
        proxy_set_header X-Client-Verified $ssl_client_verify;
    }
}
```

---

## 3. API Key Management Endpoints

```
GET    /api/v1/api-keys           — List all API keys (shows prefix + name only, never raw key)
POST   /api/v1/api-keys           — Create new key (raw key shown ONCE in response, never again)
PATCH  /api/v1/api-keys/{id}      — Update name, scopes, expiry, active status
DELETE /api/v1/api-keys/{id}      — Revoke key permanently
```

**Create key response (raw key shown only once):**
```json
{
  "data": {
    "id": "uuid",
    "name": "n8n Production",
    "key": "qbt_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "key_prefix": "qbt_live",
    "scopes": ["tasks:read", "tasks:write", "chat"],
    "expires_at": null,
    "created_at": "2024-01-15T12:00:00Z"
  },
  "warning": "This is the only time the full key will be shown. Store it securely."
}
```

---

## 4. Inbound Webhooks (External → Qubot)

External tools like n8n can trigger Qubot actions by calling these endpoints.

### 4.1 Generic Trigger Endpoint

```
POST /api/v1/webhooks/trigger/{slug}
Authorization: X-API-Key: qbt_live_...
X-Qubot-Timestamp: 1705315200
X-Qubot-Signature: sha256=abc123...
```

Each `slug` maps to a pre-configured `WebhookTrigger` record in the DB:

**Table: `WebhookTrigger`**
```python
class WebhookTrigger(SQLModel, table=True):
    __tablename__ = "webhook_trigger"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    slug: str = Field(unique=True)    # URL-safe name, e.g. "new-customer-signup"
    name: str                          # Human label
    description: str
    # What to do when triggered:
    action: WebhookActionEnum          # CREATE_TASK | SEND_CHAT | ASSIGN_AGENT | CUSTOM
    # Template for the action payload (supports {{variable}} substitution from request body)
    action_config: dict = Field(sa_column=Column(JSONB))
    signing_secret_ref: str            # Env var name for HMAC secret
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WebhookActionEnum(str, enum.Enum):
    CREATE_TASK = "create_task"
    SEND_CHAT = "send_chat"
    ASSIGN_AGENT = "assign_agent"
```

**Example: Create a task when a new customer signs up**

Configure in UI:
- Slug: `new-customer-signup`
- Action: `CREATE_TASK`
- Action config:
```json
{
  "title": "Onboard new customer: {{body.customer_name}}",
  "description": "Customer {{body.customer_email}} signed up. Plan: {{body.plan}}. Setup their account.",
  "priority": "HIGH",
  "domain_hint": "BUSINESS",
  "assigned_agent_id": "{{config.crm_agent_id}}"
}
```

**n8n sends:**
```http
POST https://yourdomain.com/api/v1/webhooks/trigger/new-customer-signup
X-API-Key: qbt_live_...
Content-Type: application/json

{
  "customer_name": "Acme Corp",
  "customer_email": "admin@acme.com",
  "plan": "Pro"
}
```

**Qubot responds:**
```json
{
  "data": {
    "trigger_id": "uuid",
    "action_taken": "create_task",
    "result": {
      "task_id": "uuid",
      "task_title": "Onboard new customer: Acme Corp"
    }
  }
}
```

**Implementation:**
```python
# backend/app/webhooks/router.py
@router.post("/webhooks/trigger/{slug}")
async def trigger_webhook(
    slug: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    api_key: ApiKey = Depends(require_scope("webhooks:trigger")),
):
    trigger = await session.exec(
        select(WebhookTrigger).where(WebhookTrigger.slug == slug).where(WebhookTrigger.is_active == True)
    ).first()
    if not trigger:
        raise HTTPException(404, "Webhook trigger not found")

    # Verify HMAC signature (if signing secret configured)
    if trigger.signing_secret_ref:
        secret = os.getenv(trigger.signing_secret_ref, "")
        timestamp = request.headers.get("X-Qubot-Timestamp", "0")
        signature = request.headers.get("X-Qubot-Signature", "")
        body = await request.body()
        if not verify_webhook_signature(body, signature, secret, timestamp):
            raise HTTPException(401, "Invalid webhook signature")

    body_json = await request.json()

    # Substitute {{variable}} templates in action_config
    resolved_config = resolve_template(trigger.action_config, {"body": body_json})

    # Execute action
    result = await execute_webhook_action(trigger.action, resolved_config, session)

    return {"data": {"trigger_id": str(trigger.id), "action_taken": trigger.action, "result": result}}
```

### 4.2 Webhook Trigger Management Endpoints

```
GET    /api/v1/webhook-triggers           — List all triggers
POST   /api/v1/webhook-triggers           — Create trigger
PUT    /api/v1/webhook-triggers/{id}      — Update trigger
DELETE /api/v1/webhook-triggers/{id}      — Delete trigger
POST   /api/v1/webhook-triggers/{id}/test — Test trigger with sample payload
```

---

## 5. Outbound Webhooks (Qubot → External)

Qubot can POST to external URLs when internal events happen — allowing n8n/Zapier/Make to react.

### 5.1 Outbound Webhook Subscriptions

**Table: `WebhookSubscription`**
```python
class WebhookSubscription(SQLModel, table=True):
    __tablename__ = "webhook_subscription"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    target_url: str                 # HTTPS URL to POST to
    events: list[str] = Field(sa_column=Column(JSONB))  # Event types to subscribe
    # Auth to include when calling target_url:
    auth_type: OutboundAuthEnum     # NONE | BEARER | API_KEY | BASIC | HMAC
    auth_config: dict = Field(sa_column=Column(JSONB))  # {"token_ref": "N8N_WEBHOOK_SECRET"}
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OutboundAuthEnum(str, enum.Enum):
    NONE = "none"
    BEARER = "bearer"       # Authorization: Bearer {token}
    API_KEY = "api_key"     # Custom header with API key
    BASIC = "basic"         # Authorization: Basic {b64(user:pass)}
    HMAC = "hmac"           # X-Signature: sha256={hmac}
```

**Subscribable events:**

| Event | Payload |
|-------|---------|
| `task.created` | Task object |
| `task.status_changed` | Task object + old_status + new_status |
| `task.completed` | Task object + TaskMemory summary |
| `task.failed` | Task object + failure reason |
| `agent.status_changed` | Agent object + old_status + new_status |
| `agent.memory_written` | AgentMemory entry |
| `chat.response` | User message + orchestrator response + actions |
| `tool.executed` | Tool name + input + output + agent_id |

### 5.2 Outbound Webhook Delivery

```python
# backend/app/webhooks/outbound.py

class WebhookDelivery(SQLModel, table=True):
    """Log of all outbound webhook attempts."""
    __tablename__ = "webhook_delivery"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    subscription_id: UUID = Field(foreign_key="webhook_subscription.id")
    event_type: str
    payload: dict = Field(sa_column=Column(JSONB))
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    attempt_count: int = 0
    next_retry_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


async def deliver_webhook(subscription: WebhookSubscription, event_type: str, payload: dict):
    """Fire-and-forget delivery with retry logic."""
    import httpx
    from tenacity import retry, stop_after_attempt, wait_exponential

    headers = {"Content-Type": "application/json", "X-Qubot-Event": event_type}
    timestamp = str(int(time.time()))
    body = json.dumps(payload).encode()

    # Add auth headers
    if subscription.auth_type == OutboundAuthEnum.BEARER:
        token = os.getenv(subscription.auth_config.get("token_ref", ""), "")
        headers["Authorization"] = f"Bearer {token}"
    elif subscription.auth_type == OutboundAuthEnum.API_KEY:
        key = os.getenv(subscription.auth_config.get("key_ref", ""), "")
        header_name = subscription.auth_config.get("header_name", "X-API-Key")
        headers[header_name] = key
    elif subscription.auth_type == OutboundAuthEnum.BASIC:
        user = os.getenv(subscription.auth_config.get("user_ref", ""), "")
        pwd = os.getenv(subscription.auth_config.get("password_ref", ""), "")
        import base64
        headers["Authorization"] = "Basic " + base64.b64encode(f"{user}:{pwd}".encode()).decode()
    elif subscription.auth_type == OutboundAuthEnum.HMAC:
        secret = os.getenv(subscription.auth_config.get("secret_ref", ""), "")
        sig = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
        headers["X-Qubot-Timestamp"] = timestamp
        headers["X-Qubot-Signature"] = f"sha256={sig}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=5, max=60))
    async def attempt():
        async with httpx.AsyncClient(timeout=10.0) as client:
            return await client.post(subscription.target_url, content=body, headers=headers)

    try:
        resp = await attempt()
        await log_delivery(subscription.id, event_type, payload, resp.status_code, "")
    except Exception as e:
        await log_delivery(subscription.id, event_type, payload, None, str(e))
```

### 5.3 Outbound Subscription Management Endpoints

```
GET    /api/v1/webhook-subscriptions              — List all subscriptions
POST   /api/v1/webhook-subscriptions              — Create subscription
PUT    /api/v1/webhook-subscriptions/{id}         — Update
DELETE /api/v1/webhook-subscriptions/{id}         — Delete
GET    /api/v1/webhook-subscriptions/{id}/deliveries  — Delivery history + status
POST   /api/v1/webhook-subscriptions/{id}/test    — Send test payload to target URL
```

---

## 6. n8n Integration Guide

### 6.1 Connecting n8n to Qubot

**Option A — API Key (Recommended)**

1. In Qubot UI: `Settings → API Keys → Create Key`
   - Name: "n8n"
   - Scopes: `tasks:read`, `tasks:write`, `chat`, `webhooks:trigger`
2. In n8n: Add "Header Auth" credential:
   - Name: `Qubot API`
   - Header: `X-API-Key`
   - Value: `qbt_live_...`

**Option B — OAuth 2.0**

1. In Qubot UI: `Settings → OAuth Clients → Create Client`
   - Name: "n8n"
   - Grant types: `authorization_code`
   - Redirect URI: `https://your-n8n.com/rest/oauth2-credential/callback`
2. In n8n: Add "Generic OAuth2" credential with Qubot's URLs

### 6.2 n8n Workflow: Create Task via Chat

```
[Webhook Trigger]
    │ receives external event
    ▼
[HTTP Request] POST https://qubot.yourdomain.com/api/v1/chat
    Headers: X-API-Key: {{$credentials.qubot.apiKey}}
    Body:
    {
      "message": "Create a task to analyze this data: {{$json.data}}"
    }
    │
    ▼
[IF] {{$json.data.actions.length > 0}}
    │ True
    ▼
[Slack] Notify team: "Qubot created task: {{$json.data.actions[0].payload.title}}"
```

### 6.3 n8n Workflow: React to Task Completion

Configure outbound webhook subscription in Qubot for `task.completed` pointing to n8n Webhook node URL.

```
[Webhook] receives POST from Qubot when task completes
    │
    ▼
[IF] {{$json.event_type == "task.completed"}}
    │
    ▼
[HTTP Request] POST to Slack/Email/CRM with task summary
```

### 6.4 n8n Workflow: Trigger from External CRM

```
[CRM Webhook] receives new lead
    │
    ▼
[HTTP Request] POST https://qubot.yourdomain.com/api/v1/webhooks/trigger/new-lead
    Headers: X-API-Key: {{$credentials.qubot.apiKey}}
    Body:
    {
      "lead_name": "{{$json.name}}",
      "lead_email": "{{$json.email}}",
      "company": "{{$json.company}}"
    }
    │
    ▼
Qubot creates task automatically via WebhookTrigger config
```

---

## 7. Security Headers & Rate Limiting

### 7.1 Rate Limiting

All API endpoints have rate limiting via `slowapi`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Applied in main.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

# Per-endpoint limits
@router.post("/chat")
@limiter.limit("30/minute")   # Max 30 chat requests per minute per IP
async def chat(request: Request, ...): ...

@router.post("/webhooks/trigger/{slug}")
@limiter.limit("100/minute")  # Webhook triggers
async def trigger(...): ...

@router.post("/auth/login")
@limiter.limit("10/minute")   # Login attempts
async def login(...): ...
```

Rate limit headers returned on every response:
```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 27
X-RateLimit-Reset: 1705315260
Retry-After: 60   # Only on 429 responses
```

### 7.2 Security Headers (Nginx)

```nginx
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

### 7.3 CORS Policy

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,   # ["https://yourdomain.com"] in prod — no wildcards
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Qubot-Timestamp", "X-Qubot-Signature"],
)
```

### 7.4 Auth Decision Tree

```
Incoming request
    │
    ├── Has "Authorization: Bearer ..." header?
    │       └── YES → JWT verification → get_current_user()
    │
    ├── Has "X-API-Key: ..." header?
    │       └── YES → API key lookup + scope check → require_scope()
    │
    ├── Has OAuth Bearer token?
    │       └── YES → OAuth token verification → get_oauth_user()
    │
    ├── Is it a platform webhook endpoint (/webhooks/telegram|whatsapp|discord|slack)?
    │       └── YES → Platform-specific HMAC/Ed25519 verification (no JWT)
    │
    ├── Is it GET /api/v1/system/health or GET /api/v1/system/metrics?
    │       └── YES → Public endpoint, no auth required
    │
    └── None of the above → HTTP 401 Unauthorized
```

---

## 8. Webhook Security Checklist

```markdown
## For every webhook endpoint
- [ ] HTTPS only (HTTP → HTTPS redirect in Nginx)
- [ ] Signature verification before processing
- [ ] Replay protection (timestamp within 5 minutes)
- [ ] Rate limiting on trigger endpoints (100/min)
- [ ] 200 response returned immediately (async processing)
- [ ] All deliveries logged to webhook_delivery table

## For outbound webhooks
- [ ] Target URL validated (HTTPS only, not localhost)
- [ ] Auth credentials stored as env var refs
- [ ] Retry with exponential backoff (max 3 attempts)
- [ ] Delivery log with status code + response body
- [ ] Dead letter queue for permanently failed deliveries

## API Keys
- [ ] Raw key shown only once (at creation)
- [ ] Only hash stored in DB (bcrypt)
- [ ] Scopes principle of least privilege
- [ ] Expiry dates for temporary integrations
- [ ] Immediate revocation via DELETE endpoint
```

---

## 9. Project Structure Addition

```
backend/app/webhooks/
├── __init__.py
├── router.py          # All webhook + API key + subscription endpoints
├── inbound.py         # Trigger handling: template resolution + action execution
├── outbound.py        # Subscription delivery: HTTP POST with auth + retry
└── security.py        # HMAC verification, API key validation, rate limit setup

backend/app/models/
├── api_key.py         # ApiKey, WebhookTrigger, WebhookSubscription, WebhookDelivery
└── oauth.py           # OAuthClient, OAuthToken (optional)

frontend/app/settings/
├── api-keys/
│   └── page.tsx       # Create/list/revoke API keys, show scopes
├── webhooks/
│   ├── triggers/
│   │   └── page.tsx   # Inbound webhook triggers: create, configure, test
│   └── subscriptions/
│       └── page.tsx   # Outbound subscriptions: events, target URL, auth, delivery history
```

Register in `app/main.py`:
```python
from app.webhooks.router import router as webhooks_router
app.include_router(webhooks_router, prefix=API_PREFIX)
```
