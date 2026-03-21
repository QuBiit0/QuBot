"""
Secrets Management Package
Secure storage and retrieval of sensitive data
"""

from .manager import (
    SecretsManager,
    SecretsVault,
    SecretEntry,
    secrets_manager,
    secrets_vault,
)

__all__ = [
    "SecretsManager",
    "SecretsVault",
    "SecretEntry",
    "secrets_manager",
    "secrets_vault",
]
