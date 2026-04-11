from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.models.classes import Class
from app.models.enrollments import Enrollment
from app.models.exam_results import ExamResult, ExamResultStatus
from app.models.exams import Exam, ExamType, ExamTypeDetail
from app.models.grading_schemas import GradingSchema, GradingSchemaType
from app.models.schools import School
from app.models.students import Student
from app.models.teachers import Teacher
from app.models.grading_schemas import (
    GradingSchema,
    GradingSchemaType,
    GradingSchemaGrade,
    GradingSchemaRange,
)


def make_percentage_grading_schema(
    db_session, school_id, teacher_id, name="Default Percentage Schema"
):
    grading_schema = GradingSchema(
        school_id=school_id,
        teacher_id=teacher_id,
        name=name,
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
    )
    db_session.add(grading_schema)
    db_session.commit()
    db_session.refresh(grading_schema)
    return grading_schema


def test_create_exam_result(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = make_percentage_grading_schema(
        db_session=db_session,
        school_id=test_user.school_id,
        teacher_id=teacher.id,
    )

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    student = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    enrollment = Enrollment(
        class_id=class_.id,
        student_id=student.id,
    )
    db_session.add(enrollment)
    db_session.commit()

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

    graded_at = datetime.now(timezone.utc).isoformat()

    response = client.post(
        "/exam-results",
        json={
            "exam_id": str(exam.id),
            "student_id": str(student.id),
            "points": "87.50",
            "comment": "Strong work.",
            "status": "present",
            "graded_at": graded_at,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["exam_id"] == str(exam.id)
    assert data["student_id"] == str(student.id)
    assert Decimal(data["points"]) == Decimal("87.50")
    assert data["comment"] == "Strong work."
    assert data["status"] == "present"
    assert data["graded_at"] is not None


def test_create_exam_result_student_not_enrolled_returns_404(
    client, db_session, test_user
):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = make_percentage_grading_schema(
        db_session=db_session,
        school_id=test_user.school_id,
        teacher_id=teacher.id,
    )

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    student = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

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

    response = client.post(
        "/exam-results",
        json={
            "exam_id": str(exam.id),
            "student_id": str(student.id),
            "points": "87.50",
            "status": "present",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not enrolled in the exam class."


def test_create_exam_result_points_exceed_max_returns_422(
    client, db_session, test_user
):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = make_percentage_grading_schema(
        db_session=db_session,
        school_id=test_user.school_id,
        teacher_id=teacher.id,
    )

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    student = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    enrollment = Enrollment(
        class_id=class_.id,
        student_id=student.id,
    )
    db_session.add(enrollment)
    db_session.commit()

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

    response = client.post(
        "/exam-results",
        json={
            "exam_id": str(exam.id),
            "student_id": str(student.id),
            "points": "101.00",
            "status": "present",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Points cannot exceed exam max_points."


def test_create_exam_result_duplicate_returns_409(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = make_percentage_grading_schema(
        db_session=db_session,
        school_id=test_user.school_id,
        teacher_id=teacher.id,
    )

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    student = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    enrollment = Enrollment(
        class_id=class_.id,
        student_id=student.id,
    )
    db_session.add(enrollment)
    db_session.commit()

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

    exam_result = ExamResult(
        exam_id=exam.id,
        student_id=student.id,
        points=Decimal("87.50"),
        status=ExamResultStatus.PRESENT,
    )
    db_session.add(exam_result)
    db_session.commit()

    response = client.post(
        "/exam-results",
        json={
            "exam_id": str(exam.id),
            "student_id": str(student.id),
            "points": "88.00",
            "status": "present",
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Exam result already exists for this student and exam."
    )


def test_get_exam_result(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = make_percentage_grading_schema(
        db_session=db_session,
        school_id=test_user.school_id,
        teacher_id=teacher.id,
    )

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    student = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

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

    exam_result = ExamResult(
        exam_id=exam.id,
        student_id=student.id,
        points=Decimal("87.50"),
        comment="Strong work.",
        status=ExamResultStatus.PRESENT,
    )
    db_session.add(exam_result)
    db_session.commit()
    db_session.refresh(exam_result)

    response = client.get(f"/exam-results/{exam_result.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(exam_result.id)
    assert Decimal(data["points"]) == Decimal("87.50")
    assert data["comment"] == "Strong work."
    assert data["status"] == "present"


def test_get_exam_result_not_found(client):
    response = client.get("/exam-results/00000000-0000-0000-0000-000000000999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Exam result not found."


def test_list_exam_results_for_exam(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = make_percentage_grading_schema(
        db_session=db_session,
        school_id=test_user.school_id,
        teacher_id=teacher.id,
    )

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

    db_session.add_all(
        [
            ExamResult(
                exam_id=exam.id,
                student_id=student_1.id,
                points=Decimal("87.50"),
                status=ExamResultStatus.PRESENT,
            ),
            ExamResult(
                exam_id=exam.id,
                student_id=student_2.id,
                points=Decimal("91.00"),
                status=ExamResultStatus.PRESENT,
            ),
        ]
    )
    db_session.commit()

    response = client.get(f"/exam-results/exam/{exam.id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_exam_results_for_student(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = make_percentage_grading_schema(
        db_session=db_session,
        school_id=test_user.school_id,
        teacher_id=teacher.id,
    )

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    student = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    db_session.add(Enrollment(class_id=class_.id, student_id=student.id))
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
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    db_session.add_all([exam_1, exam_2])
    db_session.commit()
    db_session.refresh(exam_1)
    db_session.refresh(exam_2)

    db_session.add_all(
        [
            ExamResult(
                exam_id=exam_1.id,
                student_id=student.id,
                points=Decimal("87.50"),
                status=ExamResultStatus.PRESENT,
            ),
            ExamResult(
                exam_id=exam_2.id,
                student_id=student.id,
                points=Decimal("91.00"),
                status=ExamResultStatus.PRESENT,
            ),
        ]
    )
    db_session.commit()

    response = client.get(f"/exam-results/student/{student.id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_delete_exam_result(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    grading_schema = make_percentage_grading_schema(
        db_session=db_session,
        school_id=test_user.school_id,
        teacher_id=teacher.id,
    )

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    student = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

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

    exam_result = ExamResult(
        exam_id=exam.id,
        student_id=student.id,
        points=Decimal("87.50"),
        status=ExamResultStatus.PRESENT,
    )
    db_session.add(exam_result)
    db_session.commit()
    db_session.refresh(exam_result)

    response = client.delete(f"/exam-results/{exam_result.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(exam_result.id)


def test_delete_exam_result_not_found(client):
    response = client.delete("/exam-results/00000000-0000-0000-0000-000000000999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Exam result not found."


def test_get_exam_result_includes_resolved_grade_label(client, db_session, test_user):
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

    grade = GradingSchemaGrade(
        grading_schema_id=grading_schema.id,
        label="2",
        sort_order=10,
    )
    db_session.add(grade)
    db_session.commit()
    db_session.refresh(grade)

    range_rule = GradingSchemaRange(
        grading_schema_id=grading_schema.id,
        grade_id=grade.id,
        min_value=Decimal("80.00"),
        max_value=Decimal("90.00"),
        min_inclusive=True,
        max_inclusive=False,
    )
    db_session.add(range_rule)
    db_session.commit()

    class_ = Class(
        school_id=test_user.school_id,
        teacher_id=teacher.id,
        name="Math 10A",
    )
    db_session.add(class_)
    db_session.commit()
    db_session.refresh(class_)

    student = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

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

    exam_result = ExamResult(
        exam_id=exam.id,
        student_id=student.id,
        points=Decimal("87.50"),
        status=ExamResultStatus.PRESENT,
    )
    db_session.add(exam_result)
    db_session.commit()
    db_session.refresh(exam_result)

    response = client.get(f"/exam-results/{exam_result.id}")

    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["resolved_input_value"]) == Decimal("87.50")
    assert data["resolved_grade_label"] == "2"


def test_update_exam_result(client, db_session, test_user):
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
        name="Percentage Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
        is_template=False,
        is_system=False,
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

    student = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    db_session.add(
        Enrollment(
            class_id=class_.id,
            student_id=student.id,
        )
    )
    db_session.commit()

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

    exam_result = ExamResult(
        exam_id=exam.id,
        student_id=student.id,
        points=Decimal("80.00"),
        comment="Initial comment.",
        status=ExamResultStatus.PRESENT,
    )
    db_session.add(exam_result)
    db_session.commit()
    db_session.refresh(exam_result)

    graded_at = datetime.now(timezone.utc).isoformat()

    response = client.put(
        f"/exam-results/{exam_result.id}",
        json={
            "points": "87.50",
            "comment": "Strong work.",
            "status": "present",
            "graded_at": graded_at,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(exam_result.id)
    assert Decimal(data["points"]) == Decimal("87.50")
    assert data["comment"] == "Strong work."
    assert data["status"] == "present"
    assert data["graded_at"] is not None
    assert data["exam_id"] == str(exam.id)
    assert data["student_id"] == str(student.id)


def test_update_exam_result_points_exceed_max_returns_422(
    client, db_session, test_user
):
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
        name="Percentage Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
        is_template=False,
        is_system=False,
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

    student = Student(
        school_id=test_user.school_id,
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    db_session.add(
        Enrollment(
            class_id=class_.id,
            student_id=student.id,
        )
    )
    db_session.commit()

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

    exam_result = ExamResult(
        exam_id=exam.id,
        student_id=student.id,
        points=Decimal("80.00"),
        status=ExamResultStatus.PRESENT,
    )
    db_session.add(exam_result)
    db_session.commit()
    db_session.refresh(exam_result)

    response = client.put(
        f"/exam-results/{exam_result.id}",
        json={
            "points": "101.00",
            "comment": "Too high.",
            "status": "present",
            "graded_at": None,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Points cannot exceed exam max_points."


def test_update_exam_result_not_found(client):
    response = client.put(
        "/exam-results/00000000-0000-0000-0000-000000000999",
        json={
            "points": "87.50",
            "comment": "Strong work.",
            "status": "present",
            "graded_at": None,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Exam result not found."


def test_update_exam_result_from_other_school_returns_404(
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

    other_schema = GradingSchema(
        school_id=other_school.id,
        teacher_id=other_teacher.id,
        name="Other Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
        is_template=False,
        is_system=False,
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

    other_student = Student(
        school_id=other_school.id,
        first_name="Grace",
        last_name="Hopper",
    )
    db_session.add(other_student)
    db_session.commit()
    db_session.refresh(other_student)

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

    other_exam_result = ExamResult(
        exam_id=other_exam.id,
        student_id=other_student.id,
        points=Decimal("80.00"),
        status=ExamResultStatus.PRESENT,
    )
    db_session.add(other_exam_result)
    db_session.commit()
    db_session.refresh(other_exam_result)

    response = client.put(
        f"/exam-results/{other_exam_result.id}",
        json={
            "points": "87.50",
            "comment": "Strong work.",
            "status": "present",
            "graded_at": None,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Exam result not found."
