from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db_session


DbSession = Annotated[Session, Depends(get_db_session)]


class CurrentUserStub:
    def __init__(
        self,
        user_id: str = "stub-user",
        school_id: str = "stub-school",
        role: str = "school_admin",
        is_active: bool = True,
    ) -> None:
        self.user_id = user_id
        self.school_id = school_id
        self.role = role
        self.is_active = is_active


def get_current_user() -> CurrentUserStub:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not implemented yet.",
    )


CurrentUser = Annotated[CurrentUserStub, Depends(get_current_user)]


def require_active_user(current_user: CurrentUser) -> CurrentUserStub:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user.",
        )
    return current_user


ActiveUser = Annotated[CurrentUserStub, Depends(require_active_user)]


def require_role(*allowed_roles: str):
    def role_checker(current_user: CurrentUser) -> CurrentUserStub:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return role_checker
