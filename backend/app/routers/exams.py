from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import ActiveUser, DbSession
from app.schemas.exams import ExamCreate, ExamRead
from app.services import exams_service


router = APIRouter(prefix="/exams", tags=["exams"])


@router.post(
    "",
    response_model=ExamRead,
    status_code=status.HTTP_201_CREATED,
)
def create_exam(
    payload: ExamCreate,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    result, exam = exams_service.create_exam(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )

    if result == "class_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found.",
        )

    if result == "grading_schema_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grading schema not found.",
        )

    if result == "grading_schema_teacher_mismatch":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Grading schema teacher does not match the class teacher.",
        )

    if result == "points_schema_max_points_mismatch":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Exam max_points must equal grading schema max_points for points-based schemas.",
        )

    return exam


@router.get("", response_model=list[ExamRead])
def list_exams(
    db: DbSession,
    current_user: ActiveUser,
    class_id: UUID | None = None,
    teacher_id: UUID | None = None,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    return exams_service.list_exams(
        db=db,
        school_id=current_user.school_id,
        class_id=class_id,
        teacher_id=teacher_id,
    )


@router.get("/{exam_id}", response_model=ExamRead)
def get_exam(
    exam_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    exam = exams_service.get_exam(
        db=db,
        exam_id=exam_id,
        school_id=current_user.school_id,
    )
    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )

    return exam
