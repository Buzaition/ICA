from httpx import AsyncClient

from tests.test_phase_5_assignments import create_class, create_student, create_teacher, enroll, login


async def setup_final_project_context(client: AsyncClient, admin_headers: dict[str, str], suffix: str) -> dict:
    teacher = await create_teacher(client, admin_headers, f"12T{suffix}")
    student = await create_student(client, admin_headers, f"12S{suffix}")
    academic_class = await create_class(
        client,
        admin_headers,
        f"BE1{suffix[-3:]}",
        teacher["teacher_profile"]["id"],
    )
    await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
    teacher_headers = await login(client, teacher["email"], "Teacher@123456")
    student_headers = await login(client, student["email"], "Student@123456")
    return {
        "teacher": teacher,
        "student": student,
        "class": academic_class,
        "teacher_headers": teacher_headers,
        "student_headers": student_headers,
    }


async def submit_final_project(client: AsyncClient, headers: dict[str, str], link: str = "https://github.com/student/final-project"):
    return await client.post("/api/students/me/final-project", headers=headers, json={"project_link": link})


async def test_student_can_submit_final_project_for_active_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_final_project_context(client, admin_headers, "201")

    response = await submit_final_project(client, context["student_headers"])

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["student_id"] == context["student"]["student_profile"]["id"]
    assert data["class_id"] == context["class"]["id"]
    assert data["level_id"] == context["class"]["level_id"]
    assert data["status"] == "pending"


async def test_student_cannot_submit_without_active_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    student = await create_student(client, admin_headers, "12NOACTIVE")
    headers = await login(client, student["email"], "Student@123456")

    response = await submit_final_project(client, headers)

    assert response.status_code == 404


async def test_student_can_update_pending_project(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_final_project_context(client, admin_headers, "203")
    submitted = await submit_final_project(client, context["student_headers"])

    response = await client.put(
        "/api/students/me/final-project",
        headers=context["student_headers"],
        json={"project_link": "https://github.com/student/final-project-v2"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["final_project_id"] == submitted.json()["data"]["final_project_id"]
    assert response.json()["data"]["project_link"] == "https://github.com/student/final-project-v2"


async def test_student_cannot_update_approved_or_rejected_project(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_final_project_context(client, admin_headers, "204")
    submitted = await submit_final_project(client, context["student_headers"])
    review = await client.post(
        f"/api/final-projects/{submitted.json()['data']['final_project_id']}/review",
        headers=admin_headers,
        json={"status": "approved", "grade": 90, "feedback": "Good project"},
    )

    response = await client.put(
        "/api/students/me/final-project",
        headers=context["student_headers"],
        json={"project_link": "https://github.com/student/changed"},
    )

    assert review.status_code == 200
    assert response.status_code == 400


async def test_duplicate_final_project_for_same_class_level_updates_pending_one(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_final_project_context(client, admin_headers, "205")
    first = await submit_final_project(client, context["student_headers"], "https://github.com/student/one")
    second = await submit_final_project(client, context["student_headers"], "https://github.com/student/two")

    assert second.status_code == 200
    assert second.json()["data"]["final_project_id"] == first.json()["data"]["final_project_id"]
    assert second.json()["data"]["project_link"] == "https://github.com/student/two"


async def test_teacher_can_view_final_projects_for_assigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_final_project_context(client, admin_headers, "206")
    submitted = await submit_final_project(client, context["student_headers"])

    response = await client.get(
        f"/api/teachers/me/classes/{context['class']['id']}/final-projects",
        headers=context["teacher_headers"],
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["final_project_id"] == submitted.json()["data"]["final_project_id"]


async def test_teacher_cannot_view_final_projects_for_unassigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_final_project_context(client, admin_headers, "207")
    second = await setup_final_project_context(client, admin_headers, "208")

    response = await client.get(
        f"/api/teachers/me/classes/{second['class']['id']}/final-projects",
        headers=first["teacher_headers"],
    )

    assert response.status_code == 403


async def test_admin_can_list_all_final_projects(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_final_project_context(client, admin_headers, "209")
    second = await setup_final_project_context(client, admin_headers, "210")
    first_project = await submit_final_project(client, first["student_headers"])
    second_project = await submit_final_project(client, second["student_headers"])

    response = await client.get("/api/final-projects", headers=admin_headers)

    assert response.status_code == 200
    assert {item["final_project_id"] for item in response.json()["data"]} == {
        first_project.json()["data"]["final_project_id"],
        second_project.json()["data"]["final_project_id"],
    }


async def test_admin_can_approve_final_project(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_final_project_context(client, admin_headers, "211")
    submitted = await submit_final_project(client, context["student_headers"])

    response = await client.post(
        f"/api/final-projects/{submitted.json()['data']['final_project_id']}/review",
        headers=admin_headers,
        json={"status": "approved", "grade": 90, "feedback": "Good project"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "approved"
    assert data["grade"] == 90
    assert data["reviewed_at"] is not None
    assert data["reviewed_by_admin"] == "Default Admin"


async def test_admin_can_reject_final_project(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_final_project_context(client, admin_headers, "212")
    submitted = await submit_final_project(client, context["student_headers"])

    response = await client.post(
        f"/api/final-projects/{submitted.json()['data']['final_project_id']}/review",
        headers=admin_headers,
        json={"status": "rejected", "feedback": "Needs work"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "rejected"
    assert response.json()["data"]["feedback"] == "Needs work"


async def test_non_admin_cannot_review_final_project(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_final_project_context(client, admin_headers, "213")
    submitted = await submit_final_project(client, context["student_headers"])

    response = await client.post(
        f"/api/final-projects/{submitted.json()['data']['final_project_id']}/review",
        headers=context["teacher_headers"],
        json={"status": "approved"},
    )

    assert response.status_code == 403


async def test_student_can_view_own_final_project(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_final_project_context(client, admin_headers, "214")
    submitted = await submit_final_project(client, context["student_headers"])

    response = await client.get("/api/students/me/final-project", headers=context["student_headers"])

    assert response.status_code == 200
    assert response.json()["data"]["final_project_id"] == submitted.json()["data"]["final_project_id"]


async def test_student_cannot_view_another_student_project(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_final_project_context(client, admin_headers, "215")
    second = await setup_final_project_context(client, admin_headers, "216")
    submitted = await submit_final_project(client, first["student_headers"])

    response = await client.get(
        f"/api/final-projects/{submitted.json()['data']['final_project_id']}",
        headers=second["student_headers"],
    )

    assert response.status_code == 403
