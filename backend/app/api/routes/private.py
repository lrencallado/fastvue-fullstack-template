from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.core.security import get_password_hash
from app.models import User, UserPublic
from app.api.dependencies import SessionDependency
from app.services.userservice import get_user_by_email

router = APIRouter(tags=["Private"], prefix="/private")

class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False

@router.post("/users", response_model=UserPublic)
async def create_user(user_in: PrivateUserCreate, session: SessionDependency) -> Any:
    """
    Create a new user.
    """

    # check if user already exists
    user = await get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_verified=user_in.is_verified
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user