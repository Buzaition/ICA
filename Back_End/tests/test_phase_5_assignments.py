from datetime import UTC, datetime, timedelta

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
            "email": f"phase5.teacher{suffix}@ica.eg",
            "password": "Teacher@123456",
            "role": "teacher",
            "teacher_profile": {
                "teacher_code": f"P5T{suffix}",
                "full_name": f"Phase 5 Teacher {suffix}",
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
            "email": f"phase5.student{suffix}@ica.eg",
            "password": "Student@123456",
            "role": "student",
            "student_profile": {
                "student_code": f"P5S{suffix}",
                "full_name": f"Phase 5 Student {suffix}",
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
    return {"branch": branches[0], "cycle": cycles[0], "track": backend, "level": backend["levels"][0]}


async def create_class(
    client: AsyncClient,
    admin_headers: dict[str, str],
    code: str,
    instructor_id: str,
    mentor_id: str | None = None,
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
            "mentor_id": mentor_id or instructor_id,
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


async def enroll(client: AsyncClient, admin_headers: dict[str, str], student_id: str, class_id: str) -> None:
    response = await client.post(
        "/api/enrollments",
        headers=admin_headers,
        json={"student_id": student_id, "class_id": class_id},
    )
    assert response.status_code == 200


def future_deadline() -> str:
    return (datetime.now(UTC) + timedelta(days=5)).isoformat()


def past_deadline() -> str:
    return (datetime.now(UTC) - timedelta(days=1)).isoformat()


async def create_assignment(
    client: AsyncClient,
    headers: dict[str, str],
    class_id: str,
    title: str = "HTML Task 1",
    deadline: str | None = None,
    created_by_teacher_id: str | None = None,
    max_grade: int = 10,
) -> dict:
    payload = {
        "class_id": class_id,
        "title": title,
        "description": "Build a simple page",
        "requirement_url": "https://example.com/requirements",
        "deadline": deadline or future_deadline(),
        "max_grade": max_grade,
    }
    if created_by_teacher_id:
        payload["created_by_teacher_id"] = created_by_teacher_id
    response = await client.post("/api/assignments", headers=headers, json=payload)
    assert response.status_code == 200
    return response.json()["data"]


async def submit_assignment(client: AsyncClient, headers: dict[str, str], assignment_id: str, url: str = "https://github.com/student/repo"):
    return await client.post(
        f"/api/assignments/{assignment_id}/submit",
        headers=headers,
        json={"submission_url": url},
    )


async def setup_assignment_context(client: AsyncClient, admin_headers: dict[str, str], suffix: str, deadline: str | None = None) -> dict:
    teacher = await create_teacher(client, admin_headers, suffix)
    student = await create_student(client, admin_headers, suffix)
    academic_class = await create_class(client, admin_headers, f"BE12{suffix[-2:]}", teacher["teacher_profile"]["id"])
    await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
    teacher_headers = await login(client, teacher["email"], "Teacher@123456")
    student_headers = await login(client, student["email"], "Student@123456")
    assignment = await create_assignment(client, teacher_headers, academic_class["id"], deadline=deadline)
    return {
        "teacher": teacher,
        "student": student,
        "class": academic_class,
        "assignment": assignment,
        "teacher_headers": teacher_headers,
        "student_headers": student_headers,
    }


async def test_teacher_can_create_assignment_for_assigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "001")
    academic_class = await create_class(client, admin_headers, "BE1201", teacher["teacher_profile"]["id"])
    teacher_headers = await login(client, teacher["email"], "Teacher@123456")

    assignment = await create_assignment(client, teacher_headers, academic_class["id"])

    assert assignment["class_code"] == "BE1201"
    assert assignment["created_by_teacher_id"] == teacher["teacher_profile"]["id"]


async def test_teacher_cannot_create_assignment_for_unassigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    assigned_teacher = await create_teacher(client, admin_headers, "002A")
    other_teacher = await create_teacher(client, admin_headers, "002B")
    academic_class = await create_class(client, admin_headers, "BE1202", assigned_teacher["teacher_profile"]["id"])
    other_headers = await login(client, other_teacher["email"], "Teacher@123456")
    response = await client.post(
        "/api/assignments",
        headers=other_headers,
        json={
            "class_id": academic_class["id"],
            "title": "Blocked",
            "requirement_url": "https://example.com/requirements",
            "deadline": future_deadline(),
            "max_grade": 10,
        },
    )

    assert response.status_code == 403


async def test_admin_can_create_assignment_for_any_class_with_teacher_id(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    teacher = await create_teacher(client, admin_headers, "003")
    academic_class = await create_class(client, admin_headers, "BE1203", teacher["teacher_profile"]["id"])

    assignment = await create_assignment(
        client,
        admin_headers,
        academic_class["id"],
        created_by_teacher_id=teacher["teacher_profile"]["id"],
    )

    assert assignment["created_by_teacher_id"] == teacher["teacher_profile"]["id"]


async def test_student_can_view_assignments_for_own_active_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "004")

    response = await client.get("/api/students/me/assignments", headers=context["student_headers"])

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [context["assignment"]["id"]]


async def test_student_cannot_view_assignments_for_other_classes(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_assignment_context(client, admin_headers, "005")
    second = await setup_assignment_context(client, admin_headers, "006")

    response = await client.get("/api/students/me/assignments", headers=second["student_headers"])

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [second["assignment"]["id"]]
    assert first["assignment"]["id"] not in [item["id"] for item in response.json()["data"]]


async def test_student_can_submit_assignment_in_active_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "007")

    response = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "submitted"


async def test_student_cannot_submit_assignment_outside_active_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_assignment_context(client, admin_headers, "008")
    second = await setup_assignment_context(client, admin_headers, "009")

    response = await submit_assignment(client, second["student_headers"], first["assignment"]["id"])

    assert response.status_code == 403


async def test_resubmission_before_deadline_marks_old_submission_replaced(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "010")
    first = await submit_assignment(client, context["student_headers"], context["assignment"]["id"], "https://github.com/student/first")
    second = await submit_assignment(client, context["student_headers"], context["assignment"]["id"], "https://github.com/student/second")

    submissions = await client.get("/api/students/me/submissions", headers=context["student_headers"])

    assert first.status_code == 200
    assert second.status_code == 200
    statuses = {item["submission_url"]: item["status"] for item in submissions.json()["data"]}
    assert statuses["https://github.com/student/first"] == "replaced"
    assert statuses["https://github.com/student/second"] == "submitted"


async def test_late_submission_gets_late_status(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "011", deadline=past_deadline())

    response = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "late"


async def test_pending_assignments_include_submitted_and_late_unreviewed(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    submitted = await setup_assignment_context(client, admin_headers, "012")
    late = await setup_assignment_context(client, admin_headers, "013", deadline=past_deadline())
    await submit_assignment(client, submitted["student_headers"], submitted["assignment"]["id"])
    await submit_assignment(client, late["student_headers"], late["assignment"]["id"])

    response = await client.get("/api/teachers/me/assignments/pending", headers=submitted["teacher_headers"])
    late_response = await client.get("/api/teachers/me/assignments/pending", headers=late["teacher_headers"])

    assert response.status_code == 200
    assert response.json()["data"][0]["status"] == "submitted"
    assert late_response.json()["data"][0]["status"] == "late"
    assert response.json()["data"][0]["current_student_progress"] is None


async def test_teacher_can_review_submission_in_assigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "014")
    submission = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])

    response = await client.post(
        f"/api/assignment-submissions/{submission.json()['data']['id']}/review",
        headers=context["teacher_headers"],
        json={"grade": 8, "feedback": "Good work"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "reviewed"
    assert response.json()["data"]["grade"] == 8


async def test_teacher_cannot_review_submission_in_unassigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "015")
    other_teacher = await create_teacher(client, admin_headers, "015B")
    other_headers = await login(client, other_teacher["email"], "Teacher@123456")
    submission = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])

    response = await client.post(
        f"/api/assignment-submissions/{submission.json()['data']['id']}/review",
        headers=other_headers,
        json={"grade": 8},
    )

    assert response.status_code == 403


async def test_grade_above_max_grade_is_rejected(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "016")
    submission = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])

    response = await client.post(
        f"/api/assignment-submissions/{submission.json()['data']['id']}/review",
        headers=context["teacher_headers"],
        json={"grade": 11},
    )

    assert response.status_code == 400


async def test_reviewed_submission_disappears_from_pending(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "017")
    submission = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])
    pending_before = await client.get("/api/teachers/me/assignments/pending", headers=context["teacher_headers"])
    await client.post(
        f"/api/assignment-submissions/{submission.json()['data']['id']}/review",
        headers=context["teacher_headers"],
        json={"grade": 9},
    )
    pending_after = await client.get("/api/teachers/me/assignments/pending", headers=context["teacher_headers"])

    assert len(pending_before.json()["data"]) == 1
    assert pending_after.json()["data"] == []


async def test_reviewed_assignments_page_returns_reviewed_submissions(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "018")
    submission = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])
    await client.post(
        f"/api/assignment-submissions/{submission.json()['data']['id']}/review",
        headers=context["teacher_headers"],
        json={"grade": 7, "feedback": "Solid"},
    )

    response = await client.get("/api/teachers/me/assignments/reviewed", headers=context["teacher_headers"])

    assert response.status_code == 200
    assert response.json()["data"][0]["grade"] == 7
    assert response.json()["data"][0]["reviewed_by_teacher"] == context["teacher"]["teacher_profile"]["full_name"]


async def test_late_assignments_page_returns_late_unreviewed_submissions(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "019", deadline=past_deadline())
    await submit_assignment(client, context["student_headers"], context["assignment"]["id"])

    response = await client.get("/api/teachers/me/assignments/late", headers=context["teacher_headers"])

    assert response.status_code == 200
    assert response.json()["data"][0]["status"] == "late"


async def test_teacher_can_reject_late_submission(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "020", deadline=past_deadline())
    submission = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])

    response = await client.post(
        f"/api/assignment-submissions/{submission.json()['data']['id']}/reject",
        headers=context["teacher_headers"],
        json={"feedback": "Submitted too late"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "rejected"
    assert response.json()["data"]["grade"] is None


async def test_rejected_late_submission_has_no_grade(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "021", deadline=past_deadline())
    submission = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])

    rejected = await client.post(
        f"/api/assignment-submissions/{submission.json()['data']['id']}/reject",
        headers=context["teacher_headers"],
        json={"feedback": "Too late"},
    )
    get_response = await client.get(f"/api/assignment-submissions/{submission.json()['data']['id']}", headers=admin_headers)

    assert rejected.status_code == 200
    assert get_response.json()["data"]["status"] == "rejected"
    assert get_response.json()["data"]["grade"] is None
