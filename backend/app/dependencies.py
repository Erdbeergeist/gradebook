from dataclasses import dataclass
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.authz import *

from app.core.dev_constants import DEV_SCHOOL_ID, DEV_USER_ID

DbSession = Annotated[Session, Depends(get_db_session)]


@dataclass(frozen=True)
class CurrentUserContext:
    user_id: UUID
    school_id: UUID | None
    role: str
    is_active: bool


def get_current_user() -> CurrentUserContext:
    return CurrentUserContext(
        user_id=DEV_USER_ID,
        school_id=DEV_SCHOOL_ID,
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
