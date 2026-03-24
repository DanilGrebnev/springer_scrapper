from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import Response

from src.auth import service
from src.auth.deps import get_current_user_id
from src.auth.schemas import (
    LoginIn,
    LogoutIn,
    ProfileOut,
    RefreshIn,
    RegisterIn,
    RegisterOut,
    TokenPairOut,
)
from src.db.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=RegisterOut, status_code=201)
async def register(body: RegisterIn):
    user = await service.register_user(
        name=body.name,
        last_name=body.last_name,
        username=body.username,
        email=body.email,
        password=body.password,
    )
    return RegisterOut(
        id=user.id,
        username=user.username,
        email=user.email,
        balance=user.balance,
    )


@router.post("/login", response_model=TokenPairOut)
async def login(body: LoginIn):
    access, refresh, expires_in = await service.authenticate(body.login, body.password)
    return TokenPairOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=TokenPairOut)
async def refresh(body: RefreshIn):
    access, refresh_tok, expires_in = await service.refresh_session(body.refresh_token)
    return TokenPairOut(
        access_token=access,
        refresh_token=refresh_tok,
        expires_in=expires_in,
    )


@router.post("/logout", status_code=204, response_class=Response)
async def logout(body: LogoutIn):
    await service.revoke_refresh(body.refresh_token)


@router.get("/profile", response_model=ProfileOut)
async def profile(user_id: int = Depends(get_current_user_id)):
    user = await User.filter(id=user_id).first()
    if user is None:
        raise HTTPException(404, "User not found")
    return ProfileOut(
        id=user.id,
        name=user.name,
        last_name=user.last_name,
        username=user.username,
        status=user.status,
        balance=user.balance,
        datetime=user.datetime,
    )
