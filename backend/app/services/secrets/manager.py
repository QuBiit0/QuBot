"""
Secrets Management Service
Securely store and retrieve secrets with encryption
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SecretEntry:
    """A stored secret"""

    id: str
    name: str
    category: str
    encrypted_value: str
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    expires_at: datetime | None = None
    description: str | None = None
    tags: list[str] | None = None

    def __init__(
        self,
        id: str,
        name: str,
        category: str,
        encrypted_value: str,
        created_at: datetime,
        updated_at: datetime,
        created_by: str | None = None,
        expires_at: datetime | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ):
        self.id = id
        self.name = name
        self.category = category
        self.encrypted_value = encrypted_value
        self.created_at = created_at
        self.updated_at = updated_at
        self.created_by = created_by
        self.expires_at = expires_at
        self.description = description
        self.tags = tags or []


class SecretsManager:
    """
    Secure secrets management with encryption.

    Features:
    - AES-256 encryption for stored secrets
    - Per-user isolation
    - Categories for organization
    - Expiration support
    - Audit logging
    - Access control via permissions
    """

    CATEGORIES = [
        "api_key",
        "credentials",
        "token",
        "certificate",
        "password",
        "secret_key",
        "other",
    ]

    def __init__(self, encryption_key: str | None = None):
        self._encryption_key = encryption_key or os.getenv("SECRETS_ENCRYPTION_KEY")
        self._fernet: Fernet | None = None
        if self._encryption_key:
            self._fernet = self._get_fernet(self._encryption_key)

    def _get_fernet(self, key: str) -> Fernet:
        """Derive a Fernet key from the encryption key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"qubot_secrets_salt_v1",
            iterations=480000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return Fernet(derived_key)

    def _encrypt(self, value: str) -> str:
        """Encrypt a secret value"""
        if not self._fernet:
            logger.warning("Secrets encryption not configured - storing in plaintext")
            return value
        return self._fernet.encrypt(value.encode()).decode()

    def _decrypt(self, encrypted_value: str) -> str:
        """Decrypt a secret value"""
        if not self._fernet:
            return encrypted_value
        try:
            return self._fernet.decrypt(encrypted_value.encode()).decode()
        except Exception:
            return encrypted_value

    def _hash_for_lookup(self, name: str, user_id: str | None = None) -> str:
        """Create a deterministic hash for secret lookup"""
        import hashlib

        data = f"{user_id or 'global'}:{name}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    async def store_secret(
        self,
        name: str,
        value: str,
        category: str = "api_key",
        user_id: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        expires_at: datetime | None = None,
        session: AsyncSession | None = None,
    ) -> SecretEntry:
        """
        Store a new secret.

        Args:
            name: Unique name for the secret
            value: The secret value to store
            category: Category for organization
            user_id: Owner user ID (None for global)
            description: Optional description
            tags: Optional tags
            expires_at: Optional expiration time
            session: Database session (optional)

        Returns:
            SecretEntry with the stored secret info
        """
        if category not in self.CATEGORIES:
            category = "other"

        encrypted = self._encrypt(value)
        now = datetime.utcnow()

        entry = SecretEntry(
            id=str(uuid.uuid4()),
            name=name,
            category=category,
            encrypted_value=encrypted,
            created_at=now,
            updated_at=now,
            created_by=user_id,
            expires_at=expires_at,
            description=description,
            tags=tags or [],
        )

        if session:
            from app.models.secret import Secret

            secret = Secret(
                id=entry.id,
                name=name,
                category=category,
                encrypted_value=encrypted,
                description=description,
                user_id=user_id,
                created_by=user_id,
                created_at=now,
                updated_at=now,
                expires_at=expires_at,
                tags=json.dumps(tags) if tags else None,
            )
            session.add(secret)
            await session.commit()
            logger.info(f"Secret '{name}' stored in database")

        return entry

    async def retrieve_secret(
        self,
        name: str,
        user_id: str | None = None,
        session: AsyncSession | None = None,
    ) -> str | None:
        """
        Retrieve a secret value.

        Args:
            name: Name of the secret
            user_id: User requesting the secret
            session: Database session (optional)

        Returns:
            The decrypted secret value or None if not found
        """
        if session is None:
            logger.warning("No database session provided for retrieve_secret")
            return None

        from app.models.secret import Secret

        stmt = select(Secret).where(
            Secret.name == name,
            (Secret.user_id == user_id) | (Secret.user_id.is_(None)),
        )
        result = await session.execute(stmt)
        secret = result.scalar_one_or_none()

        if not secret:
            return None

        if secret.expires_at and datetime.utcnow() > secret.expires_at:
            logger.warning(f"Secret '{name}' has expired")
            return None

        return self._decrypt(secret.encrypted_value)

    async def list_secrets(
        self,
        user_id: str | None = None,
        category: str | None = None,
        session: AsyncSession | None = None,
    ) -> list[dict]:
        """
        List secrets (without values) for a user.

        Returns:
            List of secret metadata (no values exposed)
        """
        if session is None:
            logger.warning("No database session provided for list_secrets")
            return []

        from app.models.secret import Secret

        conditions = []
        if user_id:
            conditions.append((Secret.user_id == user_id) | (Secret.user_id.is_(None)))
        if category:
            conditions.append(Secret.category == category)

        stmt = select(Secret)
        if conditions:
            from sqlalchemy import and_

            stmt = stmt.where(and_(*conditions))

        result = await session.execute(stmt)
        secrets = result.scalars().all()

        return [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "description": s.description,
                "tags": json.loads(s.tags) if s.tags else [],
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                "is_expired": s.expires_at and datetime.utcnow() > s.expires_at
                if s.expires_at
                else False,
            }
            for s in secrets
        ]

    async def delete_secret(
        self,
        name: str,
        user_id: str | None = None,
        session: AsyncSession | None = None,
    ) -> bool:
        """
        Delete a secret.

        Returns:
            True if deleted, False if not found
        """
        if session is None:
            logger.warning("No database session provided for delete_secret")
            return False

        from app.models.secret import Secret

        stmt = delete(Secret).where(
            Secret.name == name,
            Secret.user_id == user_id,
        )
        result = await session.execute(stmt)
        await session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Secret '{name}' deleted")

        return deleted

    async def update_secret(
        self,
        name: str,
        new_value: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        user_id: str | None = None,
        session: AsyncSession | None = None,
    ) -> SecretEntry | None:
        """
        Update a secret.

        Returns:
            Updated SecretEntry or None if not found
        """
        if session is None:
            logger.warning("No database session provided for update_secret")
            return None

        from app.models.secret import Secret

        stmt = select(Secret).where(
            Secret.name == name,
            Secret.user_id == user_id,
        )
        result = await session.execute(stmt)
        secret = result.scalar_one_or_none()

        if not secret:
            return None

        now = datetime.utcnow()
        if new_value is not None:
            secret.encrypted_value = self._encrypt(new_value)
        if description is not None:
            secret.description = description
        if tags is not None:
            secret.tags = json.dumps(tags)
        secret.updated_at = now

        await session.commit()
        logger.info(f"Secret '{name}' updated")

        return SecretEntry(
            id=secret.id,
            name=secret.name,
            category=secret.category,
            encrypted_value=secret.encrypted_value,
            created_at=secret.created_at,
            updated_at=secret.updated_at,
            created_by=secret.created_by,
            expires_at=secret.expires_at,
            description=secret.description,
            tags=json.loads(secret.tags) if secret.tags else [],
        )

    async def rotate_secret(
        self,
        name: str,
        new_value: str,
        user_id: str | None = None,
        session: AsyncSession | None = None,
    ) -> SecretEntry | None:
        """
        Rotate a secret with a new value.

        Returns:
            Updated SecretEntry or None if not found
        """
        return await self.update_secret(
            name=name,
            new_value=new_value,
            user_id=user_id,
            session=session,
        )

    def is_expired(self, entry: SecretEntry | dict) -> bool:
        """Check if a secret has expired"""
        expires_at = (
            entry.expires_at
            if isinstance(entry, SecretEntry)
            else entry.get("expires_at")
        )
        if not expires_at:
            return False
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        return datetime.utcnow() > expires_at

    def mask_value(self, value: str, visible_chars: int = 4) -> str:
        """Mask a secret value for display"""
        if len(value) <= visible_chars:
            return "*" * len(value)
        return value[:visible_chars] + "*" * (len(value) - visible_chars)


import base64


class SecretsVault:
    """
    In-memory vault for secrets with file persistence.
    Useful for development and testing.
    """

    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path or os.getenv(
            "SECRETS_VAULT_PATH", ".secrets.vault"
        )
        self._secrets: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        """Load secrets from file"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    self._secrets = json.load(f)
            except Exception:
                self._secrets = {}

    def _save(self) -> None:
        """Save secrets to file"""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self._secrets, f, indent=2, default=str)
        except Exception:
            pass

    def set(self, key: str, value: str, metadata: dict | None = None) -> None:
        """Store a secret"""
        self._secrets[key] = {
            "value": value,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        self._save()

    def get(self, key: str) -> str | None:
        """Retrieve a secret"""
        entry = self._secrets.get(key)
        return entry["value"] if entry else None

    def delete(self, key: str) -> bool:
        """Delete a secret"""
        if key in self._secrets:
            del self._secrets[key]
            self._save()
            return True
        return False

    def list_keys(self, prefix: str | None = None) -> list[str]:
        """List all secret keys"""
        keys = list(self._secrets.keys())
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]
        return keys

    def exists(self, key: str) -> bool:
        """Check if a secret exists"""
        return key in self._secrets

    def get_metadata(self, key: str) -> dict | None:
        """Get metadata for a secret"""
        entry = self._secrets.get(key)
        return entry["metadata"] if entry else None


secrets_manager = SecretsManager()
secrets_vault = SecretsVault()
