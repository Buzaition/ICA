from httpx import AsyncClient

from tests.test_phase_5_assignments import create_class, create_student, create_teacher, enroll, login


async def setup_notification_context(client: AsyncClient, admin_headers: dict[str, str], suffix: str) -> dict:
    teacher = await create_teacher(client, admin_headers, f"13T{suffix}")
    student = await create_student(client, admin_headers, f"13S{suffix}")
    academic_class = await create_class(
        client,
        admin_headers,
        f"BE13{suffix[-2:]}",
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


async def run_progress_check(client: AsyncClient, admin_headers: dict[str, str]) -> dict:
    response = await client.post("/api/admin/notifications/check-progress", headers=admin_headers)
    assert response.status_code == 200
    return response.json()["data"]


async def test_admin_can_run_progress_check(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    await setup_notification_context(client, admin_headers, "001")

    data = await run_progress_check(client, admin_headers)

    assert data["created_count"] == 3
    assert len(data["notifications"]) == 3


async def test_student_below_50_creates_notification(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_notification_context(client, admin_headers, "002")

    data = await run_progress_check(client, admin_headers)

    student_notifications = [item for item in data["notifications"] if item["type"] == "student_low_progress"]
    assert len(student_notifications) == 1
    assert student_notifications[0]["target_student_id"] == context["student"]["student_profile"]["id"]
    assert student_notifications[0]["class_id"] == context["class"]["id"]


async def test_instructor_below_50_creates_notification(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_notification_context(client, admin_headers, "003")

    data = await run_progress_check(client, admin_headers)

    instructor_notifications = [item for item in data["notifications"] if item["type"] == "instructor_low_progress"]
    assert len(instructor_notifications) == 1
    assert instructor_notifications[0]["target_teacher_id"] == context["teacher"]["teacher_profile"]["id"]
    assert instructor_notifications[0]["class_id"] == context["class"]["id"]


async def test_mentor_below_70_creates_notification(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_notification_context(client, admin_headers, "004")

    data = await run_progress_check(client, admin_headers)

    mentor_notifications = [item for item in data["notifications"] if item["type"] == "mentor_low_progress"]
    assert len(mentor_notifications) == 1
    assert mentor_notifications[0]["target_teacher_id"] == context["teacher"]["teacher_profile"]["id"]
    assert mentor_notifications[0]["class_id"] == context["class"]["id"]


async def test_duplicate_unread_notification_is_not_created(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    await setup_notification_context(client, admin_headers, "005")

    first = await run_progress_check(client, admin_headers)
    second = await run_progress_check(client, admin_headers)
    list_response = await client.get("/api/admin/notifications", headers=admin_headers)

    assert first["created_count"] == 3
    assert second["created_count"] == 0
    assert len(list_response.json()["data"]) == 3


async def test_admin_can_list_notifications(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    await setup_notification_context(client, admin_headers, "006")
    await run_progress_check(client, admin_headers)

    response = await client.get("/api/admin/notifications", headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()["data"]) == 3


async def test_admin_can_get_unread_count(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    await setup_notification_context(client, admin_headers, "007")
    await run_progress_check(client, admin_headers)

    response = await client.get("/api/admin/notifications/unread-count", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["data"]["unread_count"] == 3


async def test_admin_can_mark_one_notification_read(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    await setup_notification_context(client, admin_headers, "008")
    data = await run_progress_check(client, admin_headers)
    notification_id = data["notifications"][0]["id"]

    response = await client.post(f"/api/admin/notifications/{notification_id}/mark-read", headers=admin_headers)
    count_response = await client.get("/api/admin/notifications/unread-count", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["data"]["is_read"] is True
    assert response.json()["data"]["read_at"] is not None
    assert count_response.json()["data"]["unread_count"] == 2


async def test_admin_can_mark_all_notifications_read(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    await setup_notification_context(client, admin_headers, "009")
    await run_progress_check(client, admin_headers)

    response = await client.post("/api/admin/notifications/mark-all-read", headers=admin_headers)
    count_response = await client.get("/api/admin/notifications/unread-count", headers=admin_headers)

    assert response.status_code == 200
    assert all(item["is_read"] for item in response.json()["data"])
    assert count_response.json()["data"]["unread_count"] == 0


async def test_non_admin_cannot_access_notification_endpoints(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_notification_context(client, admin_headers, "010")

    responses = [
        await client.get("/api/admin/notifications", headers=context["teacher_headers"]),
        await client.get("/api/admin/notifications/unread-count", headers=context["teacher_headers"]),
        await client.post("/api/admin/notifications/check-progress", headers=context["teacher_headers"]),
        await client.post("/api/admin/notifications/mark-all-read", headers=context["student_headers"]),
    ]

    assert all(response.status_code == 403 for response in responses)
