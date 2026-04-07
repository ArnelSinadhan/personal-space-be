"""
Vault password encryption using AES-256-GCM.

Passwords are encrypted with a key derived from the VAULT_ENCRYPTION_SECRET.
Each encrypted value includes a random IV (nonce) for uniqueness.

Format stored in DB: base64(iv + ciphertext + tag)
"""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


def _get_key() -> bytes:
    """Derive a 32-byte key from the configured secret."""
    secret = settings.vault_encryption_secret.encode("utf-8")
    # Pad or truncate to exactly 32 bytes
    return secret.ljust(32, b"\0")[:32]


def encrypt_password(plaintext: str) -> str:
    """Encrypt a vault password. Returns base64-encoded string."""
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Store as: nonce (12) + ciphertext + tag (16 appended by GCM)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_password(encrypted: str) -> str:
    """Decrypt a vault password from base64-encoded string."""
    key = _get_key()
    aesgcm = AESGCM(key)
    raw = base64.b64decode(encrypted)
    nonce = raw[:12]
    ciphertext = raw[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
