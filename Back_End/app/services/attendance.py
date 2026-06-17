import csv
from dataclasses import dataclass
from http import HTTPStatus
from io import StringIO
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import (
    AttendanceSessionType,
    AttendanceSourceType,
    AttendanceStatus,
    EnrollmentStatus,
    GradeCategory,
    GradeSourceType,
    StudentStatus,
    UserRole,
)
from app.models.attendance import AttendanceRecord, AttendanceSession
from app.models.grade import GradeEntry
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.attendance import AttendanceRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.grades import GradeRepository
from app.schemas.attendance import (
    AttendanceRecordUpdate,
    AttendanceUploadErrorRead,
    ManualAttendanceCreate,
    ManualAttendanceRecordCreate,
    attendance_grade_for_status,
)


@dataclass
class AttendanceSubmissionResult:
    session: AttendanceSession
    records: list[AttendanceRecord]
    total_rows: int
    errors: list[AttendanceUploadErrorRead]

    @property
    def success_count(self) -> int:
        return len(self.records)

    @property
    def error_count(self) -> int:
        return len(self.errors)


class AttendanceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.attendance = AttendanceRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.enrollments = EnrollmentRepository(session)
        self.grades = GradeRepository(session)

    async def submit_manual_attendance(self, payload: ManualAttendanceCreate, actor: User) -> AttendanceSubmissionResult:
        academic_class = await self._require_class(payload.class_id)
        teacher_id = await self._resolve_teacher_id(actor, academic_class, payload.teacher_id, payload.session_type)
        attendance_session = await self._get_or_create_session(
            payload.class_id,
            teacher_id,
            payload.session_type,
            payload.session_date,
            AttendanceSourceType.manual,
            actor,
        )
        errors: list[AttendanceUploadErrorRead] = []
        records = await self._process_records(
            attendance_session,
            payload.records,
            AttendanceSourceType.manual,
            actor,
            errors,
        )
        await self.session.commit()
        refreshed = await self._refresh_result(attendance_session.id, records)
        return AttendanceSubmissionResult(refreshed["session"], refreshed["records"], len(payload.records), errors)

    async def upload_csv_attendance(
        self,
        class_id: UUID,
        teacher_id: UUID | None,
        session_type: AttendanceSessionType,
        session_date,
        file: UploadFile,
        actor: User,
    ) -> AttendanceSubmissionResult:
        academic_class = await self._require_class(class_id)
        resolved_teacher_id = await self._resolve_teacher_id(actor, academic_class, teacher_id, session_type)
        attendance_session = await self._get_or_create_session(
            class_id,
            resolved_teacher_id,
            session_type,
            session_date,
            AttendanceSourceType.csv_upload,
            actor,
        )
        rows, errors, total_rows = await self._parse_csv(file)
        records = await self._process_records(attendance_session, rows, AttendanceSourceType.csv_upload, actor, errors)
        await self.audit_logs.add(
            actor.id,
            "upload_attendance_csv",
            "attendance_session",
            attendance_session.id,
            new_value={"total_rows": total_rows, "success_count": len(records), "error_count": len(errors)},
        )
        await self.session.commit()
        refreshed = await self._refresh_result(attendance_session.id, records)
        return AttendanceSubmissionResult(refreshed["session"], refreshed["records"], total_rows, errors)

    async def list_sessions_for_user(self, actor: User) -> list[AttendanceSession]:
        if actor.role == UserRole.admin:
            return await self.attendance.list_sessions()
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            return await self.attendance.list_sessions_for_teacher(actor.teacher_profile.id)
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def get_session_for_user(self, session_id: UUID, actor: User) -> AttendanceSession:
        attendance_session = await self._require_session(session_id)
        self._ensure_can_view_session(attendance_session, actor)
        return attendance_session

    async def list_records_for_session(self, session_id: UUID, actor: User) -> list[AttendanceRecord]:
        attendance_session = await self._require_session(session_id)
        self._ensure_can_view_session(attendance_session, actor)
        return await self.attendance.list_records_for_session(session_id)

    async def update_record(self, record_id: UUID, payload: AttendanceRecordUpdate, actor: User) -> AttendanceRecord:
        record = await self.attendance.get_record_by_id(record_id)
        if record is None:
            raise AppException("Attendance record not found", HTTPStatus.NOT_FOUND)
        self._ensure_can_edit_session(record.attendance_session, actor)
        if record.status == payload.status:
            return record
        old_status = record.status
        old_grade = attendance_grade_for_status(old_status)
        new_grade = attendance_grade_for_status(payload.status)
        original_grade_entry_id = record.grade_entry_id
        if original_grade_entry_id is None:
            original_grade_entry = await self._create_attendance_grade_entry(
                record,
                record.attendance_session.source_type,
                actor,
            )
            original_grade_entry_id = original_grade_entry.id
            record.grade_entry_id = original_grade_entry.id
        correction = GradeEntry(
            student_id=record.student_id,
            class_id=record.attendance_session.class_id,
            teacher_id=record.attendance_session.teacher_id,
            category=GradeCategory.correction,
            earned_grade=new_grade - old_grade,
            max_grade=0,
            source_type=GradeSourceType.correction,
            reason=f"Attendance status correction from {old_status.value} to {payload.status.value}",
            related_entry_id=original_grade_entry_id,
            created_by_user_id=actor.id,
        )
        await self.grades.add(correction)
        record.status = payload.status
        await self.audit_logs.add(
            actor.id,
            "update_attendance_record",
            "attendance_record",
            record.id,
            old_value={"status": old_status.value},
            new_value={"status": record.status.value, "correction_grade_entry_id": str(correction.id)},
        )
        await self.audit_logs.add(
            actor.id,
            "create_attendance_correction",
            "grade_entry",
            correction.id,
            new_value={"related_entry_id": str(original_grade_entry_id), "earned_grade": float(correction.earned_grade)},
        )
        await self.session.commit()
        return await self.attendance.get_record_by_id(record.id)

    async def list_teacher_class_attendance(self, class_id: UUID, actor: User) -> list[AttendanceSession]:
        academic_class = await self._require_class(class_id)
        self._require_teacher_assigned(actor, academic_class)
        return await self.attendance.list_sessions_for_class(class_id)

    async def list_student_attendance(self, actor: User) -> list[AttendanceRecord]:
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.attendance.list_records_for_student(actor.student_profile.id)

    async def list_all_records_for_admin(self, actor: User) -> list[AttendanceRecord]:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.attendance.list_records_all()

    async def _process_records(
        self,
        attendance_session: AttendanceSession,
        records: list[ManualAttendanceRecordCreate],
        source_type: AttendanceSourceType,
        actor: User,
        errors: list[AttendanceUploadErrorRead],
    ) -> list[AttendanceRecord]:
        active_enrollments = await self.enrollments.list_for_class(attendance_session.class_id)
        enrolled_students = {
            enrollment.student_id: enrollment.student
            for enrollment in active_enrollments
            if enrollment.status == EnrollmentStatus.active
            and enrollment.deleted_at is None
            and enrollment.student.status == StudentStatus.active
        }
        saved_records: list[AttendanceRecord] = []
        for index, row in enumerate(records, start=2):
            student = enrolled_students.get(row.student_id)
            if student is None:
                errors.append(
                    AttendanceUploadErrorRead(
                        row_number=row.row_number or index,
                        student_code=row.student_code,
                        reason="Student is not actively enrolled in this class",
                    )
                )
                continue
            existing = await self.attendance.get_record_for_session_student(attendance_session.id, row.student_id)
            if existing is None:
                record = AttendanceRecord(
                    attendance_session_id=attendance_session.id,
                    student_id=row.student_id,
                    status=row.status,
                )
                await self.attendance.add_record(record)
                record.attendance_session = attendance_session
                grade_entry = await self._create_attendance_grade_entry(record, source_type, actor)
                record.grade_entry_id = grade_entry.id
                await self.audit_logs.add(
                    actor.id,
                    "create_attendance_record",
                    "attendance_record",
                    record.id,
                    new_value={"student_id": str(record.student_id), "status": record.status.value},
                )
                saved_records.append(record)
                continue
            if existing.status != row.status:
                updated = await self._update_existing_record_without_commit(existing, row.status, actor)
                saved_records.append(updated)
            else:
                if existing.grade_entry_id is None:
                    grade_entry = await self._create_attendance_grade_entry(existing, source_type, actor)
                    existing.grade_entry_id = grade_entry.id
                saved_records.append(existing)
        return saved_records

    async def _update_existing_record_without_commit(
        self,
        record: AttendanceRecord,
        status: AttendanceStatus,
        actor: User,
    ) -> AttendanceRecord:
        old_status = record.status
        old_grade = attendance_grade_for_status(old_status)
        new_grade = attendance_grade_for_status(status)
        if record.grade_entry_id is None:
            original_grade_entry = await self._create_attendance_grade_entry(record, record.attendance_session.source_type, actor)
            record.grade_entry_id = original_grade_entry.id
        correction = GradeEntry(
            student_id=record.student_id,
            class_id=record.attendance_session.class_id,
            teacher_id=record.attendance_session.teacher_id,
            category=GradeCategory.correction,
            earned_grade=new_grade - old_grade,
            max_grade=0,
            source_type=GradeSourceType.correction,
            reason=f"Attendance status correction from {old_status.value} to {status.value}",
            related_entry_id=record.grade_entry_id,
            created_by_user_id=actor.id,
        )
        await self.grades.add(correction)
        record.status = status
        await self.audit_logs.add(
            actor.id,
            "update_attendance_record",
            "attendance_record",
            record.id,
            old_value={"status": old_status.value},
            new_value={"status": status.value, "correction_grade_entry_id": str(correction.id)},
        )
        return record

    async def _create_attendance_grade_entry(
        self,
        record: AttendanceRecord,
        source_type: AttendanceSourceType,
        actor: User,
    ) -> GradeEntry:
        grade_entry = GradeEntry(
            student_id=record.student_id,
            class_id=record.attendance_session.class_id,
            teacher_id=record.attendance_session.teacher_id,
            category=GradeCategory.attendance,
            earned_grade=attendance_grade_for_status(record.status),
            max_grade=record.attendance_session.max_grade,
            source_type=GradeSourceType(source_type.value),
            reason="Attendance",
            created_by_user_id=actor.id,
        )
        await self.grades.add(grade_entry)
        await self.audit_logs.add(
            actor.id,
            "create_attendance_grade_entry",
            "grade_entry",
            grade_entry.id,
            new_value={
                "student_id": str(grade_entry.student_id),
                "class_id": str(grade_entry.class_id),
                "earned_grade": float(grade_entry.earned_grade),
            },
        )
        return grade_entry

    async def _get_or_create_session(
        self,
        class_id: UUID,
        teacher_id: UUID,
        session_type: AttendanceSessionType,
        session_date,
        source_type: AttendanceSourceType,
        actor: User,
    ) -> AttendanceSession:
        existing = await self.attendance.get_session_by_identity(class_id, teacher_id, session_type, session_date)
        if existing is not None:
            return existing
        attendance_session = AttendanceSession(
            class_id=class_id,
            teacher_id=teacher_id,
            session_type=session_type,
            session_date=session_date,
            max_grade=1,
            source_type=source_type,
            created_by_user_id=actor.id,
        )
        await self.attendance.add_session(attendance_session)
        await self.audit_logs.add(
            actor.id,
            "create_attendance_session",
            "attendance_session",
            attendance_session.id,
            new_value={
                "class_id": str(class_id),
                "teacher_id": str(teacher_id),
                "session_type": session_type.value,
                "session_date": str(session_date),
            },
        )
        return attendance_session

    async def _parse_csv(
        self,
        file: UploadFile,
    ) -> tuple[list[ManualAttendanceRecordCreate], list[AttendanceUploadErrorRead], int]:
        content = (await file.read()).decode("utf-8-sig")
        reader = csv.DictReader(StringIO(content))
        rows: list[ManualAttendanceRecordCreate] = []
        errors: list[AttendanceUploadErrorRead] = []
        if reader.fieldnames is None or "student_code" not in reader.fieldnames or "status" not in reader.fieldnames:
            raise AppException("CSV must include student_code and status columns", HTTPStatus.BAD_REQUEST)
        active_students_by_code = await self._active_students_by_code()
        total_rows = 0
        for row_number, row in enumerate(reader, start=2):
            total_rows += 1
            student_code = (row.get("student_code") or "").strip()
            raw_status = (row.get("status") or "").strip().lower()
            student = active_students_by_code.get(student_code)
            if student is None:
                errors.append(
                    AttendanceUploadErrorRead(row_number=row_number, student_code=student_code, reason="Invalid student_code")
                )
                continue
            try:
                status = AttendanceStatus(raw_status)
            except ValueError:
                errors.append(
                    AttendanceUploadErrorRead(row_number=row_number, student_code=student_code, reason="Invalid status")
                )
                continue
            rows.append(
                ManualAttendanceRecordCreate(
                    student_id=student.id,
                    status=status,
                    student_code=student_code,
                    row_number=row_number,
                )
            )
        return rows, errors, total_rows

    async def _active_students_by_code(self) -> dict[str, object]:
        from sqlalchemy import select

        from app.models.profiles import StudentProfile

        result = await self.session.scalars(select(StudentProfile).where(StudentProfile.status == StudentStatus.active))
        return {student.student_code: student for student in result.all()}

    async def _refresh_result(self, session_id: UUID, records: list[AttendanceRecord]) -> dict:
        attendance_session = await self._require_session(session_id)
        record_ids = {record.id for record in records}
        refreshed_records = [
            record for record in await self.attendance.list_records_for_session(session_id) if record.id in record_ids
        ]
        return {"session": attendance_session, "records": refreshed_records}

    async def _require_class(self, class_id: UUID):
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        return academic_class

    async def _require_session(self, session_id: UUID) -> AttendanceSession:
        attendance_session = await self.attendance.get_session_by_id(session_id)
        if attendance_session is None:
            raise AppException("Attendance session not found", HTTPStatus.NOT_FOUND)
        return attendance_session

    async def _resolve_teacher_id(
        self,
        actor: User,
        academic_class,
        teacher_id: UUID | None,
        session_type: AttendanceSessionType,
    ) -> UUID:
        if actor.role == UserRole.admin:
            if teacher_id is None:
                raise AppException("teacher_id is required for admin attendance", HTTPStatus.BAD_REQUEST)
            teacher = await self.academic.get_teacher_profile(teacher_id)
            if teacher is None:
                raise AppException("Teacher profile not found", HTTPStatus.NOT_FOUND)
            self._ensure_teacher_session_role(teacher_id, academic_class, session_type)
            return teacher_id
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            self._ensure_teacher_session_role(actor.teacher_profile.id, academic_class, session_type)
            return actor.teacher_profile.id
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    def _ensure_teacher_session_role(self, teacher_id: UUID, academic_class, session_type: AttendanceSessionType) -> None:
        if session_type == AttendanceSessionType.instructor and academic_class.instructor_id != teacher_id:
            raise AppException("Teacher is not assigned as instructor for this class", HTTPStatus.FORBIDDEN)
        if session_type == AttendanceSessionType.mentor and academic_class.mentor_id != teacher_id:
            raise AppException("Teacher is not assigned as mentor for this class", HTTPStatus.FORBIDDEN)

    def _require_teacher_assigned(self, actor: User, academic_class) -> None:
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    def _ensure_can_view_session(self, attendance_session: AttendanceSession, actor: User) -> None:
        if actor.role == UserRole.admin:
            return
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id in {
                attendance_session.academic_class.instructor_id,
                attendance_session.academic_class.mentor_id,
            }:
                return
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    def _ensure_can_edit_session(self, attendance_session: AttendanceSession, actor: User) -> None:
        if actor.role == UserRole.admin:
            return
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            self._ensure_teacher_session_role(actor.teacher_profile.id, attendance_session.academic_class, attendance_session.session_type)
            return
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
