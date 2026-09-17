import os
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from bot.app.config import settings

def _fernet() -> Fernet:
    # Derive 32-byte key from SECRET_KEY + optional ENCRYPTION_KEY
    raw = os.getenv("ENCRYPTION_KEY") or settings.secret_key
    digest = hashlib.sha256(raw.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)

def encrypt(text: str) -> str:
    if not text:
        return ""
    try:
        return _fernet().encrypt(text.encode()).decode()
    except Exception:
        # fallback XOR (legacy)
        return text

def decrypt(token: str) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        # try legacy XOR
        try:
            import hashlib as h
            key = h.sha256(settings.secret_key.encode()).digest()
            data = base64.urlsafe_b64decode(token.encode())
            dec = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
            return dec.decode()
        except:
            return token
    except:
        return token

def mask_account(info: str) -> str:
    if not info or len(info) <= 4:
        return "***"
    return info[:2] + "***" + info[-4:]
