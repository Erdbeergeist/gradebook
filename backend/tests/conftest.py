from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, get_db_session
from app.dependencies import CurrentUserContext, get_current_user
from app.main import app


TEST_SUPERUSER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)

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
        school_id=None,
        role="superuser",
        is_active=True,
    )


@pytest.fixture
def client(
    db_session: Session,
    test_user: CurrentUserContext,
) -> Generator[TestClient, None, None]:
    def override_get_db_session() -> Generator[Session, None, None]:
        yield db_session

    def override_get_current_user() -> CurrentUserContext:
        return test_user

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
