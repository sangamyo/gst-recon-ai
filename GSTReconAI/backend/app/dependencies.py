"""FastAPI dependencies for authentication and database sessions."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import models
from app.auth import decode_access_token
from app.database import get_db
from app.schemas import TokenPayload
from app.config import get_settings

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        token_data = TokenPayload(**payload)
    except Exception as exc:  # pragma: no cover
        raise credentials_exception from exc

    user = db.query(models.User).filter(models.User.email == token_data.sub).first()
    if not user:
        raise credentials_exception
    return user


def require_role(required: models.UserRole):
    def role_dependency(current_user: models.User = Depends(get_current_user)):
        if current_user.role != required and current_user.role != models.UserRole.admin:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return role_dependency
