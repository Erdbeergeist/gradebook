from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import ActiveUser, DbSession
from app.schemas.exam_results import ExamResultCreate, ExamResultRead, ExamResultUpdate
from app.services import exam_results_service

router = APIRouter(prefix="/exam-results", tags=["exam-results"])


@router.post("", response_model=ExamResultRead, status_code=status.HTTP_201_CREATED)
def create_exam_result(
    payload: ExamResultCreate,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    result, exam_result = exam_results_service.create_exam_result(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )

    if result == "exam_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )
    if result == "student_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )
    if result == "student_not_enrolled":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not enrolled in the exam class.",
        )
    if result == "duplicate":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exam result already exists for this student and exam.",
        )
    if result == "points_exceed_max":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Points cannot exceed exam max_points.",
        )

    return exam_result


@router.put("/{exam_result_id}", response_model=ExamResultRead)
def update_exam_result(
    exam_result_id: UUID,
    payload: ExamResultUpdate,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    result, exam_result = exam_results_service.update_exam_result(
        db=db,
        school_id=current_user.school_id,
        exam_result_id=exam_result_id,
        payload=payload,
    )

    if result == "exam_result_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam result not found.",
        )
    if result == "points_exceed_max":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Points cannot exceed exam max_points.",
        )

    return exam_result


@router.get("/{exam_result_id}", response_model=ExamResultRead)
def get_exam_result(
    exam_result_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    exam_result = exam_results_service.get_exam_result(
        db=db,
        school_id=current_user.school_id,
        exam_result_id=exam_result_id,
    )
    if exam_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam result not found.",
        )

    return exam_result


@router.get("/exam/{exam_id}", response_model=list[ExamResultRead])
def list_exam_results_for_exam(
    exam_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    return exam_results_service.list_exam_results_for_exam(
        db=db,
        school_id=current_user.school_id,
        exam_id=exam_id,
    )


@router.get("/student/{student_id}", response_model=list[ExamResultRead])
def list_exam_results_for_student(
    student_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    return exam_results_service.list_exam_results_for_student(
        db=db,
        school_id=current_user.school_id,
        student_id=student_id,
    )


@router.delete("/{exam_result_id}", response_model=ExamResultRead)
def delete_exam_result(
    exam_result_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    exam_result = exam_results_service.delete_exam_result(
        db=db,
        school_id=current_user.school_id,
        exam_result_id=exam_result_id,
    )
    if exam_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam result not found.",
        )

    return exam_result
