from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.grade import GradeEntry


class BonusCreate(BaseModel):
    student_id: UUID
    class_id: UUID
    reason: str | None = Field(default=None, min_length=1, max_length=500)


class BonusRead(BaseModel):
    grade_entry_id: UUID
    student_id: UUID
    student_code: str
    student_name: str
    class_id: UUID
    class_code: str
    earned_grade: float
    max_grade: float
    reason: str
    weekly_bonus_count: int
    weekly_bonus_remaining: int
    created_at: datetime

    @classmethod
    def from_model(cls, grade_entry: GradeEntry, weekly_bonus_count: int, weekly_bonus_remaining: int) -> "BonusRead":
        return cls(
            grade_entry_id=grade_entry.id,
            student_id=grade_entry.student_id,
            student_code=grade_entry.student.student_code,
            student_name=grade_entry.student.full_name,
            class_id=grade_entry.class_id,
            class_code=grade_entry.academic_class.code,
            earned_grade=float(grade_entry.earned_grade),
            max_grade=float(grade_entry.max_grade),
            reason=grade_entry.reason or "Bonus",
            weekly_bonus_count=weekly_bonus_count,
            weekly_bonus_remaining=weekly_bonus_remaining,
            created_at=grade_entry.created_at,
        )
