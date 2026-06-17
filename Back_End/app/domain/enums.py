from enum import StrEnum


class UserRole(StrEnum):
    admin = "admin"
    teacher = "teacher"
    student = "student"


class TeacherType(StrEnum):
    mentor = "mentor"
    instructor = "instructor"
    instructor_and_mentor = "instructor_and_mentor"


class StudentStatus(StrEnum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    dropped = "dropped"
    graduated = "graduated"


class CycleStatus(StrEnum):
    active = "active"
    closed = "closed"


class ClassType(StrEnum):
    onsite = "onsite"
    online = "online"


class ClassStatus(StrEnum):
    planned = "planned"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class EnrollmentStatus(StrEnum):
    active = "active"
    completed = "completed"
    removed = "removed"


class MaterialType(StrEnum):
    pdf = "pdf"
    video = "video"
    external_file = "external_file"


class MaterialCreatorRole(StrEnum):
    instructor = "instructor"
    mentor = "mentor"


class AssignmentSubmissionStatus(StrEnum):
    submitted = "submitted"
    reviewed = "reviewed"
    late = "late"
    replaced = "replaced"
    rejected = "rejected"


class GradeCategory(StrEnum):
    assignment = "assignment"
    attendance = "attendance"
    quiz = "quiz"
    bonus = "bonus"
    correction = "correction"


class GradeSourceType(StrEnum):
    manual = "manual"
    csv_upload = "csv_upload"
    system_bonus = "system_bonus"
    correction = "correction"


class AttendanceSessionType(StrEnum):
    instructor = "instructor"
    mentor = "mentor"


class AttendanceSourceType(StrEnum):
    manual = "manual"
    csv_upload = "csv_upload"


class AttendanceStatus(StrEnum):
    present = "present"
    late = "late"
    absent = "absent"


class QuizSourceType(StrEnum):
    manual = "manual"
    csv_upload = "csv_upload"


class FinalProjectStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class NotificationType(StrEnum):
    student_low_progress = "student_low_progress"
    instructor_low_progress = "instructor_low_progress"
    mentor_low_progress = "mentor_low_progress"


class NotificationSeverity(StrEnum):
    info = "info"
    warning = "warning"
    critical = "critical"
