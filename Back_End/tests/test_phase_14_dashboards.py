from httpx import AsyncClient

from tests.test_phase_10_progress import add_assignment_grade
from tests.test_phase_13_notifications import run_progress_check
from tests.test_phase_4_materials import create_material
from tests.test_phase_5_assignments import create_class, create_student, create_teacher, enroll, login


async def setup_dashboard_context(client: AsyncClient, admin_headers: dict[str, str], suffix: str) -> dict:
    teacher = await create_teacher(client, admin_headers, f"14T{suffix}")
    student = await create_student(client, admin_headers, f"14S{suffix}")
    academic_class = await create_class(
        client,
        admin_headers,
        f"BE14{suffix[-2:]}",
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


async def test_admin_can_access_admin_dashboard(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    await setup_dashboard_context(client, admin_headers, "001")

    response = await client.get("/api/admin/dashboard", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_students"] == 1
    assert data["active_students"] == 1
    assert data["total_teachers"] == 1
    assert data["total_classes"] >= 1
    assert "tracks_summary" in data
    assert "classes_summary" in data


async def test_non_admin_cannot_access_admin_dashboard(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_dashboard_context(client, admin_headers, "002")

    response = await client.get("/api/admin/dashboard", headers=context["teacher_headers"])

    assert response.status_code == 403


async def test_teacher_can_access_own_dashboard(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_dashboard_context(client, admin_headers, "003")

    response = await client.get("/api/teachers/me/dashboard", headers=context["teacher_headers"])

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["teacher_id"] == context["teacher"]["teacher_profile"]["id"]
    assert data["teacher_name"] == context["teacher"]["teacher_profile"]["full_name"]
    assert data["assigned_classes_count"] == 1
    assert data["low_progress_students_count"] == 1


async def test_student_can_access_own_dashboard(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_dashboard_context(client, admin_headers, "004")
    await create_material(client, context["teacher_headers"], context["class"]["id"])

    response = await client.get("/api/students/me/dashboard", headers=context["student_headers"])

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["student_id"] == context["student"]["student_profile"]["id"]
    assert data["active_class"]["class_id"] == context["class"]["id"]
    assert data["progress"]["student_id"] == context["student"]["student_profile"]["id"]
    assert data["materials_count"] == 1
    assert "unread_notifications_count" not in data


async def test_teacher_dashboard_only_counts_assigned_classes(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_dashboard_context(client, admin_headers, "005")
    second_teacher = await create_teacher(client, admin_headers, "14T005B")
    second_student = await create_student(client, admin_headers, "14S005B")
    second_class = await create_class(
        client,
        admin_headers,
        "BE1455",
        second_teacher["teacher_profile"]["id"],
    )
    await enroll(client, admin_headers, second_student["student_profile"]["id"], second_class["id"])

    response = await client.get("/api/teachers/me/dashboard", headers=first["teacher_headers"])

    assert response.status_code == 200
    data = response.json()["data"]
    class_ids = {item["class_id"] for item in data["assigned_classes"]}
    assert first["class"]["id"] in class_ids
    assert second_class["id"] not in class_ids
    assert data["assigned_classes_count"] == 1


async def test_student_dashboard_only_returns_own_class_data(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_dashboard_context(client, admin_headers, "006")
    second = await setup_dashboard_context(client, admin_headers, "007")
    await create_material(client, first["teacher_headers"], first["class"]["id"])
    await create_material(client, second["teacher_headers"], second["class"]["id"])

    response = await client.get("/api/students/me/dashboard", headers=first["student_headers"])

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["active_class"]["class_id"] == first["class"]["id"]
    assert data["active_class"]["class_id"] != second["class"]["id"]
    assert data["materials_count"] == 1


async def test_admin_dashboard_includes_notification_counts(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    await setup_dashboard_context(client, admin_headers, "008")
    await run_progress_check(client, admin_headers)

    response = await client.get("/api/admin/dashboard", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["data"]["unread_notifications_count"] == 3


async def test_dashboards_do_not_mutate_data(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_dashboard_context(client, admin_headers, "009")
    await run_progress_check(client, admin_headers)
    before = await client.get("/api/admin/notifications/unread-count", headers=admin_headers)

    await client.get("/api/admin/dashboard", headers=admin_headers)
    await client.get("/api/teachers/me/dashboard", headers=context["teacher_headers"])
    await client.get("/api/students/me/dashboard", headers=context["student_headers"])
    after = await client.get("/api/admin/notifications/unread-count", headers=admin_headers)

    assert before.json()["data"]["unread_count"] == after.json()["data"]["unread_count"]


async def test_student_dashboard_reflects_assignment_submission_progress(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_dashboard_context(client, admin_headers, "010")
    await add_assignment_grade(client, context, grade=10, max_grade=10)

    response = await client.get("/api/students/me/dashboard", headers=context["student_headers"])

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["assignments_count"] == 1
    assert data["submissions_count"] == 1
    assert data["progress"]["assignment_progress"] == 50
