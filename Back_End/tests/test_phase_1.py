from httpx import AsyncClient


async def test_health_endpoint(public_client: AsyncClient) -> None:
    response = await public_client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"


async def test_admin_login(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login",
        json={"email": "admin@ica.eg", "password": "Admin@123456"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


async def test_refresh_token(client: AsyncClient, admin_tokens: dict) -> None:
    response = await client.post("/api/auth/refresh", json={"refresh_token": admin_tokens["refresh_token"]})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["refresh_token"] != admin_tokens["refresh_token"]


async def test_protected_endpoint_without_token(public_client: AsyncClient) -> None:
    response = await public_client.get("/api/auth/me")

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Authentication required"
    assert body["errors"] == []


async def test_validation_error_uses_unified_format(public_client: AsyncClient) -> None:
    response = await public_client.post(
        "/api/auth/login",
        json={"email": "not-an-email", "password": "short"},
    )

    body = response.json()
    assert response.status_code == 422
    assert body["success"] is False
    assert body["message"] == "Validation failed"
    assert isinstance(body["errors"], list)


async def test_me_with_token(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.get("/api/auth/me", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "admin@ica.eg"
    assert data["role"] == "admin"
    assert "password_hash" not in data


async def test_admin_creates_user(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "email": "student1@ica.eg",
            "password": "Student@123456",
            "role": "student",
            "student_profile": {
                "student_code": "S001",
                "full_name": "Student One",
                "phone_number": "01000000000",
                "status": "active",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "student1@ica.eg"
    assert data["must_change_password"] is True
    assert data["student_profile"]["student_code"] == "S001"
    assert "password_hash" not in data


async def test_non_admin_cannot_create_user(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    create_response = await client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "email": "teacher1@ica.eg",
            "password": "Teacher@123456",
            "role": "teacher",
            "teacher_profile": {
                "teacher_code": "T001",
                "full_name": "Teacher One",
                "phone_number": "01100000000",
                "teacher_type": "mentor",
                "is_team_leader": False,
            },
        },
    )
    assert create_response.status_code == 200

    login_response = await client.post(
        "/api/auth/login",
        json={"email": "teacher1@ica.eg", "password": "Teacher@123456"},
    )
    teacher_headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}
    response = await client.post(
        "/api/users",
        headers=teacher_headers,
        json={
            "email": "student2@ica.eg",
            "password": "Student@123456",
            "role": "student",
            "student_profile": {
                "student_code": "S002",
                "full_name": "Student Two",
                "status": "active",
            },
        },
    )

    assert response.status_code == 403


async def test_soft_delete_user(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    create_response = await client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "email": "student3@ica.eg",
            "password": "Student@123456",
            "role": "student",
            "student_profile": {
                "student_code": "S003",
                "full_name": "Student Three",
                "status": "active",
            },
        },
    )
    user_id = create_response.json()["data"]["id"]

    delete_response = await client.delete(f"/api/users/{user_id}", headers=admin_headers)
    get_response = await client.get(f"/api/users/{user_id}", headers=admin_headers)

    assert delete_response.status_code == 200
    assert get_response.status_code == 404
