from httpx import AsyncClient


async def create_teacher(client: AsyncClient, admin_headers: dict[str, str], suffix: str) -> dict:
    response = await client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "email": f"teacher{suffix}@ica.eg",
            "password": "Teacher@123456",
            "role": "teacher",
            "teacher_profile": {
                "teacher_code": f"T{suffix}",
                "full_name": f"Teacher {suffix}",
                "phone_number": "01100000000",
                "teacher_type": "instructor_and_mentor",
                "is_team_leader": False,
            },
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def login(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


async def get_seed_context(client: AsyncClient, admin_headers: dict[str, str]) -> dict:
    branches = (await client.get("/api/branches", headers=admin_headers)).json()["data"]
    cycles = (await client.get("/api/cycles", headers=admin_headers)).json()["data"]
    tracks = (await client.get("/api/tracks", headers=admin_headers)).json()["data"]
    backend = next(track for track in tracks if track["code"] == "BE")
    frontend = next(track for track in tracks if track["code"] == "FE")
    return {
        "branch": branches[0],
        "cycle": cycles[0],
        "backend": backend,
        "frontend": frontend,
        "backend_level": backend["levels"][0],
        "frontend_level": frontend["levels"][0],
    }


async def test_admin_can_create_branch(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.post("/api/branches", headers=admin_headers, json={"name": "East Branch"})

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "East Branch"


async def test_non_admin_cannot_create_branch(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "201")
    teacher_headers = await login(client, teacher["email"], "Teacher@123456")

    response = await client.post("/api/branches", headers=teacher_headers, json={"name": "Teacher Branch"})

    assert response.status_code == 403


async def test_admin_can_create_cycle(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.post(
        "/api/cycles",
        headers=admin_headers,
        json={
            "cycle_number": 2,
            "name": "Cycle 2",
            "start_date": "2027-01-01",
            "end_date": "2027-12-31",
            "status": "active",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["cycle_number"] == 2


async def test_admin_can_create_track(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.post(
        "/api/tracks",
        headers=admin_headers,
        json={"code": "QA", "name": "Quality Assurance", "track_number": 20},
    )

    assert response.status_code == 200
    assert response.json()["data"]["code"] == "QA"


async def test_create_track_auto_creates_three_levels_when_requested(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/api/tracks",
        headers=admin_headers,
        json={"code": "MO", "name": "Mobile", "track_number": 21, "create_default_levels": True},
    )

    assert response.status_code == 200
    levels = response.json()["data"]["levels"]
    assert [level["level_number"] for level in levels] == [1, 2, 3]


async def test_cannot_create_duplicate_track_code(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.post(
        "/api/tracks",
        headers=admin_headers,
        json={"code": "BE", "name": "Backend Duplicate", "track_number": 30},
    )

    assert response.status_code == 409


async def test_cannot_create_duplicate_level_number_inside_same_track(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await get_seed_context(client, admin_headers)
    response = await client.post(
        "/api/levels",
        headers=admin_headers,
        json={
            "track_id": context["backend"]["id"],
            "level_number": 1,
            "title": "Duplicate Backend Level 1",
            "duration_months": 2,
        },
    )

    assert response.status_code == 409


async def test_cannot_create_class_with_max_students_above_25(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await get_seed_context(client, admin_headers)
    teacher = await create_teacher(client, admin_headers, "301")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    response = await client.post(
        "/api/classes",
        headers=admin_headers,
        json={
            "code": "BE1001",
            "branch_id": context["branch"]["id"],
            "cycle_id": context["cycle"]["id"],
            "track_id": context["backend"]["id"],
            "level_id": context["backend_level"]["id"],
            "instructor_id": teacher_profile_id,
            "mentor_id": teacher_profile_id,
            "schedule_text": "Sunday and Tuesday 18:00",
            "max_students": 26,
            "class_type": "online",
            "start_date": "2027-01-01",
            "end_date": "2027-03-01",
            "status": "planned",
        },
    )

    assert response.status_code == 422


async def test_cannot_create_class_when_level_does_not_belong_to_track(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await get_seed_context(client, admin_headers)
    teacher = await create_teacher(client, admin_headers, "302")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    response = await client.post(
        "/api/classes",
        headers=admin_headers,
        json={
            "code": "BE1002",
            "branch_id": context["branch"]["id"],
            "cycle_id": context["cycle"]["id"],
            "track_id": context["backend"]["id"],
            "level_id": context["frontend_level"]["id"],
            "instructor_id": teacher_profile_id,
            "mentor_id": teacher_profile_id,
            "schedule_text": "Sunday and Tuesday 18:00",
            "max_students": 25,
            "class_type": "online",
            "start_date": "2027-01-01",
            "end_date": "2027-03-01",
            "status": "planned",
        },
    )

    assert response.status_code == 400


async def test_teacher_can_view_only_assigned_classes(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await get_seed_context(client, admin_headers)
    assigned_teacher = await create_teacher(client, admin_headers, "401")
    other_teacher = await create_teacher(client, admin_headers, "402")
    assigned_profile_id = assigned_teacher["teacher_profile"]["id"]
    create_response = await client.post(
        "/api/classes",
        headers=admin_headers,
        json={
            "code": "BE1003",
            "branch_id": context["branch"]["id"],
            "cycle_id": context["cycle"]["id"],
            "track_id": context["backend"]["id"],
            "level_id": context["backend_level"]["id"],
            "instructor_id": assigned_profile_id,
            "mentor_id": assigned_profile_id,
            "schedule_text": "Sunday and Tuesday 18:00",
            "max_students": 25,
            "class_type": "online",
            "start_date": "2027-01-01",
            "end_date": "2027-03-01",
            "status": "planned",
        },
    )
    assert create_response.status_code == 200

    assigned_headers = await login(client, assigned_teacher["email"], "Teacher@123456")
    other_headers = await login(client, other_teacher["email"], "Teacher@123456")
    assigned_response = await client.get("/api/teachers/me/classes", headers=assigned_headers)
    other_response = await client.get("/api/teachers/me/classes", headers=other_headers)

    assert assigned_response.status_code == 200
    assert [item["code"] for item in assigned_response.json()["data"]] == ["BE1003"]
    assert other_response.status_code == 200
    assert other_response.json()["data"] == []


async def test_soft_delete_branch_works(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    create_response = await client.post("/api/branches", headers=admin_headers, json={"name": "Delete Branch"})
    branch_id = create_response.json()["data"]["id"]

    delete_response = await client.delete(f"/api/branches/{branch_id}", headers=admin_headers)
    get_response = await client.get(f"/api/branches/{branch_id}", headers=admin_headers)

    assert delete_response.status_code == 200
    assert get_response.status_code == 404
