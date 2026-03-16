"""
Qubot Configuration - Centralized settings management
All configuration is loaded from environment variables
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # ============================================
    # Core Settings
    # ============================================
    PROJECT_NAME: str = Field(default="Qubot", description="Project name")
    API_V1_STR: str = Field(default="/api/v1", description="API version prefix")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # ============================================
    # Database
    # ============================================
    POSTGRES_USER: str = Field(default="qubot", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(
        default="qubot_pass", description="PostgreSQL password"
    )
    POSTGRES_DB: str = Field(default="qubot_db", description="PostgreSQL database name")
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://qubot:qubot_pass@db:5432/qubot_db",
        description="Full database connection URL",
    )

    # Database pool settings
    DB_POOL_SIZE: int = Field(default=20, description="SQLAlchemy connection pool size")
    DB_POOL_MAX_OVERFLOW: int = Field(
        default=40, description="Max connections above pool_size"
    )
    DB_POOL_RECYCLE: int = Field(
        default=3600, description="Recycle connections after N seconds"
    )
    DB_POOL_PRE_PING: bool = Field(
        default=True, description="Test connections before use"
    )

    # ============================================
    # Redis
    # ============================================
    REDIS_URL: str = Field(
        default="redis://redis:6379/0", description="Redis connection URL"
    )

    # ============================================
    # Security
    # ============================================
    SECRET_KEY: str = Field(
        ...,
        description="Secret key for JWT and encryption (min 32 chars, required)",
        min_length=32,
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="JWT access token expiry"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="JWT refresh token expiry"
    )

    # ============================================
    # CORS
    # ============================================
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed origins",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # ============================================
    # LLM Provider API Keys
    # ============================================
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key")
    GOOGLE_API_KEY: str = Field(default="", description="Google AI API key")
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API key")
    DEEPSEEK_API_KEY: str = Field(default="", description="DeepSeek API key")
    KIMI_API_KEY: str = Field(default="", description="Kimi API key")
    MINIMAX_API_KEY: str = Field(default="", description="MiniMax API key")
    ZHIPU_API_KEY: str = Field(default="", description="Zhipu API key")

    # ============================================
    # Ollama (Local LLM)
    # ============================================
    OLLAMA_HOST: str = Field(
        default="http://ollama:11434", description="Ollama host URL"
    )
    ENABLE_OLLAMA: bool = Field(default=True, description="Enable Ollama integration")

    # ============================================
    # Default LLM Configuration
    # ============================================
    DEFAULT_LLM_PROVIDER: str = Field(
        default="OPENAI", description="Default LLM provider"
    )
    DEFAULT_LLM_MODEL: str = Field(
        default="gpt-4o-mini", description="Default LLM model"
    )
    DEFAULT_LLM_TEMPERATURE: float = Field(
        default=0.7, description="Default temperature"
    )
    DEFAULT_LLM_MAX_TOKENS: int = Field(default=2000, description="Default max tokens")

    # ============================================
    # Telegram Bot
    # ============================================
    TELEGRAM_BOT_TOKEN: str = Field(
        default="", description="Telegram bot token from @BotFather"
    )
    TELEGRAM_WEBHOOK_URL: str = Field(
        default="", description="Public webhook URL for Telegram"
    )

    @property
    def telegram_enabled(self) -> bool:
        """Check if Telegram bot is configured"""
        return bool(self.TELEGRAM_BOT_TOKEN)

    # ============================================
    # Discord Bot
    # ============================================
    DISCORD_BOT_TOKEN: str = Field(default="", description="Discord bot token")
    DISCORD_APPLICATION_ID: str = Field(
        default="", description="Discord application ID"
    )
    DISCORD_PUBLIC_KEY: str = Field(default="", description="Discord public key")
    DISCORD_WEBHOOK_URL: str = Field(default="", description="Discord webhook URL")

    @property
    def discord_enabled(self) -> bool:
        """Check if Discord bot is configured"""
        return bool(self.DISCORD_BOT_TOKEN)

    # ============================================
    # Slack Bot
    # ============================================
    SLACK_BOT_TOKEN: str = Field(default="", description="Slack bot token (xoxb-...)")
    SLACK_SIGNING_SECRET: str = Field(default="", description="Slack signing secret")
    SLACK_APP_TOKEN: str = Field(default="", description="Slack app token (xapp-...)")
    SLACK_WEBHOOK_URL: str = Field(default="", description="Slack webhook URL")

    @property
    def slack_enabled(self) -> bool:
        """Check if Slack bot is configured"""
        return bool(self.SLACK_BOT_TOKEN)

    # ============================================
    # WhatsApp Business API
    # ============================================
    WHATSAPP_API_TOKEN: str = Field(default="", description="WhatsApp API token")
    WHATSAPP_PHONE_NUMBER_ID: str = Field(
        default="", description="WhatsApp phone number ID"
    )
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = Field(
        default="", description="WhatsApp business account ID"
    )
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = Field(
        default="", description="WhatsApp webhook verify token"
    )
    WHATSAPP_WEBHOOK_URL: str = Field(default="", description="WhatsApp webhook URL")

    @property
    def whatsapp_enabled(self) -> bool:
        """Check if WhatsApp is configured"""
        return bool(self.WHATSAPP_API_TOKEN and self.WHATSAPP_PHONE_NUMBER_ID)

    # ============================================
    # Messaging Platform General
    # ============================================
    PUBLIC_DOMAIN: str = Field(default="", description="Public domain for webhooks")

    @property
    def default_webhook_base(self) -> str:
        """Get default webhook base URL"""
        return self.PUBLIC_DOMAIN or "http://localhost:8000"

    # ============================================
    # Task Execution
    # ============================================
    MAX_TASK_ITERATIONS: int = Field(default=10, description="Maximum task iterations")
    TASK_TIMEOUT_SECONDS: int = Field(
        default=300, description="Task timeout in seconds"
    )
    WORKER_HEARTBEAT_INTERVAL: int = Field(
        default=10, description="Worker heartbeat interval"
    )
    WORKER_CLAIM_INTERVAL: int = Field(default=30, description="Worker claim interval")

    # ============================================
    # Rate Limiting
    # ============================================
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=60, description="Rate limit per minute"
    )
    RATE_LIMIT_BURST: int = Field(default=10, description="Rate limit burst")

    # ============================================
    # Feature Flags
    # ============================================
    ENABLE_REGISTRATION: bool = Field(
        default=True, description="Enable user registration"
    )

    # ============================================
    # Email (Optional)
    # ============================================
    SMTP_HOST: str = Field(default="", description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USER: str = Field(default="", description="SMTP username")
    SMTP_PASSWORD: str = Field(default="", description="SMTP password")
    SMTP_FROM: str = Field(default="noreply@qubot.io", description="SMTP from address")

    @property
    def email_enabled(self) -> bool:
        """Check if email is configured"""
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)

    # ============================================
    # S3/Storage (Optional)
    # ============================================
    S3_BUCKET: str = Field(default="", description="S3 bucket name")
    S3_ACCESS_KEY: str = Field(default="", description="S3 access key")
    S3_SECRET_KEY: str = Field(default="", description="S3 secret key")
    S3_REGION: str = Field(default="us-east-1", description="S3 region")

    @property
    def s3_enabled(self) -> bool:
        """Check if S3 is configured"""
        return bool(self.S3_BUCKET and self.S3_ACCESS_KEY and self.S3_SECRET_KEY)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
