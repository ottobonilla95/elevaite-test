"""Cryptographic utilities for secure credential storage.

This module provides Fernet-based symmetric encryption for storing
sensitive data like API keys and OAuth credentials at rest.
"""

import base64
import json
import logging
import os
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken


logger = logging.getLogger(__name__)

# Environment variable for the encryption key
ENCRYPTION_KEY_ENV = "CREDENTIAL_ENCRYPTION_KEY"


def get_encryption_key() -> Optional[bytes]:
    """Get the encryption key from environment.

    Returns:
        The encryption key as bytes, or None if not configured.
    """
    key = os.environ.get(ENCRYPTION_KEY_ENV)
    if not key:
        return None
    # Key should be base64-encoded 32-byte key
    return key.encode("utf-8")


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key.

    Returns:
        A base64-encoded encryption key suitable for CREDENTIAL_ENCRYPTION_KEY.
    """
    return Fernet.generate_key().decode("utf-8")


def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """Encrypt credentials dictionary to a string.

    Args:
        credentials: The credentials dictionary to encrypt.

    Returns:
        Base64-encoded encrypted string.

    Raises:
        ValueError: If encryption key is not configured.
    """
    key = get_encryption_key()
    if not key:
        raise ValueError(
            f"Encryption key not configured. Set {ENCRYPTION_KEY_ENV} environment variable."
        )

    fernet = Fernet(key)
    json_bytes = json.dumps(credentials).encode("utf-8")
    encrypted = fernet.encrypt(json_bytes)
    return base64.urlsafe_b64encode(encrypted).decode("utf-8")


def decrypt_credentials(encrypted_data: str) -> Dict[str, Any]:
    """Decrypt an encrypted credentials string.

    Args:
        encrypted_data: Base64-encoded encrypted string.

    Returns:
        The decrypted credentials dictionary.

    Raises:
        ValueError: If encryption key is not configured or decryption fails.
    """
    key = get_encryption_key()
    if not key:
        raise ValueError(
            f"Encryption key not configured. Set {ENCRYPTION_KEY_ENV} environment variable."
        )

    try:
        fernet = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
        decrypted = fernet.decrypt(encrypted_bytes)
        return json.loads(decrypted.decode("utf-8"))
    except InvalidToken as e:
        raise ValueError(
            "Failed to decrypt credentials: invalid key or corrupted data"
        ) from e
    except Exception as e:
        raise ValueError(f"Failed to decrypt credentials: {e}") from e


def is_encrypted(data: Any) -> bool:
    """Check if data appears to be encrypted.

    Encrypted data is stored as a string with a specific prefix.

    Args:
        data: The data to check.

    Returns:
        True if the data appears to be encrypted.
    """
    if not isinstance(data, str):
        return False
    # Encrypted data is base64-encoded and starts with 'gAAAAA' (Fernet token prefix)
    try:
        decoded = base64.urlsafe_b64decode(data.encode("utf-8"))
        return decoded.startswith(b"gAAAAA") or len(decoded) > 50
    except Exception:
        return False


def encrypt_if_configured(
    credentials: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any] | str]:
    """Encrypt credentials if encryption is configured, otherwise return as-is.

    This is a convenience function for optional encryption.

    Args:
        credentials: The credentials to potentially encrypt.

    Returns:
        Encrypted string if encryption is configured, otherwise the original dict.
    """
    if credentials is None:
        return None

    key = get_encryption_key()
    if not key:
        logger.debug("Encryption key not configured, storing credentials in plaintext")
        return credentials

    return encrypt_credentials(credentials)


def decrypt_if_encrypted(
    data: Optional[Dict[str, Any] | str],
) -> Optional[Dict[str, Any]]:
    """Decrypt data if it's encrypted, otherwise return as-is.

    This is a convenience function for handling both encrypted and plaintext data.

    Args:
        data: The data to potentially decrypt.

    Returns:
        Decrypted dict if data was encrypted, otherwise the original dict.
    """
    if data is None:
        return None

    if isinstance(data, dict):
        # Already a dict, not encrypted
        return data

    if isinstance(data, str) and is_encrypted(data):
        return decrypt_credentials(data)

    # Unknown format, return as-is (shouldn't happen in normal use)
    logger.warning(f"Unexpected credential data format: {type(data)}")
    return None
