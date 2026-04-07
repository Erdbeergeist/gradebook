from decimal import Decimal

from app.models.classes import Class
from app.models.exams import Exam, ExamType, ExamTypeDetail
from app.models.grading_schemas import GradingSchema, GradingSchemaType
from app.models.schools import School
from app.models.teachers import Teacher


def test_create_exam(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = GradingSchema(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Default Percentage Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
    )
    db_session.add(grading_schema)
    db_session.commit()
    db_session.refresh(grading_schema)

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    response = client.post(
        "/exams",
        json={
            "class_id": str(class_.id),
            "template_grading_schema_id": str(grading_schema.id),
            "name": "Midterm",
            "exam_type": "written",
            "exam_type_detail": "essay",
            "max_points": "100.00",
            "weight": "1.00",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["class_id"] == str(class_.id)
    assert data["grading_schema_id"] != str(grading_schema.id)

    cloned_schema = db_session.get(GradingSchema, data["grading_schema_id"])
    assert cloned_schema is not None
    assert cloned_schema.teacher_id == teacher.id
    assert cloned_schema.is_template is False
    assert cloned_schema.is_system is False
    assert cloned_schema.source_schema_id == grading_schema.id
    assert data["name"] == "Midterm"
    assert data["exam_type"] == "written"
    assert data["exam_type_detail"] == "essay"
    assert Decimal(data["max_points"]) == Decimal("100.00")
    assert Decimal(data["weight"]) == Decimal("1.00")


def test_create_exam_with_other_school_class_returns_404(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = GradingSchema(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Default Percentage Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
    )
    db_session.add(grading_schema)
    db_session.commit()
    db_session.refresh(grading_schema)

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

    response = client.post(
        "/exams",
        json={
            "class_id": str(other_class.id),
            "template_grading_schema_id": str(grading_schema.id),
            "name": "Midterm",
            "exam_type": "written",
            "exam_type_detail": "essay",
            "max_points": "100.00",
            "weight": "1.00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found."


def test_create_exam_with_unknown_grading_schema_returns_404(
    client, db_session, test_user
):
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

    response = client.post(
        "/exams",
        json={
            "class_id": str(class_.id),
            "template_grading_schema_id": "00000000-0000-0000-0000-000000000999",
            "name": "Midterm",
            "exam_type": "written",
            "exam_type_detail": "essay",
            "max_points": "100.00",
            "weight": "1.00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Grading schema not found."


def test_create_exam_with_grading_schema_from_other_teacher_returns_422(
    client, db_session, test_user
):
    teacher_1 = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    teacher_2 = Teacher(
        school_id=test_user.school_id,
        name="Teacher Two",
    )
    db_session.add_all([teacher_1, teacher_2])
    db_session.commit()
    db_session.refresh(teacher_1)
    db_session.refresh(teacher_2)

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher_1.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    grading_schema = GradingSchema(
        school_id=test_user.school_id,
        teacher_id=teacher_2.id,
        name="Teacher Two Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
    )
    db_session.add(grading_schema)
    db_session.commit()
    db_session.refresh(grading_schema)

    response = client.post(
        "/exams",
        json={
            "class_id": str(class_.id),
            "template_grading_schema_id": str(grading_schema.id),
            "name": "Midterm",
            "exam_type": "written",
            "exam_type_detail": "essay",
            "max_points": "100.00",
            "weight": "1.00",
        },
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Grading schema teacher does not match the class teacher."
    )


def test_create_exam_with_points_schema_max_points_mismatch_returns_422(
    client, db_session, test_user
):
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
        name="15 Point Schema",
        scheme_type=GradingSchemaType.POINTS,
        max_points=Decimal("15.00"),
    )
    db_session.add(grading_schema)
    db_session.commit()
    db_session.refresh(grading_schema)

    response = client.post(
        "/exams",
        json={
            "class_id": str(class_.id),
            "template_grading_schema_id": str(grading_schema.id),
            "name": "Quiz",
            "exam_type": "written",
            "exam_type_detail": "short_answer",
            "max_points": "20.00",
            "weight": "1.00",
        },
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Exam max_points must equal grading schema max_points for points-based schemas."
    )


def test_list_exams(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = GradingSchema(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Default Percentage Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
    )
    db_session.add(grading_schema)
    db_session.commit()
    db_session.refresh(grading_schema)

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

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
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("2.00"),
    )
    db_session.add_all([exam_1, exam_2])
    db_session.commit()

    response = client.get("/exams")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["grading_schema_id"] == str(grading_schema.id)
    assert data[1]["grading_schema_id"] == str(grading_schema.id)


def test_list_exams_filtered_by_class_id(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = GradingSchema(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Default Percentage Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
    )
    db_session.add(grading_schema)
    db_session.commit()
    db_session.refresh(grading_schema)

    class_1 = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    class_2 = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10B",
    )
    db_session.add_all([class_1, class_2])
    db_session.commit()
    db_session.refresh(class_1)
    db_session.refresh(class_2)

    exam_1 = Exam(
        school_id=test_user.school_id,
        class_id=class_1.id,
        grading_schema_id=grading_schema.id,
        name="Midterm A",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    exam_2 = Exam(
        school_id=test_user.school_id,
        class_id=class_2.id,
        grading_schema_id=grading_schema.id,
        name="Midterm B",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    db_session.add_all([exam_1, exam_2])
    db_session.commit()

    response = client.get(f"/exams?class_id={class_1.id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["class_id"] == str(class_1.id)


def test_list_exams_filtered_by_teacher_id(client, db_session, test_user):
    teacher_1 = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    teacher_2 = Teacher(
        school_id=test_user.school_id,
        name="Teacher Two",
    )
    db_session.add_all([teacher_1, teacher_2])
    db_session.commit()
    db_session.refresh(teacher_1)
    db_session.refresh(teacher_2)

    grading_schema_1 = GradingSchema(
        school_id=test_user.school_id,
        teacher_id=teacher_1.id,
        name="Schema One",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
    )
    grading_schema_2 = GradingSchema(
        school_id=test_user.school_id,
        teacher_id=teacher_2.id,
        name="Schema Two",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
    )
    db_session.add_all([grading_schema_1, grading_schema_2])
    db_session.commit()
    db_session.refresh(grading_schema_1)
    db_session.refresh(grading_schema_2)

    class_1 = Class(
        school_id=test_user.school_id,
        teacher_id=teacher_1.id,
        name="Math 10A",
    )
    class_2 = Class(
        school_id=test_user.school_id,
        teacher_id=teacher_2.id,
        name="Math 10B",
    )
    db_session.add_all([class_1, class_2])
    db_session.commit()
    db_session.refresh(class_1)
    db_session.refresh(class_2)

    exam_1 = Exam(
        school_id=test_user.school_id,
        class_id=class_1.id,
        grading_schema_id=grading_schema_1.id,
        name="Teacher One Exam",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    exam_2 = Exam(
        school_id=test_user.school_id,
        class_id=class_2.id,
        grading_schema_id=grading_schema_2.id,
        name="Teacher Two Exam",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    db_session.add_all([exam_1, exam_2])
    db_session.commit()

    response = client.get(f"/exams?teacher_id={teacher_1.id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Teacher One Exam"


def test_get_exam(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = GradingSchema(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Default Percentage Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
    )
    db_session.add(grading_schema)
    db_session.commit()
    db_session.refresh(grading_schema)

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    exam = Exam(
        school_id=test_user.school_id,
        class_id=class_.id,
        grading_schema_id=grading_schema.id,
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
    assert data["grading_schema_id"] == str(grading_schema.id)


def test_get_exam_not_found(client):
    response = client.get("/exams/00000000-0000-0000-0000-000000000999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Exam not found."


def test_get_exam_from_other_school_returns_404(client, db_session, test_user):
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

    other_schema = GradingSchema(
        school_id=other_school.id,
        teacher_id=other_teacher.id,
        name="Other Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
    )
    db_session.add(other_schema)
    db_session.commit()
    db_session.refresh(other_schema)

    other_class = Class(
        school_id=other_school.id,
        teacher_id=other_teacher.id,
        name="Foreign Class",
    )
    db_session.add(other_class)
    db_session.commit()
    db_session.refresh(other_class)

    other_exam = Exam(
        school_id=other_school.id,
        class_id=other_class.id,
        grading_schema_id=other_schema.id,
        name="Foreign Exam",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    db_session.add(other_exam)
    db_session.commit()
    db_session.refresh(other_exam)

    response = client.get(f"/exams/{other_exam.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Exam not found."
