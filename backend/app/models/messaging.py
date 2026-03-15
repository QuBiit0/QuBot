"""
Messaging models - MessagingChannel, Conversation, ConversationMessage
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import JSON, Index
from .enums import MessagingPlatformEnum, MessageDirectionEnum


class MessagingChannel(SQLModel, table=True):
    """Stores one record per connected messaging platform bot/app"""
    __tablename__ = "messaging_channel"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    platform: MessagingPlatformEnum
    name: str = Field(max_length=100)  # Human label, e.g. "Main Telegram Bot"
    is_active: bool = Field(default=True)

    # JSON with env var name references — NEVER actual tokens
    # Telegram: {"bot_token_ref": "TELEGRAM_BOT_TOKEN", "secret_token_ref": "..."}
    # WhatsApp: {"phone_number_id_ref": "...", "access_token_ref": "...", ...}
    # Discord:  {"bot_token_ref": "...", "public_key_ref": "..."}
    # Slack:    {"bot_token_ref": "...", "signing_secret_ref": "..."}
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Optional: route all messages from this channel to a specific agent
    # If null, uses the global orchestrator agent
    assigned_agent_id: Optional[UUID] = Field(default=None, foreign_key="agent.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    conversations: List["Conversation"] = Relationship(back_populates="channel")
    
    __table_args__ = (
        Index("idx_messaging_channel_platform", "platform"),
    )


class Conversation(SQLModel, table=True):
    """One record per (channel × external user). Tracks conversation identity and rolling history"""
    __tablename__ = "conversation"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    channel_id: UUID = Field(foreign_key="messaging_channel.id", index=True)

    external_user_id: str = Field(max_length=200)  # Platform user ID / phone number
    external_chat_id: str = Field(max_length=200)  # Platform chat/channel ID

    # Last N messages kept as context for the orchestrator
    # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    history: List[dict] = Field(default_factory=list, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    channel: Optional[MessagingChannel] = Relationship(back_populates="conversations")
    messages: List["ConversationMessage"] = Relationship(back_populates="conversation")
    
    __table_args__ = (
        Index("idx_conversation_channel_user", "channel_id", "external_user_id"),
    )


class ConversationMessage(SQLModel, table=True):
    """Append-only log of every inbound and outbound message across all messaging platforms"""
    __tablename__ = "conversation_message"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id", index=True)
    direction: MessageDirectionEnum  # INBOUND | OUTBOUND
    content: str  # Plain text content
    platform_message_id: str = Field(max_length=200)  # Native platform message ID
    meta: dict = Field(default_factory=dict, sa_column=Column(JSON))  # 'metadata' is reserved
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
    
    __table_args__ = (
        Index("idx_conv_message_conv_time", "conversation_id", "created_at"),
    )
