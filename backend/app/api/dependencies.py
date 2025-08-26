from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from app.core.config import settings
from collections.abc import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import async_session, get_db_session
from typing import Annotated
from app.models import User, TokenPayload
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

reusable_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PATH}/auth/login/access-token",
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None, None]:
    async with async_session() as session:
        yield session

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]
TokenDependency = Annotated[str, Depends(reusable_oauth2_scheme)]

async def get_current_user(session: SessionDependency, token: TokenDependency) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await session.get(User, token_data.sub)
    print('--USER--')
    print(user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

async def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

