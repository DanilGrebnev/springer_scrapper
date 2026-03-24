import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from src.auth.config import REFRESH_TOKEN_EXPIRE_DAYS, REFRESH_TOKEN_PEPPER


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256((token + REFRESH_TOKEN_PEPPER).encode()).hexdigest()


def verify_refresh_token(plain: str, hashed: str) -> bool:
    return hash_refresh_token(plain) == hashed


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
