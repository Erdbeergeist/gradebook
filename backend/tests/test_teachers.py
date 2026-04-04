from uuid import uuid4

from fastapi.testclient import TestClient


def test_create_teacher(client: TestClient) -> None:
    response = client.post(
        "/teachers",
        json={"name": "Alice Teacher"},
    )

    assert response.status_code == 201

    body = response.json()
    assert body["name"] == "Alice Teacher"
    assert body["school_id"] == "00000000-0000-0000-0000-000000000100"
    assert body["user_id"] is None
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


def test_list_teachers(client: TestClient) -> None:
    response_1 = client.post(
        "/teachers",
        json={"name": "Teacher A"},
    )
    response_2 = client.post(
        "/teachers",
        json={"name": "Teacher B"},
    )

    assert response_1.status_code == 201
    assert response_2.status_code == 201

    response = client.get("/teachers")

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0]["name"] == "Teacher A"
    assert body[1]["name"] == "Teacher B"


def test_get_teacher(client: TestClient) -> None:
    create_response = client.post(
        "/teachers",
        json={"name": "Lookup Teacher"},
    )

    assert create_response.status_code == 201

    teacher_id = create_response.json()["id"]

    response = client.get(f"/teachers/{teacher_id}")

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == teacher_id
    assert body["name"] == "Lookup Teacher"
    assert body["school_id"] == "00000000-0000-0000-0000-000000000100"


def test_get_teacher_not_found(client: TestClient) -> None:
    missing_id = uuid4()

    response = client.get(f"/teachers/{missing_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Teacher not found."}
