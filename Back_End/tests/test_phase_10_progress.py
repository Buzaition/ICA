from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from tests.test_phase_5_assignments import create_assignment, create_class, create_student, create_teacher, enroll, login, submit_assignment
from tests.test_phase_7_attendance import create_manual_attendance
from tests.test_phase_8_quizzes import create_manual_quiz
from tests.test_phase_9_bonus import give_bonus


async def setup_progress_context(client: AsyncClient, admin_headers: dict[str, str], suffix: str) -> dict:
    teacher = await create_teacher(client, admin_headers, f"10T{suffix}")
    student = await create_student(client, admin_headers, f"10S{suffix}")
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


async def add_assignment_grade(
    client: AsyncClient,
    context: dict,
    grade: float = 8,
    max_grade: int = 10,
) -> dict:
    assignment = await create_assignment(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        title=f"Progress Assignment {context['class']['code']}",
        deadline=(datetime.now(UTC) + timedelta(days=5)).isoformat(),
        max_grade=max_grade,
    )
    submission = await submit_assignment(client, context["student_headers"], assignment["id"])
    response = await client.post(
        f"/api/assignment-submissions/{submission.json()['data']['id']}/review",
        headers=context["teacher_headers"],
        json={"grade": grade},
    )
    assert response.status_code == 200
    return response.json()["data"]


async def add_full_progress_grades(client: AsyncClient, context: dict) -> None:
    await create_manual_attendance(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        status="present",
    )
    await create_manual_quiz(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        earned_grade=8,
        max_grade=10,
    )
    await add_assignment_grade(client, context, grade=8, max_grade=10)
    bonus = await give_bonus(
        client,
        context["teacher_headers"],
        context["student"]["student_profile"]["id"],
        context["class"]["id"],
    )
    assert bonus.status_code == 200


async def test_student_progress_calculates_attendance_quiz_assignment_and_bonus(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_progress_context(client, admin_headers, "001")
    await add_full_progress_grades(client, context)

    response = await client.get("/api/students/me/progress", headers=context["student_headers"])

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["attendance_progress"] == 20
    assert data["quiz_progress"] == 24
    assert data["assignment_progress"] == 40
    assert data["bonus_progress"] == 1
    assert data["final_progress"] == 85


async def test_correction_affects_original_category(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_progress_context(client, admin_headers, "002")
    attendance = await create_manual_attendance(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        status="late",
    )

    response_before = await client.get("/api/students/me/progress", headers=context["student_headers"])
    update = await client.put(
        f"/api/attendance/records/{attendance['records'][0]['id']}",
        headers=context["teacher_headers"],
        json={"status": "present"},
    )
    response_after = await client.get("/api/students/me/progress", headers=context["student_headers"])

    assert update.status_code == 200
    assert response_before.json()["data"]["attendance_progress"] == 10
    assert response_after.json()["data"]["attendance_progress"] == 20


async def test_bonus_increases_final_progress_but_never_above_100(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_progress_context(client, admin_headers, "003")
    await create_manual_attendance(client, context["teacher_headers"], context["class"]["id"], context["student"]["student_profile"]["id"])
    await create_manual_quiz(client, context["teacher_headers"], context["class"]["id"], context["student"]["student_profile"]["id"], earned_grade=10)
    await add_assignment_grade(client, context, grade=10, max_grade=10)
    for _ in range(5):
        response = await give_bonus(client, context["teacher_headers"], context["student"]["student_profile"]["id"], context["class"]["id"])
        assert response.status_code == 200

    progress = await client.get("/api/students/me/progress", headers=context["student_headers"])

    assert progress.json()["data"]["bonus_progress"] == 5
    assert progress.json()["data"]["final_progress"] == 100


async def test_empty_categories_count_as_zero(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_progress_context(client, admin_headers, "004")
    response = await client.get("/api/students/me/progress", headers=context["student_headers"])

    assert response.status_code == 200
    assert response.json()["data"]["final_progress"] == 0


async def test_student_cannot_view_other_student_progress(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_progress_context(client, admin_headers, "005")

    response = await client.get(f"/api/progress/students/{context['student']['student_profile']['id']}", headers=context["student_headers"])

    assert response.status_code == 403


async def test_teacher_can_view_only_assigned_class_progress(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_progress_context(client, admin_headers, "006")
    second = await setup_progress_context(client, admin_headers, "007")

    assigned = await client.get(f"/api/teachers/me/classes/{first['class']['id']}/progress", headers=first["teacher_headers"])
    unassigned = await client.get(f"/api/teachers/me/classes/{second['class']['id']}/progress", headers=first["teacher_headers"])

    assert assigned.status_code == 200
    assert assigned.json()["data"]["class_id"] == first["class"]["id"]
    assert unassigned.status_code == 403


async def test_class_progress_is_average_of_active_students(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_progress_context(client, admin_headers, "008")
    second_student = await create_student(client, admin_headers, "10S008B")
    await enroll(client, admin_headers, second_student["student_profile"]["id"], context["class"]["id"])
    await create_manual_attendance(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        status="present",
    )

    response = await client.get(f"/api/progress/classes/{context['class']['id']}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["data"]["student_count"] == 2
    assert response.json()["data"]["class_progress"] == 10


async def test_instructor_and_mentor_progress_formulas(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    instructor_context = await setup_progress_context(client, admin_headers, "009")
    await create_manual_attendance(
        client,
        instructor_context["teacher_headers"],
        instructor_context["class"]["id"],
        instructor_context["student"]["student_profile"]["id"],
        status="present",
    )
    instructor_progress = await client.get(
        f"/api/progress/teachers/{instructor_context['teacher']['teacher_profile']['id']}",
        headers=admin_headers,
    )

    mentor_teacher = await create_teacher(client, admin_headers, "10M010")
    instructor_teacher = await create_teacher(client, admin_headers, "10I010")
    student = await create_student(client, admin_headers, "10S010")
    academic_class = await create_class(
        client,
        admin_headers,
        "BE1010",
        instructor_teacher["teacher_profile"]["id"],
        mentor_teacher["teacher_profile"]["id"],
    )
    await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
    instructor_headers = await login(client, instructor_teacher["email"], "Teacher@123456")
    await create_manual_attendance(client, instructor_headers, academic_class["id"], student["student_profile"]["id"], status="present")
    mentor_progress = await client.get(f"/api/progress/teachers/{mentor_teacher['teacher_profile']['id']}", headers=admin_headers)

    assert instructor_progress.json()["data"]["instructor_progress"] == 20
    assert mentor_progress.json()["data"]["mentor_progress"] == 60


async def test_admin_can_view_any_student_and_class_progress(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_progress_context(client, admin_headers, "011")

    student_response = await client.get(f"/api/progress/students/{context['student']['student_profile']['id']}", headers=admin_headers)
    class_response = await client.get(f"/api/progress/classes/{context['class']['id']}", headers=admin_headers)

    assert student_response.status_code == 200
    assert class_response.status_code == 200


async def test_teacher_can_create_snapshots_for_assigned_class_and_student_cannot(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_progress_context(client, admin_headers, "012")

    teacher_response = await client.post(
        f"/api/teachers/me/classes/{context['class']['id']}/progress-snapshots",
        headers=context["teacher_headers"],
    )
    student_response = await client.post(
        f"/api/progress/classes/{context['class']['id']}/snapshots",
        headers=context["student_headers"],
    )

    assert teacher_response.status_code == 200
    assert len(teacher_response.json()["data"]) == 1
    assert student_response.status_code == 403


async def test_snapshots_are_immutable_historical_rows(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_progress_context(client, admin_headers, "013")
    await client.post(f"/api/progress/classes/{context['class']['id']}/snapshots", headers=admin_headers)
    await create_manual_attendance(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        status="present",
    )
    await client.post(f"/api/progress/classes/{context['class']['id']}/snapshots", headers=admin_headers)

    snapshots = await client.get(f"/api/progress/classes/{context['class']['id']}/snapshots", headers=admin_headers)
    finals = sorted(item["final_progress"] for item in snapshots.json()["data"])

    assert snapshots.status_code == 200
    assert len(snapshots.json()["data"]) == 2
    assert finals == [0, 20]
