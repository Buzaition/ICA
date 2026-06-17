from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import EnrollmentStatus, StudentStatus
from app.models.enrollment import ClassEnrollment


class EnrollmentCreate(BaseModel):
    student_id: UUID
    class_id: UUID


class EnrollmentRead(BaseModel):
    id: UUID
    student_id: UUID
    student_code: str
    student_full_name: str
    class_id: UUID
    class_code: str
    track_name: str
    level_number: int
    branch_name: str
    cycle_name: str
    status: EnrollmentStatus
    enrolled_at: datetime

    @classmethod
    def from_model(cls, enrollment: ClassEnrollment) -> "EnrollmentRead":
        academic_class = enrollment.academic_class
        return cls(
            id=enrollment.id,
            student_id=enrollment.student_id,
            student_code=enrollment.student.student_code,
            student_full_name=enrollment.student.full_name,
            class_id=enrollment.class_id,
            class_code=academic_class.code,
            track_name=academic_class.track.name,
            level_number=academic_class.level.level_number,
            branch_name=academic_class.branch.name,
            cycle_name=academic_class.cycle.name,
            status=enrollment.status,
            enrolled_at=enrollment.enrolled_at,
        )


class TeacherClassStudentRead(BaseModel):
    student_id: UUID
    student_code: str
    student_full_name: str
    student_email: str
    student_status: StudentStatus
    class_code: str
    enrolled_at: datetime

    @classmethod
    def from_model(cls, enrollment: ClassEnrollment) -> "TeacherClassStudentRead":
        return cls(
            student_id=enrollment.student_id,
            student_code=enrollment.student.student_code,
            student_full_name=enrollment.student.full_name,
            student_email=enrollment.student.user.email,
            student_status=enrollment.student.status,
            class_code=enrollment.academic_class.code,
            enrolled_at=enrollment.enrolled_at,
        )
