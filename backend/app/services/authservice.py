from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import User
from typing import Union
from .userservice import get_user_by_email
from app.core.security import verify_password

async def authenticate(*, session: AsyncSession, email: str, password: str) -> Union[User, None]:
    db_user = await get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user