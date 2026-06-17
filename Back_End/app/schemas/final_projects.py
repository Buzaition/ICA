from datetime import datetime
from uuid import UUID

from pydantic import AnyUrl, BaseModel, Field

from app.domain.enums import FinalProjectStatus
from app.models.final_project import FinalProject


class FinalProjectSubmit(BaseModel):
    project_link: AnyUrl


class FinalProjectReview(BaseModel):
    status: FinalProjectStatus
    grade: float | None = Field(default=None, ge=0)
    feedback: str | None = None


class FinalProjectRead(BaseModel):
    final_project_id: UUID
    student_id: UUID
    student_code: str
    student_name: str
    class_id: UUID
    class_code: str
    level_id: UUID
    level_number: int
    project_link: str
    grade: float | None
    feedback: str | None
    status: FinalProjectStatus
    submitted_at: datetime
    reviewed_at: datetime | None
    reviewed_by_admin: str | None

    @classmethod
    def from_model(cls, final_project: FinalProject) -> "FinalProjectRead":
        return cls(
            final_project_id=final_project.id,
            student_id=final_project.student_id,
            student_code=final_project.student.student_code,
            student_name=final_project.student.full_name,
            class_id=final_project.class_id,
            class_code=final_project.academic_class.code,
            level_id=final_project.level_id,
            level_number=final_project.level.level_number,
            project_link=final_project.project_link,
            grade=float(final_project.grade) if final_project.grade is not None else None,
            feedback=final_project.feedback,
            status=final_project.status,
            submitted_at=final_project.submitted_at,
            reviewed_at=final_project.reviewed_at,
            reviewed_by_admin=final_project.reviewed_by_admin.full_name if final_project.reviewed_by_admin else None,
        )
