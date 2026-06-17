from http import HTTPStatus
from statistics import mean

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import AttendanceStatus, ClassStatus, StudentStatus, UserRole
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.assignments import AssignmentRepository
from app.repositories.dashboards import DashboardRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.final_projects import FinalProjectRepository
from app.repositories.materials import MaterialRepository
from app.schemas.dashboards import (
    ActiveClassRead,
    AdminDashboardRead,
    AttendanceSummaryRead,
    ClassSummaryRead,
    DashboardClassRead,
    QuizzesSummaryRead,
    StudentDashboardRead,
    TeacherDashboardRead,
    TrackSummaryRead,
)
from app.services.progress import ProgressService
from app.services.ranking import RankingService


class DashboardService:
    STUDENT_LOW_PROGRESS_THRESHOLD = 50
    INSTRUCTOR_LOW_PROGRESS_THRESHOLD = 50
    MENTOR_LOW_PROGRESS_THRESHOLD = 70

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.assignments = AssignmentRepository(session)
        self.dashboards = DashboardRepository(session)
        self.enrollments = EnrollmentRepository(session)
        self.final_projects = FinalProjectRepository(session)
        self.materials = MaterialRepository(session)
        self.progress = ProgressService(session)
        self.ranking = RankingService(session)

    async def get_admin_dashboard(self, actor: User) -> AdminDashboardRead:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        classes = await self.academic.list_classes()
        class_progress_items = []
        low_progress_students_count = 0
        low_progress_instructors_count = 0
        low_progress_mentors_count = 0
        teacher_role_class_pairs = set()
        classes_summary: list[ClassSummaryRead] = []
        for academic_class in classes:
            class_progress = await self.progress.get_class_progress_for_user(academic_class.id, actor)
            class_progress_items.append((academic_class, class_progress))
            low_progress_students_count += sum(
                1 for student in class_progress.students if student.final_progress < self.STUDENT_LOW_PROGRESS_THRESHOLD
            )
            classes_summary.append(
                ClassSummaryRead(
                    class_id=academic_class.id,
                    class_code=academic_class.code,
                    status=academic_class.status,
                    active_students=class_progress.student_count,
                    class_progress=class_progress.class_progress,
                )
            )
            if class_progress.class_progress < self.INSTRUCTOR_LOW_PROGRESS_THRESHOLD:
                teacher_role_class_pairs.add(("instructor", academic_class.instructor_id, academic_class.id))
            mentor_progress = 50 + (class_progress.class_progress / 2)
            if mentor_progress < self.MENTOR_LOW_PROGRESS_THRESHOLD:
                teacher_role_class_pairs.add(("mentor", academic_class.mentor_id, academic_class.id))
        low_progress_instructors_count = sum(1 for role, _, _ in teacher_role_class_pairs if role == "instructor")
        low_progress_mentors_count = sum(1 for role, _, _ in teacher_role_class_pairs if role == "mentor")
        tracks_summary = await self._tracks_summary(actor)
        return AdminDashboardRead(
            total_students=await self.dashboards.count_students(),
            active_students=await self.dashboards.count_students(StudentStatus.active),
            suspended_students=await self.dashboards.count_students(StudentStatus.suspended),
            graduated_students=await self.dashboards.count_students(StudentStatus.graduated),
            dropped_students=await self.dashboards.count_students(StudentStatus.dropped),
            total_teachers=await self.dashboards.count_teachers(),
            total_classes=await self.dashboards.count_classes(),
            active_classes=await self.dashboards.count_classes(ClassStatus.active),
            low_progress_students_count=low_progress_students_count,
            low_progress_instructors_count=low_progress_instructors_count,
            low_progress_mentors_count=low_progress_mentors_count,
            unread_notifications_count=await self.dashboards.count_unread_notifications(),
            tracks_summary=tracks_summary,
            classes_summary=classes_summary,
        )

    async def get_teacher_dashboard(self, actor: User) -> TeacherDashboardRead:
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        classes = await self.academic.list_classes_for_teacher(actor.teacher_profile.id)
        class_ids = [academic_class.id for academic_class in classes]
        assigned_classes: list[DashboardClassRead] = []
        instructor_values: list[float] = []
        mentor_values: list[float] = []
        low_progress_students_count = 0
        for academic_class in classes:
            class_progress = await self.progress.get_class_progress_for_user(academic_class.id, actor)
            low_progress_students_count += sum(
                1 for student in class_progress.students if student.final_progress < self.STUDENT_LOW_PROGRESS_THRESHOLD
            )
            if academic_class.instructor_id == actor.teacher_profile.id:
                instructor_values.append(class_progress.class_progress)
                assigned_classes.append(
                    self._dashboard_class(academic_class, class_progress.student_count, class_progress.class_progress, "instructor")
                )
            if academic_class.mentor_id == actor.teacher_profile.id:
                mentor_values.append(50 + (class_progress.class_progress / 2))
                assigned_classes.append(
                    self._dashboard_class(academic_class, class_progress.student_count, class_progress.class_progress, "mentor")
                )
        pending = await self.assignments.list_pending_for_teacher(actor.teacher_profile.id)
        reviewed = await self.assignments.list_reviewed_for_teacher(actor.teacher_profile.id)
        late = await self.assignments.list_late_for_teacher(actor.teacher_profile.id)
        return TeacherDashboardRead(
            teacher_id=actor.teacher_profile.id,
            teacher_name=actor.teacher_profile.full_name,
            assigned_classes_count=len(classes),
            assigned_classes=assigned_classes,
            average_instructor_progress=round(mean(instructor_values), 2) if instructor_values else 0,
            average_mentor_progress=round(mean(mentor_values), 2) if mentor_values else 0,
            pending_assignments_count=len(pending),
            reviewed_assignments_count=len(reviewed),
            late_assignments_count=len(late),
            low_progress_students_count=low_progress_students_count,
            materials_count=await self.dashboards.count_materials_for_classes(class_ids),
            attendance_sessions_count=await self.dashboards.count_attendance_sessions_for_classes(class_ids),
            quizzes_count=await self.dashboards.count_quizzes_for_classes(class_ids),
        )

    async def get_student_dashboard(self, actor: User) -> StudentDashboardRead:
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        enrollment = await self.enrollments.get_active_for_student(actor.student_profile.id)
        if enrollment is None:
            return StudentDashboardRead(
                student_id=actor.student_profile.id,
                student_code=actor.student_profile.student_code,
                student_name=actor.student_profile.full_name,
                status=actor.student_profile.status,
                active_class=None,
                progress=None,
                ranking_top3=[],
                materials_count=0,
                assignments_count=0,
                submissions_count=await self.dashboards.count_submissions_for_student(actor.student_profile.id),
                attendance_summary=AttendanceSummaryRead(total_records=0, present=0, late=0, absent=0),
                quizzes_summary=QuizzesSummaryRead(total_quizzes=0, completed_quizzes=0, average_grade=0),
                final_project_status=None,
            )
        academic_class = enrollment.academic_class
        progress = await self.progress.get_student_own_progress(actor)
        ranking_top3 = await self.ranking.get_student_top3(actor)
        final_project = await self.final_projects.get_for_student_active_class(actor.student_profile.id, academic_class.id)
        quiz_results = await self.dashboards.list_quiz_results_for_student_class(actor.student_profile.id, academic_class.id)
        attendance_records = await self.dashboards.list_attendance_records_for_student_class(
            actor.student_profile.id,
            academic_class.id,
        )
        return StudentDashboardRead(
            student_id=actor.student_profile.id,
            student_code=actor.student_profile.student_code,
            student_name=actor.student_profile.full_name,
            status=actor.student_profile.status,
            active_class=ActiveClassRead(
                class_id=academic_class.id,
                class_code=academic_class.code,
                status=academic_class.status,
                track_id=academic_class.track_id,
                track_name=academic_class.track.name,
                level_id=academic_class.level_id,
                level_number=academic_class.level.level_number,
            ),
            progress=progress,
            ranking_top3=ranking_top3,
            materials_count=await self.dashboards.count_materials_for_classes([academic_class.id], active_only=True),
            assignments_count=await self.dashboards.count_assignments_for_classes([academic_class.id], active_only=True),
            submissions_count=await self.dashboards.count_submissions_for_student(actor.student_profile.id),
            attendance_summary=self._attendance_summary(attendance_records),
            quizzes_summary=await self._quizzes_summary(quiz_results, academic_class.id),
            final_project_status=final_project.status.value if final_project else None,
        )

    async def _tracks_summary(self, actor: User) -> list[TrackSummaryRead]:
        tracks = await self.dashboards.list_tracks()
        summary = []
        for track in tracks:
            classes = await self.dashboards.list_classes_for_track(track.id)
            active_classes = [academic_class for academic_class in classes if academic_class.status == ClassStatus.active]
            active_students = 0
            for academic_class in active_classes:
                class_progress = await self.progress.get_class_progress_for_user(academic_class.id, actor)
                active_students += class_progress.student_count
            summary.append(
                TrackSummaryRead(
                    track_id=track.id,
                    code=track.code,
                    name=track.name,
                    total_classes=len(classes),
                    active_classes=len(active_classes),
                    active_students=active_students,
                )
            )
        return summary

    def _dashboard_class(self, academic_class, student_count: int, class_progress: float, role: str) -> DashboardClassRead:
        return DashboardClassRead(
            class_id=academic_class.id,
            class_code=academic_class.code,
            status=academic_class.status,
            role=role,
            student_count=student_count,
            class_progress=class_progress,
        )

    def _attendance_summary(self, records) -> AttendanceSummaryRead:
        return AttendanceSummaryRead(
            total_records=len(records),
            present=sum(1 for record in records if record.status == AttendanceStatus.present),
            late=sum(1 for record in records if record.status == AttendanceStatus.late),
            absent=sum(1 for record in records if record.status == AttendanceStatus.absent),
        )

    async def _quizzes_summary(self, results, class_id) -> QuizzesSummaryRead:
        total_quizzes = await self.dashboards.count_quizzes_for_classes([class_id])
        percentages = [
            (float(result.earned_grade) / float(result.max_grade)) * 100
            for result in results
            if float(result.max_grade) > 0
        ]
        return QuizzesSummaryRead(
            total_quizzes=total_quizzes,
            completed_quizzes=len(results),
            average_grade=round(mean(percentages), 2) if percentages else 0,
        )
