from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import AttendanceSessionType, AttendanceSourceType, AttendanceStatus
from app.models.attendance import AttendanceRecord, AttendanceSession


class ManualAttendanceRecordCreate(BaseModel):
    student_id: UUID
    status: AttendanceStatus
    student_code: str | None = None
    row_number: int | None = None


class ManualAttendanceCreate(BaseModel):
    class_id: UUID
    teacher_id: UUID | None = None
    session_type: AttendanceSessionType
    session_date: date
    records: list[ManualAttendanceRecordCreate] = Field(min_length=1)


class AttendanceRecordUpdate(BaseModel):
    status: AttendanceStatus


class AttendanceUploadErrorRead(BaseModel):
    row_number: int
    student_code: str | None
    reason: str


class AttendanceSessionRead(BaseModel):
    id: UUID
    class_id: UUID
    class_code: str
    teacher_id: UUID
    teacher_name: str
    session_type: AttendanceSessionType
    session_date: date
    max_grade: float
    source_type: AttendanceSourceType
    created_at: datetime

    @classmethod
    def from_model(cls, attendance_session: AttendanceSession) -> "AttendanceSessionRead":
        return cls(
            id=attendance_session.id,
            class_id=attendance_session.class_id,
            class_code=attendance_session.academic_class.code,
            teacher_id=attendance_session.teacher_id,
            teacher_name=attendance_session.teacher.full_name,
            session_type=attendance_session.session_type,
            session_date=attendance_session.session_date,
            max_grade=float(attendance_session.max_grade),
            source_type=attendance_session.source_type,
            created_at=attendance_session.created_at,
        )


class AttendanceRecordRead(BaseModel):
    id: UUID
    session_id: UUID
    student_id: UUID
    student_code: str
    student_name: str
    status: AttendanceStatus
    earned_grade: float
    max_grade: float
    grade_entry_id: UUID | None

    @classmethod
    def from_model(cls, attendance_record: AttendanceRecord) -> "AttendanceRecordRead":
        return cls(
            id=attendance_record.id,
            session_id=attendance_record.attendance_session_id,
            student_id=attendance_record.student_id,
            student_code=attendance_record.student.student_code,
            student_name=attendance_record.student.full_name,
            status=attendance_record.status,
            earned_grade=attendance_grade_for_status(attendance_record.status),
            max_grade=float(attendance_record.attendance_session.max_grade),
            grade_entry_id=attendance_record.grade_entry_id,
        )


class AttendanceSubmissionResultRead(BaseModel):
    created_session_id: UUID
    total_rows: int
    success_count: int
    error_count: int
    errors: list[AttendanceUploadErrorRead]
    session: AttendanceSessionRead
    records: list[AttendanceRecordRead]


def attendance_grade_for_status(status: AttendanceStatus) -> float:
    return {
        AttendanceStatus.present: 1.0,
        AttendanceStatus.late: 0.5,
        AttendanceStatus.absent: 0.0,
    }[status]
