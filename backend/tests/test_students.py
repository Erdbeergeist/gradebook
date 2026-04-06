from uuid import uuid4

from app.models.schools import School
from app.models.students import Student
from tests.conftest import TEST_SCHOOL_ID


def test_create_student(client):
    response = client.post(
        "/students",
        json={
            "first_name": "Alice",
            "last_name": "Smith",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["first_name"] == "Alice"
    assert data["last_name"] == "Smith"
    assert data["school_id"] == str(TEST_SCHOOL_ID)
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_list_students(client, db_session):
    student_1 = Student(
        school_id=TEST_SCHOOL_ID,
        first_name="Alice",
        last_name="Smith",
    )
    student_2 = Student(
        school_id=TEST_SCHOOL_ID,
        first_name="Bob",
        last_name="Jones",
    )

    other_school = School(name="Other School")
    db_session.add(other_school)
    db_session.flush()

    other_student = Student(
        school_id=other_school.id,
        first_name="Charlie",
        last_name="Brown",
    )

    db_session.add_all([student_1, student_2, other_student])
    db_session.commit()

    response = client.get("/students")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    names = {(item["first_name"], item["last_name"]) for item in data}
    assert ("Alice", "Smith") in names
    assert ("Bob", "Jones") in names
    assert ("Charlie", "Brown") not in names

    for item in data:
        assert item["school_id"] == str(TEST_SCHOOL_ID)


def test_get_student(client, db_session):
    student = Student(
        school_id=TEST_SCHOOL_ID,
        first_name="Alice",
        last_name="Smith",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    response = client.get(f"/students/{student.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(student.id)
    assert data["first_name"] == "Alice"
    assert data["last_name"] == "Smith"
    assert data["school_id"] == str(TEST_SCHOOL_ID)


def test_get_student_not_found(client):
    response = client.get(f"/students/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Student not found."}


def test_get_student_from_other_school_returns_404(client, db_session):
    other_school = School(name="Other School")
    db_session.add(other_school)
    db_session.flush()

    other_student = Student(
        school_id=other_school.id,
        first_name="Charlie",
        last_name="Brown",
    )
    db_session.add(other_student)
    db_session.commit()
    db_session.refresh(other_student)

    response = client.get(f"/students/{other_student.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Student not found."}
