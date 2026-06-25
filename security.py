from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import jwt
from typing import Annotated
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from model import User
from settings import settings

from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

password_hash = PasswordHash.recommended()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency for protected endpoints
    Return the current user or raise 401
    """
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )

        user_id = payload.get("sub")

        response = await db.execute(select(User).where(User.id == user_id))
        user = response.scalar_one_or_none()
        if not user:
            raise exc

        return user

    except (jwt.ExpiredSignatureError, jwt.InvalidSignatureError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.PyJWTError:
        raise exc


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
    return password_hash.verify(plain_pwd, hashed_pwd)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe()


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(to_encode: dict) -> str:
    payload = to_encode.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.EXPIRE_MINUTES
    )

    token = jwt.encode(
        payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )

    return token
