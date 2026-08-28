import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class EncryptionService:
    """Provides cryptographic protection for user API keys at rest."""

    def __init__(self, key: str | None = None):
        raw_key = key or get_settings().ENCRYPTION_KEY
        self._fernet = Fernet(self._derive_fernet_key(raw_key))

    @staticmethod
    def _derive_fernet_key(key_material: str) -> bytes:
        """Ensures key is a valid 32-byte urlsafe base64-encoded key for Fernet."""
        try:
            decoded = base64.urlsafe_b64decode(key_material)
            if len(decoded) == 32:
                return base64.urlsafe_b64encode(decoded)
        except Exception:
            pass
        # Derive standard 32 bytes using SHA-256 if arbitrary string provided
        digest = hashlib.sha256(key_material.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    def encrypt(self, plaintext: str) -> str:
        """Encrypts plaintext string and returns utf-8 encoded ciphertext string."""
        if not plaintext:
            return ""
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypts ciphertext string back to plaintext."""
        if not ciphertext:
            return ""
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Failed to decrypt secret: invalid key or corrupted payload") from exc


def mask_secret(secret: str, unmasked_suffix_length: int = 4) -> str:
    """Masks a secret string for safe display in UI/API responses."""
    if not secret:
        return ""
    if len(secret) <= unmasked_suffix_length + 2:
        return "••••••••"
    suffix = secret[-unmasked_suffix_length:]
    return f"••••••••{suffix}"


_default_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    global _default_encryption_service
    if _default_encryption_service is None:
        _default_encryption_service = EncryptionService()
    return _default_encryption_service
