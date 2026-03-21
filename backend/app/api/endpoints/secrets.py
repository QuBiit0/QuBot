"""
Secrets API Endpoints
Secure management of sensitive data
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.security import get_current_user
from ...models.user import User
from ...services.secrets import secrets_vault

router = APIRouter(prefix="/secrets", tags=["secrets"])


class SecretCreate(BaseModel):
    name: str
    value: str
    category: Literal[
        "api_key",
        "credentials",
        "token",
        "certificate",
        "password",
        "secret_key",
        "other",
    ] = "api_key"
    description: str | None = None
    tags: list[str] | None = None


class SecretUpdate(BaseModel):
    value: str | None = None
    description: str | None = None
    tags: list[str] | None = None


class SecretResponse(BaseModel):
    name: str
    category: str
    description: str | None
    tags: list[str] | None
    created_at: str
    masked_value: str


@router.get("")
async def list_secrets(
    prefix: str | None = Query(None, description="Filter secrets by name prefix"),
    current_user: User = Depends(get_current_user),
):
    """List all secrets (without values)"""
    keys = secrets_vault.list_keys(prefix)

    secrets = []
    for key in keys:
        metadata = secrets_vault.get_metadata(key) or {}
        value = secrets_vault.get(key) or ""
        masked = (
            secrets_vault._SecretsVault__class__.mask_value(secrets_vault, value)
            if hasattr(secrets_vault, "_SecretsVault__class__")
            else value[:4] + "*" * (len(value) - 4)
            if len(value) > 4
            else "****"
        )

        secrets.append(
            {
                "name": key,
                "category": metadata.get("category", "other"),
                "description": metadata.get("description"),
                "tags": metadata.get("tags", []),
                "created_at": metadata.get("created_at", ""),
                "masked_value": value[:4] + "****" if len(value) > 4 else "****",
            }
        )

    return {"secrets": secrets, "count": len(secrets)}


@router.post("")
async def create_secret(
    secret: SecretCreate,
    current_user: User = Depends(get_current_user),
):
    """Store a new secret"""
    if secrets_vault.exists(secret.name):
        raise HTTPException(
            status_code=409, detail=f"Secret '{secret.name}' already exists"
        )

    secrets_vault.set(
        secret.name,
        secret.value,
        metadata={
            "category": secret.category,
            "description": secret.description,
            "tags": secret.tags or [],
            "created_by": str(current_user.id) if current_user else None,
        },
    )

    return {
        "success": True,
        "name": secret.name,
        "category": secret.category,
        "message": "Secret stored successfully",
    }


@router.get("/{name}")
async def get_secret(
    name: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve a secret value"""
    value = secrets_vault.get(name)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")

    metadata = secrets_vault.get_metadata(name) or {}

    return {
        "name": name,
        "value": value,
        "category": metadata.get("category", "other"),
        "description": metadata.get("description"),
        "tags": metadata.get("tags", []),
    }


@router.patch("/{name}")
async def update_secret(
    name: str,
    update: SecretUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a secret"""
    if not secrets_vault.exists(name):
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")

    if update.value is not None:
        metadata = secrets_vault.get_metadata(name) or {}
        secrets_vault.set(name, update.value, metadata=metadata)

    if update.description is not None or update.tags is not None:
        metadata = secrets_vault.get_metadata(name) or {}
        if update.description is not None:
            metadata["description"] = update.description
        if update.tags is not None:
            metadata["tags"] = update.tags
        value = secrets_vault.get(name)
        if value is not None:
            secrets_vault.set(name, value, metadata=metadata)

    return {
        "success": True,
        "name": name,
        "message": "Secret updated successfully",
    }


@router.delete("/{name}")
async def delete_secret(
    name: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a secret"""
    if not secrets_vault.exists(name):
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")

    secrets_vault.delete(name)

    return {
        "success": True,
        "name": name,
        "message": "Secret deleted successfully",
    }


@router.post("/{name}/rotate")
async def rotate_secret(
    name: str,
    new_value: str,
    current_user: User = Depends(get_current_user),
):
    """Rotate a secret with a new value"""
    if not secrets_vault.exists(name):
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")

    metadata = secrets_vault.get_metadata(name) or {}
    metadata["rotated_at"] = datetime.utcnow().isoformat()
    metadata["rotated_by"] = str(current_user.id) if current_user else None

    secrets_vault.set(name, new_value, metadata=metadata)

    return {
        "success": True,
        "name": name,
        "message": "Secret rotated successfully",
    }


@router.get("/{name}/reference")
async def get_secret_reference(
    name: str,
    current_user: User = Depends(get_current_user),
):
    """Get a reference to a secret for use in tools"""
    if not secrets_vault.exists(name):
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")

    return {
        "type": "secret",
        "name": name,
        "reference": f"{{{{ secrets.{name} }}}}",
    }


@router.get("/categories")
async def get_categories():
    """Get available secret categories"""
    return {
        "categories": [
            {"id": "api_key", "label": "API Key", "description": "External API keys"},
            {
                "id": "credentials",
                "label": "Credentials",
                "description": "Username/password pairs",
            },
            {
                "id": "token",
                "label": "Token",
                "description": "OAuth tokens, access tokens",
            },
            {
                "id": "certificate",
                "label": "Certificate",
                "description": "SSL/TLS certificates",
            },
            {"id": "password", "label": "Password", "description": "Generic passwords"},
            {
                "id": "secret_key",
                "label": "Secret Key",
                "description": "Encryption keys",
            },
            {"id": "other", "label": "Other", "description": "Other secrets"},
        ]
    }
