from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.progress import ProgressSnapshot


class StudentProgressRead(BaseModel):
    student_id: UUID
    student_code: str
    student_name: str
    class_id: UUID
    class_code: str
    attendance_progress: float
    quiz_progress: float
    assignment_progress: float
    bonus_progress: float
    final_progress: float


class ClassProgressRead(BaseModel):
    class_id: UUID
    class_code: str
    student_count: int
    class_progress: float
    students: list[StudentProgressRead]


class TeacherProgressClassRead(BaseModel):
    class_id: UUID
    class_code: str
    role: str
    class_progress: float


class TeacherProgressRead(BaseModel):
    teacher_id: UUID
    teacher_name: str
    assigned_classes: list[TeacherProgressClassRead]
    instructor_progress: float
    mentor_progress: float


class ProgressSnapshotRead(BaseModel):
    id: UUID
    student_id: UUID
    student_code: str
    student_name: str
    class_id: UUID
    class_code: str
    week_number: int
    year: int
    attendance_progress: float
    quiz_progress: float
    assignment_progress: float
    bonus_progress: float
    final_progress: float
    created_at: datetime

    @classmethod
    def from_model(cls, snapshot: ProgressSnapshot) -> "ProgressSnapshotRead":
        return cls(
            id=snapshot.id,
            student_id=snapshot.student_id,
            student_code=snapshot.student.student_code,
            student_name=snapshot.student.full_name,
            class_id=snapshot.class_id,
            class_code=snapshot.academic_class.code,
            week_number=snapshot.week_number,
            year=snapshot.year,
            attendance_progress=float(snapshot.attendance_progress),
            quiz_progress=float(snapshot.quiz_progress),
            assignment_progress=float(snapshot.assignment_progress),
            bonus_progress=float(snapshot.bonus_progress),
            final_progress=float(snapshot.final_progress),
            created_at=snapshot.created_at,
        )
