from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Union
from app.models import User

async def get_user_by_email(*, session: AsyncSession, email: str) -> Union[User, None]:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement=statement)
    return result.scalar_one_or_none()