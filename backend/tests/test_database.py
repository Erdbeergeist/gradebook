from sqlalchemy.orm import Session

from app.database import get_db_session


def test_get_db_session_yields_session() -> None:
    generator = get_db_session()
    session = next(generator)

    try:
        assert isinstance(session, Session)
    finally:
        generator.close()
