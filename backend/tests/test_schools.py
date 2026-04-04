from uuid import uuid4

from fastapi.testclient import TestClient


def test_create_school(client: TestClient) -> None:
    response = client.post(
        "/schools",
        json={"name": "Test School"},
    )

    assert response.status_code == 201

    body = response.json()
    assert body["name"] == "Test School"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


def test_list_schools(client: TestClient) -> None:
    response_1 = client.post(
        "/schools",
        json={"name": "School A"},
    )
    response_2 = client.post(
        "/schools",
        json={"name": "School B"},
    )

    assert response_1.status_code == 201
    assert response_2.status_code == 201

    response = client.get("/schools")

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0]["name"] == "School A"
    assert body[1]["name"] == "School B"


def test_get_school(client: TestClient) -> None:
    create_response = client.post(
        "/schools",
        json={"name": "Lookup School"},
    )

    assert create_response.status_code == 201

    school_id = create_response.json()["id"]

    response = client.get(f"/schools/{school_id}")

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == school_id
    assert body["name"] == "Lookup School"


def test_get_school_not_found(client: TestClient) -> None:
    missing_id = uuid4()

    response = client.get(f"/schools/{missing_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "School not found."}
