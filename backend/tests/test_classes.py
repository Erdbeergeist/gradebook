from uuid import uuid4
from decimal import Decimal

from app.models.enrollments import Enrollment
from app.models.exam_results import ExamResult, ExamResultStatus
from app.models.exams import Exam, ExamType, ExamTypeDetail
from app.models.grading_schemas import (
    GradingSchema,
    GradingSchemaGrade,
    GradingSchemaRange,
    GradingSchemaType,
)
from app.models.classes import Class
from app.models.schools import School
from app.models.teachers import Teacher
from app.models.students import Student
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


def test_get_class_gradebook(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    grading_schema = GradingSchema(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Percentage Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
        is_template=False,
        is_system=False,
    )
    db_session.add(grading_schema)
    db_session.flush()

    grade_1 = GradingSchemaGrade(
        grading_schema_id=grading_schema.id,
        label="1",
        sort_order=10,
    )
    grade_2 = GradingSchemaGrade(
        grading_schema_id=grading_schema.id,
        label="2",
        sort_order=20,
    )
    db_session.add_all([grade_1, grade_2])
    db_session.flush()

    db_session.add_all(
        [
            GradingSchemaRange(
                grading_schema_id=grading_schema.id,
                grade_id=grade_1.id,
                min_value=Decimal("90.00"),
                max_value=Decimal("100.00"),
                min_inclusive=True,
                max_inclusive=True,
            ),
            GradingSchemaRange(
                grading_schema_id=grading_schema.id,
                grade_id=grade_2.id,
                min_value=Decimal("80.00"),
                max_value=Decimal("90.00"),
                min_inclusive=True,
                max_inclusive=False,
            ),
        ]
    )
    db_session.commit()
    db_session.refresh(grading_schema)

    student_1 = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    student_2 = Student(
        school_id=test_user.school_id,
        first_name="Grace",
        last_name="Hopper",
    )
    db_session.add_all([student_1, student_2])
    db_session.commit()
    db_session.refresh(student_1)
    db_session.refresh(student_2)

    db_session.add_all(
        [
            Enrollment(class_id=class_.id, student_id=student_1.id),
            Enrollment(class_id=class_.id, student_id=student_2.id),
        ]
    )
    db_session.commit()

    exam_1 = Exam(
        school_id=test_user.school_id,
        class_id=class_.id,
        grading_schema_id=grading_schema.id,
        name="Midterm",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    exam_2 = Exam(
        school_id=test_user.school_id,
        class_id=class_.id,
        grading_schema_id=grading_schema.id,
        name="Final",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.SHORT_ANSWER,
        max_points=Decimal("100.00"),
        weight=Decimal("1.50"),
    )
    db_session.add_all([exam_1, exam_2])
    db_session.commit()
    db_session.refresh(exam_1)
    db_session.refresh(exam_2)

    result_1 = ExamResult(
        exam_id=exam_1.id,
        student_id=student_1.id,
        points=Decimal("92.00"),
        comment="Strong work.",
        status=ExamResultStatus.PRESENT,
    )
    result_2 = ExamResult(
        exam_id=exam_2.id,
        student_id=student_2.id,
        points=Decimal("84.00"),
        comment="Solid.",
        status=ExamResultStatus.PRESENT,
    )
    db_session.add_all([result_1, result_2])
    db_session.commit()

    response = client.get(f"/classes/{class_.id}/gradebook")

    assert response.status_code == 200
    data = response.json()

    assert data["class_"]["id"] == str(class_.id)
    assert data["class_"]["name"] == "Math 10A"

    assert len(data["students"]) == 2
    assert len(data["exams"]) == 2
    assert len(data["cells"]) == 4

    student_ids = {item["id"] for item in data["students"]}
    exam_ids = {item["id"] for item in data["exams"]}

    assert student_ids == {str(student_1.id), str(student_2.id)}
    assert exam_ids == {str(exam_1.id), str(exam_2.id)}

    cells_by_pair = {
        (cell["student_id"], cell["exam_id"]): cell for cell in data["cells"]
    }

    ada_midterm = cells_by_pair[(str(student_1.id), str(exam_1.id))]
    assert ada_midterm["points"] == "92.00"
    assert ada_midterm["comment"] == "Strong work."
    assert ada_midterm["status"] == "present"
    assert ada_midterm["resolved_grade_label"] == "1"

    grace_final = cells_by_pair[(str(student_2.id), str(exam_2.id))]
    assert grace_final["points"] == "84.00"
    assert grace_final["comment"] == "Solid."
    assert grace_final["status"] == "present"
    assert grace_final["resolved_grade_label"] == "2"

    ada_final = cells_by_pair[(str(student_1.id), str(exam_2.id))]
    assert ada_final["exam_result_id"] is None
    assert ada_final["points"] is None
    assert ada_final["resolved_grade_label"] is None

    grace_midterm = cells_by_pair[(str(student_2.id), str(exam_1.id))]
    assert grace_midterm["exam_result_id"] is None
    assert grace_midterm["points"] is None
    assert grace_midterm["resolved_grade_label"] is None


def test_get_class_gradebook_not_found(client):
    response = client.get("/classes/00000000-0000-0000-0000-000000000999/gradebook")
    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found."


def test_get_class_gradebook_from_other_school_returns_404(
    client, db_session, test_user
):
    from app.models.schools import School

    other_school = School(name="Other School")
    db_session.add(other_school)
    db_session.commit()
    db_session.refresh(other_school)

    other_teacher = Teacher(
        school_id=other_school.id,
        name="Other Teacher",
    )
    db_session.add(other_teacher)
    db_session.commit()
    db_session.refresh(other_teacher)

    other_class = Class(
        school_id=other_school.id,
        teacher_id=other_teacher.id,
        name="Foreign Class",
    )
    db_session.add(other_class)
    db_session.commit()
    db_session.refresh(other_class)

    response = client.get(f"/classes/{other_class.id}/gradebook")

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found."


def test_get_class_gradebook_orders_students_by_name(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    student_1 = Student(
        school_id=test_user.school_id,
        first_name="Zoe",
        last_name="Alpha",
    )
    student_2 = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Alpha",
    )
    student_3 = Student(
        school_id=test_user.school_id,
        first_name="Bob",
        last_name="Zulu",
    )
    db_session.add_all([student_1, student_2, student_3])
    db_session.commit()
    db_session.refresh(student_1)
    db_session.refresh(student_2)
    db_session.refresh(student_3)

    db_session.add_all(
        [
            Enrollment(class_id=class_.id, student_id=student_1.id),
            Enrollment(class_id=class_.id, student_id=student_2.id),
            Enrollment(class_id=class_.id, student_id=student_3.id),
        ]
    )
    db_session.commit()

    response = client.get(f"/classes/{class_.id}/gradebook")

    assert response.status_code == 200
    names = [
        (item["last_name"], item["first_name"]) for item in response.json()["students"]
    ]
    assert names == [
        ("Alpha", "Ada"),
        ("Alpha", "Zoe"),
        ("Zulu", "Bob"),
    ]
