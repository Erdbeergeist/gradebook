from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.schools import School
from app.models.teachers import Teacher

DEV_SCHOOL_ID = UUID("00000000-0000-0000-0000-000000000100")
DEV_SCHOOL_NAME = "Development School"

DEV_TEACHER_ID = UUID("00000000-0000-0000-0000-000000000200")
DEV_TEACHER_NAME = "Dev Teacher"


def seed_dev_data(db: Session) -> None:
    try:
        school = db.get(School, DEV_SCHOOL_ID)

        if school is None:
            school = School(
                id=DEV_SCHOOL_ID,
                name=DEV_SCHOOL_NAME,
            )
            db.add(school)
        elif school.name != DEV_SCHOOL_NAME:
            school.name = DEV_SCHOOL_NAME

        teacher = db.get(Teacher, DEV_TEACHER_ID)

        if teacher is None:
            teacher = Teacher(
                id=DEV_TEACHER_ID,
                school_id=DEV_SCHOOL_ID,
                name=DEV_TEACHER_NAME,
            )
            db.add(teacher)
        else:
            teacher.school_id = DEV_SCHOOL_ID
            teacher.name = DEV_TEACHER_NAME

        db.commit()
    except Exception:
        db.rollback()
        raise
