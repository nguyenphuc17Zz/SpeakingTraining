import pytest

from app.core.security import EncryptionService, mask_secret


def test_encryption_and_decryption():
    service = EncryptionService()
    secret = "AIzaSyDummyGeminiApiKey123456789"

    ciphertext = service.encrypt(secret)
    assert ciphertext != secret
    assert len(ciphertext) > len(secret)

    decrypted = service.decrypt(ciphertext)
    assert decrypted == secret


def test_encryption_custom_key():
    custom_key = "custom_secret_key_material_for_training"
    service = EncryptionService(key=custom_key)
    secret = "gsk_groq_api_token_test_12345"

    ciphertext = service.encrypt(secret)
    decrypted = service.decrypt(ciphertext)
    assert decrypted == secret


def test_secret_masking():
    gemini_key = "AIzaSyABCDEFGHIJKLMN1234"
    masked = mask_secret(gemini_key)
    assert masked.startswith("••••••••")
    assert masked.endswith("1234")
    assert "ABCDEF" not in masked

    short_key = "abc"
    assert mask_secret(short_key) == "••••••••"


def test_corrupted_ciphertext_raises_error():
    service = EncryptionService()
    with pytest.raises(ValueError, match="Failed to decrypt secret"):
        service.decrypt("corrupted_invalid_base64_payload")
