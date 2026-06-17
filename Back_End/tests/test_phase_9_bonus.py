from httpx import AsyncClient

from tests.test_phase_5_assignments import create_class, create_student, create_teacher, enroll, login


async def setup_bonus_context(client: AsyncClient, admin_headers: dict[str, str], suffix: str) -> dict:
    teacher = await create_teacher(client, admin_headers, f"9T{suffix}")
    student = await create_student(client, admin_headers, f"9S{suffix}")
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


async def give_bonus(
    client: AsyncClient,
    headers: dict[str, str],
    student_id: str,
    class_id: str,
    reason: str | None = "Excellent participation",
):
    payload = {"student_id": student_id, "class_id": class_id}
    if reason is not None:
        payload["reason"] = reason
    return await client.post("/api/bonus", headers=headers, json=payload)


async def test_teacher_can_give_bonus_to_student_in_assigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_bonus_context(client, admin_headers, "901")

    response = await give_bonus(
        client,
        context["teacher_headers"],
        context["student"]["student_profile"]["id"],
        context["class"]["id"],
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["student_id"] == context["student"]["student_profile"]["id"]
    assert data["class_id"] == context["class"]["id"]
    assert data["weekly_bonus_count"] == 1
    assert data["weekly_bonus_remaining"] == 4


async def test_teacher_cannot_give_bonus_to_student_in_unassigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_bonus_context(client, admin_headers, "902")
    second = await setup_bonus_context(client, admin_headers, "903")

    response = await give_bonus(
        client,
        first["teacher_headers"],
        second["student"]["student_profile"]["id"],
        second["class"]["id"],
    )

    assert response.status_code == 403


async def test_admin_can_give_bonus_to_any_active_enrolled_student(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_bonus_context(client, admin_headers, "904")

    response = await give_bonus(
        client,
        admin_headers,
        context["student"]["student_profile"]["id"],
        context["class"]["id"],
    )

    assert response.status_code == 200
    grade_entry = (await client.get(f"/api/grade-entries/{response.json()['data']['grade_entry_id']}", headers=admin_headers)).json()["data"]
    assert grade_entry["teacher_id"] is None
    assert grade_entry["created_by_user_id"] is not None


async def test_student_cannot_give_bonus(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_bonus_context(client, admin_headers, "905")

    response = await give_bonus(
        client,
        context["student_headers"],
        context["student"]["student_profile"]["id"],
        context["class"]["id"],
    )

    assert response.status_code == 403


async def test_bonus_creates_grade_entry_with_bonus_values(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_bonus_context(client, admin_headers, "906")

    response = await give_bonus(
        client,
        context["teacher_headers"],
        context["student"]["student_profile"]["id"],
        context["class"]["id"],
        reason=None,
    )
    grade_entry = (await client.get(f"/api/grade-entries/{response.json()['data']['grade_entry_id']}", headers=admin_headers)).json()["data"]

    assert grade_entry["category"] == "bonus"
    assert grade_entry["earned_grade"] == 1
    assert grade_entry["max_grade"] == 0
    assert grade_entry["source_type"] == "system_bonus"
    assert grade_entry["reason"] == "Bonus"
    assert grade_entry["teacher_id"] == context["teacher"]["teacher_profile"]["id"]


async def test_weekly_limit_allows_five_bonuses_and_rejects_sixth(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    context = await setup_bonus_context(client, admin_headers, "907")
    responses = []

    for _ in range(5):
        responses.append(
            await give_bonus(
                client,
                context["teacher_headers"],
                context["student"]["student_profile"]["id"],
                context["class"]["id"],
            )
        )
    sixth = await give_bonus(
        client,
        context["teacher_headers"],
        context["student"]["student_profile"]["id"],
        context["class"]["id"],
    )

    assert [response.status_code for response in responses] == [200, 200, 200, 200, 200]
    assert responses[-1].json()["data"]["weekly_bonus_count"] == 5
    assert responses[-1].json()["data"]["weekly_bonus_remaining"] == 0
    assert sixth.status_code == 400


async def test_bonus_can_be_viewed_by_owning_student_only(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_bonus_context(client, admin_headers, "908")
    second = await setup_bonus_context(client, admin_headers, "909")
    first_bonus = await give_bonus(
        client,
        first["teacher_headers"],
        first["student"]["student_profile"]["id"],
        first["class"]["id"],
    )
    await give_bonus(
        client,
        second["teacher_headers"],
        second["student"]["student_profile"]["id"],
        second["class"]["id"],
    )

    response = await client.get("/api/students/me/bonus", headers=first["student_headers"])

    assert response.status_code == 200
    assert [item["grade_entry_id"] for item in response.json()["data"]] == [first_bonus.json()["data"]["grade_entry_id"]]


async def test_teacher_can_list_bonus_only_for_assigned_class(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_bonus_context(client, admin_headers, "910")
    second = await setup_bonus_context(client, admin_headers, "911")
    bonus = await give_bonus(
        client,
        first["teacher_headers"],
        first["student"]["student_profile"]["id"],
        first["class"]["id"],
    )

    assigned = await client.get(f"/api/teachers/me/classes/{first['class']['id']}/bonus", headers=first["teacher_headers"])
    unassigned = await client.get(f"/api/teachers/me/classes/{second['class']['id']}/bonus", headers=first["teacher_headers"])

    assert assigned.status_code == 200
    assert assigned.json()["data"][0]["grade_entry_id"] == bonus.json()["data"]["grade_entry_id"]
    assert unassigned.status_code == 403


async def test_admin_can_list_all_bonus_entries(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    first = await setup_bonus_context(client, admin_headers, "912")
    second = await setup_bonus_context(client, admin_headers, "913")
    first_bonus = await give_bonus(client, first["teacher_headers"], first["student"]["student_profile"]["id"], first["class"]["id"])
    second_bonus = await give_bonus(client, second["teacher_headers"], second["student"]["student_profile"]["id"], second["class"]["id"])

    response = await client.get("/api/bonus", headers=admin_headers)

    assert response.status_code == 200
    assert {item["grade_entry_id"] for item in response.json()["data"]} == {
        first_bonus.json()["data"]["grade_entry_id"],
        second_bonus.json()["data"]["grade_entry_id"],
    }


async def test_bonus_to_non_active_or_non_enrolled_student_is_rejected(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    context = await setup_bonus_context(client, admin_headers, "914")
    non_enrolled = await create_student(client, admin_headers, "9NE914")
    suspended_response = await client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "email": "phase9.suspended@ica.eg",
            "password": "Student@123456",
            "role": "student",
            "student_profile": {
                "student_code": "P9SUSP",
                "full_name": "Phase 9 Suspended",
                "phone_number": "01000000000",
                "status": "suspended",
            },
        },
    )
    assert suspended_response.status_code == 200

    non_enrolled_bonus = await give_bonus(
        client,
        admin_headers,
        non_enrolled["student_profile"]["id"],
        context["class"]["id"],
    )
    suspended_bonus = await give_bonus(
        client,
        admin_headers,
        suspended_response.json()["data"]["student_profile"]["id"],
        context["class"]["id"],
    )

    assert non_enrolled_bonus.status_code == 400
    assert suspended_bonus.status_code == 400
