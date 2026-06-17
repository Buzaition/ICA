from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import UserRole
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.enrollments import EnrollmentRepository
from app.schemas.progress import StudentProgressRead
from app.schemas.ranking import RankingItemRead
from app.services.progress import ProgressService


class RankingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.enrollments = EnrollmentRepository(session)
        self.progress = ProgressService(session)

    async def get_student_top3(self, actor: User) -> list[RankingItemRead]:
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        enrollment = await self.enrollments.get_active_for_student(actor.student_profile.id)
        if enrollment is None:
            raise AppException("Active class not found", HTTPStatus.NOT_FOUND)
        ranking = await self._ranking_for_class(enrollment.academic_class)
        return ranking[:3]

    async def get_teacher_class_ranking(self, class_id: UUID, actor: User) -> list[RankingItemRead]:
        academic_class = await self._require_class(class_id)
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self._ranking_for_class(academic_class)

    async def get_admin_class_ranking(self, class_id: UUID, actor: User) -> list[RankingItemRead]:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        academic_class = await self._require_class(class_id)
        return await self._ranking_for_class(academic_class)

    async def get_admin_track_ranking(self, track_id: UUID, actor: User) -> list[RankingItemRead]:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        track = await self.academic.get_track(track_id)
        if track is None:
            raise AppException("Track not found", HTTPStatus.NOT_FOUND)
        classes = await self.academic.list_active_classes_for_track(track_id)
        students: list[StudentProgressRead] = []
        for academic_class in classes:
            class_progress = await self.progress._class_progress(academic_class)
            students.extend(class_progress.students)
        return self._rank_students(students)

    async def _ranking_for_class(self, academic_class) -> list[RankingItemRead]:
        class_progress = await self.progress._class_progress(academic_class)
        return self._rank_students(class_progress.students)

    async def _require_class(self, class_id: UUID):
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        return academic_class

    def _rank_students(self, students: list[StudentProgressRead]) -> list[RankingItemRead]:
        sorted_students = sorted(students, key=lambda item: (-item.final_progress, item.student_code))
        ranked: list[RankingItemRead] = []
        last_progress: float | None = None
        current_rank = 0
        for student in sorted_students:
            if last_progress is None or student.final_progress != last_progress:
                current_rank += 1
                last_progress = student.final_progress
            ranked.append(RankingItemRead.from_progress(current_rank, student))
        return ranked
