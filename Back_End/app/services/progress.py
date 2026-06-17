from datetime import UTC, datetime
from http import HTTPStatus
from statistics import mean
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import GradeCategory, StudentStatus, UserRole
from app.models.progress import ProgressSnapshot
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.progress import ProgressRepository
from app.schemas.progress import (
    ClassProgressRead,
    StudentProgressRead,
    TeacherProgressClassRead,
    TeacherProgressRead,
)


class ProgressService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.enrollments = EnrollmentRepository(session)
        self.progress = ProgressRepository(session)

    async def get_student_own_progress(self, actor: User) -> StudentProgressRead:
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        enrollment = await self.enrollments.get_active_for_student(actor.student_profile.id)
        if enrollment is None:
            raise AppException("Active class not found", HTTPStatus.NOT_FOUND)
        return await self._student_progress(actor.student_profile, enrollment.academic_class)

    async def get_student_progress_admin(self, student_id: UUID, actor: User) -> StudentProgressRead:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        student = await self.enrollments.get_student_profile(student_id)
        if student is None:
            raise AppException("Student profile not found", HTTPStatus.NOT_FOUND)
        enrollment = await self.enrollments.get_active_for_student(student_id)
        if enrollment is None:
            raise AppException("Active class not found", HTTPStatus.NOT_FOUND)
        return await self._student_progress(student, enrollment.academic_class)

    async def get_class_progress_for_user(self, class_id: UUID, actor: User) -> ClassProgressRead:
        academic_class = await self._require_class(class_id)
        if actor.role == UserRole.teacher:
            self._require_teacher_assigned(actor, academic_class)
        elif actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self._class_progress(academic_class)

    async def get_teacher_progress(self, teacher_id: UUID, actor: User) -> TeacherProgressRead:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        teacher = await self.academic.get_teacher_profile(teacher_id)
        if teacher is None:
            raise AppException("Teacher profile not found", HTTPStatus.NOT_FOUND)
        classes = await self.academic.list_classes_for_teacher(teacher_id)
        assigned: list[TeacherProgressClassRead] = []
        instructor_values: list[float] = []
        mentor_values: list[float] = []
        for academic_class in classes:
            class_progress = await self._class_progress(academic_class)
            if academic_class.instructor_id == teacher_id:
                instructor_values.append(class_progress.class_progress)
                assigned.append(
                    TeacherProgressClassRead(
                        class_id=academic_class.id,
                        class_code=academic_class.code,
                        role="instructor",
                        class_progress=class_progress.class_progress,
                    )
                )
            if academic_class.mentor_id == teacher_id:
                mentor_value = 50 + (class_progress.class_progress / 2)
                mentor_values.append(mentor_value)
                assigned.append(
                    TeacherProgressClassRead(
                        class_id=academic_class.id,
                        class_code=academic_class.code,
                        role="mentor",
                        class_progress=class_progress.class_progress,
                    )
                )
        return TeacherProgressRead(
            teacher_id=teacher.id,
            teacher_name=teacher.full_name,
            assigned_classes=assigned,
            instructor_progress=round(mean(instructor_values), 2) if instructor_values else 0,
            mentor_progress=round(mean(mentor_values), 2) if mentor_values else 0,
        )

    async def create_snapshots_for_class(self, class_id: UUID, actor: User) -> list[ProgressSnapshot]:
        academic_class = await self._require_class(class_id)
        if actor.role == UserRole.teacher:
            self._require_teacher_assigned(actor, academic_class)
        elif actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        class_progress = await self._class_progress(academic_class)
        now = datetime.now(UTC)
        iso_year, iso_week, _ = now.isocalendar()
        snapshots: list[ProgressSnapshot] = []
        for student_progress in class_progress.students:
            snapshot = ProgressSnapshot(
                student_id=student_progress.student_id,
                class_id=student_progress.class_id,
                week_number=iso_week,
                year=iso_year,
                attendance_progress=student_progress.attendance_progress,
                quiz_progress=student_progress.quiz_progress,
                assignment_progress=student_progress.assignment_progress,
                bonus_progress=student_progress.bonus_progress,
                final_progress=student_progress.final_progress,
            )
            await self.progress.add_snapshot(snapshot)
            snapshots.append(snapshot)
        await self.audit_logs.add(
            actor.id,
            "create_progress_snapshots",
            "class",
            academic_class.id,
            new_value={"snapshot_count": len(snapshots), "week_number": iso_week, "year": iso_year},
        )
        await self.session.commit()
        return await self.progress.list_snapshots_for_class(class_id)

    async def list_snapshots_for_class(self, class_id: UUID, actor: User) -> list[ProgressSnapshot]:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        await self._require_class(class_id)
        return await self.progress.list_snapshots_for_class(class_id)

    async def _class_progress(self, academic_class) -> ClassProgressRead:
        enrollments = await self.progress.list_active_enrollments_for_class(academic_class.id)
        students = [
            await self._student_progress(enrollment.student, academic_class)
            for enrollment in enrollments
            if enrollment.student.status == StudentStatus.active
        ]
        class_progress = round(mean([student.final_progress for student in students]), 2) if students else 0
        return ClassProgressRead(
            class_id=academic_class.id,
            class_code=academic_class.code,
            student_count=len(students),
            class_progress=class_progress,
            students=students,
        )

    async def _student_progress(self, student, academic_class) -> StudentProgressRead:
        entries = await self.progress.list_grade_entries_for_student_class(student.id, academic_class.id)
        totals = {
            GradeCategory.attendance: {"earned": 0.0, "max": 0.0},
            GradeCategory.quiz: {"earned": 0.0, "max": 0.0},
            GradeCategory.assignment: {"earned": 0.0, "max": 0.0},
        }
        bonus_progress = 0.0
        for entry in entries:
            earned = float(entry.earned_grade)
            max_grade = float(entry.max_grade)
            if entry.category == GradeCategory.bonus:
                bonus_progress += earned
            elif entry.category in totals:
                totals[entry.category]["earned"] += earned
                totals[entry.category]["max"] += max_grade
            elif entry.category == GradeCategory.correction and entry.related_entry is not None:
                original_category = entry.related_entry.category
                if original_category == GradeCategory.bonus:
                    bonus_progress += earned
                elif original_category in totals:
                    totals[original_category]["earned"] += earned
        attendance_progress = self._weighted(totals[GradeCategory.attendance], 20)
        quiz_progress = self._weighted(totals[GradeCategory.quiz], 30)
        assignment_progress = self._weighted(totals[GradeCategory.assignment], 50)
        final_progress = min(100, attendance_progress + quiz_progress + assignment_progress + bonus_progress)
        return StudentProgressRead(
            student_id=student.id,
            student_code=student.student_code,
            student_name=student.full_name,
            class_id=academic_class.id,
            class_code=academic_class.code,
            attendance_progress=round(attendance_progress, 2),
            quiz_progress=round(quiz_progress, 2),
            assignment_progress=round(assignment_progress, 2),
            bonus_progress=round(bonus_progress, 2),
            final_progress=round(final_progress, 2),
        )

    def _weighted(self, values: dict[str, float], weight: float) -> float:
        if values["max"] <= 0:
            return 0
        return (values["earned"] / values["max"]) * weight

    async def _require_class(self, class_id: UUID):
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        return academic_class

    def _require_teacher_assigned(self, actor: User, academic_class) -> None:
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
