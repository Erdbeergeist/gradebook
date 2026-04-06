from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import ActiveUser, DbSession
from app.schemas.classes import ClassCreate, ClassRead
from app.services import classes_service


router = APIRouter(prefix="/classes", tags=["classes"])


@router.post(
    "",
    response_model=ClassRead,
    status_code=status.HTTP_201_CREATED,
)
def create_class(
    payload: ClassCreate,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    class_ = classes_service.create_class(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found.",
        )

    return class_


@router.get("", response_model=list[ClassRead])
def list_classes(
    db: DbSession,
    current_user: ActiveUser,
    teacher_id: UUID | None = None,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    return classes_service.list_classes(
        db=db,
        school_id=current_user.school_id,
        teacher_id=teacher_id,
    )


@router.get("/{class_id}", response_model=ClassRead)
def get_class(
    class_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    class_ = classes_service.get_class(
        db=db,
        class_id=class_id,
        school_id=current_user.school_id,
    )
    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found.",
        )

    return class_
