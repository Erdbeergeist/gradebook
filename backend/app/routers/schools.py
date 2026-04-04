from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.authz import ROLE_SUPERUSER
from app.dependencies import ActiveUser, DbSession, require_role
from app.schemas.schools import SchoolCreate, SchoolRead
from app.services import schools_service


router = APIRouter(prefix="/schools", tags=["schools"])


@router.post(
    "",
    response_model=SchoolRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(ROLE_SUPERUSER))],
)
def create_school(
    payload: SchoolCreate,
    db: DbSession,
    current_user: ActiveUser,
):
    return schools_service.create_school(db=db, payload=payload)


@router.get("", response_model=list[SchoolRead])
def list_schools(
    db: DbSession,
    current_user: ActiveUser,
):
    return schools_service.list_schools(db=db)


@router.get("/{school_id}", response_model=SchoolRead)
def get_school(
    school_id: UUID,
    db: DbSession,
    current_user: ActiveUser,
):
    school = schools_service.get_school(db=db, school_id=school_id)
    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )
    return school
