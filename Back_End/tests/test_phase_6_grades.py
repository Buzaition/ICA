from httpx import AsyncClient

from tests.test_phase_5_assignments import (
    create_class,
    create_teacher,
    login,
    past_deadline,
    setup_assignment_context,
    submit_assignment,
)


async def review_submission(client: AsyncClient, headers: dict[str, str], submission_id: str, grade: int = 8) -> dict:
    response = await client.post(
        f"/api/assignment-submissions/{submission_id}/review",
        headers=headers,
        json={"grade": grade, "feedback": "Reviewed"},
    )
    assert response.status_code == 200
    return response.json()["data"]


async def reviewed_grade_context(client: AsyncClient, admin_headers: dict[str, str], suffix: str, grade: int = 8) -> dict:
    context = await setup_assignment_context(client, admin_headers, suffix)
    submission = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])
    assert submission.status_code == 200
    reviewed = await review_submission(client, context["teacher_headers"], submission.json()["data"]["id"], grade=grade)
    return {**context, "submission": submission.json()["data"], "reviewed": reviewed}


async def test_reviewing_assignment_creates_grade_entry(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "601", grade=9)

    response = await client.get(f"/api/grade-entries/{context['reviewed']['grade_entry_id']}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["data"]["category"] == "assignment"
    assert response.json()["data"]["assignment_submission_id"] == context["submission"]["id"]


async def test_reviewing_same_submission_twice_does_not_create_duplicate_grade_entry(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await reviewed_grade_context(client, admin_headers, "602", grade=7)

    second_review = await review_submission(client, context["teacher_headers"], context["submission"]["id"], grade=10)
    entries = await client.get("/api/grade-entries", headers=admin_headers)

    assert second_review["grade_entry_id"] == context["reviewed"]["grade_entry_id"]
    assert second_review["grade"] == 7
    assert len([entry for entry in entries.json()["data"] if entry["assignment_submission_id"] == context["submission"]["id"]]) == 1


async def test_rejected_late_submission_does_not_create_grade_entry(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_assignment_context(client, admin_headers, "603", deadline=past_deadline())
    submission = await submit_assignment(client, context["student_headers"], context["assignment"]["id"])

    rejected = await client.post(
        f"/api/assignment-submissions/{submission.json()['data']['id']}/reject",
        headers=context["teacher_headers"],
        json={"feedback": "Late"},
    )
    entries = await client.get("/api/grade-entries", headers=admin_headers)

    assert rejected.status_code == 200
    assert entries.json()["data"] == []


async def test_grade_entry_values_match_assignment_review_values(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "604", grade=6)

    entry = (await client.get(f"/api/grade-entries/{context['reviewed']['grade_entry_id']}", headers=admin_headers)).json()["data"]

    assert entry["earned_grade"] == 6
    assert entry["max_grade"] == context["assignment"]["max_grade"]
    assert entry["reason"] == "Assignment Review"
    assert entry["teacher_id"] == context["teacher"]["teacher_profile"]["id"]


async def test_admin_can_list_all_grade_entries(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "605")

    response = await client.get("/api/grade-entries", headers=admin_headers)

    assert response.status_code == 200
    assert context["reviewed"]["grade_entry_id"] in [entry["id"] for entry in response.json()["data"]]


async def test_teacher_can_list_assigned_class_entries(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "606")

    response = await client.get(
        f"/api/teachers/me/classes/{context['class']['id']}/grade-entries",
        headers=context["teacher_headers"],
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == context["reviewed"]["grade_entry_id"]


async def test_teacher_cannot_list_unassigned_class_entries(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "607")
    other_teacher = await create_teacher(client, admin_headers, "607B")
    other_headers = await login(client, other_teacher["email"], "Teacher@123456")

    response = await client.get(
        f"/api/teachers/me/classes/{context['class']['id']}/grade-entries",
        headers=other_headers,
    )

    assert response.status_code == 403


async def test_student_can_list_own_grade_entries(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "608")

    response = await client.get("/api/students/me/grade-entries", headers=context["student_headers"])

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == context["reviewed"]["grade_entry_id"]


async def test_student_cannot_view_other_student_grade_entry(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await reviewed_grade_context(client, admin_headers, "609")
    second = await setup_assignment_context(client, admin_headers, "610")

    response = await client.get(
        f"/api/grade-entries/{first['reviewed']['grade_entry_id']}",
        headers=second["student_headers"],
    )

    assert response.status_code == 403


async def test_reviewed_assignments_page_includes_grade_entry_id(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "611")

    response = await client.get("/api/teachers/me/assignments/reviewed", headers=context["teacher_headers"])

    assert response.status_code == 200
    assert response.json()["data"][0]["grade_entry_id"] == context["reviewed"]["grade_entry_id"]


async def test_teacher_can_create_correction_for_assigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "612")

    response = await client.post(
        f"/api/grade-entries/{context['reviewed']['grade_entry_id']}/corrections",
        headers=context["teacher_headers"],
        json={"earned_grade": 1, "reason": "Manual correction"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["category"] == "correction"
    assert response.json()["data"]["related_entry_id"] == context["reviewed"]["grade_entry_id"]


async def test_teacher_cannot_correct_unassigned_grade_entry(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "613")
    other_teacher = await create_teacher(client, admin_headers, "613B")
    other_headers = await login(client, other_teacher["email"], "Teacher@123456")

    response = await client.post(
        f"/api/grade-entries/{context['reviewed']['grade_entry_id']}/corrections",
        headers=other_headers,
        json={"earned_grade": 1, "reason": "Blocked"},
    )

    assert response.status_code == 403


async def test_admin_can_correct_any_grade_entry(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "614")

    response = await client.post(
        f"/api/grade-entries/{context['reviewed']['grade_entry_id']}/corrections",
        headers=admin_headers,
        json={"earned_grade": -1, "reason": "Admin correction"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["source_type"] == "correction"


async def test_student_cannot_create_correction(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "615")

    response = await client.post(
        f"/api/grade-entries/{context['reviewed']['grade_entry_id']}/corrections",
        headers=context["student_headers"],
        json={"earned_grade": 1, "reason": "Please"},
    )

    assert response.status_code == 403


async def test_correction_requires_reason(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "616")

    response = await client.post(
        f"/api/grade-entries/{context['reviewed']['grade_entry_id']}/corrections",
        headers=admin_headers,
        json={"earned_grade": 1},
    )

    assert response.status_code == 422


async def test_correction_references_original(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "617")
    correction = await client.post(
        f"/api/grade-entries/{context['reviewed']['grade_entry_id']}/corrections",
        headers=admin_headers,
        json={"earned_grade": 1, "reason": "Reference check"},
    )

    response = await client.get(
        f"/api/grade-entries/{context['reviewed']['grade_entry_id']}/corrections",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == correction.json()["data"]["id"]
    assert response.json()["data"][0]["related_entry_id"] == context["reviewed"]["grade_entry_id"]


async def test_cannot_create_correction_for_correction(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "618")
    correction = await client.post(
        f"/api/grade-entries/{context['reviewed']['grade_entry_id']}/corrections",
        headers=admin_headers,
        json={"earned_grade": 1, "reason": "First correction"},
    )

    response = await client.post(
        f"/api/grade-entries/{correction.json()['data']['id']}/corrections",
        headers=admin_headers,
        json={"earned_grade": 1, "reason": "Nested"},
    )

    assert response.status_code == 400


async def test_corrections_history_works(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await reviewed_grade_context(client, admin_headers, "619")
    correction = await client.post(
        f"/api/grade-entries/{context['reviewed']['grade_entry_id']}/corrections",
        headers=context["teacher_headers"],
        json={"earned_grade": -1, "reason": "History"},
    )

    teacher_history = await client.get("/api/teachers/me/corrections-history", headers=context["teacher_headers"])
    admin_history = await client.get("/api/admin/corrections-history", headers=admin_headers)

    assert correction.status_code == 200
    assert teacher_history.status_code == 200
    assert admin_history.status_code == 200
    assert teacher_history.json()["data"][0]["correction_id"] == correction.json()["data"]["id"]
    assert admin_history.json()["data"][0]["correction_id"] == correction.json()["data"]["id"]
