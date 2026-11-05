def test_create_and_get_user(client):
    response = client.post("/users", json={
        "name": "Alex Johnson",
        "email": "alex@example.com",
        "role": "member",
    })
    assert response.status_code == 201
    created = response.json()
    assert created["email"] == "alex@example.com"
    assert created["role"] == "member"

    fetched = client.get(f"/users/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]


def test_duplicate_email_returns_409(client):
    payload = {"name": "Alex", "email": "alex@example.com", "role": "member"}
    assert client.post("/users", json=payload).status_code == 201
    response = client.post("/users", json={**payload, "name": "Another Alex"})
    assert response.status_code == 409


def test_validation_returns_400_for_invalid_payload(client):
    response = client.post(
        "/users",
        json={
            "name": " ",
            "email": "not-an-email",
            "role": "owner"
        }
    )

    assert response.status_code == 400


def test_update_preserves_created_at(client):
    created = client.post("/users", json={
        "name": "Alex", "email": "alex@example.com", "role": "member"
    }).json()

    updated_response = client.patch(f"/users/{created['id']}", json={"name": "Alex Johnson"})
    assert updated_response.status_code == 200
    updated = updated_response.json()
    assert updated["name"] == "Alex Johnson"
    assert updated["created_at"] == created["created_at"]


def test_delete_user(client):
    created = client.post("/users", json={
        "name": "Alex", "email": "alex@example.com", "role": "member"
    }).json()

    deleted = client.delete(f"/users/{created['id']}")
    assert deleted.status_code == 200
    assert client.get(f"/users/{created['id']}").status_code == 404


def test_invalid_id_returns_400(client):
    assert client.get("/users/not-a-uuid").status_code == 400


def test_missing_user_returns_404(client):
    import uuid
    assert client.get(f"/users/{uuid.uuid4()}").status_code == 404
