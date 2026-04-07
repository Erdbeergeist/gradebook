from decimal import Decimal

from app.models.schools import School
from app.models.teachers import Teacher


def test_list_grade_catalogs(client):
    response = client.get("/grading-schemas/catalogs")
    assert response.status_code == 200

    data = response.json()
    codes = {item["code"] for item in data}
    assert "de_standard" in codes
    assert "de_oberstufe" in codes


def test_create_percentage_grading_schema_from_catalog(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    response = client.post(
        "/grading-schemas",
        json={
            "teacher_id": str(teacher.id),
            "name": "Default German",
            "scheme_type": "percentage",
            "max_points": None,
            "grade_catalog_code": "de_standard",
            "ranges": [
                {
                    "grade_label": "1",
                    "min_value": "95.00",
                    "max_value": "100.00",
                    "min_inclusive": True,
                    "max_inclusive": True,
                },
                {
                    "grade_label": "1-",
                    "min_value": "90.00",
                    "max_value": "95.00",
                    "min_inclusive": True,
                    "max_inclusive": False,
                },
            ],
            "overrides": [
                {
                    "input_value": "92.00",
                    "grade_label": "1",
                }
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["teacher_id"] == str(teacher.id)
    assert data["scheme_type"] == "percentage"
    assert data["max_points"] is None
    assert len(data["grades"]) == 15
    assert any(item["label"] == "5" for item in data["grades"])


def test_create_points_grading_schema_requires_max_points(
    client, db_session, test_user
):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    response = client.post(
        "/grading-schemas",
        json={
            "teacher_id": str(teacher.id),
            "name": "Points Schema",
            "scheme_type": "points",
            "grade_catalog_code": "de_oberstufe",
        },
    )

    assert response.status_code == 422


def test_create_grading_schema_with_teacher_from_other_school_returns_404(
    client, db_session, test_user
):
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

    response = client.post(
        "/grading-schemas",
        json={
            "teacher_id": str(other_teacher.id),
            "name": "Foreign Schema",
            "scheme_type": "percentage",
            "grade_catalog_code": "de_standard",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Teacher not found."


def test_create_grading_schema_rejects_duplicate_grade_labels(
    client, db_session, test_user
):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    response = client.post(
        "/grading-schemas",
        json={
            "teacher_id": str(teacher.id),
            "name": "Custom Schema",
            "scheme_type": "percentage",
            "grades": [
                {"label": "1", "sort_order": 10},
                {"label": "1", "sort_order": 20},
            ],
        },
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Grade labels must be unique within a grading schema."
    )


def test_create_grading_schema_rejects_overlapping_ranges(
    client, db_session, test_user
):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    response = client.post(
        "/grading-schemas",
        json={
            "teacher_id": str(teacher.id),
            "name": "Overlap Schema",
            "scheme_type": "percentage",
            "grades": [
                {"label": "1", "sort_order": 10},
                {"label": "2", "sort_order": 20},
            ],
            "ranges": [
                {
                    "grade_label": "1",
                    "min_value": "80.00",
                    "max_value": "90.00",
                    "min_inclusive": True,
                    "max_inclusive": True,
                },
                {
                    "grade_label": "2",
                    "min_value": "90.00",
                    "max_value": "100.00",
                    "min_inclusive": True,
                    "max_inclusive": True,
                },
            ],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Grading schema ranges must not overlap."


def test_list_grading_schemas_filtered_by_teacher_id(client, db_session, test_user):
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

    response_1 = client.post(
        "/grading-schemas",
        json={
            "teacher_id": str(teacher_1.id),
            "name": "Schema One",
            "scheme_type": "percentage",
            "grade_catalog_code": "de_standard",
        },
    )
    assert response_1.status_code == 201

    response_2 = client.post(
        "/grading-schemas",
        json={
            "teacher_id": str(teacher_2.id),
            "name": "Schema Two",
            "scheme_type": "percentage",
            "grade_catalog_code": "de_standard",
        },
    )
    assert response_2.status_code == 201

    response = client.get(f"/grading-schemas?teacher_id={teacher_1.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["teacher_id"] == str(teacher_1.id)


def test_create_grading_schema_sets_template_flags(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    response = client.post(
        "/grading-schemas",
        json={
            "teacher_id": str(teacher.id),
            "name": "Default German",
            "scheme_type": "percentage",
            "grade_catalog_code": "de_standard",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["is_template"] is True
    assert data["is_system"] is False
    assert data["source_schema_id"] is None


def test_list_grading_schemas_exposes_template_flags(client, db_session, test_user):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    response = client.post(
        "/grading-schemas",
        json={
            "teacher_id": str(teacher.id),
            "name": "Schema One",
            "scheme_type": "percentage",
            "grade_catalog_code": "de_standard",
        },
    )
    assert response.status_code == 201

    response = client.get(f"/grading-schemas?teacher_id={teacher.id}")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["is_template"] is True
    assert data[0]["is_system"] is False
    assert data[0]["source_schema_id"] is None
