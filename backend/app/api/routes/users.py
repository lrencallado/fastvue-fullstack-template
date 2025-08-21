from fastapi import APIRouter, Depends
from app.api.dependencies import SessionDependency, get_current_active_superuser, CurrentUser
from app.models import User, UserPublic, UsersPublic
from typing import Any
from sqlmodel import select, func

router = APIRouter(prefix="/users", tags=["users"])

@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
async def read_users(session: SessionDependency, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count =  await session.scalar(count_statement)

    statement = select(User).offset(skip).limit(limit)
    result_users = await session.scalars(statement)
    users = result_users.all()

    return UsersPublic(data=users, count=count)

@router.get("/me", response_model=UserPublic)
async def read_user_me(current_user: CurrentUser) -> UserPublic:
    """
    Get current user.
    """
    return current_user