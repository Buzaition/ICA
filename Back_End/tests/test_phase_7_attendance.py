from httpx import AsyncClient

from tests.test_phase_5_assignments import create_class, create_student, create_teacher, enroll, login


async def setup_attendance_context(client: AsyncClient, admin_headers: dict[str, str], suffix: str) -> dict:
    instructor = await create_teacher(client, admin_headers, f"7I{suffix}")
    mentor = await create_teacher(client, admin_headers, f"7M{suffix}")
    student = await create_student(client, admin_headers, f"7S{suffix}")
    academic_class = await create_class(
        client,
        admin_headers,
        f"BE1{suffix[-3:]}",
        instructor["teacher_profile"]["id"],
        mentor["teacher_profile"]["id"],
    )
    await enroll(client, admin_headers, student["student_profile"]["id"], academic_class["id"])
    instructor_headers = await login(client, instructor["email"], "Teacher@123456")
    mentor_headers = await login(client, mentor["email"], "Teacher@123456")
    student_headers = await login(client, student["email"], "Student@123456")
    return {
        "instructor": instructor,
        "mentor": mentor,
        "student": student,
        "class": academic_class,
        "instructor_headers": instructor_headers,
        "mentor_headers": mentor_headers,
        "student_headers": student_headers,
    }


async def create_manual_attendance(
    client: AsyncClient,
    headers: dict[str, str],
    class_id: str,
    student_id: str,
    status: str = "present",
    session_type: str = "instructor",
    session_date: str = "2026-07-01",
    teacher_id: str | None = None,
) -> dict:
    payload = {
        "class_id": class_id,
        "session_type": session_type,
        "session_date": session_date,
        "records": [{"student_id": student_id, "status": status}],
    }
    if teacher_id is not None:
        payload["teacher_id"] = teacher_id
    response = await client.post("/api/attendance/manual", headers=headers, json=payload)
    assert response.status_code == 200
    return response.json()["data"]


async def test_teacher_can_create_manual_attendance_for_assigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_attendance_context(client, admin_headers, "701")

    result = await create_manual_attendance(
        client,
        context["instructor_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
    )

    assert result["session"]["class_code"] == context["class"]["code"]
    assert result["records"][0]["status"] == "present"


async def test_teacher_cannot_create_attendance_for_unassigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_attendance_context(client, admin_headers, "702")
    other_teacher = await create_teacher(client, admin_headers, "7O702")
    other_headers = await login(client, other_teacher["email"], "Teacher@123456")

    response = await client.post(
        "/api/attendance/manual",
        headers=other_headers,
        json={
            "class_id": context["class"]["id"],
            "session_type": "instructor",
            "session_date": "2026-07-02",
            "records": [{"student_id": context["student"]["student_profile"]["id"], "status": "present"}],
        },
    )

    assert response.status_code == 403


async def test_instructor_cannot_create_mentor_session_unless_assigned_as_mentor(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_attendance_context(client, admin_headers, "703")

    response = await client.post(
        "/api/attendance/manual",
        headers=context["instructor_headers"],
        json={
            "class_id": context["class"]["id"],
            "session_type": "mentor",
            "session_date": "2026-07-03",
            "records": [{"student_id": context["student"]["student_profile"]["id"], "status": "present"}],
        },
    )

    assert response.status_code == 403


async def test_mentor_cannot_create_instructor_session_unless_assigned_as_instructor(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_attendance_context(client, admin_headers, "704")

    response = await client.post(
        "/api/attendance/manual",
        headers=context["mentor_headers"],
        json={
            "class_id": context["class"]["id"],
            "session_type": "instructor",
            "session_date": "2026-07-04",
            "records": [{"student_id": context["student"]["student_profile"]["id"], "status": "present"}],
        },
    )

    assert response.status_code == 403


async def test_admin_can_create_attendance_for_any_class_with_teacher_id(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_attendance_context(client, admin_headers, "705")

    result = await create_manual_attendance(
        client,
        admin_headers,
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        teacher_id=context["instructor"]["teacher_profile"]["id"],
    )

    assert result["session"]["teacher_id"] == context["instructor"]["teacher_profile"]["id"]


async def test_manual_attendance_creates_grade_entry(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_attendance_context(client, admin_headers, "706")

    result = await create_manual_attendance(
        client,
        context["instructor_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
    )

    grade_entry = await client.get(f"/api/grade-entries/{result['records'][0]['grade_entry_id']}", headers=admin_headers)
    assert grade_entry.status_code == 200
    assert grade_entry.json()["data"]["category"] == "attendance"


async def test_present_late_absent_create_expected_grade_entries(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_attendance_context(client, admin_headers, "707")
    expected = [("present", 1), ("late", 0.5), ("absent", 0)]

    for index, (status, earned_grade) in enumerate(expected, start=1):
        result = await create_manual_attendance(
            client,
            context["instructor_headers"],
            context["class"]["id"],
            context["student"]["student_profile"]["id"],
            status=status,
            session_date=f"2026-07-1{index}",
        )
        grade_entry = (
            await client.get(f"/api/grade-entries/{result['records'][0]['grade_entry_id']}", headers=admin_headers)
        ).json()["data"]
        assert grade_entry["earned_grade"] == earned_grade
        assert grade_entry["max_grade"] == 1


async def test_duplicate_session_reuses_existing_session_and_does_not_duplicate_grade_entry(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_attendance_context(client, admin_headers, "708")
    first = await create_manual_attendance(
        client,
        context["instructor_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        session_date="2026-07-18",
    )
    second = await create_manual_attendance(
        client,
        context["instructor_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        session_date="2026-07-18",
    )
    entries = await client.get("/api/grade-entries", headers=admin_headers)

    matching_entries = [
        entry
        for entry in entries.json()["data"]
        if entry["category"] == "attendance" and entry["student_id"] == context["student"]["student_profile"]["id"]
    ]
    assert second["created_session_id"] == first["created_session_id"]
    assert second["records"][0]["grade_entry_id"] == first["records"][0]["grade_entry_id"]
    assert len(matching_entries) == 1


async def test_updating_attendance_status_creates_correction_without_mutating_original(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_attendance_context(client, admin_headers, "709")
    result = await create_manual_attendance(
        client,
        context["instructor_headers"],
        context["class"]["id"],
        context["student"]["student_profile"]["id"],
        status="late",
    )
    record_id = result["records"][0]["id"]
    original_grade_entry_id = result["records"][0]["grade_entry_id"]
    original_before = (await client.get(f"/api/grade-entries/{original_grade_entry_id}", headers=admin_headers)).json()["data"]

    updated = await client.put(
        f"/api/attendance/records/{record_id}",
        headers=context["instructor_headers"],
        json={"status": "present"},
    )
    original_after = (await client.get(f"/api/grade-entries/{original_grade_entry_id}", headers=admin_headers)).json()["data"]
    corrections = (await client.get(f"/api/grade-entries/{original_grade_entry_id}/corrections", headers=admin_headers)).json()["data"]

    assert updated.status_code == 200
    assert updated.json()["data"]["status"] == "present"
    assert original_before["earned_grade"] == 0.5
    assert original_after["earned_grade"] == 0.5
    assert corrections[0]["earned_grade"] == 0.5
    assert corrections[0]["reason"] == "Attendance status correction from late to present"


async def test_csv_upload_partial_success_with_invalid_and_non_enrolled_rows(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_attendance_context(client, admin_headers, "710")
    non_enrolled = await create_student(client, admin_headers, "7NE710")
    csv_content = (
        "student_code,status\n"
        f"{context['student']['student_profile']['student_code']},present\n"
        "UNKNOWN,present\n"
        f"{non_enrolled['student_profile']['student_code']},late\n"
    )

    response = await client.post(
        "/api/attendance/upload-csv",
        headers=context["instructor_headers"],
        data={
            "class_id": context["class"]["id"],
            "session_type": "instructor",
            "session_date": "2026-07-20",
        },
        files={"file": ("attendance.csv", csv_content, "text/csv")},
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


async def test_student_can_view_own_attendance_only(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_attendance_context(client, admin_headers, "711")
    second = await setup_attendance_context(client, admin_headers, "712")
    first_result = await create_manual_attendance(
        client,
        first["instructor_headers"],
        first["class"]["id"],
        first["student"]["student_profile"]["id"],
    )
    await create_manual_attendance(
        client,
        second["instructor_headers"],
        second["class"]["id"],
        second["student"]["student_profile"]["id"],
    )

    response = await client.get("/api/students/me/attendance", headers=first["student_headers"])

    assert response.status_code == 200
    assert [record["id"] for record in response.json()["data"]] == [first_result["records"][0]["id"]]


async def test_teacher_can_view_attendance_only_for_assigned_classes(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_attendance_context(client, admin_headers, "713")
    second = await setup_attendance_context(client, admin_headers, "714")
    await create_manual_attendance(
        client,
        first["instructor_headers"],
        first["class"]["id"],
        first["student"]["student_profile"]["id"],
    )

    assigned = await client.get(
        f"/api/teachers/me/classes/{first['class']['id']}/attendance",
        headers=first["instructor_headers"],
    )
    unassigned = await client.get(
        f"/api/teachers/me/classes/{second['class']['id']}/attendance",
        headers=first["instructor_headers"],
    )

    assert assigned.status_code == 200
    assert assigned.json()["data"][0]["class_id"] == first["class"]["id"]
    assert unassigned.status_code == 403
