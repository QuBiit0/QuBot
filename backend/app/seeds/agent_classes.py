"""
Seed data for AgentClass - 17 predefined classes
Run this after migrations to populate the database
"""

import asyncio

from sqlmodel import select

from ..database import AsyncSessionLocal
from ..models.agent import AgentClass
from ..models.enums import DomainEnum

PREDEFINED_CLASSES = [
    # TECH Domain
    {
        "name": "Ethical Hacker",
        "description": "Security specialist focused on finding vulnerabilities and hardening systems",
        "domain": DomainEnum.TECH,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "hacker",
            "color_primary": "#00FF41",
            "color_secondary": "#1a1a1a",
            "icon": "🔐",
            "badge": "SEC",
        },
    },
    {
        "name": "Systems Architect",
        "description": "Designs and oversees complex software architectures and infrastructure",
        "domain": DomainEnum.TECH,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "architect",
            "color_primary": "#4A90E2",
            "color_secondary": "#1a2744",
            "icon": "🏗️",
            "badge": "ARCH",
        },
    },
    {
        "name": "Backend Developer",
        "description": "Builds APIs, services, databases, and server-side logic",
        "domain": DomainEnum.TECH,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "backend_dev",
            "color_primary": "#7B2FBE",
            "color_secondary": "#2d1a44",
            "icon": "⚙️",
            "badge": "BE",
        },
    },
    {
        "name": "Frontend Developer",
        "description": "Creates user interfaces and interactive web applications",
        "domain": DomainEnum.TECH,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "frontend_dev",
            "color_primary": "#F59E0B",
            "color_secondary": "#44300a",
            "icon": "🎨",
            "badge": "FE",
        },
    },
    {
        "name": "DevOps Engineer",
        "description": "Manages CI/CD pipelines, infrastructure, deployments and reliability",
        "domain": DomainEnum.TECH,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "devops",
            "color_primary": "#10B981",
            "color_secondary": "#0a3327",
            "icon": "🚀",
            "badge": "OPS",
        },
    },
    {
        "name": "Data Scientist",
        "description": "Analyzes data, builds models, and extracts insights from large datasets",
        "domain": DomainEnum.TECH,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "data_scientist",
            "color_primary": "#EF4444",
            "color_secondary": "#440a0a",
            "icon": "📊",
            "badge": "DS",
        },
    },
    {
        "name": "ML Engineer",
        "description": "Designs, trains, and deploys machine learning models and pipelines",
        "domain": DomainEnum.TECH,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "ml_engineer",
            "color_primary": "#8B5CF6",
            "color_secondary": "#2a1a44",
            "icon": "🧠",
            "badge": "ML",
        },
    },
    {
        "name": "Data Analyst",
        "description": "Transforms raw data into actionable business insights and reports",
        "domain": DomainEnum.TECH,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "data_analyst",
            "color_primary": "#06B6D4",
            "color_secondary": "#0a2a30",
            "icon": "📈",
            "badge": "DA",
        },
    },
    {
        "name": "QA Engineer",
        "description": "Designs and executes test strategies to ensure software quality",
        "domain": DomainEnum.TECH,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "qa",
            "color_primary": "#84CC16",
            "color_secondary": "#1a2a06",
            "icon": "✅",
            "badge": "QA",
        },
    },
    {
        "name": "AI Researcher",
        "description": "Researches AI capabilities, prompt engineering, and LLM optimization",
        "domain": DomainEnum.TECH,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "ai_researcher",
            "color_primary": "#F97316",
            "color_secondary": "#44200a",
            "icon": "🔬",
            "badge": "AI",
        },
    },
    # FINANCE Domain
    {
        "name": "Finance Manager",
        "description": "Oversees financial operations, budgeting, and strategic financial decisions",
        "domain": DomainEnum.FINANCE,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "finance_manager",
            "color_primary": "#D97706",
            "color_secondary": "#44260a",
            "icon": "💰",
            "badge": "FIN",
        },
    },
    {
        "name": "Financial Analyst",
        "description": "Analyzes financial data, models, and provides investment recommendations",
        "domain": DomainEnum.FINANCE,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "fin_analyst",
            "color_primary": "#B45309",
            "color_secondary": "#3a1a06",
            "icon": "📉",
            "badge": "FA",
        },
    },
    # BUSINESS Domain
    {
        "name": "Product Manager",
        "description": "Defines product strategy, roadmaps, and coordinates cross-functional teams",
        "domain": DomainEnum.BUSINESS,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "pm",
            "color_primary": "#0EA5E9",
            "color_secondary": "#0a2a38",
            "icon": "📋",
            "badge": "PM",
        },
    },
    {
        "name": "Operations Manager",
        "description": "Optimizes business processes, logistics, and operational efficiency",
        "domain": DomainEnum.BUSINESS,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "ops_manager",
            "color_primary": "#64748B",
            "color_secondary": "#1a2030",
            "icon": "⚡",
            "badge": "OPS",
        },
    },
    # HR Domain
    {
        "name": "HR Manager",
        "description": "Manages recruitment, employee relations, and organizational culture",
        "domain": DomainEnum.HR,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "hr_manager",
            "color_primary": "#EC4899",
            "color_secondary": "#44102a",
            "icon": "👥",
            "badge": "HR",
        },
    },
    # MARKETING Domain
    {
        "name": "Digital Marketing Specialist",
        "description": "Plans and executes digital marketing campaigns, SEO, and growth strategies",
        "domain": DomainEnum.MARKETING,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "marketer",
            "color_primary": "#F43F5E",
            "color_secondary": "#44101a",
            "icon": "📣",
            "badge": "MKT",
        },
    },
    # LEGAL Domain
    {
        "name": "Legal Counsel",
        "description": "Provides legal guidance, contract review, and compliance advice",
        "domain": DomainEnum.LEGAL,
        "is_custom": False,
        "default_avatar_config": {
            "sprite_id": "legal",
            "color_primary": "#1E293B",
            "color_secondary": "#0a1020",
            "icon": "⚖️",
            "badge": "LEG",
        },
    },
]


async def seed_agent_classes():
    """Seed the database with predefined agent classes"""
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(AgentClass))
        existing = result.scalars().all()

        if existing:
            print(f"Agent classes already seeded ({len(existing)} found). Skipping...")
            return

        # Create all predefined classes
        for class_data in PREDEFINED_CLASSES:
            agent_class = AgentClass(**class_data)
            session.add(agent_class)

        await session.commit()
        print(f"Seeded {len(PREDEFINED_CLASSES)} agent classes")


def seed():
    """Synchronous wrapper for seeding"""
    asyncio.run(seed_agent_classes())


if __name__ == "__main__":
    seed()
