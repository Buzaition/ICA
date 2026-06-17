from datetime import date
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.academic import Class as AcademicClass
from app.models.attendance import AttendanceRecord, AttendanceSession
from app.models.profiles import StudentProfile


class AttendanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_session(self, attendance_session: AttendanceSession) -> AttendanceSession:
        self.session.add(attendance_session)
        await self.session.flush()
        await self.session.refresh(attendance_session)
        return attendance_session

    async def add_record(self, attendance_record: AttendanceRecord) -> AttendanceRecord:
        self.session.add(attendance_record)
        await self.session.flush()
        await self.session.refresh(attendance_record)
        return attendance_record

    async def get_session_by_identity(
        self,
        class_id: UUID,
        teacher_id: UUID,
        session_type,
        session_date: date,
    ) -> AttendanceSession | None:
        return await self.session.scalar(
            self._session_query().where(
                AttendanceSession.class_id == class_id,
                AttendanceSession.teacher_id == teacher_id,
                AttendanceSession.session_type == session_type,
                AttendanceSession.session_date == session_date,
                AttendanceSession.deleted_at.is_(None),
            )
        )

    async def get_session_by_id(self, session_id: UUID, include_deleted: bool = False) -> AttendanceSession | None:
        statement = self._session_query().where(AttendanceSession.id == session_id)
        if not include_deleted:
            statement = statement.where(AttendanceSession.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_sessions(self) -> list[AttendanceSession]:
        result = await self.session.scalars(
            self._session_query().where(AttendanceSession.deleted_at.is_(None)).order_by(AttendanceSession.session_date.desc())
        )
        return list(result.all())

    async def list_sessions_for_class(self, class_id: UUID) -> list[AttendanceSession]:
        result = await self.session.scalars(
            self._session_query()
            .where(AttendanceSession.class_id == class_id, AttendanceSession.deleted_at.is_(None))
            .order_by(AttendanceSession.session_date.desc())
        )
        return list(result.all())

    async def list_sessions_for_teacher(self, teacher_profile_id: UUID) -> list[AttendanceSession]:
        result = await self.session.scalars(
            self._session_query()
            .join(AttendanceSession.academic_class)
            .where(
                AttendanceSession.deleted_at.is_(None),
                or_(AcademicClass.instructor_id == teacher_profile_id, AcademicClass.mentor_id == teacher_profile_id),
            )
            .order_by(AttendanceSession.session_date.desc())
        )
        return list(result.all())

    async def get_record_by_id(self, record_id: UUID, include_deleted: bool = False) -> AttendanceRecord | None:
        statement = self._record_query().where(AttendanceRecord.id == record_id)
        if not include_deleted:
            statement = statement.where(AttendanceRecord.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_record_for_session_student(self, session_id: UUID, student_id: UUID) -> AttendanceRecord | None:
        return await self.session.scalar(
            self._record_query().where(
                AttendanceRecord.attendance_session_id == session_id,
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.deleted_at.is_(None),
            )
        )

    async def list_records_for_session(self, session_id: UUID) -> list[AttendanceRecord]:
        result = await self.session.scalars(
            self._record_query()
            .where(AttendanceRecord.attendance_session_id == session_id, AttendanceRecord.deleted_at.is_(None))
            .order_by(AttendanceRecord.created_at)
        )
        return list(result.all())

    async def list_records_for_student(self, student_id: UUID) -> list[AttendanceRecord]:
        result = await self.session.scalars(
            self._record_query()
            .join(AttendanceRecord.attendance_session)
            .where(AttendanceRecord.student_id == student_id, AttendanceRecord.deleted_at.is_(None))
            .order_by(AttendanceSession.session_date.desc())
        )
        return list(result.all())

    async def list_records_for_class(self, class_id: UUID) -> list[AttendanceRecord]:
        result = await self.session.scalars(
            self._record_query()
            .join(AttendanceRecord.attendance_session)
            .where(
                AttendanceSession.class_id == class_id,
                AttendanceSession.deleted_at.is_(None),
                AttendanceRecord.deleted_at.is_(None),
            )
            .order_by(AttendanceSession.session_date.desc())
        )
        return list(result.all())

    async def list_records_all(self) -> list[AttendanceRecord]:
        result = await self.session.scalars(
            self._record_query()
            .join(AttendanceRecord.attendance_session)
            .where(AttendanceRecord.deleted_at.is_(None), AttendanceSession.deleted_at.is_(None))
            .order_by(AttendanceSession.session_date.desc())
        )
        return list(result.all())

    def _session_query(self):
        return select(AttendanceSession).options(
            selectinload(AttendanceSession.academic_class).selectinload(AcademicClass.branch),
            selectinload(AttendanceSession.academic_class).selectinload(AcademicClass.cycle),
            selectinload(AttendanceSession.academic_class).selectinload(AcademicClass.track),
            selectinload(AttendanceSession.academic_class).selectinload(AcademicClass.level),
            selectinload(AttendanceSession.teacher),
            selectinload(AttendanceSession.created_by_user),
        )

    def _record_query(self):
        return select(AttendanceRecord).options(
            selectinload(AttendanceRecord.attendance_session).selectinload(AttendanceSession.academic_class),
            selectinload(AttendanceRecord.attendance_session).selectinload(AttendanceSession.teacher),
            selectinload(AttendanceRecord.student).selectinload(StudentProfile.user),
            selectinload(AttendanceRecord.grade_entry),
        )
