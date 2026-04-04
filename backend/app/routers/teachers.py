from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import ActiveUser, DbSession
from app.schemas.teachers import TeacherCreate, TeacherRead
from app.services import teachers_service


router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.post(
    "",
    response_model=TeacherRead,
    status_code=status.HTTP_201_CREATED,
)
def create_teacher(
    payload: TeacherCreate,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    return teachers_service.create_teacher(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )


@router.get("", response_model=list[TeacherRead])
def list_teachers(
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    return teachers_service.list_teachers(
        db=db,
        school_id=current_user.school_id,
    )


@router.get("/{teacher_id}", response_model=TeacherRead)
def get_teacher(
    teacher_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    teacher = teachers_service.get_teacher(
        db=db,
        teacher_id=teacher_id,
        school_id=current_user.school_id,
    )
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found.",
        )
    return teacher
