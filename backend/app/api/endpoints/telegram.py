"""
Telegram Bot Integration - Webhook endpoint for Telegram updates

This module provides:
- Webhook endpoint for Telegram bot updates
- Command handlers (/start, /help, /status, /tasks)
- Integration with OrchestratorService for task processing
- Real-time message responses

Setup:
1. Create a bot via @BotFather on Telegram
2. Set TELEGRAM_BOT_TOKEN environment variable
3. Set PUBLIC_DOMAIN or TELEGRAM_WEBHOOK_URL environment variable
4. Call GET /api/v1/telegram/setup to configure webhook
5. Start chatting with your bot!

Environment Variables:
- TELEGRAM_BOT_TOKEN: Required. Get from @BotFather
- PUBLIC_DOMAIN: Optional. Your public domain (e.g., https://api.qubot.io)
- TELEGRAM_WEBHOOK_URL: Optional. Full webhook URL override
"""
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.enums import PriorityEnum, DomainEnum
from app.core.realtime import broadcast_activity, EventType
from app.services.orchestrator_service import OrchestratorService
from app.services.llm_service import LLMService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


def get_bot_token() -> str:
    """Get Telegram bot token from configuration."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot token not configured. Set TELEGRAM_BOT_TOKEN environment variable."
        )
    return token


# ── Domain Detection ─────────────────────────────────────────────────────────

_DOMAIN_KEYWORDS: Dict[DomainEnum, list[str]] = {
    DomainEnum.TECH: [
        "code", "develop", "build", "fix", "bug", "feature", "api",
        "backend", "frontend", "deploy", "database", "test", "program",
        "software", "script", "function", "class", "module", "refactor",
    ],
    DomainEnum.BUSINESS: [
        "business", "strategy", "revenue", "profit", "sales", "client",
        "customer", "market", "product", "service", "contract", "deal",
    ],
    DomainEnum.FINANCE: [
        "finance", "budget", "cost", "expense", "revenue", "investment",
        "accounting", "tax", "invoice", "payment", "financial", "money",
    ],
    DomainEnum.HR: [
        "hire", "recruit", "employee", "team", "salary", "benefits",
        "onboarding", "training", "performance", "review", "hr", "human resources",
    ],
    DomainEnum.MARKETING: [
        "marketing", "campaign", "seo", "content", "social", "email",
        "ads", "brand", "audience", "analytics", "promotion", "advertising",
    ],
    DomainEnum.LEGAL: [
        "legal", "contract", "agreement", "compliance", "regulation",
        "law", "policy", "terms", "privacy", "gdpr", "license",
    ],
    DomainEnum.PERSONAL: [
        "personal", "reminder", "todo", "task", "schedule", "appointment",
        "meeting", "call", "follow up", "organize",
    ],
}


def _detect_domain(message: str) -> DomainEnum:
    """Detect the domain based on keywords."""
    lower = message.lower()
    scores: Dict[DomainEnum, int] = {d: 0 for d in DomainEnum}
    
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[domain] += 1
    
    best = max(scores, key=lambda d: scores[d])
    return best if scores[best] > 0 else DomainEnum.OTHER


# ── Telegram API Client ──────────────────────────────────────────────────────

class TelegramClient:
    """Simple async client for Telegram Bot API."""
    
    API_BASE = "https://api.telegram.org/bot"
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"{self.API_BASE}{token}"
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "Markdown",
        reply_to_message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Send a text message."""
        import aiohttp
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                result = await resp.json()
                if not result.get("ok"):
                    logger.error(f"Telegram API error: {result}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Telegram API error: {result.get('description')}"
                    )
                return result["result"]
    
    async def send_chat_action(self, chat_id: int, action: str = "typing"):
        """Send a chat action (typing, uploading_photo, etc.)."""
        import aiohttp
        
        url = f"{self.base_url}/sendChatAction"
        payload = {"chat_id": chat_id, "action": action}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                return await resp.json()
    
    async def set_webhook(self, url: str, secret_token: Optional[str] = None) -> bool:
        """Set the webhook URL."""
        import aiohttp
        
        api_url = f"{self.base_url}/setWebhook"
        payload = {"url": url}
        if secret_token:
            payload["secret_token"] = secret_token
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as resp:
                result = await resp.json()
                return result.get("ok", False)
    
    async def delete_webhook(self) -> bool:
        """Delete the webhook."""
        import aiohttp
        
        url = f"{self.base_url}/deleteWebhook"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as resp:
                result = await resp.json()
                return result.get("ok", False)
    
    async def get_me(self) -> Dict[str, Any]:
        """Get bot information."""
        import aiohttp
        
        url = f"{self.base_url}/getMe"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                result = await resp.json()
                if result.get("ok"):
                    return result["result"]
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to get bot info"
                )


# ── Message Handlers ─────────────────────────────────────────────────────────

async def handle_start_command(
    client: TelegramClient,
    chat_id: int,
    user_name: str,
) -> None:
    """Handle /start command."""
    welcome_text = f"""Hello {user_name}!

I'm **Qubot**, your AI team coordinator. I can help you:

*Create and assign tasks* to specialized AI agents
*Track progress* on your tasks
*Chat naturally* - just tell me what you need

*Quick commands:*
/start - Show this welcome message
/help - Get help and examples
/status - Check system status
/tasks - List your recent tasks

Just send me a message like:
"Create a Python script to fetch weather data"
"""
    
    await client.send_message(chat_id, welcome_text)


async def handle_help_command(
    client: TelegramClient,
    chat_id: int,
) -> None:
    """Handle /help command."""
    help_text = """**Qubot Help**

*How to use me:*

1. **Create a task** - Just describe what you need:
   - "Build a React login form"
   - "Analyze my sales data"
   - "Write a marketing email"

2. **I'll analyze your request** and assign it to the best AI agent

3. **Track progress** - You'll get updates as the agent works

4. **Get results** - The agent will deliver the completed work

*Domains I can help with:*
- Tech - Coding, scripts, APIs, databases
- Business - Strategy, planning, analysis
- Finance - Budgets, reports, accounting
- HR - Hiring, training, team management
- Marketing - Campaigns, SEO, content
- Legal - Contracts, compliance, policies
- Personal - Reminders, todos, scheduling

*Need help?* Just ask! I'm here to coordinate your AI team.
"""
    
    await client.send_message(chat_id, help_text)


async def handle_status_command(
    client: TelegramClient,
    chat_id: int,
    session: AsyncSession,
) -> None:
    """Handle /status command."""
    from sqlalchemy import select, func
    from app.models.task import Task
    from app.models.agent import Agent
    from app.models.enums import TaskStatusEnum, AgentStatusEnum
    
    # Get stats
    total_tasks = await session.scalar(select(func.count(Task.id)))
    active_tasks = await session.scalar(
        select(func.count(Task.id)).where(Task.status == TaskStatusEnum.IN_PROGRESS)
    )
    completed_tasks = await session.scalar(
        select(func.count(Task.id)).where(Task.status == TaskStatusEnum.DONE)
    )
    
    total_agents = await session.scalar(select(func.count(Agent.id)))
    active_agents = await session.scalar(
        select(func.count(Agent.id)).where(Agent.status == AgentStatusEnum.WORKING)
    )
    
    status_text = f"""**System Status**

*Agents:*
   - Total: {total_agents or 0}
   - Active: {active_agents or 0}

*Tasks:*
   - Total: {total_tasks or 0}
   - In Progress: {active_tasks or 0}
   - Completed: {completed_tasks or 0}

All systems operational!
"""
    
    await client.send_message(chat_id, status_text)


async def handle_tasks_command(
    client: TelegramClient,
    chat_id: int,
    session: AsyncSession,
    user_id: int,
) -> None:
    """Handle /tasks command."""
    from sqlalchemy import select
    from app.models.task import Task
    from app.models.enums import TaskStatusEnum
    
    # Get recent tasks (limit 5)
    result = await session.execute(
        select(Task)
        .where(Task.created_by == str(user_id))
        .order_by(Task.created_at.desc())
        .limit(5)
    )
    tasks = result.scalars().all()
    
    if not tasks:
        await client.send_message(
            chat_id,
            "You don't have any tasks yet.\n\nSend me a message to create your first task!"
        )
        return
    
    tasks_text = "**Your Recent Tasks**\n\n"
    
    status_emoji = {
        TaskStatusEnum.PENDING: "⏳",
        TaskStatusEnum.IN_PROGRESS: "🔄",
        TaskStatusEnum.DONE: "✅",
        TaskStatusEnum.FAILED: "❌",
    }
    
    for task in tasks:
        emoji = status_emoji.get(task.status, "❓")
        title = task.title[:40] + "..." if len(task.title) > 40 else task.title
        tasks_text += f"{emoji} *{title}*\n"
        tasks_text += f"   Status: `{task.status.value}`\n\n"
    
    tasks_text += f"_Showing last {len(tasks)} tasks_"
    
    await client.send_message(chat_id, tasks_text)


async def handle_message(
    client: TelegramClient,
    chat_id: int,
    message_text: str,
    user_id: int,
    user_name: str,
    session: AsyncSession,
    reply_to_message_id: Optional[int] = None,
) -> None:
    """Handle incoming message - process through orchestrator."""
    
    # Send typing indicator
    await client.send_chat_action(chat_id, "typing")
    
    # Detect domain
    domain = _detect_domain(message_text)
    logger.info(f"[telegram] User {user_id} sent message, detected domain: {domain.value}")
    
    # Get LLM config
    llm_service = LLMService(session)
    configs = await llm_service.get_default_configs()
    
    if not configs:
        await client.send_message(
            chat_id,
            "I'm not fully set up yet. No LLM configuration found.",
            reply_to_message_id=reply_to_message_id,
        )
        return
    
    llm_config_id = configs[0].id
    
    try:
        # Process through orchestrator
        orchestrator = OrchestratorService(session)
        
        result = await orchestrator.process_task(
            title=message_text[:200],
            description=message_text,
            llm_config_id=llm_config_id,
            priority=PriorityEnum.MEDIUM,
            requested_domain=domain,
            input_data={
                "source": "telegram",
                "telegram_user_id": user_id,
                "telegram_user_name": user_name,
            },
            created_by=str(user_id),
        )
        
        # Build response
        if result.get("success"):
            task_id = result.get("parent_task_id", "unknown")
            assigned_agent = result.get("assigned_agent", "an agent")
            
            subtasks = result.get("subtasks", [])
            
            if subtasks:
                response = f"""Task created and analyzed!

I've broken this down into *{len(subtasks)} steps* and assigned them to specialized agents.

Task ID: `{task_id}`
Coordinator: {assigned_agent}
Domain: {domain.value}

You'll receive updates as each step completes."""
            else:
                response = f"""Task created and assigned!

Task ID: `{task_id}`
Agent: {assigned_agent}
Domain: {domain.value}

The agent is working on it now. I'll notify you when it's done!"""
            
            # Broadcast activity
            await broadcast_activity(
                "task_created",
                "Telegram Bot",
                f"New task from {user_name}: {message_text[:50]}...",
                {"source": "telegram", "user_id": user_id},
            )
        else:
            error = result.get("error", "Unknown error")
            response = f"I couldn't process your request: {error}"
        
        await client.send_message(
            chat_id,
            response,
            reply_to_message_id=reply_to_message_id,
        )
        
    except Exception as e:
        logger.exception("Error processing Telegram message")
        await client.send_message(
            chat_id,
            "Sorry, something went wrong processing your request. Please try again!",
            reply_to_message_id=reply_to_message_id,
        )


# ── Webhook Endpoint ─────────────────────────────────────────────────────────

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Receive webhook updates from Telegram.
    
    Configure this URL in Telegram:
    POST https://your-domain/api/v1/telegram/webhook
    """
    try:
        data = await request.json()
        logger.debug(f"[telegram] webhook received: {data}")
        
        # Validate message structure
        if "message" not in data:
            logger.warning(f"[telegram] no message in update: {data}")
            return {"ok": True}  # Acknowledge anyway
        
        message = data["message"]
        chat = message.get("chat", {})
        from_user = message.get("from", {})
        
        chat_id = chat.get("id")
        user_id = from_user.get("id")
        user_name = from_user.get("first_name", "User")
        message_text = message.get("text", "")
        message_id = message.get("message_id")
        
        if not chat_id or not message_text:
            logger.warning("[telegram] missing chat_id or message_text")
            return {"ok": True}
        
        # Initialize client
        token = get_bot_token()
        client = TelegramClient(token)
        
        # Handle commands
        if message_text.startswith("/"):
            command = message_text.split()[0].lower()
            
            if command == "/start":
                await handle_start_command(client, chat_id, user_name)
            elif command == "/help":
                await handle_help_command(client, chat_id)
            elif command == "/status":
                await handle_status_command(client, chat_id, session)
            elif command == "/tasks":
                await handle_tasks_command(client, chat_id, session, user_id)
            else:
                await client.send_message(
                    chat_id,
                    f"Unknown command: {command}\n\nUse /help to see available commands."
                )
        else:
            # Handle regular message
            await handle_message(
                client,
                chat_id,
                message_text,
                user_id,
                user_name,
                session,
                reply_to_message_id=message_id,
            )
        
        return {"ok": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error handling Telegram webhook")
        return {"ok": False, "error": str(e)}


@router.get("/setup")
async def setup_telegram_webhook(
    url: Optional[str] = None,
):
    """
    Setup webhook URL with Telegram.
    
    Query params:
    - url: The webhook URL (e.g., https://your-domain/api/v1/telegram/webhook)
    
    If no URL provided, uses TELEGRAM_WEBHOOK_URL from config or constructs from PUBLIC_DOMAIN.
    """
    token = get_bot_token()
    client = TelegramClient(token)
    
    # Determine webhook URL
    webhook_url = url or settings.TELEGRAM_WEBHOOK_URL
    if not webhook_url and settings.PUBLIC_DOMAIN:
        webhook_url = f"{settings.PUBLIC_DOMAIN}/api/v1/telegram/webhook"
    
    if webhook_url:
        success = await client.set_webhook(webhook_url)
        if success:
            return {
                "ok": True,
                "message": f"Webhook set to: {webhook_url}",
                "configuration": {
                    "token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
                    "public_domain": settings.PUBLIC_DOMAIN or "Not set",
                    "webhook_url": webhook_url,
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to set webhook with Telegram"
            )
    
    # Return bot info and configuration status
    bot_info = await client.get_me()
    return {
        "ok": True,
        "bot": bot_info,
        "configuration": {
            "token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
            "public_domain": settings.PUBLIC_DOMAIN or "Not set",
            "webhook_url_configured": bool(settings.TELEGRAM_WEBHOOK_URL),
            "enabled": settings.telegram_enabled,
        },
        "setup_instructions": {
            "step1": "Get bot token from @BotFather on Telegram",
            "step2": "Set TELEGRAM_BOT_TOKEN environment variable",
            "step3": "Set PUBLIC_DOMAIN (e.g., https://your-domain.com)",
            "step4": "Call this endpoint or it will auto-configure on startup",
            "step5": "Start chatting with your bot on Telegram!",
        },
    }


@router.delete("/webhook")
async def delete_telegram_webhook():
    """Remove webhook and switch to polling mode (for development)."""
    token = get_bot_token()
    client = TelegramClient(token)
    
    success = await client.delete_webhook()
    if success:
        return {"ok": True, "message": "Webhook deleted"}
    else:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to delete webhook"
        )


@router.get("/config")
async def get_telegram_config():
    """
    Get current Telegram configuration (safe - no sensitive data exposed).
    Use this to check if Telegram is properly configured.
    """
    return {
        "enabled": settings.telegram_enabled,
        "token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
        "public_domain": settings.PUBLIC_DOMAIN or "Not set",
        "webhook_url_configured": bool(settings.TELEGRAM_WEBHOOK_URL),
        "webhook_url": settings.TELEGRAM_WEBHOOK_URL or f"{settings.PUBLIC_DOMAIN}/api/v1/telegram/webhook" if settings.PUBLIC_DOMAIN else None,
    }
