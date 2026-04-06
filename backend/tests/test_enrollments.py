from uuid import uuid4

from app.models.classes import Class
from app.models.enrollments import Enrollment
from app.models.schools import School
from app.models.students import Student
from app.models.teachers import Teacher
from tests.conftest import TEST_SCHOOL_ID


def test_create_enrollment(client, db_session):
    teacher = Teacher(
        school_id=TEST_SCHOOL_ID,
        name="Alice Teacher",
    )
    student = Student(
        school_id=TEST_SCHOOL_ID,
        first_name="Alice",
        last_name="Smith",
    )
    db_session.add_all([teacher, student])
    db_session.flush()

    class_ = Class(
        school_id=TEST_SCHOOL_ID,
        teacher_id=teacher.id,
        name="Mathematics 101",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    response = client.post(
        "/enrollments",
        json={
            "class_id": str(class_.id),
            "student_id": str(student.id),
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["class_id"] == str(class_.id)
    assert data["student_id"] == str(student.id)
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_enrollment_with_other_school_student_returns_404(client, db_session):
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
    db_session.flush()

    other_school = School(name="Other School")
    db_session.add(other_school)
    db_session.flush()

    other_student = Student(
        school_id=other_school.id,
        first_name="Bob",
        last_name="Jones",
    )
    db_session.add(other_student)
    db_session.commit()
    db_session.refresh(other_student)

    response = client.post(
        "/enrollments",
        json={
            "class_id": str(class_.id),
            "student_id": str(other_student.id),
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Class or student not found."}


def test_get_enrollment(client, db_session):
    teacher = Teacher(
        school_id=TEST_SCHOOL_ID,
        name="Alice Teacher",
    )
    student = Student(
        school_id=TEST_SCHOOL_ID,
        first_name="Alice",
        last_name="Smith",
    )
    db_session.add_all([teacher, student])
    db_session.flush()

    class_ = Class(
        school_id=TEST_SCHOOL_ID,
        teacher_id=teacher.id,
        name="Mathematics 101",
    )
    db_session.add(class_)
    db_session.flush()

    enrollment = Enrollment(
        class_id=class_.id,
        student_id=student.id,
    )
    db_session.add(enrollment)
    db_session.commit()
    db_session.refresh(enrollment)

    response = client.get(f"/enrollments/{enrollment.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(enrollment.id)
    assert data["class_id"] == str(class_.id)
    assert data["student_id"] == str(student.id)


def test_get_enrollment_not_found(client):
    response = client.get(f"/enrollments/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Enrollment not found."}


def test_list_enrollments_for_class(client, db_session):
    teacher = Teacher(
        school_id=TEST_SCHOOL_ID,
        name="Alice Teacher",
    )
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
    db_session.add_all([teacher, student_1, student_2])
    db_session.flush()

    class_ = Class(
        school_id=TEST_SCHOOL_ID,
        teacher_id=teacher.id,
        name="Mathematics 101",
    )
    db_session.add(class_)
    db_session.flush()

    enrollment_1 = Enrollment(
        class_id=class_.id,
        student_id=student_1.id,
    )
    enrollment_2 = Enrollment(
        class_id=class_.id,
        student_id=student_2.id,
    )

    other_school = School(name="Other School")
    db_session.add(other_school)
    db_session.flush()

    other_teacher = Teacher(
        school_id=other_school.id,
        name="Other Teacher",
    )
    other_student = Student(
        school_id=other_school.id,
        first_name="Charlie",
        last_name="Brown",
    )
    db_session.add_all([other_teacher, other_student])
    db_session.flush()

    other_class = Class(
        school_id=other_school.id,
        teacher_id=other_teacher.id,
        name="Physics 101",
    )
    db_session.add(other_class)
    db_session.flush()

    other_enrollment = Enrollment(
        class_id=other_class.id,
        student_id=other_student.id,
    )

    db_session.add_all([enrollment_1, enrollment_2, other_enrollment])
    db_session.commit()

    response = client.get(f"/enrollments/class/{class_.id}")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    student_ids = {item["student_id"] for item in data}
    assert str(student_1.id) in student_ids
    assert str(student_2.id) in student_ids
    assert str(other_student.id) not in student_ids

    for item in data:
        assert item["class_id"] == str(class_.id)


def test_list_enrollments_for_student(client, db_session):
    teacher = Teacher(
        school_id=TEST_SCHOOL_ID,
        name="Alice Teacher",
    )
    student = Student(
        school_id=TEST_SCHOOL_ID,
        first_name="Alice",
        last_name="Smith",
    )
    db_session.add_all([teacher, student])
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
    db_session.add_all([class_1, class_2])
    db_session.flush()

    enrollment_1 = Enrollment(
        class_id=class_1.id,
        student_id=student.id,
    )
    enrollment_2 = Enrollment(
        class_id=class_2.id,
        student_id=student.id,
    )

    other_school = School(name="Other School")
    db_session.add(other_school)
    db_session.flush()

    other_teacher = Teacher(
        school_id=other_school.id,
        name="Other Teacher",
    )
    other_student = Student(
        school_id=other_school.id,
        first_name="Charlie",
        last_name="Brown",
    )
    db_session.add_all([other_teacher, other_student])
    db_session.flush()

    other_class = Class(
        school_id=other_school.id,
        teacher_id=other_teacher.id,
        name="Chemistry 101",
    )
    db_session.add(other_class)
    db_session.flush()

    other_enrollment = Enrollment(
        class_id=other_class.id,
        student_id=other_student.id,
    )

    db_session.add_all([enrollment_1, enrollment_2, other_enrollment])
    db_session.commit()

    response = client.get(f"/enrollments/student/{student.id}")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    class_ids = {item["class_id"] for item in data}
    assert str(class_1.id) in class_ids
    assert str(class_2.id) in class_ids
    assert str(other_class.id) not in class_ids

    for item in data:
        assert item["student_id"] == str(student.id)


def test_delete_enrollment(client, db_session):
    teacher = Teacher(
        school_id=TEST_SCHOOL_ID,
        name="Alice Teacher",
    )
    student = Student(
        school_id=TEST_SCHOOL_ID,
        first_name="Alice",
        last_name="Smith",
    )
    db_session.add_all([teacher, student])
    db_session.flush()

    class_ = Class(
        school_id=TEST_SCHOOL_ID,
        teacher_id=teacher.id,
        name="Mathematics 101",
    )
    db_session.add(class_)
    db_session.flush()

    enrollment = Enrollment(
        class_id=class_.id,
        student_id=student.id,
    )
    db_session.add(enrollment)
    db_session.commit()
    db_session.refresh(enrollment)

    response = client.delete(f"/enrollments/{enrollment.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(enrollment.id)

    response = client.get(f"/enrollments/{enrollment.id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Enrollment not found."}


def test_delete_enrollment_not_found(client):
    response = client.delete(f"/enrollments/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Enrollment not found."}
