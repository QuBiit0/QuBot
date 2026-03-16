"""
Seed database with initial data for Qubot
Uses async SQLModel
"""

import asyncio
import logging
from uuid import uuid4

from app.database import AsyncSessionLocal
from app.models.agent import AgentClass
from app.models.enums import DomainEnum, LlmProviderEnum
from app.models.llm import LlmConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_agent_classes(session):
    """Create default agent classes"""
    logger.info("Creating agent classes...")

    classes = [
        {
            "id": uuid4(),
            "name": "Orchestrator",
            "description": "Coordinates multi-agent task execution and breaks down complex tasks",
            "domain": DomainEnum.TECH,
            "is_custom": False,
        },
        {
            "id": uuid4(),
            "name": "Frontend Developer",
            "description": "Specializes in UI/UX development with React, Next.js, and modern frontend technologies",
            "domain": DomainEnum.TECH,
            "is_custom": False,
        },
        {
            "id": uuid4(),
            "name": "Backend Developer",
            "description": "Builds APIs, databases, and server-side logic with Python, FastAPI, and SQL",
            "domain": DomainEnum.TECH,
            "is_custom": False,
        },
        {
            "id": uuid4(),
            "name": "DevOps Engineer",
            "description": "Manages infrastructure, CI/CD, Docker, Kubernetes, and cloud deployments",
            "domain": DomainEnum.TECH,
            "is_custom": False,
        },
        {
            "id": uuid4(),
            "name": "Data Analyst",
            "description": "Analyzes data, creates reports, and provides insights",
            "domain": DomainEnum.BUSINESS,
            "is_custom": False,
        },
        {
            "id": uuid4(),
            "name": "Content Writer",
            "description": "Creates marketing content, blog posts, and copywriting",
            "domain": DomainEnum.MARKETING,
            "is_custom": False,
        },
        {
            "id": uuid4(),
            "name": "Financial Analyst",
            "description": "Analyzes financial data, budgets, and investment opportunities",
            "domain": DomainEnum.FINANCE,
            "is_custom": False,
        },
        {
            "id": uuid4(),
            "name": "HR Specialist",
            "description": "Handles recruitment, employee relations, and HR processes",
            "domain": DomainEnum.HR,
            "is_custom": False,
        },
    ]

    for cls_data in classes:
        agent_class = AgentClass(**cls_data)
        session.add(agent_class)

    await session.commit()
    logger.info(f"Created {len(classes)} agent classes")


async def seed_llm_configs(session):
    """Create default LLM configurations"""
    logger.info("Creating LLM configs...")

    configs = [
        {
            "id": uuid4(),
            "name": "OpenAI GPT-4o Mini",
            "provider": LlmProviderEnum.OPENAI,
            "model_name": "gpt-4o-mini",
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 2000,
            "api_key_ref": "OPENAI_API_KEY",
        },
        {
            "id": uuid4(),
            "name": "OpenAI GPT-4o",
            "provider": LlmProviderEnum.OPENAI,
            "model_name": "gpt-4o",
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 4000,
            "api_key_ref": "OPENAI_API_KEY",
        },
        {
            "id": uuid4(),
            "name": "Anthropic Claude 3.5 Sonnet",
            "provider": LlmProviderEnum.ANTHROPIC,
            "model_name": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 4000,
            "api_key_ref": "ANTHROPIC_API_KEY",
        },
        {
            "id": uuid4(),
            "name": "Groq Llama 3.1",
            "provider": LlmProviderEnum.GROQ,
            "model_name": "llama-3.1-70b-versatile",
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 2000,
            "api_key_ref": "GROQ_API_KEY",
        },
    ]

    for config_data in configs:
        config = LlmConfig(**config_data)
        session.add(config)

    await session.commit()
    logger.info(f"Created {len(configs)} LLM configs")


async def seed():
    """Main seed function"""
    logger.info("Starting database seeding...")

    async with AsyncSessionLocal() as session:
        try:
            # Check if already seeded
            from sqlalchemy import select

            result = await session.execute(select(AgentClass).limit(1))
            if result.scalar_one_or_none():
                logger.info("Database already seeded, skipping...")
                return

            await seed_agent_classes(session)
            await seed_llm_configs(session)

            logger.info("Database seeding completed successfully!")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())
