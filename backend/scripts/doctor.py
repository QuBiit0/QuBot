import asyncio
import os
import sys

from sqlalchemy import text

# ANSI escape codes for colors
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

# Add backend directory to sys.path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine

async def check_database():
    """Test database connection"""
    print(f"{Colors.CYAN}Checking Database...{Colors.ENDC}")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print(f"{Colors.GREEN}✅ Database connection successful{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Database connection failed: {e}{Colors.ENDC}")
        return False
    return True

def check_security_env():
    """Verify security environment variables are set correctly"""
    print(f"\n{Colors.CYAN}Checking Security Config...{Colors.ENDC}")
    
    # Using list to bypass Pyre's strict reassignment + syntax analysis on local vars
    issue_tracker = [0]

    defaults_to_avoid = {
        "JWT_SECRET": "qubot_super_secret_key_change_in_production",
        "ENCRYPTION_KEY": "0123456789abcdef0123456789abcdef",
    }

    for env_var, default_val in defaults_to_avoid.items():
        val = os.getenv(env_var, default_val)
        if val == default_val:
            print(f"{Colors.YELLOW}⚠️  WARNING: {env_var} is using the default insecure value! Change it.{Colors.ENDC}")
            issue_tracker[0] += 1
        else:
            print(f"{Colors.GREEN}✅ {env_var} is securely configured.{Colors.ENDC}")

    # Check TLS/SSL in prod
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        db_url = os.getenv("DATABASE_URL", "")
        if "?sslmode=" not in db_url:
            print(f"{Colors.YELLOW}⚠️  WARNING: Production DATABASE_URL does not specify sslmode.{Colors.ENDC}")
            issue_tracker[0] += 1

    if issue_tracker[0] == 0:
        print(f"{Colors.GREEN}✅ No obvious security misconfigurations found.{Colors.ENDC}")

def check_providers_env():
    """Verify LLM and plugin environment variables are present"""
    print(f"\n{Colors.CYAN}Checking Integration Keys...{Colors.ENDC}")
    keys_to_check = [
        "OPENROUTER_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "DISCORD_BOT_TOKEN",
        "SLACK_BOT_TOKEN",
    ]

    for key in keys_to_check:
        if os.getenv(key):
            print(f"{Colors.GREEN}✅ {key} is set.{Colors.ENDC}")
        else:
            print(f"{Colors.BLUE}ℹ️  {key} is NOT set.{Colors.ENDC}")

async def main():
    print(f"{Colors.CYAN}{Colors.BOLD}================================={Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}   Qubot Diagnostic Doctor 🩺    {Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}=================================\n{Colors.ENDC}")

    db_ok = await check_database()
    if db_ok:
        check_security_env()
        check_providers_env()

    print(f"\n{Colors.CYAN}{Colors.BOLD}================================={Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}   Diagnostic Complete           {Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}=================================\n{Colors.ENDC}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Diagnostic aborted by user.{Colors.ENDC}")
