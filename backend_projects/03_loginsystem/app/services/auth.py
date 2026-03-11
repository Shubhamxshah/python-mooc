from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    decode_token,
)
from app.models.user import RefreshToken, User
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse


async def register_user(payload: RegisterRequest, db: AsyncSession) -> User:
    existing = await db.execute(
        select(User).where(
            (User.email == payload.email) | (User.username == payload.username)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already taken",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(payload: LoginRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = create_access_token(str(user.id))
    refresh_token_str, expires_at = create_refresh_token(str(user.id))

    db.add(RefreshToken(token=refresh_token_str, user_id=user.id, expires_at=expires_at))
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)


async def refresh_tokens(token: str, db: AsyncSession) -> TokenResponse:
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(RefreshToken).where(RefreshToken.token == token))
    stored = result.scalar_one_or_none()

    if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")

    # Rotate: revoke old, issue new
    stored.revoked = True

    user_id = payload["sub"]
    access_token = create_access_token(user_id)
    new_refresh_str, expires_at = create_refresh_token(user_id)

    db.add(RefreshToken(token=new_refresh_str, user_id=stored.user_id, expires_at=expires_at))
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_str)


async def logout_user(token: str, db: AsyncSession) -> None:
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == token))
    stored = result.scalar_one_or_none()
    if stored:
        stored.revoked = True
        await db.commit()
