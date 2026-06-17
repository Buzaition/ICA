from httpx import AsyncClient

from tests.test_phase_5_assignments import create_class, create_student, create_teacher, enroll, login


async def setup_quiz_context(client: AsyncClient, admin_headers: dict[str, str], suffix: str) -> dict:
    teacher = await create_teacher(client, admin_headers, f"8T{suffix}")
    student = await create_student(client, admin_headers, f"8S{suffix}")
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


async def create_manual_quiz(
    client: AsyncClient,
    headers: dict[str, str],
    class_id: str,
    student_id: str,
    earned_grade: float = 8,
    title: str = "Quiz 1",
    quiz_date: str = "2026-07-01",
    max_grade: float = 10,
    teacher_id: str | None = None,
) -> dict:
    payload = {
        "class_id": class_id,
        "title": title,
        "description": "Basics",
        "quiz_date": quiz_date,
        "max_grade": max_grade,
        "results": [{"student_id": student_id, "earned_grade": earned_grade}],
    }
    if teacher_id is not None:
        payload["teacher_id"] = teacher_id
    response = await client.post("/api/quizzes/manual", headers=headers, json=payload)
    assert response.status_code == 200
    return response.json()["data"]


async def test_teacher_can_create_manual_quiz_results_for_assigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_quiz_context(client, admin_headers, "801")

    result = await create_manual_quiz(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
    )

    assert result["quiz"]["class_code"] == context["class"]["code"]
    assert result["results"][0]["earned_grade"] == 8


async def test_teacher_cannot_create_quiz_for_unassigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_quiz_context(client, admin_headers, "802")
    other_teacher = await create_teacher(client, admin_headers, "8O802")
    other_headers = await login(client, other_teacher["email"], "Teacher@123456")

    response = await client.post(
        "/api/quizzes/manual",
        headers=other_headers,
        json={
            "class_id": context["class"]["id"],
            "title": "Blocked Quiz",
            "quiz_date": "2026-07-02",
            "max_grade": 10,
            "results": [{"student_id": context["student"]["student_profile"]["id"], "earned_grade": 8}],
        },
    )

    assert response.status_code == 403


async def test_admin_can_create_quiz_for_any_class_with_teacher_id(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_quiz_context(client, admin_headers, "803")

    result = await create_manual_quiz(
        client,
        admin_headers,
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        teacher_id=context["teacher"]["teacher_profile"]["id"],
    )

    assert result["quiz"]["teacher_id"] == context["teacher"]["teacher_profile"]["id"]


async def test_manual_quiz_result_creates_grade_entry(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_quiz_context(client, admin_headers, "804")

    result = await create_manual_quiz(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
    )
    grade_entry = await client.get(f"/api/grade-entries/{result['results'][0]['grade_entry_id']}", headers=admin_headers)

    assert grade_entry.status_code == 200
    assert grade_entry.json()["data"]["category"] == "quiz"
    assert grade_entry.json()["data"]["reason"] == "Quiz Result"


async def test_csv_upload_creates_quiz_and_grade_entries(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_quiz_context(client, admin_headers, "805")
    csv_content = f"student_code,earned_grade,max_grade\n{context['student']['student_profile']['student_code']},9,10\n"

    response = await client.post(
        "/api/quizzes/upload-csv",
        headers=context["teacher_headers"],
        data={
            "class_id": context["class"]["id"],
            "title": "CSV Quiz",
            "quiz_date": "2026-07-05",
            "max_grade": "10",
        },
        files={"file": ("quiz.csv", csv_content, "text/csv")},
    )

    data = response.json()["data"]
    grade_entry = await client.get(f"/api/grade-entries/{data['results'][0]['grade_entry_id']}", headers=admin_headers)
    assert response.status_code == 200
    assert data["success_count"] == 1
    assert grade_entry.json()["data"]["source_type"] == "csv_upload"


async def test_csv_partial_success_with_invalid_and_non_enrolled_rows(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_quiz_context(client, admin_headers, "806")
    non_enrolled = await create_student(client, admin_headers, "8NE806")
    csv_content = (
        "student_code,earned_grade,max_grade\n"
        f"{context['student']['student_profile']['student_code']},8,10\n"
        "UNKNOWN,8,10\n"
        f"{non_enrolled['student_profile']['student_code']},8,10\n"
    )

    response = await client.post(
        "/api/quizzes/upload-csv",
        headers=context["teacher_headers"],
        data={"class_id": context["class"]["id"], "title": "Partial Quiz", "quiz_date": "2026-07-06", "max_grade": "10"},
        files={"file": ("quiz.csv", csv_content, "text/csv")},
    )

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["total_rows"] == 3
    assert data["success_count"] == 1
    assert data["error_count"] == 2
    assert {error["reason"] for error in data["errors"]} == {
        "Invalid student_code",
        "Student is not actively enrolled in this class",
    }


async def test_csv_max_grade_mismatch_returns_error_row(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_quiz_context(client, admin_headers, "807")
    csv_content = f"student_code,earned_grade,max_grade\n{context['student']['student_profile']['student_code']},8,9\n"

    response = await client.post(
        "/api/quizzes/upload-csv",
        headers=context["teacher_headers"],
        data={"class_id": context["class"]["id"], "title": "Mismatch Quiz", "quiz_date": "2026-07-07", "max_grade": "10"},
        files={"file": ("quiz.csv", csv_content, "text/csv")},
    )

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["success_count"] == 0
    assert data["errors"][0]["reason"] == "CSV max_grade does not match quiz max_grade"


async def test_earned_grade_above_max_grade_is_rejected(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_quiz_context(client, admin_headers, "808")

    response = await client.post(
        "/api/quizzes/manual",
        headers=context["teacher_headers"],
        json={
            "class_id": context["class"]["id"],
            "title": "Too High",
            "quiz_date": "2026-07-08",
            "max_grade": 10,
            "results": [{"student_id": context["student"]["student_profile"]["id"], "earned_grade": 11}],
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["success_count"] == 0
    assert response.json()["data"]["errors"][0]["reason"] == "earned_grade cannot exceed max_grade"


async def test_duplicate_quiz_reuses_existing_quiz_and_does_not_duplicate_result(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_quiz_context(client, admin_headers, "809")
    first = await create_manual_quiz(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        title="Duplicate Quiz",
        quiz_date="2026-07-09",
    )
    second = await create_manual_quiz(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        title="Duplicate Quiz",
        quiz_date="2026-07-09",
    )
    entries = await client.get("/api/grade-entries", headers=admin_headers)
    matching_entries = [
        entry
        for entry in entries.json()["data"]
        if entry["category"] == "quiz" and entry["student_id"] == context["student"]["student_profile"]["id"]
    ]

    assert second["quiz_id"] == first["quiz_id"]
    assert second["results"][0]["id"] == first["results"][0]["id"]
    assert second["results"][0]["grade_entry_id"] == first["results"][0]["grade_entry_id"]
    assert len(matching_entries) == 1


async def test_updating_quiz_result_creates_correction_without_mutating_original(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_quiz_context(client, admin_headers, "810")
    result = await create_manual_quiz(
        client,
        context["teacher_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        earned_grade=7,
        title="Correction Quiz",
        quiz_date="2026-07-10",
    )
    quiz_result_id = result["results"][0]["id"]
    original_grade_entry_id = result["results"][0]["grade_entry_id"]
    original_before = (await client.get(f"/api/grade-entries/{original_grade_entry_id}", headers=admin_headers)).json()["data"]

    updated = await client.put(
        f"/api/quiz-results/{quiz_result_id}",
        headers=context["teacher_headers"],
        json={"earned_grade": 9},
    )
    original_after = (await client.get(f"/api/grade-entries/{original_grade_entry_id}", headers=admin_headers)).json()["data"]
    corrections = (await client.get(f"/api/grade-entries/{original_grade_entry_id}/corrections", headers=admin_headers)).json()["data"]

    assert updated.status_code == 200
    assert updated.json()["data"]["earned_grade"] == 9
    assert original_before["earned_grade"] == 7
    assert original_after["earned_grade"] == 7
    assert corrections[0]["earned_grade"] == 2
    assert corrections[0]["reason"] == "Quiz result correction from 7 to 9"


async def test_student_can_view_own_quiz_results(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_quiz_context(client, admin_headers, "811")
    second = await setup_quiz_context(client, admin_headers, "812")
    first_result = await create_manual_quiz(
        client,
        first["teacher_headers"],
        first["class"]["id"],
        first["student"]["student_profile"]["id"],
    )
    await create_manual_quiz(
        client,
        second["teacher_headers"],
        second["class"]["id"],
        second["student"]["student_profile"]["id"],
    )

    response = await client.get("/api/students/me/quizzes", headers=first["student_headers"])

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]] == [first_result["results"][0]["id"]]


async def test_teacher_can_view_quizzes_only_for_assigned_classes(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_quiz_context(client, admin_headers, "813")
    second = await setup_quiz_context(client, admin_headers, "814")
    await create_manual_quiz(
        client,
        first["teacher_headers"],
        first["class"]["id"],
        first["student"]["student_profile"]["id"],
    )

    assigned = await client.get(f"/api/teachers/me/classes/{first['class']['id']}/quizzes", headers=first["teacher_headers"])
    unassigned = await client.get(f"/api/teachers/me/classes/{second['class']['id']}/quizzes", headers=first["teacher_headers"])

    assert assigned.status_code == 200
    assert assigned.json()["data"][0]["class_id"] == first["class"]["id"]
    assert unassigned.status_code == 403
