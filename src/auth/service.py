from datetime import datetime, timezone

from fastapi import HTTPException, status
from tortoise.exceptions import IntegrityError

from src.auth.config import ACCESS_TOKEN_EXPIRE_MINUTES
from src.auth.security import create_access_token, hash_password, verify_password
from src.auth.tokens import (
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
    verify_refresh_token,
)
from src.db.models.authorization import Authorization
from src.db.models.user import User


async def register_user(
    name: str,
    last_name: str,
    username: str,
    email: str,
    password: str,
) -> User:
    try:
        user = await User.create(
            name=name,
            last_name=last_name,
            username=username,
            email=email,
            password=hash_password(password),
            balance=5.0,
        )
    except IntegrityError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Username or email already taken",
        )
    return user


async def authenticate(login: str, password: str) -> tuple[str, str, int]:
    """Возвращает (access_token, refresh_token, expires_in_seconds)."""
    user = await User.filter(email=login).first()
    if user is None:
        user = await User.filter(username=login).first()
    if user is None or not verify_password(password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    access_token, expires_in = create_access_token(user.id)
    refresh_raw = generate_refresh_token()

    # Upsert локальной сессии в Authorization
    auth = await Authorization.filter(user=user, type_auth="local").first()
    if auth is None:
        await Authorization.create(
            user=user,
            type_auth="local",
            hash_refresh_token=hash_refresh_token(refresh_raw),
            refresh_expires_at=refresh_token_expiry(),
        )
    else:
        auth.hash_refresh_token = hash_refresh_token(refresh_raw)
        auth.refresh_expires_at = refresh_token_expiry()
        auth.logout_datetime = None
        auth.count_uses += 1
        await auth.save()

    return access_token, refresh_raw, expires_in


async def refresh_session(refresh_token: str) -> tuple[str, str, int]:
    """Ротация refresh-токена: возвращает новый access + новый refresh."""
    hashed = hash_refresh_token(refresh_token)
    auth = await Authorization.filter(
        hash_refresh_token=hashed,
        type_auth="local",
    ).first()

    if auth is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    # Проверяем срок действия
    if auth.refresh_expires_at is not None:
        exp = auth.refresh_expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")

    # Ротация: новый refresh → новый хэш + новый срок
    new_refresh = generate_refresh_token()
    auth.hash_refresh_token = hash_refresh_token(new_refresh)
    auth.refresh_expires_at = refresh_token_expiry()
    await auth.save()

    access_token, expires_in = create_access_token(auth.user_id)
    return access_token, new_refresh, expires_in


async def revoke_refresh(refresh_token: str) -> None:
    """Logout: обнуляем refresh в Authorization."""
    hashed = hash_refresh_token(refresh_token)
    auth = await Authorization.filter(
        hash_refresh_token=hashed,
        type_auth="local",
    ).first()

    if auth is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    auth.hash_refresh_token = None
    auth.refresh_expires_at = None
    auth.logout_datetime = datetime.now(timezone.utc)
    await auth.save()
