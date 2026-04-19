from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import ActiveUser, DbSession
from app.schemas.classes import (
    ClassCreate,
    ClassRead,
    ClassGradebookRead,
    ClassGradebookBulkUpsertRequest,
    ClassGradebookBulkUpsertResponse,
)
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


@router.get("/{class_id}/gradebook", response_model=ClassGradebookRead)
def get_class_gradebook(
    class_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    gradebook = classes_service.get_class_gradebook(
        db=db,
        class_id=class_id,
        school_id=current_user.school_id,
    )
    if gradebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found.",
        )

    return gradebook


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


@router.post(
    "/{class_id}/gradebook/bulk-upsert",
    response_model=ClassGradebookBulkUpsertResponse,
)
def bulk_upsert_class_gradebook_results(
    class_id: UUID,
    payload: ClassGradebookBulkUpsertRequest,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    result, items = classes_service.bulk_upsert_class_gradebook_results(
        db=db,
        school_id=current_user.school_id,
        class_id=class_id,
        payload=payload,
    )

    if result == "class_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found.",
        )
    if result == "duplicate_pairs_in_payload":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Duplicate exam/student pairs are not allowed in one bulk upsert request.",
        )
    if result == "exam_not_in_class":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more exams were not found in this class.",
        )
    if result == "student_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more students were not found.",
        )
    if result == "student_not_enrolled":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more students are not enrolled in this class.",
        )
    if result == "points_exceed_max":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Points cannot exceed exam max_points.",
        )

    assert items is not None
    return ClassGradebookBulkUpsertResponse(items=items)
