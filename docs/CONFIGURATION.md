# Qubot Configuration Guide

This guide explains how to configure all services and integrations in Qubot.

## Overview

All configuration is done via environment variables. You can:
1. Create a `.env` file (recommended for development)
2. Set environment variables directly (recommended for production)
3. Use Docker Compose environment section

## Quick Start

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and configure the services you need

3. Start the application:
```bash
docker-compose up -d
```

4. Check configuration status:
```bash
curl http://localhost:8000/api/v1/config/
```

## Core Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Secret for JWT tokens | `your-secret-key-min-32-chars` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@db:5432/dbname` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |

### Optional Core Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `API_V1_STR` | `/api/v1` | API version prefix |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS allowed origins (comma-separated) |

## LLM Providers

Configure at least one LLM provider to enable AI functionality.

### OpenAI
```bash
OPENAI_API_KEY=sk-your-openai-key
```

### Anthropic (Claude)
```bash
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

### Google (Gemini)
```bash
GOOGLE_API_KEY=your-google-api-key
```

### Groq (Fast Inference)
```bash
GROQ_API_KEY=gsk-your-groq-key
```

### Other Providers
```bash
# OpenRouter (multi-provider)
OPENROUTER_API_KEY=sk-or-your-key

# DeepSeek
DEEPSEEK_API_KEY=sk-your-deepseek-key

# Kimi
KIMI_API_KEY=sk-your-kimi-key

# MiniMax
MINIMAX_API_KEY=your-minimax-key

# Zhipu
ZHIPU_API_KEY=your-zhipu-key
```

### Ollama (Local Models)
```bash
ENABLE_OLLAMA=true
OLLAMA_HOST=http://ollama:11434
```

### Default LLM Settings
```bash
DEFAULT_LLM_PROVIDER=OPENAI
DEFAULT_LLM_MODEL=gpt-4o-mini
DEFAULT_LLM_TEMPERATURE=0.7
DEFAULT_LLM_MAX_TOKENS=2000
```

## Messaging Bots

### Telegram Bot

1. **Create Bot**:
   - Open Telegram and search for [@BotFather](https://t.me/botfather)
   - Send `/newbot` and follow instructions
   - Copy the bot token

2. **Configure**:
```bash
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
PUBLIC_DOMAIN=https://your-domain.com
```

3. **Setup Webhook**:
```bash
curl http://localhost:8000/api/v1/telegram/setup
```

4. **Test**:
   - Open your bot on Telegram
   - Send `/start`
   - Send any message

### Discord Bot

1. **Create Application**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create New Application
   - Go to Bot section and create a bot
   - Copy the token

2. **Configure**:
```bash
DISCORD_BOT_TOKEN=your-discord-bot-token
DISCORD_APPLICATION_ID=your-application-id
DISCORD_PUBLIC_KEY=your-public-key
PUBLIC_DOMAIN=https://your-domain.com
```

3. **Setup**:
```bash
curl http://localhost:8000/api/v1/discord/setup
```

### Slack Bot

1. **Create App**:
   - Go to [Slack API](https://api.slack.com/apps)
   - Create New App
   - Go to OAuth & Permissions
   - Add Bot Token Scopes: `chat:write`, `im:history`, `im:read`
   - Install to workspace

2. **Configure**:
```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
PUBLIC_DOMAIN=https://your-domain.com
```

3. **Setup**:
```bash
curl http://localhost:8000/api/v1/slack/setup
```

### WhatsApp Business API

1. **Set up Meta Business Account**:
   - Go to [Meta for Developers](https://developers.facebook.com/)
   - Create app with WhatsApp product
   - Add phone number

2. **Configure**:
```bash
WHATSAPP_API_TOKEN=your-api-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_BUSINESS_ACCOUNT_ID=your-business-account-id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-verify-token
PUBLIC_DOMAIN=https://your-domain.com
```

3. **Setup**:
```bash
curl http://localhost:8000/api/v1/whatsapp/setup
```

## Public Domain Configuration

For webhook-based integrations (Telegram, Discord, Slack, WhatsApp), you need a public domain:

### Development (Local Tunnel)

Use ngrok or similar:
```bash
ngrok http 8000
```

Then set:
```bash
PUBLIC_DOMAIN=https://your-ngrok-url.ngrok.io
```

### Production

Set your actual domain:
```bash
PUBLIC_DOMAIN=https://api.yourdomain.com
```

## Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_REGISTRATION` | `true` | Allow new user registration |
| `ENABLE_OLLAMA` | `true` | Enable Ollama local LLM integration |
| `RATE_LIMIT_ENABLED` | `true` | Enable API rate limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Rate limit per minute |

## Task Execution Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_TASK_ITERATIONS` | `10` | Maximum iterations for task execution |
| `TASK_TIMEOUT_SECONDS` | `300` | Task timeout (5 minutes) |
| `WORKER_HEARTBEAT_INTERVAL` | `10` | Worker heartbeat interval (seconds) |
| `WORKER_CLAIM_INTERVAL` | `30` | Worker claim interval (seconds) |

## Email Configuration (Optional)

For email notifications:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com
```

## S3 Storage (Optional)

For file uploads:
```bash
S3_BUCKET=your-bucket-name
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_REGION=us-east-1
```

## Checking Configuration

### Check All Configuration
```bash
curl http://localhost:8000/api/v1/config/
```

### Check LLM Providers
```bash
curl http://localhost:8000/api/v1/config/llm-providers
```

### Check Messaging Status
```bash
curl http://localhost:8000/api/v1/config/messaging
```

### Check Telegram Config
```bash
curl http://localhost:8000/api/v1/telegram/config
```

## Environment-Specific Examples

### Development
```bash
DEBUG=true
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
PUBLIC_DOMAIN=https://your-ngrok-url.ngrok.io

# Use OpenAI for development
OPENAI_API_KEY=sk-your-key
DEFAULT_LLM_PROVIDER=OPENAI
DEFAULT_LLM_MODEL=gpt-4o-mini

# Enable all bots
TELEGRAM_BOT_TOKEN=your-telegram-token
DISCORD_BOT_TOKEN=your-discord-token
SLACK_BOT_TOKEN=your-slack-token
```

### Production
```bash
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://app.yourdomain.com
PUBLIC_DOMAIN=https://api.yourdomain.com

# Use multiple providers for redundancy
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
GROQ_API_KEY=gsk-your-key
DEFAULT_LLM_PROVIDER=OPENAI
DEFAULT_LLM_MODEL=gpt-4o

# Enable Telegram for production
TELEGRAM_BOT_TOKEN=your-telegram-token
TELEGRAM_WEBHOOK_URL=https://api.yourdomain.com/api/v1/telegram/webhook

# Security
SECRET_KEY=your-super-secret-production-key-min-32-chars
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Docker Compose Configuration

You can also set configuration in `docker-compose.yml`:

```yaml
services:
  api:
    environment:
      - DEBUG=false
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - PUBLIC_DOMAIN=${PUBLIC_DOMAIN}
```

## Troubleshooting

### Check Configuration Not Loading
1. Verify `.env` file exists in project root
2. Check file permissions: `chmod 600 .env`
3. Restart containers: `docker-compose restart`

### Webhook Not Working
1. Verify `PUBLIC_DOMAIN` is set to your public URL
2. Check domain is accessible via HTTPS
3. Verify bot token is correct
4. Check logs: `docker-compose logs api`

### LLM Not Working
1. Check API key is set: `curl http://localhost:8000/api/v1/config/llm-providers`
2. Verify API key is valid
3. Check rate limits on provider dashboard

## Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use strong `SECRET_KEY`** in production (min 32 chars)
3. **Rotate API keys** regularly
4. **Use different keys** for development and production
5. **Enable HTTPS** for webhooks in production
6. **Set up proper CORS** origins
7. **Use environment-specific databases**

## Complete Example .env

See `.env.example` for a complete template with all available options.
