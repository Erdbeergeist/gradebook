from uuid import uuid4

from app.models.classes import Class
from app.models.schools import School
from app.models.teachers import Teacher
from tests.conftest import TEST_SCHOOL_ID


def test_create_class(client, db_session):
    teacher = Teacher(
        school_id=TEST_SCHOOL_ID,
        name="Alice Teacher",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    response = client.post(
        "/classes",
        json={
            "teacher_id": str(teacher.id),
            "name": "Mathematics 101",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Mathematics 101"
    assert data["school_id"] == str(TEST_SCHOOL_ID)
    assert data["teacher_id"] == str(teacher.id)
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_class_with_teacher_from_other_school_returns_404(client, db_session):
    other_school = School(name="Other School")
    db_session.add(other_school)
    db_session.flush()

    other_teacher = Teacher(
        school_id=other_school.id,
        name="Other Teacher",
    )
    db_session.add(other_teacher)
    db_session.commit()
    db_session.refresh(other_teacher)

    response = client.post(
        "/classes",
        json={
            "teacher_id": str(other_teacher.id),
            "name": "Mathematics 101",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Teacher not found."}


def test_list_classes(client, db_session):
    teacher = Teacher(
        school_id=TEST_SCHOOL_ID,
        name="Alice Teacher",
    )
    db_session.add(teacher)
    db_session.flush()

    class_1 = Class(
        school_id=TEST_SCHOOL_ID,
        teacher_id=teacher.id,
        name="Mathematics 101",
    )
    class_2 = Class(
        school_id=TEST_SCHOOL_ID,
        teacher_id=teacher.id,
        name="Physics 101",
    )

    other_school = School(name="Other School")
    db_session.add(other_school)
    db_session.flush()

    other_teacher = Teacher(
        school_id=other_school.id,
        name="Other Teacher",
    )
    db_session.add(other_teacher)
    db_session.flush()

    other_class = Class(
        school_id=other_school.id,
        teacher_id=other_teacher.id,
        name="Chemistry 101",
    )

    db_session.add_all([class_1, class_2, other_class])
    db_session.commit()

    response = client.get("/classes")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    names = {item["name"] for item in data}
    assert "Mathematics 101" in names
    assert "Physics 101" in names
    assert "Chemistry 101" not in names

    for item in data:
        assert item["school_id"] == str(TEST_SCHOOL_ID)
        assert item["teacher_id"] == str(teacher.id)


def test_get_class(client, db_session):
    teacher = Teacher(
        school_id=TEST_SCHOOL_ID,
        name="Alice Teacher",
    )
    db_session.add(teacher)
    db_session.flush()

    class_ = Class(
        school_id=TEST_SCHOOL_ID,
        teacher_id=teacher.id,
        name="Mathematics 101",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    response = client.get(f"/classes/{class_.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(class_.id)
    assert data["name"] == "Mathematics 101"
    assert data["school_id"] == str(TEST_SCHOOL_ID)
    assert data["teacher_id"] == str(teacher.id)


def test_get_class_not_found(client):
    response = client.get(f"/classes/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Class not found."}


def test_get_class_from_other_school_returns_404(client, db_session):
    other_school = School(name="Other School")
    db_session.add(other_school)
    db_session.flush()

    other_teacher = Teacher(
        school_id=other_school.id,
        name="Other Teacher",
    )
    db_session.add(other_teacher)
    db_session.flush()

    other_class = Class(
        school_id=other_school.id,
        teacher_id=other_teacher.id,
        name="Chemistry 101",
    )
    db_session.add(other_class)
    db_session.commit()
    db_session.refresh(other_class)

    response = client.get(f"/classes/{other_class.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Class not found."}


def test_list_classes_filtered_by_teacher_id(client, db_session):
    teacher_1 = Teacher(
        school_id=TEST_SCHOOL_ID,
        name="Alice Teacher",
    )
    teacher_2 = Teacher(
        school_id=TEST_SCHOOL_ID,
        name="Bob Teacher",
    )
    db_session.add_all([teacher_1, teacher_2])
    db_session.flush()

    class_1 = Class(
        school_id=TEST_SCHOOL_ID,
        teacher_id=teacher_1.id,
        name="Mathematics 101",
    )
    class_2 = Class(
        school_id=TEST_SCHOOL_ID,
        teacher_id=teacher_1.id,
        name="Physics 101",
    )
    class_3 = Class(
        school_id=TEST_SCHOOL_ID,
        teacher_id=teacher_2.id,
        name="Chemistry 101",
    )

    other_school = School(name="Other School")
    db_session.add(other_school)
    db_session.flush()

    other_teacher = Teacher(
        school_id=other_school.id,
        name="Other Teacher",
    )
    db_session.add(other_teacher)
    db_session.flush()

    other_class = Class(
        school_id=other_school.id,
        teacher_id=other_teacher.id,
        name="Biology 101",
    )

    db_session.add_all([class_1, class_2, class_3, other_class])
    db_session.commit()

    response = client.get(f"/classes?teacher_id={teacher_1.id}")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    names = {item["name"] for item in data}
    assert "Mathematics 101" in names
    assert "Physics 101" in names
    assert "Chemistry 101" not in names
    assert "Biology 101" not in names

    for item in data:
        assert item["school_id"] == str(TEST_SCHOOL_ID)
        assert item["teacher_id"] == str(teacher_1.id)


def test_list_classes_filtered_by_unknown_teacher_id_returns_empty_list(client):
    response = client.get(f"/classes?teacher_id={uuid4()}")

    assert response.status_code == 200
    assert response.json() == []
