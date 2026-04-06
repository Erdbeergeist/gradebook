from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import ActiveUser, DbSession
from app.schemas.enrollments import EnrollmentCreate, EnrollmentRead
from app.services import enrollments_service


router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post(
    "",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    payload: EnrollmentCreate,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    enrollment = enrollments_service.create_enrollment(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class or student not found.",
        )

    return enrollment


@router.get("/{enrollment_id}", response_model=EnrollmentRead)
def get_enrollment(
    enrollment_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    enrollment = enrollments_service.get_enrollment(
        db=db,
        enrollment_id=enrollment_id,
        school_id=current_user.school_id,
    )
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    return enrollment


@router.get("/class/{class_id}", response_model=list[EnrollmentRead])
def list_enrollments_for_class(
    class_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    return enrollments_service.list_enrollments_for_class(
        db=db,
        class_id=class_id,
        school_id=current_user.school_id,
    )


@router.get("/student/{student_id}", response_model=list[EnrollmentRead])
def list_enrollments_for_student(
    student_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    return enrollments_service.list_enrollments_for_student(
        db=db,
        student_id=student_id,
        school_id=current_user.school_id,
    )


@router.delete("/{enrollment_id}", response_model=EnrollmentRead)
def delete_enrollment(
    enrollment_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    enrollment = enrollments_service.delete_enrollment(
        db=db,
        enrollment_id=enrollment_id,
        school_id=current_user.school_id,
    )
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    return enrollment
