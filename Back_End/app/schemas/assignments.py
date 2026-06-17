from datetime import datetime
from uuid import UUID

from pydantic import AnyUrl, BaseModel, Field

from app.domain.enums import AssignmentSubmissionStatus, GradeCategory
from app.models.assignment import Assignment, AssignmentSubmission


class AssignmentCreate(BaseModel):
    class_id: UUID
    created_by_teacher_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    requirement_url: AnyUrl
    deadline: datetime
    max_grade: float = Field(gt=0)


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    requirement_url: AnyUrl | None = None
    deadline: datetime | None = None
    max_grade: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class AssignmentRead(BaseModel):
    id: UUID
    class_id: UUID
    class_code: str
    created_by_teacher_id: UUID
    created_by_teacher_name: str
    title: str
    description: str | None
    requirement_url: str
    deadline: datetime
    max_grade: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, assignment: Assignment) -> "AssignmentRead":
        return cls(
            id=assignment.id,
            class_id=assignment.class_id,
            class_code=assignment.academic_class.code,
            created_by_teacher_id=assignment.created_by_teacher_id,
            created_by_teacher_name=assignment.created_by_teacher.full_name,
            title=assignment.title,
            description=assignment.description,
            requirement_url=assignment.requirement_url,
            deadline=assignment.deadline,
            max_grade=float(assignment.max_grade),
            is_active=assignment.is_active,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
        )


class SubmissionCreate(BaseModel):
    submission_url: AnyUrl


class SubmissionReview(BaseModel):
    grade: float = Field(ge=0)
    feedback: str | None = None


class SubmissionReject(BaseModel):
    feedback: str | None = None
    reviewed_by_teacher_id: UUID | None = None


class AdminSubmissionReview(SubmissionReview):
    reviewed_by_teacher_id: UUID | None = None


class SubmissionRead(BaseModel):
    id: UUID
    assignment_id: UUID
    assignment_title: str
    student_id: UUID
    student_code: str
    student_full_name: str
    class_id: UUID
    class_code: str
    submission_url: str
    submitted_at: datetime
    grade: float | None
    feedback: str | None
    status: AssignmentSubmissionStatus
    reviewed_at: datetime | None
    reviewed_by_teacher: str | None
    grade_entry_id: UUID | None

    @classmethod
    def from_model(cls, submission: AssignmentSubmission) -> "SubmissionRead":
        return cls(
            id=submission.id,
            assignment_id=submission.assignment_id,
            assignment_title=submission.assignment.title,
            student_id=submission.student_id,
            student_code=submission.student.student_code,
            student_full_name=submission.student.full_name,
            class_id=submission.assignment.class_id,
            class_code=submission.assignment.academic_class.code,
            submission_url=submission.submission_url,
            submitted_at=submission.submitted_at,
            grade=float(submission.grade) if submission.grade is not None else None,
            feedback=submission.feedback,
            status=submission.status,
            reviewed_at=submission.reviewed_at,
            reviewed_by_teacher=submission.reviewed_by_teacher.full_name if submission.reviewed_by_teacher else None,
            grade_entry_id=_assignment_grade_entry_id(submission),
        )


class PendingSubmissionRead(BaseModel):
    submission_id: UUID
    student_id: UUID
    student_code: str
    student_full_name: str
    student_email: str
    class_id: UUID
    class_code: str
    branch_name: str
    assignment_id: UUID
    assignment_title: str
    requirement_url: str
    submission_url: str
    assignment_max_grade: float
    submitted_at: datetime
    status: AssignmentSubmissionStatus
    current_student_progress: None = None

    @classmethod
    def from_model(cls, submission: AssignmentSubmission) -> "PendingSubmissionRead":
        assignment = submission.assignment
        return cls(
            submission_id=submission.id,
            student_id=submission.student_id,
            student_code=submission.student.student_code,
            student_full_name=submission.student.full_name,
            student_email=submission.student.user.email,
            class_id=assignment.class_id,
            class_code=assignment.academic_class.code,
            branch_name=assignment.academic_class.branch.name,
            assignment_id=assignment.id,
            assignment_title=assignment.title,
            requirement_url=assignment.requirement_url,
            submission_url=submission.submission_url,
            assignment_max_grade=float(assignment.max_grade),
            submitted_at=submission.submitted_at,
            status=submission.status,
        )


class ReviewedSubmissionRead(BaseModel):
    submission_id: UUID
    student_name: str
    student_code: str
    class_code: str
    assignment_title: str
    grade: float
    assignment_max_grade: float
    feedback: str | None
    reviewed_at: datetime
    reviewed_by_teacher: str
    grade_entry_id: UUID | None

    @classmethod
    def from_model(cls, submission: AssignmentSubmission) -> "ReviewedSubmissionRead":
        return cls(
            submission_id=submission.id,
            student_name=submission.student.full_name,
            student_code=submission.student.student_code,
            class_code=submission.assignment.academic_class.code,
            assignment_title=submission.assignment.title,
            grade=float(submission.grade),
            assignment_max_grade=float(submission.assignment.max_grade),
            feedback=submission.feedback,
            reviewed_at=submission.reviewed_at,
            reviewed_by_teacher=submission.reviewed_by_teacher.full_name,
            grade_entry_id=_assignment_grade_entry_id(submission),
        )


def _assignment_grade_entry_id(submission: AssignmentSubmission) -> UUID | None:
    direct_grade_entry_id = getattr(submission, "grade_entry_id", None)
    if direct_grade_entry_id is not None:
        return direct_grade_entry_id
    for grade_entry in getattr(submission, "grade_entries", []):
        if (
            grade_entry.deleted_at is None
            and grade_entry.category == GradeCategory.assignment
            and grade_entry.assignment_submission_id == submission.id
        ):
            return grade_entry.id
    return None
