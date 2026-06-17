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
            "email": f"phase3.teacher{suffix}@ica.eg",
            "password": "Teacher@123456",
            "role": "teacher",
            "teacher_profile": {
                "teacher_code": f"P3T{suffix}",
                "full_name": f"Phase 3 Teacher {suffix}",
                "phone_number": "01100000000",
                "teacher_type": "instructor_and_mentor",
                "is_team_leader": False,
            },
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def create_student(
    client: AsyncClient,
    admin_headers: dict[str, str],
    suffix: str,
    status: str = "active",
) -> dict:
    response = await client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "email": f"phase3.student{suffix}@ica.eg",
            "password": "Student@123456",
            "role": "student",
            "student_profile": {
                "student_code": f"P3S{suffix}",
                "full_name": f"Phase 3 Student {suffix}",
                "phone_number": "01000000000",
                "status": status,
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
    teacher_profile_id: str,
    max_students: int = 25,
    status: str = "active",
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
            "instructor_id": teacher_profile_id,
            "mentor_id": teacher_profile_id,
            "schedule_text": "Sunday and Tuesday 18:00",
            "max_students": max_students,
            "class_type": "online",
            "start_date": "2027-01-01",
            "end_date": "2027-03-01",
            "status": status,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def enroll(client: AsyncClient, admin_headers: dict[str, str], student_id: str, class_id: str):
    return await client.post(
        "/api/enrollments",
        headers=admin_headers,
        json={"student_id": student_id, "class_id": class_id},
    )


async def test_admin_can_enroll_student_in_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "001")
    student = await create_student(client, admin_headers, "001")
    academic_class = await create_class(client, admin_headers, "BE1001", teacher["teacher_profile"]["id"])

    response = await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["student_code"] == "P3S001"
    assert data["class_code"] == "BE1001"
    assert data["track_name"] == "Backend"
    assert data["level_number"] == 1
    assert data["status"] == "active"


async def test_non_admin_cannot_enroll_student(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "002")
    student = await create_student(client, admin_headers, "002")
    academic_class = await create_class(client, admin_headers, "BE1002", teacher["teacher_profile"]["id"])
    teacher_headers = await login(client, teacher["email"], "Teacher@123456")

    response = await enroll(client, teacher_headers, student["student_profile"]["id"], academic_class["id"])

    assert response.status_code == 403


async def test_cannot_enroll_same_student_in_two_active_classes(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    teacher = await create_teacher(client, admin_headers, "003")
    student = await create_student(client, admin_headers, "003")
    first_class = await create_class(client, admin_headers, "BE1003", teacher["teacher_profile"]["id"])
    second_class = await create_class(client, admin_headers, "BE1004", teacher["teacher_profile"]["id"])

    first_response = await enroll(client, admin_headers, student["student_profile"]["id"], first_class["id"])
    second_response = await enroll(client, admin_headers, student["student_profile"]["id"], second_class["id"])

    assert first_response.status_code == 200
    assert second_response.status_code == 400


async def test_cannot_exceed_class_capacity(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "004")
    first_student = await create_student(client, admin_headers, "004A")
    second_student = await create_student(client, admin_headers, "004B")
    academic_class = await create_class(
        client,
        admin_headers,
        "BE1005",
        teacher["teacher_profile"]["id"],
        max_students=1,
    )

    first_response = await enroll(client, admin_headers, first_student["student_profile"]["id"], academic_class["id"])
    second_response = await enroll(client, admin_headers, second_student["student_profile"]["id"], academic_class["id"])

    assert first_response.status_code == 200
    assert second_response.status_code == 400


async def test_cannot_enroll_into_cancelled_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "005")
    student = await create_student(client, admin_headers, "005")
    academic_class = await create_class(
        client,
        admin_headers,
        "BE1006",
        teacher["teacher_profile"]["id"],
        status="cancelled",
    )

    response = await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])

    assert response.status_code == 400


async def test_cannot_enroll_inactive_suspended_dropped_or_graduated_student(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    teacher = await create_teacher(client, admin_headers, "006")
    academic_class = await create_class(client, admin_headers, "BE1007", teacher["teacher_profile"]["id"])
    for index, status in enumerate(("inactive", "suspended", "dropped", "graduated"), start=1):
        student = await create_student(client, admin_headers, f"006{index}", status=status)
        response = await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
        assert response.status_code == 400


async def test_admin_can_remove_enrollment(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "007")
    student = await create_student(client, admin_headers, "007")
    academic_class = await create_class(client, admin_headers, "BE1008", teacher["teacher_profile"]["id"])
    create_response = await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
    enrollment_id = create_response.json()["data"]["id"]

    delete_response = await client.delete(f"/api/enrollments/{enrollment_id}", headers=admin_headers)
    get_response = await client.get(f"/api/enrollments/{enrollment_id}", headers=admin_headers)

    assert delete_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "removed"


async def test_removed_enrollment_no_longer_counts_as_active(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    teacher = await create_teacher(client, admin_headers, "008")
    first_student = await create_student(client, admin_headers, "008A")
    second_student = await create_student(client, admin_headers, "008B")
    academic_class = await create_class(
        client,
        admin_headers,
        "BE1009",
        teacher["teacher_profile"]["id"],
        max_students=1,
    )
    first_response = await enroll(client, admin_headers, first_student["student_profile"]["id"], academic_class["id"])
    await client.delete(f"/api/enrollments/{first_response.json()['data']['id']}", headers=admin_headers)

    second_response = await enroll(client, admin_headers, second_student["student_profile"]["id"], academic_class["id"])

    assert second_response.status_code == 200


async def test_teacher_can_view_students_only_in_assigned_class(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    teacher = await create_teacher(client, admin_headers, "009")
    student = await create_student(client, admin_headers, "009")
    academic_class = await create_class(client, admin_headers, "BE1010", teacher["teacher_profile"]["id"])
    await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
    teacher_headers = await login(client, teacher["email"], "Teacher@123456")

    response = await client.get(
        f"/api/teachers/me/classes/{academic_class['id']}/students",
        headers=teacher_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["student_email"] == student["email"]
    assert data[0]["class_code"] == "BE1010"


async def test_teacher_cannot_view_students_in_unassigned_class(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    assigned_teacher = await create_teacher(client, admin_headers, "010A")
    other_teacher = await create_teacher(client, admin_headers, "010B")
    student = await create_student(client, admin_headers, "010")
    academic_class = await create_class(client, admin_headers, "BE1011", assigned_teacher["teacher_profile"]["id"])
    await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
    other_headers = await login(client, other_teacher["email"], "Teacher@123456")

    response = await client.get(
        f"/api/teachers/me/classes/{academic_class['id']}/students",
        headers=other_headers,
    )

    assert response.status_code == 403


async def test_student_can_view_own_active_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "011")
    student = await create_student(client, admin_headers, "011")
    academic_class = await create_class(client, admin_headers, "BE1012", teacher["teacher_profile"]["id"])
    await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
    student_headers = await login(client, student["email"], "Student@123456")

    response = await client.get("/api/students/me/class", headers=student_headers)

    assert response.status_code == 200
    assert response.json()["data"]["class_code"] == "BE1012"
    assert response.json()["data"]["student_id"] == student["student_profile"]["id"]


async def test_student_cannot_view_other_students_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "012")
    first_student = await create_student(client, admin_headers, "012A")
    second_student = await create_student(client, admin_headers, "012B")
    first_class = await create_class(client, admin_headers, "BE1013", teacher["teacher_profile"]["id"])
    second_class = await create_class(client, admin_headers, "BE1014", teacher["teacher_profile"]["id"])
    first_enrollment = await enroll(client, admin_headers, first_student["student_profile"]["id"], first_class["id"])
    await enroll(client, admin_headers, second_student["student_profile"]["id"], second_class["id"])
    second_student_headers = await login(client, second_student["email"], "Student@123456")

    admin_endpoint_response = await client.get(
        f"/api/enrollments/{first_enrollment.json()['data']['id']}",
        headers=second_student_headers,
    )
    own_class_response = await client.get("/api/students/me/class", headers=second_student_headers)

    assert admin_endpoint_response.status_code == 403
    assert own_class_response.status_code == 200
    assert own_class_response.json()["data"]["class_code"] == "BE1014"
