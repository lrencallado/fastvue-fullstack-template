from fastapi import APIRouter, HTTPException, status, Depends
from app.api.dependencies import SessionDependency
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from app.models import User, Token
from app.services import authservice
from datetime import timedelta
from app.core import config, security

router = APIRouter(tags=["authentication"], prefix="/auth")

@router.post("/login/access-token")
async def login_access_token(session: SessionDependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await authservice.authenticate(session=session, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    access_token_expires = timedelta(config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )