from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dependencies import CurrentUserContext, get_current_user
from app.main import app
from app.models.schools import School
from app.database import SessionLocal, engine, get_db_session


TEST_SUPERUSER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_SCHOOL_ID = UUID("00000000-0000-0000-0000-000000000100")


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_user() -> CurrentUserContext:
    return CurrentUserContext(
        user_id=TEST_SUPERUSER_ID,
        school_id=TEST_SCHOOL_ID,
        role="superuser",
        is_active=True,
    )


@pytest.fixture
def seeded_school(db_session: Session) -> School:
    school = School(
        id=TEST_SCHOOL_ID,
        name="Test School",
    )
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


@pytest.fixture
def client(db_session: Session, test_user: CurrentUserContext, seeded_school: School):
    def override_get_db_session():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user() -> CurrentUserContext:
        return test_user

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
