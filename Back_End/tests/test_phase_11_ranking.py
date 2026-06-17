from httpx import AsyncClient

from tests.test_phase_5_assignments import create_class, create_student, create_teacher, enroll, login
from tests.test_phase_7_attendance import create_manual_attendance


async def setup_ranking_class(client: AsyncClient, admin_headers: dict[str, str], suffix: str, student_count: int = 4) -> dict:
    teacher = await create_teacher(client, admin_headers, f"11T{suffix}")
    academic_class = await create_class(client, admin_headers, f"BE1{suffix[-3:]}", teacher["teacher_profile"]["id"])
    teacher_headers = await login(client, teacher["email"], "Teacher@123456")
    students = []
    student_headers = []
    enrollments = []
    for index in range(student_count):
        student = await create_student(client, admin_headers, f"11S{suffix}{index}")
        response = await client.post(
            "/api/enrollments",
            headers=admin_headers,
            json={"student_id": student["student_profile"]["id"], "class_id": academic_class["id"]},
        )
        assert response.status_code == 200
        students.append(student)
        enrollments.append(response.json()["data"])
        student_headers.append(await login(client, student["email"], "Student@123456"))
    return {
        "teacher": teacher,
        "class": academic_class,
        "teacher_headers": teacher_headers,
        "students": students,
        "student_headers": student_headers,
        "enrollments": enrollments,
    }


async def add_attendance_progress(
    client: AsyncClient,
    context: dict,
    student_index: int,
    status: str,
    session_date: str,
) -> None:
    await create_manual_attendance(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["students"][student_index]["student_profile"]["id"],
        status=status,
        session_date=session_date,
    )


async def seed_dense_ranking_scores(client: AsyncClient, context: dict) -> None:
    await add_attendance_progress(client, context, 0, "present", "2026-08-01")
    await add_attendance_progress(client, context, 1, "late", "2026-08-02")
    await add_attendance_progress(client, context, 2, "late", "2026-08-03")


async def test_student_can_view_top3_ranking_for_own_active_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_ranking_class(client, admin_headers, "001", student_count=4)
    await seed_dense_ranking_scores(client, context)

    response = await client.get("/api/students/me/ranking/top3", headers=context["student_headers"][3])

    assert response.status_code == 200
    assert len(response.json()["data"]) == 3
    assert [item["rank"] for item in response.json()["data"]] == [1, 2, 2]


async def test_student_cannot_view_full_class_ranking(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_ranking_class(client, admin_headers, "002", student_count=1)

    response = await client.get(f"/api/ranking/classes/{context['class']['id']}", headers=context["student_headers"][0])

    assert response.status_code == 403


async def test_teacher_can_view_full_ranking_for_assigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_ranking_class(client, admin_headers, "003", student_count=4)
    await seed_dense_ranking_scores(client, context)

    response = await client.get(f"/api/teachers/me/classes/{context['class']['id']}/ranking", headers=context["teacher_headers"])

    assert response.status_code == 200
    assert len(response.json()["data"]) == 4


async def test_teacher_cannot_view_ranking_for_unassigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_ranking_class(client, admin_headers, "004", student_count=1)
    second = await setup_ranking_class(client, admin_headers, "005", student_count=1)

    response = await client.get(f"/api/teachers/me/classes/{second['class']['id']}/ranking", headers=first["teacher_headers"])

    assert response.status_code == 403


async def test_admin_can_view_class_and_track_ranking(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_ranking_class(client, admin_headers, "006", student_count=2)
    await add_attendance_progress(client, context, 0, "present", "2026-08-04")

    class_response = await client.get(f"/api/ranking/classes/{context['class']['id']}", headers=admin_headers)
    track_response = await client.get(f"/api/ranking/tracks/{context['class']['track_id']}", headers=admin_headers)

    assert class_response.status_code == 200
    assert track_response.status_code == 200
    assert context["students"][0]["student_profile"]["id"] in [item["student_id"] for item in track_response.json()["data"]]


async def test_ranking_orders_by_final_progress_descending_and_uses_dense_rank(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_ranking_class(client, admin_headers, "007", student_count=4)
    await seed_dense_ranking_scores(client, context)

    response = await client.get(f"/api/ranking/classes/{context['class']['id']}", headers=admin_headers)
    data = response.json()["data"]

    assert response.status_code == 200
    assert [item["final_progress"] for item in data] == [20, 10, 10, 0]
    assert [item["rank"] for item in data] == [1, 2, 2, 3]


async def test_removed_enrollments_are_excluded_from_current_ranking(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_ranking_class(client, admin_headers, "008", student_count=2)
    await add_attendance_progress(client, context, 0, "present", "2026-08-05")
    delete_response = await client.delete(f"/api/enrollments/{context['enrollments'][0]['id']}", headers=admin_headers)

    response = await client.get(f"/api/ranking/classes/{context['class']['id']}", headers=admin_headers)

    assert delete_response.status_code == 200
    assert response.status_code == 200
    assert context["students"][0]["student_profile"]["id"] not in [item["student_id"] for item in response.json()["data"]]
    assert len(response.json()["data"]) == 1
