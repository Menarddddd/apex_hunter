from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from model import Application, User
from schema import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    PasswordChangeRequest,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)
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
    """
    Returns JWT tokens or raise 401
    """
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
    """
    Create a new user or raise 409
    """
    user = User(
        first_name=form_data.first_name.strip(),
        last_name=form_data.last_name.strip(),
        username=form_data.username.lower().strip(),
        hashed_password=hash_password(form_data.password),
    )

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Return the current user
    """
    return current_user


@router.patch("/users", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    form_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Update user information
    """
    user_data = form_data.model_dump(exclude_unset=True)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

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
    """
    Change user's password or raise 401
    """
    if not verify_password(form_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    current_user.hashed_password = hash_password(form_data.new_password)
    await db.commit()


# ============================================================================================


@router.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_application(
    form_data: ApplicationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    new_application = Application(
        user_id=current_user.id,
        company_name=form_data.company_name.strip(),
        job_title=form_data.job_title.strip(),
        status=form_data.status.value,
        applied_date=form_data.applied_date,
    )

    db.add(new_application)
    await db.commit()
    await db.refresh(new_application)

    return new_application


@router.get(
    "/applications",
    response_model=list[ApplicationResponse],
    status_code=status.HTTP_200_OK,
)
async def get_applications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    response = await db.execute(
        select(Application).where(Application.user_id == current_user.id)
    )
    return response.scalars().all()


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_application(
    application_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    response = await db.execute(
        select(Application).where(
            Application.id == application_id, Application.user_id == current_user.id
        )
    )

    application = response.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application id '{application_id}' not found",
        )

    return application


@router.patch(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
)
async def update_application(
    application_id: UUID,
    form_data: ApplicationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    application_data = form_data.model_dump(exclude_unset=True)

    if not application_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    response = await db.execute(
        select(Application).where(
            Application.id == application_id, Application.user_id == current_user.id
        )
    )
    application = response.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application id '{application_id}' not found",
        )

    for key, val in application_data.items():
        setattr(application, key, val)

    await db.commit()
    await db.refresh(application)

    return application


@router.delete(
    "/applications/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_application(
    application_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    response = await db.execute(
        select(Application).where(
            Application.id == application_id, Application.user_id == current_user.id
        )
    )

    application = response.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application id '{application_id}' not found",
        )

    await db.delete(application)
    await db.commit()
