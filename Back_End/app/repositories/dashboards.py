from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ClassStatus, EnrollmentStatus, StudentStatus
from app.models.academic import Class, Track
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.attendance import AttendanceRecord, AttendanceSession
from app.models.enrollment import ClassEnrollment
from app.models.material import Material
from app.models.notification import Notification
from app.models.profiles import StudentProfile, TeacherProfile
from app.models.quiz import Quiz, QuizResult
from app.models.user import User


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def count_students(self, status: StudentStatus | None = None) -> int:
        statement = select(func.count(StudentProfile.id)).join(StudentProfile.user).where(User.deleted_at.is_(None))
        if status is not None:
            statement = statement.where(StudentProfile.status == status)
        return int(await self.session.scalar(statement) or 0)

    async def count_teachers(self) -> int:
        return int(
            await self.session.scalar(
                select(func.count(TeacherProfile.id)).join(TeacherProfile.user).where(User.deleted_at.is_(None))
            )
            or 0
        )

    async def count_classes(self, status: ClassStatus | None = None) -> int:
        statement = select(func.count(Class.id)).where(Class.deleted_at.is_(None))
        if status is not None:
            statement = statement.where(Class.status == status)
        return int(await self.session.scalar(statement) or 0)

    async def count_unread_notifications(self) -> int:
        return int(
            await self.session.scalar(
                select(func.count(Notification.id)).where(
                    Notification.is_read.is_(False),
                    Notification.deleted_at.is_(None),
                )
            )
            or 0
        )

    async def list_tracks(self) -> list[Track]:
        result = await self.session.scalars(select(Track).where(Track.deleted_at.is_(None)).order_by(Track.track_number))
        return list(result.all())

    async def list_classes_for_track(self, track_id: UUID) -> list[Class]:
        result = await self.session.scalars(
            select(Class).where(Class.track_id == track_id, Class.deleted_at.is_(None)).order_by(Class.code)
        )
        return list(result.all())

    async def count_active_enrollments_for_class(self, class_id: UUID) -> int:
        return int(
            await self.session.scalar(
                select(func.count(ClassEnrollment.id)).where(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.status == EnrollmentStatus.active,
                    ClassEnrollment.deleted_at.is_(None),
                )
            )
            or 0
        )

    async def count_materials_for_classes(self, class_ids: list[UUID], active_only: bool = False) -> int:
        if not class_ids:
            return 0
        statement = select(func.count(Material.id)).where(Material.class_id.in_(class_ids), Material.deleted_at.is_(None))
        if active_only:
            statement = statement.where(Material.is_active.is_(True))
        return int(await self.session.scalar(statement) or 0)

    async def count_assignments_for_classes(self, class_ids: list[UUID], active_only: bool = False) -> int:
        if not class_ids:
            return 0
        statement = select(func.count(Assignment.id)).where(Assignment.class_id.in_(class_ids), Assignment.deleted_at.is_(None))
        if active_only:
            statement = statement.where(Assignment.is_active.is_(True))
        return int(await self.session.scalar(statement) or 0)

    async def count_submissions_for_student(self, student_id: UUID) -> int:
        return int(
            await self.session.scalar(
                select(func.count(AssignmentSubmission.id)).where(
                    AssignmentSubmission.student_id == student_id,
                    AssignmentSubmission.deleted_at.is_(None),
                )
            )
            or 0
        )

    async def count_attendance_sessions_for_classes(self, class_ids: list[UUID]) -> int:
        if not class_ids:
            return 0
        return int(
            await self.session.scalar(
                select(func.count(AttendanceSession.id)).where(
                    AttendanceSession.class_id.in_(class_ids),
                    AttendanceSession.deleted_at.is_(None),
                )
            )
            or 0
        )

    async def list_attendance_records_for_student_class(self, student_id: UUID, class_id: UUID) -> list[AttendanceRecord]:
        result = await self.session.scalars(
            select(AttendanceRecord)
            .join(AttendanceRecord.attendance_session)
            .where(
                AttendanceRecord.student_id == student_id,
                AttendanceSession.class_id == class_id,
                AttendanceRecord.deleted_at.is_(None),
                AttendanceSession.deleted_at.is_(None),
            )
        )
        return list(result.all())

    async def count_quizzes_for_classes(self, class_ids: list[UUID]) -> int:
        if not class_ids:
            return 0
        return int(
            await self.session.scalar(
                select(func.count(Quiz.id)).where(Quiz.class_id.in_(class_ids), Quiz.deleted_at.is_(None))
            )
            or 0
        )

    async def list_quiz_results_for_student_class(self, student_id: UUID, class_id: UUID) -> list[QuizResult]:
        result = await self.session.scalars(
            select(QuizResult)
            .join(QuizResult.quiz)
            .where(
                QuizResult.student_id == student_id,
                Quiz.class_id == class_id,
                QuizResult.deleted_at.is_(None),
                Quiz.deleted_at.is_(None),
            )
        )
        return list(result.all())
