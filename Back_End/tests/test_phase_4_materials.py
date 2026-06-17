from httpx import AsyncClient


async def login(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


async def create_teacher(client: AsyncClient, admin_headers: dict[str, str], suffix: str) -> dict:
    response = await client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "email": f"phase4.teacher{suffix}@ica.eg",
            "password": "Teacher@123456",
            "role": "teacher",
            "teacher_profile": {
                "teacher_code": f"P4T{suffix}",
                "full_name": f"Phase 4 Teacher {suffix}",
                "phone_number": "01100000000",
                "teacher_type": "instructor_and_mentor",
                "is_team_leader": False,
            },
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def create_student(client: AsyncClient, admin_headers: dict[str, str], suffix: str) -> dict:
    response = await client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "email": f"phase4.student{suffix}@ica.eg",
            "password": "Student@123456",
            "role": "student",
            "student_profile": {
                "student_code": f"P4S{suffix}",
                "full_name": f"Phase 4 Student {suffix}",
                "phone_number": "01000000000",
                "status": "active",
            },
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def get_seed_context(client: AsyncClient, admin_headers: dict[str, str]) -> dict:
    branches = (await client.get("/api/branches", headers=admin_headers)).json()["data"]
    cycles = (await client.get("/api/cycles", headers=admin_headers)).json()["data"]
    tracks = (await client.get("/api/tracks", headers=admin_headers)).json()["data"]
    backend = next(track for track in tracks if track["code"] == "BE")
    return {
        "branch": branches[0],
        "cycle": cycles[0],
        "track": backend,
        "level": backend["levels"][0],
    }


async def create_class(
    client: AsyncClient,
    admin_headers: dict[str, str],
    code: str,
    instructor_id: str,
    mentor_id: str,
) -> dict:
    context = await get_seed_context(client, admin_headers)
    response = await client.post(
        "/api/classes",
        headers=admin_headers,
        json={
            "code": code,
            "branch_id": context["branch"]["id"],
            "cycle_id": context["cycle"]["id"],
            "track_id": context["track"]["id"],
            "level_id": context["level"]["id"],
            "instructor_id": instructor_id,
            "mentor_id": mentor_id,
            "schedule_text": "Sunday and Tuesday 18:00",
            "max_students": 25,
            "class_type": "online",
            "start_date": "2027-01-01",
            "end_date": "2027-03-01",
            "status": "active",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def create_material(
    client: AsyncClient,
    headers: dict[str, str],
    class_id: str,
    creator_role: str = "instructor",
    creator_id: str | None = None,
    title: str = "Session 1 PDF",
    url: str = "https://example.com/session-1.pdf",
):
    payload = {
        "class_id": class_id,
        "creator_role": creator_role,
        "title": title,
        "description": "Intro material",
        "material_type": "pdf",
        "url": url,
    }
    if creator_id is not None:
        payload["creator_id"] = creator_id
    return await client.post("/api/materials", headers=headers, json=payload)


async def enroll(client: AsyncClient, admin_headers: dict[str, str], student_id: str, class_id: str) -> None:
    response = await client.post(
        "/api/enrollments",
        headers=admin_headers,
        json={"student_id": student_id, "class_id": class_id},
    )
    assert response.status_code == 200


async def test_admin_can_create_material(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "001")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    academic_class = await create_class(client, admin_headers, "BE1101", teacher_profile_id, teacher_profile_id)

    response = await create_material(
        client,
        admin_headers,
        academic_class["id"],
        creator_id=teacher_profile_id,
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["class_code"] == "BE1101"
    assert data["creator_id"] == teacher_profile_id
    assert data["creator_name"] == teacher["teacher_profile"]["full_name"]
    assert data["title"] == "Session 1 PDF"


async def test_teacher_can_create_material_for_assigned_class(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    teacher = await create_teacher(client, admin_headers, "002")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    academic_class = await create_class(client, admin_headers, "BE1102", teacher_profile_id, teacher_profile_id)
    teacher_headers = await login(client, teacher["email"], "Teacher@123456")

    response = await create_material(client, teacher_headers, academic_class["id"])

    assert response.status_code == 200
    assert response.json()["data"]["creator_role"] == "instructor"


async def test_teacher_cannot_create_material_for_unassigned_class(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    assigned_teacher = await create_teacher(client, admin_headers, "003A")
    other_teacher = await create_teacher(client, admin_headers, "003B")
    assigned_profile_id = assigned_teacher["teacher_profile"]["id"]
    academic_class = await create_class(client, admin_headers, "BE1103", assigned_profile_id, assigned_profile_id)
    other_headers = await login(client, other_teacher["email"], "Teacher@123456")

    response = await create_material(client, other_headers, academic_class["id"])

    assert response.status_code == 403


async def test_instructor_can_create_instructor_material_when_assigned_as_instructor(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    instructor = await create_teacher(client, admin_headers, "004I")
    mentor = await create_teacher(client, admin_headers, "004M")
    academic_class = await create_class(
        client,
        admin_headers,
        "BE1104",
        instructor["teacher_profile"]["id"],
        mentor["teacher_profile"]["id"],
    )
    instructor_headers = await login(client, instructor["email"], "Teacher@123456")

    response = await create_material(client, instructor_headers, academic_class["id"], creator_role="instructor")

    assert response.status_code == 200
    assert response.json()["data"]["creator_role"] == "instructor"


async def test_mentor_can_create_mentor_material_when_assigned_as_mentor(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    instructor = await create_teacher(client, admin_headers, "005I")
    mentor = await create_teacher(client, admin_headers, "005M")
    academic_class = await create_class(
        client,
        admin_headers,
        "BE1105",
        instructor["teacher_profile"]["id"],
        mentor["teacher_profile"]["id"],
    )
    mentor_headers = await login(client, mentor["email"], "Teacher@123456")

    response = await create_material(client, mentor_headers, academic_class["id"], creator_role="mentor")

    assert response.status_code == 200
    assert response.json()["data"]["creator_role"] == "mentor"


async def test_same_teacher_as_instructor_and_mentor_can_choose_either_role(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    teacher = await create_teacher(client, admin_headers, "006")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    academic_class = await create_class(client, admin_headers, "BE1106", teacher_profile_id, teacher_profile_id)
    teacher_headers = await login(client, teacher["email"], "Teacher@123456")

    instructor_response = await create_material(
        client,
        teacher_headers,
        academic_class["id"],
        creator_role="instructor",
        title="Instructor Material",
    )
    mentor_response = await create_material(
        client,
        teacher_headers,
        academic_class["id"],
        creator_role="mentor",
        title="Mentor Material",
    )

    assert instructor_response.status_code == 200
    assert mentor_response.status_code == 200


async def test_teacher_cannot_update_or_delete_material_created_by_another_teacher(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    creator = await create_teacher(client, admin_headers, "007A")
    other = await create_teacher(client, admin_headers, "007B")
    creator_id = creator["teacher_profile"]["id"]
    other_id = other["teacher_profile"]["id"]
    academic_class = await create_class(client, admin_headers, "BE1107", creator_id, other_id)
    creator_headers = await login(client, creator["email"], "Teacher@123456")
    other_headers = await login(client, other["email"], "Teacher@123456")
    material_response = await create_material(client, creator_headers, academic_class["id"])
    material_id = material_response.json()["data"]["id"]

    update_response = await client.put(
        f"/api/materials/{material_id}",
        headers=other_headers,
        json={"title": "Other Teacher Update"},
    )
    delete_response = await client.delete(f"/api/materials/{material_id}", headers=other_headers)

    assert update_response.status_code == 403
    assert delete_response.status_code == 403


async def test_admin_can_update_and_delete_any_material(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "008")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    academic_class = await create_class(client, admin_headers, "BE1108", teacher_profile_id, teacher_profile_id)
    material_response = await create_material(
        client,
        admin_headers,
        academic_class["id"],
        creator_id=teacher_profile_id,
    )
    material_id = material_response.json()["data"]["id"]

    update_response = await client.put(
        f"/api/materials/{material_id}",
        headers=admin_headers,
        json={"title": "Updated by Admin", "is_active": False},
    )
    delete_response = await client.delete(f"/api/materials/{material_id}", headers=admin_headers)

    assert update_response.status_code == 200
    assert update_response.json()["data"]["title"] == "Updated by Admin"
    assert delete_response.status_code == 200


async def test_student_can_view_active_materials_for_own_active_class(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    teacher = await create_teacher(client, admin_headers, "009")
    student = await create_student(client, admin_headers, "009")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    academic_class = await create_class(client, admin_headers, "BE1109", teacher_profile_id, teacher_profile_id)
    await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
    await create_material(client, admin_headers, academic_class["id"], creator_id=teacher_profile_id)
    student_headers = await login(client, student["email"], "Student@123456")

    response = await client.get("/api/students/me/materials", headers=student_headers)

    assert response.status_code == 200
    assert [item["class_code"] for item in response.json()["data"]] == ["BE1109"]


async def test_student_cannot_view_materials_for_other_classes(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    teacher = await create_teacher(client, admin_headers, "010")
    first_student = await create_student(client, admin_headers, "010A")
    second_student = await create_student(client, admin_headers, "010B")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    first_class = await create_class(client, admin_headers, "BE1110", teacher_profile_id, teacher_profile_id)
    second_class = await create_class(client, admin_headers, "BE1111", teacher_profile_id, teacher_profile_id)
    await enroll(client, admin_headers, first_student["student_profile"]["id"], first_class["id"])
    await enroll(client, admin_headers, second_student["student_profile"]["id"], second_class["id"])
    await create_material(client, admin_headers, first_class["id"], creator_id=teacher_profile_id, title="First Class")
    await create_material(client, admin_headers, second_class["id"], creator_id=teacher_profile_id, title="Second Class")
    second_student_headers = await login(client, second_student["email"], "Student@123456")

    response = await client.get("/api/students/me/materials", headers=second_student_headers)

    assert response.status_code == 200
    assert [item["title"] for item in response.json()["data"]] == ["Second Class"]


async def test_soft_deleted_materials_do_not_appear_for_students(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    teacher = await create_teacher(client, admin_headers, "011")
    student = await create_student(client, admin_headers, "011")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    academic_class = await create_class(client, admin_headers, "BE1112", teacher_profile_id, teacher_profile_id)
    await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
    material_response = await create_material(client, admin_headers, academic_class["id"], creator_id=teacher_profile_id)
    await client.delete(f"/api/materials/{material_response.json()['data']['id']}", headers=admin_headers)
    student_headers = await login(client, student["email"], "Student@123456")

    response = await client.get("/api/students/me/materials", headers=student_headers)

    assert response.status_code == 200
    assert response.json()["data"] == []


async def test_invalid_url_is_rejected(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "012")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    academic_class = await create_class(client, admin_headers, "BE1113", teacher_profile_id, teacher_profile_id)

    response = await create_material(
        client,
        admin_headers,
        academic_class["id"],
        creator_id=teacher_profile_id,
        url="not-a-url",
    )

    assert response.status_code == 422


async def test_teacher_assigned_class_materials_endpoint(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    teacher = await create_teacher(client, admin_headers, "013")
    teacher_profile_id = teacher["teacher_profile"]["id"]
    academic_class = await create_class(client, admin_headers, "BE1114", teacher_profile_id, teacher_profile_id)
    await create_material(client, admin_headers, academic_class["id"], creator_id=teacher_profile_id)
    teacher_headers = await login(client, teacher["email"], "Teacher@123456")

    response = await client.get(
        f"/api/teachers/me/classes/{academic_class['id']}/materials",
        headers=teacher_headers,
    )

    assert response.status_code == 200
    assert [item["class_code"] for item in response.json()["data"]] == ["BE1114"]
