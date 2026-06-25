from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from model import User
from schema import PasswordChangeRequest, Token, UserCreate, UserResponse, UserUpdate
from security import (
    create_access_token,
    generate_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter()


@router.post("/auth/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    response = await db.execute(select(User).where(User.username == form_data.username))
    user = response.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or password is incorrect",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = generate_refresh_token()
    # hash refresh and save to db later

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def register(
    form_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = User(
        first_name=form_data.first_name,
        last_name=form_data.last_name,
        username=form_data.username,
        hashed_password=hash_password(form_data.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return current_user


@router.patch("/users", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    form_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_data = form_data.model_dump(exclude_unset=True)

    for key, val in user_data.items():
        setattr(current_user, key, val)

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.patch("/users/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    form_data: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not verify_password(form_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    current_user.hashed_password = hash_password(form_data.new_password)
    await db.commit()
