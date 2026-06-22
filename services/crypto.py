"""Fernet symmetric encryption for storing user credentials securely."""

from cryptography.fernet import Fernet, InvalidToken
from config import Config


def _fernet():
    key = Config.MM_ENCRYPTION_KEY
    if not key:
        raise RuntimeError(
            "MM_ENCRYPTION_KEY is not set in .env. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_password(plaintext: str) -> str:
    if not plaintext:
        return ''
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_password(ciphertext: str) -> str:
    if not ciphertext:
        return ''
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception) as e:
        print(f"[Crypto] Decryption failed: {e}")
        return ''
