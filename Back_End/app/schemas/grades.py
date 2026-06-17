from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import GradeCategory, GradeSourceType
from app.models.grade import GradeEntry


class CorrectionCreate(BaseModel):
    earned_grade: float
    reason: str = Field(min_length=1, max_length=500)


class GradeEntryRead(BaseModel):
    id: UUID
    student_id: UUID
    student_code: str
    student_name: str
    class_id: UUID
    class_code: str
    teacher_id: UUID | None
    teacher_name: str | None
    category: GradeCategory
    earned_grade: float
    max_grade: float
    source_type: GradeSourceType
    reason: str | None
    related_entry_id: UUID | None
    assignment_submission_id: UUID | None
    created_by_user_id: UUID
    created_at: datetime

    @classmethod
    def from_model(cls, grade_entry: GradeEntry) -> "GradeEntryRead":
        return cls(
            id=grade_entry.id,
            student_id=grade_entry.student_id,
            student_code=grade_entry.student.student_code,
            student_name=grade_entry.student.full_name,
            class_id=grade_entry.class_id,
            class_code=grade_entry.academic_class.code,
            teacher_id=grade_entry.teacher_id,
            teacher_name=grade_entry.teacher.full_name if grade_entry.teacher else None,
            category=grade_entry.category,
            earned_grade=float(grade_entry.earned_grade),
            max_grade=float(grade_entry.max_grade),
            source_type=grade_entry.source_type,
            reason=grade_entry.reason,
            related_entry_id=grade_entry.related_entry_id,
            assignment_submission_id=grade_entry.assignment_submission_id,
            created_by_user_id=grade_entry.created_by_user_id,
            created_at=grade_entry.created_at,
        )


class CorrectionHistoryRead(BaseModel):
    correction_id: UUID
    original_grade_entry_id: UUID
    student_id: UUID
    student_code: str
    student_name: str
    class_id: UUID
    class_code: str
    original_category: GradeCategory
    original_earned_grade: float
    original_max_grade: float
    correction_earned_grade: float
    correction_reason: str
    corrected_by: str
    corrected_at: datetime

    @classmethod
    def from_model(cls, correction: GradeEntry) -> "CorrectionHistoryRead":
        original = correction.related_entry
        return cls(
            correction_id=correction.id,
            original_grade_entry_id=correction.related_entry_id,
            student_id=correction.student_id,
            student_code=correction.student.student_code,
            student_name=correction.student.full_name,
            class_id=correction.class_id,
            class_code=correction.academic_class.code,
            original_category=original.category,
            original_earned_grade=float(original.earned_grade),
            original_max_grade=float(original.max_grade),
            correction_earned_grade=float(correction.earned_grade),
            correction_reason=correction.reason,
            corrected_by=correction.created_by_user.email,
            corrected_at=correction.created_at,
        )
