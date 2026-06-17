from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import ClassStatus, StudentStatus
from app.schemas.progress import StudentProgressRead
from app.schemas.ranking import RankingItemRead


class DashboardClassRead(BaseModel):
    class_id: UUID
    class_code: str
    status: ClassStatus
    role: str | None = None
    student_count: int
    class_progress: float


class TrackSummaryRead(BaseModel):
    track_id: UUID
    code: str
    name: str
    total_classes: int
    active_classes: int
    active_students: int


class ClassSummaryRead(BaseModel):
    class_id: UUID
    class_code: str
    status: ClassStatus
    active_students: int
    class_progress: float


class AdminDashboardRead(BaseModel):
    total_students: int
    active_students: int
    suspended_students: int
    graduated_students: int
    dropped_students: int
    total_teachers: int
    total_classes: int
    active_classes: int
    low_progress_students_count: int
    low_progress_instructors_count: int
    low_progress_mentors_count: int
    unread_notifications_count: int
    tracks_summary: list[TrackSummaryRead]
    classes_summary: list[ClassSummaryRead]


class TeacherDashboardRead(BaseModel):
    teacher_id: UUID
    teacher_name: str
    assigned_classes_count: int
    assigned_classes: list[DashboardClassRead]
    average_instructor_progress: float
    average_mentor_progress: float
    pending_assignments_count: int
    reviewed_assignments_count: int
    late_assignments_count: int
    low_progress_students_count: int
    materials_count: int
    attendance_sessions_count: int
    quizzes_count: int


class ActiveClassRead(BaseModel):
    class_id: UUID
    class_code: str
    status: ClassStatus
    track_id: UUID
    track_name: str
    level_id: UUID
    level_number: int


class AttendanceSummaryRead(BaseModel):
    total_records: int
    present: int
    late: int
    absent: int


class QuizzesSummaryRead(BaseModel):
    total_quizzes: int
    completed_quizzes: int
    average_grade: float


class StudentDashboardRead(BaseModel):
    student_id: UUID
    student_code: str
    student_name: str
    status: StudentStatus
    active_class: ActiveClassRead | None
    progress: StudentProgressRead | None
    ranking_top3: list[RankingItemRead]
    materials_count: int
    assignments_count: int
    submissions_count: int
    attendance_summary: AttendanceSummaryRead
    quizzes_summary: QuizzesSummaryRead
    final_project_status: str | None
