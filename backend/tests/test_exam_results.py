from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.models.classes import Class
from app.models.enrollments import Enrollment
from app.models.exam_results import ExamResult, ExamResultStatus
from app.models.exams import Exam, ExamType, ExamTypeDetail
from app.models.schools import School
from app.models.students import Student
from app.models.teachers import Teacher


def test_create_exam_result(client, db_session, test_user):
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
        name="Midterm",
        exam_type=ExamType.WRITTEN,
        exam_type_detail=ExamTypeDetail.ESSAY,
        max_points=Decimal("100.00"),
        weight=Decimal("1.00"),
    )
    exam_2 = Exam(
        school_id=test_user.school_id,
        class_id=class_.id,
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
