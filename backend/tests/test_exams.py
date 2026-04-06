from decimal import Decimal
from uuid import uuid4

from app.models.classes import Class
from app.models.exams import Exam, ExamType, ExamTypeDetail
from app.models.schools import School
from app.models.teachers import Teacher
from tests.conftest import TEST_SCHOOL_ID


def test_create_exam(client, db_session):
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

    response = client.post(
        "/exams",
        json={
            "class_id": str(class_.id),
            "name": "Midterm",
            "exam_type": "written",
            "exam_type_detail": "essay",
            "max_points": "100.00",
            "weight": "1.50",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["school_id"] == str(TEST_SCHOOL_ID)
    assert data["class_id"] == str(class_.id)
    assert data["name"] == "Midterm"
    assert data["exam_type"] == "written"
    assert data["exam_type_detail"] == "essay"
    assert Decimal(data["max_points"]) == Decimal("100.00")
    assert Decimal(data["weight"]) == Decimal("1.50")
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_exam_with_other_school_class_returns_404(client, db_session):
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
        name="Physics 101",
    )
    db_session.add(other_class)
    db_session.commit()
    db_session.refresh(other_class)

    response = client.post(
        "/exams",
        json={
            "class_id": str(other_class.id),
            "name": "Midterm",
            "exam_type": "written",
            "exam_type_detail": "essay",
            "max_points": "100.00",
            "weight": "1.00",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Class not found."}


def test_list_exams(client, db_session):
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

    exam_1 = Exam(
        school_id=TEST_SCHOOL_ID,
        class_id=class_.id,
        name="Midterm",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    exam_2 = Exam(
        school_id=TEST_SCHOOL_ID,
        class_id=class_.id,
        name="Oral Check",
        exam_type=ExamType.ORAL,
        exam_type_detail=ExamTypeDetail.INDIVIDUAL_ORAL,
        max_points=Decimal("20.00"),
        weight=Decimal("0.50"),
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
        name="Physics 101",
    )
    db_session.add(other_class)
    db_session.flush()

    other_exam = Exam(
        school_id=other_school.id,
        class_id=other_class.id,
        name="Other Exam",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.MULTIPLE_CHOICE,
        max_points=Decimal("50.00"),
        weight=Decimal("1.00"),
    )

    db_session.add_all([exam_1, exam_2, other_exam])
    db_session.commit()

    response = client.get("/exams")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    names = {item["name"] for item in data}
    assert "Midterm" in names
    assert "Oral Check" in names
    assert "Other Exam" not in names

    for item in data:
        assert item["school_id"] == str(TEST_SCHOOL_ID)
        assert item["class_id"] == str(class_.id)


def test_list_exams_filtered_by_class_id(client, db_session):
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
    db_session.add_all([class_1, class_2])
    db_session.flush()

    exam_1 = Exam(
        school_id=TEST_SCHOOL_ID,
        class_id=class_1.id,
        name="Midterm",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    exam_2 = Exam(
        school_id=TEST_SCHOOL_ID,
        class_id=class_1.id,
        name="Quiz",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.SHORT_ANSWER,
        max_points=Decimal("20.00"),
        weight=Decimal("0.50"),
    )
    exam_3 = Exam(
        school_id=TEST_SCHOOL_ID,
        class_id=class_2.id,
        name="Presentation",
        exam_type=ExamType.PRESENTATION,
        exam_type_detail=ExamTypeDetail.SLIDES,
        max_points=Decimal("30.00"),
        weight=Decimal("1.00"),
    )

    db_session.add_all([exam_1, exam_2, exam_3])
    db_session.commit()

    response = client.get(f"/exams?class_id={class_1.id}")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    names = {item["name"] for item in data}
    assert "Midterm" in names
    assert "Quiz" in names
    assert "Presentation" not in names

    for item in data:
        assert item["school_id"] == str(TEST_SCHOOL_ID)
        assert item["class_id"] == str(class_1.id)


def test_get_exam(client, db_session):
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

    exam = Exam(
        school_id=TEST_SCHOOL_ID,
        class_id=class_.id,
        name="Midterm",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    db_session.add(exam)
    db_session.commit()
    db_session.refresh(exam)

    response = client.get(f"/exams/{exam.id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(exam.id)
    assert data["school_id"] == str(TEST_SCHOOL_ID)
    assert data["class_id"] == str(class_.id)
    assert data["name"] == "Midterm"
    assert data["exam_type"] == "written"
    assert data["exam_type_detail"] == "essay"
    assert Decimal(data["max_points"]) == Decimal("100.00")
    assert Decimal(data["weight"]) == Decimal("1.00")


def test_get_exam_not_found(client):
    response = client.get(f"/exams/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Exam not found."}


def test_get_exam_from_other_school_returns_404(client, db_session):
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
        name="Physics 101",
    )
    db_session.add(other_class)
    db_session.flush()

    other_exam = Exam(
        school_id=other_school.id,
        class_id=other_class.id,
        name="Other Exam",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.MULTIPLE_CHOICE,
        max_points=Decimal("50.00"),
        weight=Decimal("1.00"),
    )
    db_session.add(other_exam)
    db_session.commit()
    db_session.refresh(other_exam)

    response = client.get(f"/exams/{other_exam.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Exam not found."}


def test_list_exams_filtered_by_teacher_id(client, db_session):
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
    db_session.add_all([class_1, class_2, class_3])
    db_session.flush()

    exam_1 = Exam(
        school_id=TEST_SCHOOL_ID,
        class_id=class_1.id,
        name="Midterm",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    exam_2 = Exam(
        school_id=TEST_SCHOOL_ID,
        class_id=class_2.id,
        name="Quiz",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.SHORT_ANSWER,
        max_points=Decimal("20.00"),
        weight=Decimal("0.50"),
    )
    exam_3 = Exam(
        school_id=TEST_SCHOOL_ID,
        class_id=class_3.id,
        name="Oral Check",
        exam_type=ExamType.ORAL,
        exam_type_detail=ExamTypeDetail.INDIVIDUAL_ORAL,
        max_points=Decimal("25.00"),
        weight=Decimal("1.00"),
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
    db_session.add(other_class)
    db_session.flush()

    other_exam = Exam(
        school_id=other_school.id,
        class_id=other_class.id,
        name="Other Exam",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.MULTIPLE_CHOICE,
        max_points=Decimal("50.00"),
        weight=Decimal("1.00"),
    )

    db_session.add_all([exam_1, exam_2, exam_3, other_exam])
    db_session.commit()

    response = client.get(f"/exams?teacher_id={teacher_1.id}")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    names = {item["name"] for item in data}
    assert "Midterm" in names
    assert "Quiz" in names
    assert "Oral Check" not in names
    assert "Other Exam" not in names

    for item in data:
        assert item["school_id"] == str(TEST_SCHOOL_ID)
        assert item["class_id"] in {str(class_1.id), str(class_2.id)}
