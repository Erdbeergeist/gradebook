from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import ActiveUser, DbSession
from app.schemas.grading_schemas import (
    GradeCatalogRead,
    GradingSchemaCreate,
    GradingSchemaRead,
)
from app.services import grading_schemas_service

router = APIRouter(prefix="/grading-schemas", tags=["grading-schemas"])


@router.get("/catalogs", response_model=list[GradeCatalogRead])
def list_grade_catalogs(
    db: DbSession,
):
    return grading_schemas_service.list_grade_catalogs(db=db)


@router.post("", response_model=GradingSchemaRead, status_code=status.HTTP_201_CREATED)
def create_grading_schema(
    payload: GradingSchemaCreate,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    result, grading_schema = grading_schemas_service.create_grading_schema(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )

    if result == "teacher_not_found":
        raise HTTPException(status_code=404, detail="Teacher not found.")
    if result == "grade_catalog_not_found":
        raise HTTPException(status_code=404, detail="Grade catalog not found.")
    if result == "duplicate_grade_labels":
        raise HTTPException(
            status_code=422,
            detail="Grade labels must be unique within a grading schema.",
        )
    if result == "duplicate_grade_sort_orders":
        raise HTTPException(
            status_code=422,
            detail="Grade sort_order values must be unique within a grading schema.",
        )
    if result == "unknown_range_grade_label":
        raise HTTPException(
            status_code=422, detail="A range references an unknown grade label."
        )
    if result == "range_out_of_domain":
        raise HTTPException(
            status_code=422,
            detail="A range value is outside the grading schema domain.",
        )
    if result == "unknown_override_grade_label":
        raise HTTPException(
            status_code=422, detail="An override references an unknown grade label."
        )
    if result == "override_out_of_domain":
        raise HTTPException(
            status_code=422,
            detail="An override value is outside the grading schema domain.",
        )
    if result == "duplicate_override_input_values":
        raise HTTPException(
            status_code=422,
            detail="Override input values must be unique within a grading schema.",
        )
    if result == "overlapping_ranges":
        raise HTTPException(
            status_code=422, detail="Grading schema ranges must not overlap."
        )

    return grading_schema


@router.get("", response_model=list[GradingSchemaRead])
def list_grading_schemas(
    db: DbSession,
    current_user: ActiveUser,
    teacher_id: UUID | None = Query(default=None),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    return grading_schemas_service.list_grading_schemas(
        db=db,
        school_id=current_user.school_id,
        teacher_id=teacher_id,
    )


@router.get("/{grading_schema_id}", response_model=GradingSchemaRead)
def get_grading_schema(
    grading_schema_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user is not associated with a school.",
        )

    grading_schema = grading_schemas_service.get_grading_schema(
        db=db,
        school_id=current_user.school_id,
        grading_schema_id=grading_schema_id,
    )
    if grading_schema is None:
        raise HTTPException(status_code=404, detail="Grading schema not found.")

    return grading_schema
