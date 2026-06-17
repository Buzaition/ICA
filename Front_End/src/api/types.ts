export type UserRole = 'admin' | 'teacher' | 'student'

export type TeacherType = 'mentor' | 'instructor' | 'instructor_and_mentor'

export type ApiEnvelope<T> = {
  success: boolean
  message: string
  data: T
  errors?: unknown[]
}

export type ApiErrorPayload = {
  success: false
  message: string
  errors: unknown[]
  status: number
}

export type LoginRequest = {
  email: string
  password: string
}

export type TokenPair = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type RefreshRequest = {
  refresh_token: string
}

export type LogoutRequest = RefreshRequest

export type ChangePasswordRequest = {
  current_password: string
  new_password: string
}

export type ResetPasswordRequest = {
  user_id: string
  new_password: string
}

export type AdminProfile = {
  id: string
  user_id: string
  full_name: string
}

export type TeacherProfile = {
  id: string
  user_id: string
  teacher_code: string
  full_name: string
  phone_number: string | null
  teacher_type: TeacherType
  is_team_leader: boolean
}

export type StudentProfile = {
  id: string
  user_id: string
  student_code: string
  full_name: string
  phone_number: string | null
  status: 'active' | 'inactive' | 'suspended' | 'dropped' | 'graduated'
}

export type CurrentUser = {
  id: string
  email: string
  role: UserRole
  is_active: boolean
  must_change_password: boolean
  created_at: string
  updated_at: string
  deleted_at: string | null
  admin_profile: AdminProfile | null
  teacher_profile: TeacherProfile | null
  student_profile: StudentProfile | null
}

export type AdminProfileCreate = {
  full_name: string
}

export type TeacherProfileCreate = {
  teacher_code: string
  full_name: string
  phone_number?: string | null
  teacher_type: TeacherType
  is_team_leader: boolean
}

export type StudentProfileCreate = {
  student_code: string
  full_name: string
  phone_number?: string | null
  status: StudentProfile['status']
}

export type UserCreate = {
  email: string
  password: string
  role: UserRole
  admin_profile?: AdminProfileCreate | null
  teacher_profile?: TeacherProfileCreate | null
  student_profile?: StudentProfileCreate | null
}

export type UserUpdate = {
  email?: string
  is_active?: boolean
  admin_profile?: Partial<AdminProfileCreate> | null
  teacher_profile?: Partial<TeacherProfileCreate> | null
  student_profile?: Partial<StudentProfileCreate> | null
}

export type TrackSummary = {
  track_id: string
  code: string
  name: string
  total_classes: number
  active_classes: number
  active_students: number
}

export type ClassSummary = {
  class_id: string
  class_code: string
  status: string
  active_students: number
  class_progress: number
}

export type AdminDashboard = {
  total_students: number
  active_students: number
  suspended_students: number
  graduated_students: number
  dropped_students: number
  total_teachers: number
  total_classes: number
  active_classes: number
  low_progress_students_count: number
  low_progress_instructors_count: number
  low_progress_mentors_count: number
  unread_notifications_count: number
  tracks_summary: TrackSummary[]
  classes_summary: ClassSummary[]
}

export type AdminNotification = {
  id: string
  type: 'student_low_progress' | 'instructor_low_progress' | 'mentor_low_progress'
  title: string
  message: string
  target_user_id: string | null
  target_student_id: string | null
  target_teacher_id: string | null
  class_id: string | null
  severity: 'info' | 'warning' | 'critical'
  is_read: boolean
  read_at: string | null
  created_at: string
  updated_at: string
}

export type UnreadCount = {
  unread_count: number
}

export type Branch = {
  id: string
  name: string
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export type Cycle = {
  id: string
  cycle_number: number
  name: string
  start_date: string
  end_date: string
  status: 'active' | 'closed'
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export type Level = {
  id: string
  track_id: string
  level_number: number
  title: string
  duration_months: number
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export type Track = {
  id: string
  code: string
  name: string
  track_number: number
  created_at: string
  updated_at: string
  deleted_at: string | null
  levels: Level[]
}

export type AcademicClass = {
  id: string
  code: string
  branch_id: string
  cycle_id: string
  track_id: string
  level_id: string
  instructor_id: string
  mentor_id: string
  schedule_text: string
  max_students: number
  class_type: 'onsite' | 'online'
  start_date: string
  end_date: string
  status: 'planned' | 'active' | 'completed' | 'cancelled'
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export type BranchCreate = Pick<Branch, 'name'>
export type BranchUpdate = Partial<BranchCreate>

export type CycleCreate = Pick<Cycle, 'cycle_number' | 'name' | 'start_date' | 'end_date' | 'status'>
export type CycleUpdate = Partial<CycleCreate>

export type TrackCreate = Pick<Track, 'code' | 'name' | 'track_number'> & {
  create_default_levels: boolean
}
export type TrackUpdate = Partial<Pick<Track, 'code' | 'name' | 'track_number'>>

export type LevelCreate = Pick<Level, 'track_id' | 'level_number' | 'title' | 'duration_months'>
export type LevelUpdate = Partial<LevelCreate>

export type ClassCreate = Pick<
  AcademicClass,
  | 'code'
  | 'branch_id'
  | 'cycle_id'
  | 'track_id'
  | 'level_id'
  | 'instructor_id'
  | 'mentor_id'
  | 'schedule_text'
  | 'max_students'
  | 'class_type'
  | 'start_date'
  | 'end_date'
  | 'status'
>
export type ClassUpdate = Partial<ClassCreate>

export type EnrollmentStatus = 'active' | 'completed' | 'removed'

export type Enrollment = {
  id: string
  student_id: string
  student_code: string
  student_full_name: string
  class_id: string
  class_code: string
  track_name: string
  level_number: number
  branch_name: string
  cycle_name: string
  status: EnrollmentStatus
  enrolled_at: string
}

export type EnrollmentCreate = {
  student_id: string
  class_id: string
}

export type TeacherClassStudent = {
  student_id: string
  student_code: string
  student_full_name: string
  student_email: string
  student_status: StudentProfile['status']
  class_code: string
  enrolled_at: string
}

export type MaterialType = 'pdf' | 'video' | 'external_file'
export type MaterialCreatorRole = 'instructor' | 'mentor'

export type Material = {
  id: string
  class_id: string
  class_code: string
  creator_id: string
  creator_name: string
  creator_role: MaterialCreatorRole
  title: string
  description: string | null
  material_type: MaterialType
  url: string
  created_at: string
  updated_at: string
}

export type MaterialCreate = {
  class_id: string
  creator_id?: string | null
  creator_role: MaterialCreatorRole
  title: string
  description?: string | null
  material_type: MaterialType
  url: string
}

export type MaterialUpdate = Partial<Omit<MaterialCreate, 'class_id' | 'creator_id'>> & {
  is_active?: boolean
}

export type Assignment = {
  id: string
  class_id: string
  class_code: string
  created_by_teacher_id: string
  created_by_teacher_name: string
  title: string
  description: string | null
  requirement_url: string
  deadline: string
  max_grade: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export type AssignmentCreate = {
  class_id: string
  created_by_teacher_id?: string | null
  title: string
  description?: string | null
  requirement_url: string
  deadline: string
  max_grade: number
}

export type AssignmentUpdate = Partial<Omit<AssignmentCreate, 'class_id' | 'created_by_teacher_id'>> & {
  is_active?: boolean
}

export type AssignmentSubmissionStatus = 'submitted' | 'reviewed' | 'late' | 'replaced' | 'rejected'

export type SubmissionCreate = {
  submission_url: string
}

export type Submission = {
  id: string
  assignment_id: string
  assignment_title: string
  student_id: string
  student_code: string
  student_full_name: string
  class_id: string
  class_code: string
  submission_url: string
  submitted_at: string
  grade: number | null
  feedback: string | null
  status: AssignmentSubmissionStatus
  reviewed_at: string | null
  reviewed_by_teacher: string | null
  grade_entry_id: string | null
}

export type PendingSubmission = {
  submission_id: string
  student_id: string
  student_code: string
  student_full_name: string
  student_email: string
  class_id: string
  class_code: string
  branch_name: string
  assignment_id: string
  assignment_title: string
  requirement_url: string
  submission_url: string
  assignment_max_grade: number
  submitted_at: string
  status: AssignmentSubmissionStatus
  current_student_progress: null
}

export type ReviewedSubmission = {
  submission_id: string
  student_name: string
  student_code: string
  class_code: string
  assignment_title: string
  grade: number
  assignment_max_grade: number
  feedback: string | null
  reviewed_at: string
  reviewed_by_teacher: string
  grade_entry_id: string | null
}

export type SubmissionReview = {
  grade: number
  feedback?: string | null
  reviewed_by_teacher_id?: string | null
}

export type SubmissionReject = {
  feedback?: string | null
  reviewed_by_teacher_id?: string | null
}

export type AttendanceSessionType = 'instructor' | 'mentor'
export type AttendanceStatus = 'present' | 'late' | 'absent'
export type EntrySourceType = 'manual' | 'csv_upload'

export type ManualAttendanceRecordCreate = {
  student_id: string
  status: AttendanceStatus
  student_code?: string | null
  row_number?: number | null
}

export type ManualAttendanceCreate = {
  class_id: string
  teacher_id?: string | null
  session_type: AttendanceSessionType
  session_date: string
  records: ManualAttendanceRecordCreate[]
}

export type AttendanceRecordUpdate = {
  status: AttendanceStatus
}

export type UploadError = {
  row_number: number
  student_code: string | null
  reason: string
}

export type AttendanceSession = {
  id: string
  class_id: string
  class_code: string
  teacher_id: string
  teacher_name: string
  session_type: AttendanceSessionType
  session_date: string
  max_grade: number
  source_type: EntrySourceType
  created_at: string
}

export type AttendanceRecord = {
  id: string
  session_id: string
  student_id: string
  student_code: string
  student_name: string
  status: AttendanceStatus
  earned_grade: number
  max_grade: number
  grade_entry_id: string | null
}

export type AttendanceSubmissionResult = {
  created_session_id: string
  total_rows: number
  success_count: number
  error_count: number
  errors: UploadError[]
  session: AttendanceSession
  records: AttendanceRecord[]
}

export type ManualQuizResultCreate = {
  student_id: string
  earned_grade: number
  student_code?: string | null
  row_number?: number | null
}

export type ManualQuizCreate = {
  class_id: string
  teacher_id?: string | null
  title: string
  description?: string | null
  quiz_date: string
  max_grade: number
  results: ManualQuizResultCreate[]
}

export type Quiz = {
  id: string
  class_id: string
  class_code: string
  teacher_id: string
  teacher_name: string
  title: string
  description: string | null
  quiz_date: string
  max_grade: number
  source_type: EntrySourceType
  created_at: string
}

export type QuizResult = {
  id: string
  quiz_id: string
  student_id: string
  student_code: string
  student_name: string
  earned_grade: number
  max_grade: number
  grade_entry_id: string | null
}

export type QuizResultUpdate = {
  earned_grade: number
}

export type QuizSubmissionResult = {
  quiz_id: string
  total_rows: number
  success_count: number
  error_count: number
  errors: UploadError[]
  quiz: Quiz
  results: QuizResult[]
}

export type GradeCategory = 'assignment' | 'attendance' | 'quiz' | 'bonus' | 'correction'
export type GradeSourceType = 'manual' | 'csv_upload' | 'system_bonus' | 'correction'

export type GradeEntry = {
  id: string
  student_id: string
  student_code: string
  student_name: string
  class_id: string
  class_code: string
  teacher_id: string | null
  teacher_name: string | null
  category: GradeCategory
  earned_grade: number
  max_grade: number
  source_type: GradeSourceType
  reason: string | null
  related_entry_id: string | null
  assignment_submission_id: string | null
  created_by_user_id: string
  created_at: string
}

export type CorrectionCreate = {
  earned_grade: number
  reason: string
}

export type CorrectionHistory = {
  correction_id: string
  original_grade_entry_id: string
  student_id: string
  student_code: string
  student_name: string
  class_id: string
  class_code: string
  original_category: GradeCategory
  original_earned_grade: number
  original_max_grade: number
  correction_earned_grade: number
  correction_reason: string
  corrected_by: string
  corrected_at: string
}

export type BonusCreate = {
  student_id: string
  class_id: string
  reason?: string | null
}

export type BonusEntry = {
  grade_entry_id: string
  student_id: string
  student_code: string
  student_name: string
  class_id: string
  class_code: string
  earned_grade: number
  max_grade: number
  reason: string
  weekly_bonus_count: number
  weekly_bonus_remaining: number
  created_at: string
}

export type StudentProgress = {
  student_id: string
  student_code: string
  student_name: string
  class_id: string
  class_code: string
  attendance_progress: number
  quiz_progress: number
  assignment_progress: number
  bonus_progress: number
  final_progress: number
}

export type ClassProgress = {
  class_id: string
  class_code: string
  student_count: number
  class_progress: number
  students: StudentProgress[]
}

export type TeacherProgressClass = {
  class_id: string
  class_code: string
  role: string
  class_progress: number
}

export type TeacherProgress = {
  teacher_id: string
  teacher_name: string
  assigned_classes: TeacherProgressClass[]
  instructor_progress: number
  mentor_progress: number
}

export type ProgressSnapshot = StudentProgress & {
  id: string
  week_number: number
  year: number
  created_at: string
}

export type RankingItem = StudentProgress & {
  rank: number
}

export type FinalProjectStatus = 'pending' | 'approved' | 'rejected'

export type FinalProjectSubmit = {
  project_link: string
}

export type FinalProjectReview = {
  status: FinalProjectStatus
  grade?: number | null
  feedback?: string | null
}

export type FinalProject = {
  final_project_id: string
  student_id: string
  student_code: string
  student_name: string
  class_id: string
  class_code: string
  level_id: string
  level_number: number
  project_link: string
  grade: number | null
  feedback: string | null
  status: FinalProjectStatus
  submitted_at: string
  reviewed_at: string | null
  reviewed_by_admin: string | null
}
