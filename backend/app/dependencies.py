from dataclasses import dataclass
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.authz import *


DbSession = Annotated[Session, Depends(get_db_session)]


@dataclass(frozen=True)
class CurrentUserContext:
    user_id: UUID
    school_id: UUID | None
    role: str
    is_active: bool


def get_current_user() -> CurrentUserContext:
    """
    Development-only auth stub.

    Later this will be replaced by real authentication and token/session parsing.
    For now it returns a fixed active school admin context.
    """
    return CurrentUserContext(
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        school_id=UUID("00000000-0000-0000-0000-000000000100"),
        role=ROLE_SUPERUSER,
        is_active=True,
    )


CurrentUser = Annotated[CurrentUserContext, Depends(get_current_user)]


def require_active_user(current_user: CurrentUser) -> CurrentUserContext:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user.",
        )
    return current_user


ActiveUser = Annotated[CurrentUserContext, Depends(require_active_user)]


def require_role(*allowed_roles: str):
    def role_checker(current_user: CurrentUser) -> CurrentUserContext:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return role_checker
