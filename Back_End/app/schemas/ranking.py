from uuid import UUID

from pydantic import BaseModel

from app.schemas.progress import StudentProgressRead


class RankingItemRead(BaseModel):
    rank: int
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

    @classmethod
    def from_progress(cls, rank: int, progress: StudentProgressRead) -> "RankingItemRead":
        return cls(
            rank=rank,
            student_id=progress.student_id,
            student_code=progress.student_code,
            student_name=progress.student_name,
            class_id=progress.class_id,
            class_code=progress.class_code,
            attendance_progress=progress.attendance_progress,
            quiz_progress=progress.quiz_progress,
            assignment_progress=progress.assignment_progress,
            bonus_progress=progress.bonus_progress,
            final_progress=progress.final_progress,
        )
