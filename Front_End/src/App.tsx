import { type FormEvent, useEffect, useMemo, useState } from 'react'
import {
  Bell,
  BookOpen,
  CalendarCheck,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  FileCheck2,
  FileText,
  GraduationCap,
  LayoutDashboard,
  LibraryBig,
  LineChart,
  LogOut,
  Menu,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Shield,
  UserCog,
  Users,
  X,
  type LucideIcon,
} from 'lucide-react'
import { ApiError } from './api/client'
import {
  createUser,
  deleteUser,
  getAdminDashboard,
  getAdminUnreadCount,
  listAdminNotifications,
  listUsers,
  resetUserPassword,
  updateUser,
} from './api/admin'
import {
  createBranch,
  createClass,
  createCycle,
  createLevel,
  createTrack,
  deleteBranch,
  deleteClass,
  deleteCycle,
  deleteLevel,
  deleteTrack,
  listBranches,
  listClasses,
  listCycles,
  listLevels,
  listTracks,
  updateBranch,
  updateClass,
  updateCycle,
  updateLevel,
  updateTrack,
} from './api/academic'
import {
  changePassword,
  getCurrentUser,
  getTokens,
  login,
  logout,
} from './api/auth'
import {
  createEnrollment,
  listEnrollments,
  listTeacherClassStudents,
  removeEnrollment,
} from './api/enrollments'
import {
  createManualAttendance,
  createManualQuiz,
  listAttendanceSessionRecords,
  listAttendanceSessions,
  listQuizResults,
  listQuizzes,
  listStudentAttendance,
  listStudentQuizzes,
  updateAttendanceRecord,
  updateQuizResult,
  uploadAttendanceCsv,
  uploadQuizCsv,
} from './api/assessment'
import {
  createBonus,
  createCorrection,
  listAdminCorrectionsHistory,
  listBonus,
  listGradeEntries,
  listStudentBonus,
  listStudentGradeEntries,
  listTeacherClassBonus,
  listTeacherClassGradeEntries,
  listTeacherCorrectionsHistory,
} from './api/gradebook'
import {
  createClassProgressSnapshots,
  createTeacherClassProgressSnapshots,
  getClassProgress,
  getClassRanking,
  getMyFinalProject,
  getMyProgress,
  getMyTop3Ranking,
  getStudentProgress,
  getTeacherClassProgress,
  getTeacherClassRanking,
  getTeacherProgress,
  getTrackRanking,
  listClassProgressSnapshots,
  listFinalProjects,
  listTeacherClassFinalProjects,
  reviewFinalProject,
  submitMyFinalProject,
  updateMyFinalProject,
} from './api/outcomes'
import {
  createAssignment,
  createMaterial,
  deleteAssignment,
  deleteMaterial,
  listAssignmentSubmissions,
  listAssignments,
  listLateAssignments,
  listMaterials,
  listPendingAssignments,
  listReviewedAssignments,
  listStudentAssignments,
  listStudentMaterials,
  listStudentSubmissions,
  rejectSubmission,
  reviewSubmission,
  submitAssignment,
  updateAssignment,
  updateMaterial,
} from './api/lms'
import type {
  AcademicClass,
  AdminDashboard,
  AdminNotification,
  Assignment,
  AssignmentCreate,
  AssignmentSubmissionStatus,
  AssignmentUpdate,
  AttendanceRecord,
  AttendanceSession,
  AttendanceSessionType,
  AttendanceStatus,
  BonusEntry,
  Branch,
  BranchCreate,
  BranchUpdate,
  ClassCreate,
  ClassUpdate,
  CurrentUser,
  Cycle,
  CycleCreate,
  CycleUpdate,
  Enrollment,
  EnrollmentCreate,
  GradeCategory,
  GradeEntry,
  GradeSourceType,
  Level,
  LevelCreate,
  LevelUpdate,
  Material,
  MaterialCreate,
  MaterialCreatorRole,
  MaterialType,
  MaterialUpdate,
  PendingSubmission,
  Quiz,
  QuizResult,
  CorrectionHistory,
  ClassProgress,
  FinalProject,
  FinalProjectReview,
  FinalProjectStatus,
  ProgressSnapshot,
  RankingItem,
  ReviewedSubmission,
  StudentProgress,
  Submission,
  TeacherProgress,
  Track,
  TrackCreate,
  TrackUpdate,
  UserCreate,
  UserRole,
  UserUpdate,
} from './api/types'
import './App.css'

type Role = UserRole
type ModuleKey =
  | 'dashboard'
  | 'users'
  | 'academic'
  | 'classes'
  | 'content'
  | 'assignments'
  | 'attendance'
  | 'quizzes'
  | 'gradebook'
  | 'progress'
  | 'projects'
  | 'notifications'

type DataRow = Record<string, string>

type ModuleView = {
  key: ModuleKey
  title: string
  eyebrow: string
  description: string
  endpoint: string
  icon: LucideIcon
  roles: Role[]
  accent: 'blue' | 'green' | 'orange' | 'red' | 'violet'
  stats: Array<{ label: string; value: string; trend: string }>
  filters: Array<{ label: string; options: string[] }>
  columns: string[]
  rows: DataRow[]
  actions: string[]
}

type NavGroup = {
  label: string
  roles: Role[]
  items: Array<{ key: ModuleKey; label: string; icon: LucideIcon; roles: Role[] }>
}

const roleProfiles: Record<Role, { label: string; name: string; workspace: string }> = {
  admin: {
    label: 'Admin',
    name: 'ICA Operations',
    workspace: 'Full academy control',
  },
  teacher: {
    label: 'Teacher',
    name: 'Mariam Hassan',
    workspace: 'Instructor and mentor workspace',
  },
  student: {
    label: 'Student',
    name: 'Omar Nabil',
    workspace: 'Learning workspace',
  },
}

const modules: ModuleView[] = [
  {
    key: 'dashboard',
    title: 'Operational Dashboard',
    eyebrow: 'Read-only summary',
    description:
      'Role-aware snapshots for enrollment, progress, assignments, attendance, quizzes, and final project status.',
    endpoint: '/api/admin/dashboard | /api/teachers/me/dashboard | /api/students/me/dashboard',
    icon: LayoutDashboard,
    roles: ['admin', 'teacher', 'student'],
    accent: 'blue',
    stats: [
      { label: 'Active students', value: '318', trend: '+24 this cycle' },
      { label: 'Active classes', value: '18', trend: 'BE and FE tracks' },
      { label: 'Low progress alerts', value: '11', trend: 'Needs review' },
      { label: 'Pending reviews', value: '42', trend: 'Assignments queue' },
    ],
    filters: [
      { label: 'Workspace', options: ['Admin overview', 'Teacher load', 'Student view'] },
      { label: 'Cycle', options: ['Cycle 1', 'Cycle 2', 'Closed cycles'] },
      { label: 'Track', options: ['All tracks', 'Backend', 'Frontend'] },
    ],
    columns: ['Area', 'Current', 'Signal', 'Owner'],
    rows: [
      { Area: 'Attendance', Current: '88%', Signal: 'Stable', Owner: 'Instructor teams' },
      { Area: 'Assignments', Current: '42 pending', Signal: 'Busy', Owner: 'Mentors' },
      { Area: 'Progress', Current: '74% average', Signal: 'Healthy', Owner: 'Academic admin' },
      { Area: 'Final projects', Current: '16 pending', Signal: 'Review', Owner: 'Admin' },
    ],
    actions: ['Refresh dashboard', 'Export summary', 'Check progress alerts'],
  },
  {
    key: 'users',
    title: 'Users and Roles',
    eyebrow: 'Admin only',
    description:
      'Create, edit, filter, reset passwords, and soft-delete Admin, Teacher, and Student accounts.',
    endpoint: '/api/users',
    icon: UserCog,
    roles: ['admin'],
    accent: 'green',
    stats: [
      { label: 'Total users', value: '382', trend: 'Across all roles' },
      { label: 'Teachers', value: '36', trend: '9 team leaders' },
      { label: 'Students', value: '331', trend: '294 active' },
      { label: 'Password resets', value: '7', trend: 'This week' },
    ],
    filters: [
      { label: 'Role', options: ['All roles', 'Admin', 'Teacher', 'Student'] },
      { label: 'Status', options: ['All statuses', 'Active', 'Inactive', 'Suspended'] },
      { label: 'Teacher type', options: ['Any type', 'Instructor', 'Mentor', 'Instructor and mentor'] },
    ],
    columns: ['User', 'Role', 'Profile', 'Status'],
    rows: [
      { User: 'admin@ica.eg', Role: 'Admin', Profile: 'Academy Admin', Status: 'Must change password' },
      { User: 'm.hassan@ica.eg', Role: 'Teacher', Profile: 'Instructor and mentor', Status: 'Active' },
      { User: 'o.nabil@ica.eg', Role: 'Student', Profile: 'ST-1042 Backend', Status: 'Active' },
      { User: 'r.saad@ica.eg', Role: 'Student', Profile: 'ST-0987 Frontend', Status: 'Suspended' },
    ],
    actions: ['Create user', 'Reset password', 'Soft delete'],
  },
  {
    key: 'academic',
    title: 'Academic Setup',
    eyebrow: 'Branches, cycles, tracks, levels',
    description:
      'Maintain academy structure and enforce Backend/Frontend track levels before classes are opened.',
    endpoint: '/api/branches | /api/cycles | /api/tracks | /api/levels',
    icon: GraduationCap,
    roles: ['admin'],
    accent: 'orange',
    stats: [
      { label: 'Branches', value: '2', trend: 'Main and online' },
      { label: 'Cycles', value: '3', trend: '1 active' },
      { label: 'Tracks', value: '2', trend: 'BE and FE' },
      { label: 'Levels', value: '6', trend: '3 per track' },
    ],
    filters: [
      { label: 'Entity', options: ['Branches', 'Cycles', 'Tracks', 'Levels'] },
      { label: 'Cycle status', options: ['All statuses', 'Active', 'Closed'] },
      { label: 'Track', options: ['All tracks', 'Backend', 'Frontend'] },
    ],
    columns: ['Code', 'Name', 'Rule', 'Status'],
    rows: [
      { Code: 'MAIN', Name: 'Main Branch', Rule: 'Default seed branch', Status: 'Active' },
      { Code: 'C1', Name: 'Cycle 1', Rule: 'Active date range', Status: 'Active' },
      { Code: 'BE', Name: 'Backend', Rule: 'Track number 14', Status: '3 levels' },
      { Code: 'FE', Name: 'Frontend', Rule: 'Track number 13', Status: '3 levels' },
    ],
    actions: ['Create branch', 'Create cycle', 'Create track', 'Create level'],
  },
  {
    key: 'classes',
    title: 'Classes and Enrollment',
    eyebrow: 'Capacity and membership',
    description:
      'Create classes, assign instructor and mentor, enroll students, and monitor class capacity.',
    endpoint: '/api/classes | /api/enrollments | /api/teachers/me/classes',
    icon: Users,
    roles: ['admin', 'teacher', 'student'],
    accent: 'blue',
    stats: [
      { label: 'Assigned classes', value: '5', trend: 'Teacher scoped' },
      { label: 'Open seats', value: '34', trend: 'Across active classes' },
      { label: 'Max per class', value: '25', trend: 'Backend rule' },
      { label: 'Removed records', value: '12', trend: 'History retained' },
    ],
    filters: [
      { label: 'Class status', options: ['All statuses', 'Planned', 'Active', 'Completed', 'Cancelled'] },
      { label: 'Class type', options: ['All types', 'Online', 'Onsite'] },
      { label: 'Enrollment', options: ['Active', 'Completed', 'Removed'] },
    ],
    columns: ['Class', 'Track', 'Team', 'Capacity'],
    rows: [
      { Class: 'BE1001', Track: 'Backend L1 online', Team: 'Mariam / Youssef', Capacity: '21 / 25' },
      { Class: 'BE5001', Track: 'Backend L2 onsite', Team: 'Nour / Mariam', Capacity: '24 / 25' },
      { Class: 'FE1003', Track: 'Frontend L1 online', Team: 'Salma / Karim', Capacity: '18 / 25' },
      { Class: 'FE5002', Track: 'Frontend L3 onsite', Team: 'Karim / Salma', Capacity: '25 / 25' },
    ],
    actions: ['Create class', 'Enroll student', 'View roster', 'Remove enrollment'],
  },
  {
    key: 'content',
    title: 'Learning Content',
    eyebrow: 'Materials library',
    description:
      'Manage PDF, video, and external-file links for classes, scoped by teacher assignment and student active class.',
    endpoint: '/api/materials | /api/students/me/materials',
    icon: LibraryBig,
    roles: ['admin', 'teacher', 'student'],
    accent: 'violet',
    stats: [
      { label: 'Materials', value: '126', trend: 'Active links' },
      { label: 'Videos', value: '48', trend: 'External URLs' },
      { label: 'PDFs', value: '57', trend: 'Reference sheets' },
      { label: 'Inactive', value: '9', trend: 'Hidden from students' },
    ],
    filters: [
      { label: 'Material type', options: ['All types', 'PDF', 'Video', 'External file'] },
      { label: 'Creator role', options: ['Any creator', 'Instructor', 'Mentor'] },
      { label: 'Class', options: ['All classes', 'BE1001', 'BE5001', 'FE1003'] },
    ],
    columns: ['Title', 'Type', 'Class', 'Creator'],
    rows: [
      { Title: 'FastAPI routing pack', Type: 'PDF', Class: 'BE1001', Creator: 'Instructor' },
      { Title: 'Database joins walkthrough', Type: 'Video', Class: 'BE5001', Creator: 'Mentor' },
      { Title: 'React state lab', Type: 'External file', Class: 'FE1003', Creator: 'Instructor' },
      { Title: 'Portfolio checklist', Type: 'PDF', Class: 'FE5002', Creator: 'Mentor' },
    ],
    actions: ['Add material', 'Toggle active', 'Edit link', 'Delete material'],
  },
  {
    key: 'assignments',
    title: 'Assignments and Reviews',
    eyebrow: 'Submission workflow',
    description:
      'Track assignment links, student submissions, pending review queues, reviewed work, and rejected late work.',
    endpoint: '/api/assignments | /api/assignment-submissions',
    icon: ClipboardCheck,
    roles: ['admin', 'teacher', 'student'],
    accent: 'red',
    stats: [
      { label: 'Open assignments', value: '28', trend: 'Active deadlines' },
      { label: 'Pending', value: '42', trend: 'Needs grading' },
      { label: 'Late', value: '13', trend: 'Review or reject' },
      { label: 'Reviewed', value: '211', trend: 'Ledger linked' },
    ],
    filters: [
      { label: 'Queue', options: ['Pending', 'Reviewed', 'Late', 'Rejected'] },
      { label: 'Class', options: ['All classes', 'BE1001', 'BE5001', 'FE1003'] },
      { label: 'Deadline', options: ['Any deadline', 'Today', 'This week', 'Overdue'] },
    ],
    columns: ['Assignment', 'Student', 'Status', 'Grade'],
    rows: [
      { Assignment: 'REST API sprint', Student: 'Omar Nabil', Status: 'Submitted', Grade: 'Pending' },
      { Assignment: 'SQL grade ledger', Student: 'Rana Saad', Status: 'Late', Grade: 'Pending' },
      { Assignment: 'React forms', Student: 'Lina Adel', Status: 'Reviewed', Grade: '46 / 50' },
      { Assignment: 'Portfolio deploy', Student: 'Tarek Ali', Status: 'Rejected', Grade: 'No grade' },
    ],
    actions: ['Create assignment', 'Review submission', 'Reject late', 'Open submitted link'],
  },
  {
    key: 'attendance',
    title: 'Attendance',
    eyebrow: 'Manual and CSV',
    description:
      'Create instructor or mentor attendance sessions, upload CSV files, and preserve grade corrections.',
    endpoint: '/api/attendance/manual | /api/attendance/upload-csv | /api/attendance/sessions',
    icon: CalendarCheck,
    roles: ['admin', 'teacher', 'student'],
    accent: 'green',
    stats: [
      { label: 'Sessions', value: '94', trend: 'This cycle' },
      { label: 'Present rate', value: '88%', trend: 'All active students' },
      { label: 'Late records', value: '31', trend: '0.5 grade each' },
      { label: 'CSV issues', value: '6', trend: 'Skipped rows' },
    ],
    filters: [
      { label: 'Session type', options: ['All sessions', 'Instructor', 'Mentor'] },
      { label: 'Status', options: ['All statuses', 'Present', 'Late', 'Absent'] },
      { label: 'Source', options: ['All sources', 'Manual', 'CSV upload'] },
    ],
    columns: ['Session', 'Class', 'Status', 'Source'],
    rows: [
      { Session: 'Jun 12 instructor', Class: 'BE1001', Status: '23 present', Source: 'Manual' },
      { Session: 'Jun 13 mentor', Class: 'BE1001', Status: '2 late', Source: 'CSV upload' },
      { Session: 'Jun 14 instructor', Class: 'FE1003', Status: '4 absent', Source: 'Manual' },
      { Session: 'Jun 15 mentor', Class: 'BE5001', Status: '25 present', Source: 'CSV upload' },
    ],
    actions: ['Manual entry', 'Upload CSV', 'Edit record', 'View session records'],
  },
  {
    key: 'quizzes',
    title: 'Quizzes',
    eyebrow: 'Results and corrections',
    description:
      'Record quiz results manually or through CSV while creating immutable grade ledger entries.',
    endpoint: '/api/quizzes/manual | /api/quizzes/upload-csv | /api/quiz-results',
    icon: FileCheck2,
    roles: ['admin', 'teacher', 'student'],
    accent: 'orange',
    stats: [
      { label: 'Quizzes', value: '37', trend: 'Across classes' },
      { label: 'Average score', value: '82%', trend: 'Weighted in progress' },
      { label: 'CSV uploads', value: '18', trend: 'Partial success supported' },
      { label: 'Corrections', value: '4', trend: 'Grade differences' },
    ],
    filters: [
      { label: 'Class', options: ['All classes', 'BE1001', 'BE5001', 'FE1003'] },
      { label: 'Source', options: ['All sources', 'Manual', 'CSV upload'] },
      { label: 'Date range', options: ['Any date', 'This week', 'This month'] },
    ],
    columns: ['Quiz', 'Class', 'Max grade', 'Results'],
    rows: [
      { Quiz: 'HTTP fundamentals', Class: 'BE1001', 'Max grade': '20', Results: '21 recorded' },
      { Quiz: 'SQL joins', Class: 'BE5001', 'Max grade': '15', Results: '24 recorded' },
      { Quiz: 'React state', Class: 'FE1003', 'Max grade': '25', Results: '18 recorded' },
      { Quiz: 'CSS layout', Class: 'FE5002', 'Max grade': '10', Results: '25 recorded' },
    ],
    actions: ['Manual quiz entry', 'Upload quiz CSV', 'Edit result', 'Open results'],
  },
  {
    key: 'gradebook',
    title: 'Gradebook',
    eyebrow: 'Immutable ledger',
    description:
      'Audit assignment, attendance, quiz, bonus, and correction entries without mutating original grades.',
    endpoint: '/api/grade-entries | /api/bonus | /api/grade-entries/{id}/corrections',
    icon: BookOpen,
    roles: ['admin', 'teacher', 'student'],
    accent: 'blue',
    stats: [
      { label: 'Grade entries', value: '1,482', trend: 'Immutable rows' },
      { label: 'Bonus entries', value: '146', trend: 'Max 5 weekly' },
      { label: 'Corrections', value: '29', trend: 'Reason required' },
      { label: 'Student view', value: 'Own only', trend: 'Role scoped' },
    ],
    filters: [
      { label: 'Category', options: ['All categories', 'Assignment', 'Attendance', 'Quiz', 'Bonus', 'Correction'] },
      { label: 'Source', options: ['All sources', 'Manual', 'CSV upload', 'System bonus', 'Correction'] },
      { label: 'Class', options: ['All classes', 'BE1001', 'BE5001', 'FE1003'] },
    ],
    columns: ['Student', 'Category', 'Grade', 'Reason'],
    rows: [
      { Student: 'Omar Nabil', Category: 'Assignment', Grade: '46 / 50', Reason: 'Assignment Review' },
      { Student: 'Lina Adel', Category: 'Attendance', Grade: '1 / 1', Reason: 'Present' },
      { Student: 'Rana Saad', Category: 'Correction', Grade: '+2 / 0', Reason: 'Quiz CSV fix' },
      { Student: 'Tarek Ali', Category: 'Bonus', Grade: '+1 / 0', Reason: 'Team help' },
    ],
    actions: ['Give bonus', 'Create correction', 'View corrections', 'Export ledger'],
  },
  {
    key: 'progress',
    title: 'Progress and Ranking',
    eyebrow: 'Calculated results',
    description:
      'Calculate attendance, quiz, assignment, and bonus progress with class, teacher, and ranking views.',
    endpoint: '/api/progress/classes/{class_id} | /api/ranking/classes/{class_id}',
    icon: LineChart,
    roles: ['admin', 'teacher', 'student'],
    accent: 'violet',
    stats: [
      { label: 'Average progress', value: '74%', trend: 'Weighted formula' },
      { label: 'Snapshots', value: '8 weeks', trend: 'Immutable history' },
      { label: 'Top rank', value: '99%', trend: 'Dense ranking' },
      { label: 'Below threshold', value: '11', trend: 'Admin notified' },
    ],
    filters: [
      { label: 'View', options: ['Class progress', 'Student progress', 'Teacher progress', 'Snapshots'] },
      { label: 'Ranking', options: ['Class ranking', 'Track ranking', 'Student top 3'] },
      { label: 'Week', options: ['Current', 'Week 24', 'Week 23', 'Week 22'] },
    ],
    columns: ['Student', 'Progress', 'Rank', 'Signal'],
    rows: [
      { Student: 'Lina Adel', Progress: '99%', Rank: '1', Signal: 'Excellent' },
      { Student: 'Omar Nabil', Progress: '94%', Rank: '2', Signal: 'Strong' },
      { Student: 'Tarek Ali', Progress: '94%', Rank: '2', Signal: 'Strong' },
      { Student: 'Rana Saad', Progress: '48%', Rank: '9', Signal: 'Low progress' },
    ],
    actions: ['Create snapshot', 'Open ranking', 'Check progress alerts', 'View trend'],
  },
  {
    key: 'projects',
    title: 'Final Projects',
    eyebrow: 'Level completion review',
    description:
      'Students submit one active project per class and level; Admin reviews without automatic promotion.',
    endpoint: '/api/students/me/final-project | /api/final-projects',
    icon: FileText,
    roles: ['admin', 'teacher', 'student'],
    accent: 'red',
    stats: [
      { label: 'Pending review', value: '16', trend: 'Admin queue' },
      { label: 'Approved', value: '71', trend: 'Manual promotion later' },
      { label: 'Rejected', value: '8', trend: 'Feedback attached' },
      { label: 'Teacher view', value: 'Assigned', trend: 'Read-only scope' },
    ],
    filters: [
      { label: 'Status', options: ['All statuses', 'Pending', 'Approved', 'Rejected'] },
      { label: 'Track', options: ['All tracks', 'Backend', 'Frontend'] },
      { label: 'Level', options: ['All levels', 'Level 1', 'Level 2', 'Level 3'] },
    ],
    columns: ['Student', 'Class', 'Project', 'Status'],
    rows: [
      { Student: 'Omar Nabil', Class: 'BE1001', Project: 'API capstone', Status: 'Pending' },
      { Student: 'Lina Adel', Class: 'FE5002', Project: 'Portfolio app', Status: 'Approved' },
      { Student: 'Rana Saad', Class: 'BE5001', Project: 'Ledger service', Status: 'Rejected' },
      { Student: 'Tarek Ali', Class: 'FE1003', Project: 'Dashboard UI', Status: 'Pending' },
    ],
    actions: ['Submit project', 'Review project', 'Approve', 'Reject'],
  },
  {
    key: 'notifications',
    title: 'Internal Notifications',
    eyebrow: 'Admin alerts only',
    description:
      'Internal low-progress notifications for students, instructors, and mentors. No external providers.',
    endpoint: '/api/admin/notifications',
    icon: Bell,
    roles: ['admin'],
    accent: 'orange',
    stats: [
      { label: 'Unread', value: '11', trend: 'Action needed' },
      { label: 'Student alerts', value: '7', trend: 'Below 50%' },
      { label: 'Instructor alerts', value: '2', trend: 'Below 50%' },
      { label: 'Mentor alerts', value: '2', trend: 'Below 70%' },
    ],
    filters: [
      { label: 'Severity', options: ['All severities', 'Info', 'Warning', 'Critical'] },
      { label: 'Type', options: ['All types', 'Student low progress', 'Instructor low progress', 'Mentor low progress'] },
      { label: 'Read state', options: ['Unread', 'Read', 'All'] },
    ],
    columns: ['Notification', 'Target', 'Severity', 'State'],
    rows: [
      { Notification: 'Student below 50%', Target: 'Rana Saad / BE5001', Severity: 'Critical', State: 'Unread' },
      { Notification: 'Mentor below 70%', Target: 'Mariam / FE1003', Severity: 'Warning', State: 'Unread' },
      { Notification: 'Instructor below 50%', Target: 'Karim / BE1001', Severity: 'Critical', State: 'Read' },
      { Notification: 'Student below 50%', Target: 'Ahmed Samir / FE5002', Severity: 'Warning', State: 'Unread' },
    ],
    actions: ['Check progress', 'Mark read', 'Mark all read'],
  },
]

const navGroups: NavGroup[] = [
  {
    label: 'Workspace',
    roles: ['admin', 'teacher', 'student'],
    items: [{ key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin', 'teacher', 'student'] }],
  },
  {
    label: 'Administration',
    roles: ['admin'],
    items: [
      { key: 'users', label: 'Users and roles', icon: UserCog, roles: ['admin'] },
      { key: 'academic', label: 'Academic setup', icon: GraduationCap, roles: ['admin'] },
      { key: 'notifications', label: 'Notifications', icon: Bell, roles: ['admin'] },
    ],
  },
  {
    label: 'Academy Operations',
    roles: ['admin', 'teacher', 'student'],
    items: [
      { key: 'classes', label: 'Classes and enrollment', icon: Users, roles: ['admin', 'teacher', 'student'] },
      { key: 'content', label: 'Learning content', icon: LibraryBig, roles: ['admin', 'teacher', 'student'] },
      { key: 'assignments', label: 'Assignments', icon: ClipboardCheck, roles: ['admin', 'teacher', 'student'] },
      { key: 'attendance', label: 'Attendance', icon: CalendarCheck, roles: ['admin', 'teacher', 'student'] },
      { key: 'quizzes', label: 'Quizzes', icon: FileCheck2, roles: ['admin', 'teacher', 'student'] },
    ],
  },
  {
    label: 'Outcomes',
    roles: ['admin', 'teacher', 'student'],
    items: [
      { key: 'gradebook', label: 'Gradebook', icon: BookOpen, roles: ['admin', 'teacher', 'student'] },
      { key: 'progress', label: 'Progress and ranking', icon: LineChart, roles: ['admin', 'teacher', 'student'] },
      { key: 'projects', label: 'Final projects', icon: FileText, roles: ['admin', 'teacher', 'student'] },
    ],
  },
]

const workflowFields: Record<ModuleKey, Array<{ label: string; type: 'input' | 'select'; options?: string[] }>> = {
  dashboard: [
    { label: 'Dashboard view', type: 'select', options: ['Admin dashboard', 'Teacher dashboard', 'Student dashboard'] },
    { label: 'Cycle filter', type: 'select', options: ['Cycle 1', 'Cycle 2', 'Closed cycles'] },
    { label: 'Search summary', type: 'input' },
  ],
  users: [
    { label: 'Role', type: 'select', options: ['Admin', 'Teacher', 'Student'] },
    { label: 'Email', type: 'input' },
    { label: 'Teacher type / student status', type: 'select', options: ['Instructor', 'Mentor', 'Instructor and mentor', 'Active'] },
  ],
  academic: [
    { label: 'Entity', type: 'select', options: ['Branch', 'Cycle', 'Track', 'Level'] },
    { label: 'Code or number', type: 'input' },
    { label: 'Status', type: 'select', options: ['Active', 'Closed', 'Planned'] },
  ],
  classes: [
    { label: 'Track', type: 'select', options: ['Backend', 'Frontend'] },
    { label: 'Level', type: 'select', options: ['Level 1', 'Level 2', 'Level 3'] },
    { label: 'Class type', type: 'select', options: ['Online', 'Onsite'] },
  ],
  content: [
    { label: 'Material type', type: 'select', options: ['PDF', 'Video', 'External file'] },
    { label: 'Creator role', type: 'select', options: ['Instructor', 'Mentor'] },
    { label: 'URL', type: 'input' },
  ],
  assignments: [
    { label: 'Queue', type: 'select', options: ['Pending', 'Reviewed', 'Late'] },
    { label: 'Grade', type: 'input' },
    { label: 'Review action', type: 'select', options: ['Review', 'Reject late', 'Open submission'] },
  ],
  attendance: [
    { label: 'Session type', type: 'select', options: ['Instructor', 'Mentor'] },
    { label: 'Attendance status', type: 'select', options: ['Present', 'Late', 'Absent'] },
    { label: 'Source', type: 'select', options: ['Manual', 'CSV upload'] },
  ],
  quizzes: [
    { label: 'Quiz source', type: 'select', options: ['Manual', 'CSV upload'] },
    { label: 'Max grade', type: 'input' },
    { label: 'Class', type: 'select', options: ['BE1001', 'BE5001', 'FE1003'] },
  ],
  gradebook: [
    { label: 'Category', type: 'select', options: ['Assignment', 'Attendance', 'Quiz', 'Bonus', 'Correction'] },
    { label: 'Correction reason', type: 'input' },
    { label: 'Source type', type: 'select', options: ['Manual', 'CSV upload', 'System bonus', 'Correction'] },
  ],
  progress: [
    { label: 'Progress view', type: 'select', options: ['Class', 'Student', 'Teacher', 'Snapshot history'] },
    { label: 'Ranking scope', type: 'select', options: ['Class', 'Track', 'Top 3'] },
    { label: 'Week', type: 'select', options: ['Current week', 'Week 24', 'Week 23'] },
  ],
  projects: [
    { label: 'Project status', type: 'select', options: ['Pending', 'Approved', 'Rejected'] },
    { label: 'Project link', type: 'input' },
    { label: 'Review action', type: 'select', options: ['Approve', 'Reject', 'Request revision'] },
  ],
  notifications: [
    { label: 'Severity', type: 'select', options: ['Info', 'Warning', 'Critical'] },
    { label: 'Type', type: 'select', options: ['Student low progress', 'Instructor low progress', 'Mentor low progress'] },
    { label: 'Read state', type: 'select', options: ['Unread', 'Read', 'All'] },
  ],
}

const roleDashboardRoutes: Record<Role, string> = {
  admin: '#/admin/dashboard',
  teacher: '#/teacher/dashboard',
  student: '#/student/dashboard',
}

function dashboardRouteFor(role: Role) {
  return roleDashboardRoutes[role]
}

function writeRoute(hashRoute: string, replace = false) {
  if (replace) {
    window.history.replaceState(null, '', hashRoute)
    return
  }

  window.history.pushState(null, '', hashRoute)
}

function moduleKeyFromHash(role: Role): ModuleKey {
  const hash = window.location.hash.toLowerCase()
  const found = modules.find((module) => hash.includes(module.key) && module.roles.includes(role))
  return found?.key ?? 'dashboard'
}

function displayNameFor(user: CurrentUser) {
  return (
    user.admin_profile?.full_name ??
    user.teacher_profile?.full_name ??
    user.student_profile?.full_name ??
    user.email
  )
}

function workspaceFor(user: CurrentUser) {
  if (user.role === 'admin') {
    return 'Full academy control'
  }

  if (user.role === 'teacher') {
    const teacherType = user.teacher_profile?.teacher_type?.replaceAll('_', ' ') ?? 'teacher'
    return `${teacherType} workspace`
  }

  const status = user.student_profile?.status ?? 'student'
  return `${status} learning workspace`
}

function errorMessage(error: unknown) {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message
  }
  return 'Something went wrong. Please try again.'
}

function App() {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null)
  const [status, setStatus] = useState<'checking' | 'guest' | 'authenticated'>('checking')
  const [authMessage, setAuthMessage] = useState('')

  useEffect(() => {
    let mounted = true

    async function restoreSession() {
      if (!getTokens()) {
        setStatus('guest')
        return
      }

      try {
        const envelope = await getCurrentUser()
        if (!mounted) {
          return
        }
        setCurrentUser(envelope.data)
        setStatus('authenticated')
        if (!window.location.hash) {
          writeRoute(dashboardRouteFor(envelope.data.role), true)
        }
      } catch {
        if (mounted) {
          setCurrentUser(null)
          setStatus('guest')
        }
      }
    }

    void restoreSession()

    return () => {
      mounted = false
    }
  }, [])

  async function handleAuthenticated() {
    const envelope = await getCurrentUser()
    setCurrentUser(envelope.data)
    setStatus('authenticated')
    writeRoute(dashboardRouteFor(envelope.data.role), true)
  }

  async function handleLogout() {
    await logout()
    setCurrentUser(null)
    setStatus('guest')
    setAuthMessage('You have been signed out.')
    writeRoute('#/login', true)
  }

  if (status === 'checking') {
    return <AuthLoadingScreen />
  }

  if (!currentUser) {
    return (
      <LoginScreen
        message={authMessage}
        onAuthenticated={handleAuthenticated}
        onMessage={setAuthMessage}
      />
    )
  }

  if (currentUser.must_change_password) {
    return (
      <ForceChangePasswordScreen
        user={currentUser}
        onComplete={() => {
          setCurrentUser(null)
          setStatus('guest')
          setAuthMessage('Password changed. Please sign in again with the new password.')
          writeRoute('#/login', true)
        }}
      />
    )
  }

  return <DashboardShell currentUser={currentUser} onLogout={handleLogout} />
}

function DashboardShell({ currentUser, onLogout }: { currentUser: CurrentUser; onLogout: () => void }) {
  const role = currentUser.role
  const [activeKey, setActiveKey] = useState<ModuleKey>(() => moduleKeyFromHash(role))
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)

  const visibleModules = useMemo(() => modules.filter((module) => module.roles.includes(role)), [role])
  const activeModule = visibleModules.find((module) => module.key === activeKey) ?? visibleModules[0]
  const hasDedicatedExperience = ['dashboard', 'users', 'academic', 'classes', 'content', 'assignments', 'attendance', 'quizzes', 'gradebook', 'progress', 'projects'].includes(activeModule.key)

  useEffect(() => {
    function syncRoute() {
      const nextKey = moduleKeyFromHash(role)
      setActiveKey(nextKey)
      if (!window.location.hash.startsWith(`#/${role}/`)) {
        writeRoute(`#/${role}/${nextKey}`, true)
      }
    }

    syncRoute()
    window.addEventListener('hashchange', syncRoute)
    return () => window.removeEventListener('hashchange', syncRoute)
  }, [role])

  function navigateTo(moduleKey: ModuleKey) {
    setActiveKey(moduleKey)
    setSidebarOpen(false)
    writeRoute(`#/${role}/${moduleKey}`)
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? 'is-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">ICA</div>
          <div>
            <strong>ICA Academy</strong>
            <span>CRM / LMS</span>
          </div>
        </div>

        <div className="role-card">
          <span>Current role</span>
          <strong>{roleProfiles[role].label}</strong>
          <small>{currentUser.email}</small>
        </div>

        <nav className="nav-groups" aria-label="Main navigation">
          {navGroups
            .filter((group) => group.roles.includes(role))
            .map((group) => (
              <details key={group.label} open>
                <summary>
                  {group.label}
                  <ChevronDown size={16} />
                </summary>
                <div className="nav-items">
                  {group.items
                    .filter((item) => item.roles.includes(role))
                    .map((item) => (
                      <button
                        key={item.key}
                        type="button"
                        className={activeModule.key === item.key ? 'active' : ''}
                        onClick={() => navigateTo(item.key)}
                      >
                        <item.icon size={18} />
                        <span>{item.label}</span>
                      </button>
                    ))}
                </div>
              </details>
            ))}
        </nav>

        <div className="sidebar-footer">
          <button type="button">
            <Settings size={18} />
            Workspace settings
          </button>
          <button type="button" onClick={onLogout}>
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <button className="icon-button mobile-only" type="button" onClick={() => setSidebarOpen(true)} aria-label="Open menu">
            <Menu size={20} />
          </button>

          <label className="search-box">
            <Search size={18} />
            <input placeholder="Search users, classes, submissions, grade entries" />
          </label>

          <div className="topbar-actions">
            <select className="compact-select" aria-label="Global cycle">
              <option>Cycle 1</option>
              <option>Cycle 2</option>
              <option>Closed cycles</option>
            </select>

            <button className="icon-button" type="button" aria-label="Refresh data">
              <RefreshCw size={18} />
            </button>

            <details className="dropdown-menu">
              <summary aria-label="Notifications">
                <Bell size={18} />
                <span className="dot"></span>
              </summary>
              <div className="dropdown-panel dropdown-panel-right">
                <button type="button">Unread low-progress alerts</button>
                <button type="button">Run progress check</button>
                <button type="button">Mark all read</button>
              </div>
            </details>

            <details className="profile-menu">
              <summary>
                <span className="avatar">{roleProfiles[role].label.slice(0, 1)}</span>
                <span>
                  <strong>{displayNameFor(currentUser)}</strong>
                  <small>{workspaceFor(currentUser)}</small>
                </span>
                <ChevronDown size={16} />
              </summary>
              <div className="dropdown-panel dropdown-panel-right">
                <button type="button">My profile</button>
                <button type="button">Change password</button>
                <button type="button" onClick={onLogout}>Logout</button>
              </div>
            </details>
          </div>
        </header>

        <section className={`module-hero accent-${activeModule.accent}`}>
          <div>
            <span className="eyebrow">{activeModule.eyebrow}</span>
            <h1>{activeModule.title}</h1>
            <p>{activeModule.description}</p>
          </div>
          <div className="hero-actions">
            <span className="endpoint-pill">{activeModule.endpoint}</span>
            {!hasDedicatedExperience && <button className="primary-button" type="button" onClick={() => setModalOpen(true)}>
              <Plus size={18} />
              New workflow
            </button>}
          </div>
        </section>

        {role === 'admin' && activeModule.key === 'dashboard' ? (
          <AdminDashboardExperience />
        ) : role === 'admin' && activeModule.key === 'users' ? (
          <AdminUsersExperience />
        ) : role === 'admin' && activeModule.key === 'academic' ? (
          <AdminAcademicExperience />
        ) : role === 'admin' && activeModule.key === 'classes' ? (
          <AdminEnrollmentExperience />
        ) : activeModule.key === 'content' ? (
          <LmsMaterialsExperience currentUser={currentUser} />
        ) : activeModule.key === 'assignments' ? (
          <LmsAssignmentsExperience currentUser={currentUser} />
        ) : activeModule.key === 'attendance' ? (
          <AttendanceExperience currentUser={currentUser} />
        ) : activeModule.key === 'quizzes' ? (
          <QuizzesExperience currentUser={currentUser} />
        ) : activeModule.key === 'gradebook' ? (
          <GradebookExperience currentUser={currentUser} />
        ) : activeModule.key === 'progress' ? (
          <ProgressRankingExperience currentUser={currentUser} />
        ) : activeModule.key === 'projects' ? (
          <FinalProjectsExperience currentUser={currentUser} />
        ) : (
          <GenericModuleExperience activeModule={activeModule} role={role} onOpenModal={() => setModalOpen(true)} />
        )}
      </main>

      {sidebarOpen && <button className="scrim" type="button" onClick={() => setSidebarOpen(false)} aria-label="Close menu" />}

      {modalOpen && (
        <div className="modal-backdrop" role="presentation">
          <section className="modal" role="dialog" aria-modal="true" aria-labelledby="workflow-title">
            <div className="modal-header">
              <div>
                <span className="eyebrow">API workflow</span>
                <h2 id="workflow-title">{activeModule.title}</h2>
              </div>
              <button className="icon-button" type="button" onClick={() => setModalOpen(false)} aria-label="Close modal">
                <X size={20} />
              </button>
            </div>
            <div className="modal-body">
              <div className="api-callout">
                <Shield size={20} />
                <span>{activeModule.endpoint}</span>
              </div>
              <form className="modal-form">
                {workflowFields[activeModule.key].map((field) => (
                  <label key={field.label}>
                    <span>{field.label}</span>
                    {field.type === 'select' ? (
                      <select>
                        {field.options?.map((option) => (
                          <option key={option}>{option}</option>
                        ))}
                      </select>
                    ) : (
                      <input placeholder={`Enter ${field.label.toLowerCase()}`} />
                    )}
                  </label>
                ))}
              </form>
            </div>
            <div className="modal-actions">
              <button type="button" onClick={() => setModalOpen(false)}>
                Cancel
              </button>
              <button className="primary-button" type="button" onClick={() => setModalOpen(false)}>
                Save draft
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

function GenericModuleExperience({
  activeModule,
  role,
  onOpenModal,
}: {
  activeModule: ModuleView
  role: Role
  onOpenModal: () => void
}) {
  return (
    <>
      <section className="stats-grid" aria-label="Module metrics">
        {activeModule.stats.map((stat) => (
          <article className="stat-card" key={stat.label}>
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
            <small>{stat.trend}</small>
          </article>
        ))}
      </section>

      <section className="content-grid">
        <div className="data-panel">
          <div className="panel-toolbar">
            <div>
              <h2>{activeModule.title} Records</h2>
              <p>Filtered table shaped for the backend response envelopes.</p>
            </div>
            <div className="filter-row">
              {activeModule.filters.map((filter) => (
                <label key={filter.label}>
                  <span>{filter.label}</span>
                  <select>
                    {filter.options.map((option) => (
                      <option key={option}>{option}</option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {activeModule.columns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {activeModule.rows.map((row, rowIndex) => (
                  <tr key={`${activeModule.key}-${rowIndex}`}>
                    {activeModule.columns.map((column) => (
                      <td key={column}>
                        {column.toLowerCase().includes('status') || column.toLowerCase().includes('signal') ? (
                          <StatusBadge value={row[column]} />
                        ) : (
                          row[column]
                        )}
                      </td>
                    ))}
                    <td>
                      <ActionMenu actions={activeModule.actions} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="workflow-panel">
          <div className="panel-heading">
            <activeModule.icon size={22} />
            <div>
              <h2>Quick Workflow</h2>
              <p>{roleProfiles[role].label} scoped controls</p>
            </div>
          </div>

          <form>
            {workflowFields[activeModule.key].map((field) => (
              <label key={field.label}>
                <span>{field.label}</span>
                {field.type === 'select' ? (
                  <select>
                    {field.options?.map((option) => (
                      <option key={option}>{option}</option>
                    ))}
                  </select>
                ) : (
                  <input placeholder={`Enter ${field.label.toLowerCase()}`} />
                )}
              </label>
            ))}

            <div className="segmented-control" aria-label="Record state">
              <button type="button" className="selected">
                Active
              </button>
              <button type="button">Pending</button>
              <button type="button">History</button>
            </div>

            <button type="button" className="primary-button full-width" onClick={onOpenModal}>
              <CheckCircle2 size={18} />
              Open action modal
            </button>
          </form>

          <div className="rules-list">
            <strong>Backend rules reflected here</strong>
            <span>No public registration</span>
            <span>Soft delete keeps history</span>
            <span>Role scope controls every view</span>
          </div>
        </aside>
      </section>
    </>
  )
}

function AdminDashboardExperience() {
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null)
  const [notifications, setNotifications] = useState<AdminNotification[]>([])
  const [unreadCount, setUnreadCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let mounted = true

    async function loadDashboard() {
      setLoading(true)
      setMessage('')
      try {
        const [dashboardEnvelope, notificationsEnvelope, unreadEnvelope] = await Promise.all([
          getAdminDashboard(),
          listAdminNotifications(),
          getAdminUnreadCount(),
        ])
        if (!mounted) {
          return
        }
        setDashboard(dashboardEnvelope.data)
        setNotifications(notificationsEnvelope.data)
        setUnreadCount(unreadEnvelope.data.unread_count)
      } catch (error) {
        if (mounted) {
          setMessage(errorMessage(error))
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    void loadDashboard()

    return () => {
      mounted = false
    }
  }, [])

  const stats = [
    { label: 'Total students', value: dashboard?.total_students ?? '...', hint: `${dashboard?.active_students ?? 0} active` },
    { label: 'Teachers', value: dashboard?.total_teachers ?? '...', hint: 'Admin visible' },
    { label: 'Active classes', value: dashboard?.active_classes ?? '...', hint: `${dashboard?.total_classes ?? 0} total classes` },
    { label: 'Unread alerts', value: unreadCount ?? dashboard?.unread_notifications_count ?? '...', hint: 'Internal only' },
    { label: 'Low students', value: dashboard?.low_progress_students_count ?? '...', hint: 'Below 50%' },
    { label: 'Low instructors', value: dashboard?.low_progress_instructors_count ?? '...', hint: 'Below 50%' },
    { label: 'Low mentors', value: dashboard?.low_progress_mentors_count ?? '...', hint: 'Below 70%' },
    { label: 'Suspended', value: dashboard?.suspended_students ?? '...', hint: `${dashboard?.dropped_students ?? 0} dropped` },
  ]

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}

      <div className="stats-grid admin-stats" aria-label="Admin dashboard metrics">
        {stats.map((stat) => (
          <article className="stat-card" key={stat.label}>
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
            <small>{loading ? 'Loading from API' : stat.hint}</small>
          </article>
        ))}
      </div>

      <section className="content-grid">
        <div className="data-panel">
          <div className="panel-toolbar">
            <div>
              <h2>Classes Summary</h2>
              <p>Read from /api/admin/dashboard.</p>
            </div>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Class</th>
                  <th>Status</th>
                  <th>Active students</th>
                  <th>Progress</th>
                </tr>
              </thead>
              <tbody>
                {(dashboard?.classes_summary ?? []).map((item) => (
                  <tr key={item.class_id}>
                    <td>{item.class_code}</td>
                    <td><StatusBadge value={item.status} /></td>
                    <td>{item.active_students}</td>
                    <td>{formatPercent(item.class_progress)}</td>
                  </tr>
                ))}
                {!loading && !dashboard?.classes_summary.length && (
                  <tr>
                    <td colSpan={4}>No class summary records returned yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="workflow-panel">
          <div className="panel-heading">
            <Bell size={22} />
            <div>
              <h2>Admin Notifications</h2>
              <p>{unreadCount ?? 0} unread internal alerts</p>
            </div>
          </div>
          <div className="notification-list">
            {notifications.slice(0, 5).map((notification) => (
              <article key={notification.id}>
                <StatusBadge value={notification.severity} />
                <strong>{notification.title}</strong>
                <span>{notification.message}</span>
              </article>
            ))}
            {!loading && notifications.length === 0 && <span className="empty-text">No notifications returned yet.</span>}
          </div>
        </aside>
      </section>
    </section>
  )
}

type UserModalState =
  | { type: 'create'; user?: never }
  | { type: 'edit'; user: CurrentUser }
  | { type: 'delete'; user: CurrentUser }
  | { type: 'reset'; user: CurrentUser }
  | null

type UserFormState = {
  email: string
  password: string
  role: Role
  is_active: boolean
  full_name: string
  phone_number: string
  teacher_code: string
  teacher_type: 'mentor' | 'instructor' | 'instructor_and_mentor'
  is_team_leader: boolean
  student_code: string
  student_status: 'active' | 'inactive' | 'suspended' | 'dropped' | 'graduated'
}

const emptyUserForm: UserFormState = {
  email: '',
  password: '',
  role: 'student',
  is_active: true,
  full_name: '',
  phone_number: '',
  teacher_code: '',
  teacher_type: 'instructor',
  is_team_leader: false,
  student_code: '',
  student_status: 'active',
}

function AdminUsersExperience() {
  const [users, setUsers] = useState<CurrentUser[]>([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [roleFilter, setRoleFilter] = useState<'all' | Role>('all')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'must_change_password'>('all')
  const [modal, setModal] = useState<UserModalState>(null)

  async function loadUsers() {
    setLoading(true)
    setMessage('')
    try {
      const envelope = await listUsers()
      setUsers(envelope.data)
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true

    async function loadInitialUsers() {
      try {
        const envelope = await listUsers()
        if (mounted) {
          setUsers(envelope.data)
        }
      } catch (error) {
        if (mounted) {
          setMessage(errorMessage(error))
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    void loadInitialUsers()

    return () => {
      mounted = false
    }
  }, [])

  const filteredUsers = users.filter((user) => {
    const roleMatches = roleFilter === 'all' || user.role === roleFilter
    const statusMatches =
      statusFilter === 'all' ||
      (statusFilter === 'active' && user.is_active && !user.must_change_password) ||
      (statusFilter === 'inactive' && !user.is_active) ||
      (statusFilter === 'must_change_password' && user.must_change_password)
    return roleMatches && statusMatches
  })

  async function handleCreate(payload: UserCreate) {
    await createUser(payload)
    setModal(null)
    await loadUsers()
  }

  async function handleUpdate(userId: string, payload: UserUpdate) {
    await updateUser(userId, payload)
    setModal(null)
    await loadUsers()
  }

  async function handleDelete(userId: string) {
    await deleteUser(userId)
    setModal(null)
    await loadUsers()
  }

  async function handleReset(userId: string, newPassword: string) {
    await resetUserPassword({ user_id: userId, new_password: newPassword })
    setModal(null)
    await loadUsers()
  }

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}

      <section className="stats-grid" aria-label="Users summary">
        <article className="stat-card">
          <span>Total users</span>
          <strong>{loading ? '...' : users.length}</strong>
          <small>From /api/users</small>
        </article>
        <article className="stat-card">
          <span>Admins</span>
          <strong>{countUsers(users, 'admin')}</strong>
          <small>Can manage accounts</small>
        </article>
        <article className="stat-card">
          <span>Teachers</span>
          <strong>{countUsers(users, 'teacher')}</strong>
          <small>Instructor / mentor profiles</small>
        </article>
        <article className="stat-card">
          <span>Students</span>
          <strong>{countUsers(users, 'student')}</strong>
          <small>Student profiles</small>
        </article>
      </section>

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div>
            <h2>Users</h2>
            <p>Create, edit, soft-delete, and reset passwords for academy accounts.</p>
          </div>
          <div className="admin-toolbar">
            <label>
              <span>Role</span>
              <select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value as 'all' | Role)}>
                <option value="all">All roles</option>
                <option value="admin">Admin</option>
                <option value="teacher">Teacher</option>
                <option value="student">Student</option>
              </select>
            </label>
            <label>
              <span>Status</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}>
                <option value="all">All statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="must_change_password">Must change password</option>
              </select>
            </label>
            <button className="primary-button" type="button" onClick={() => setModal({ type: 'create' })}>
              <Plus size={18} />
              Create user
            </button>
          </div>
        </div>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Profile</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr key={user.id}>
                  <td>{user.email}</td>
                  <td>{titleCase(user.role)}</td>
                  <td>{profileSummary(user)}</td>
                  <td><StatusBadge value={userStatus(user)} /></td>
                  <td>
                    <AdminUserActionMenu
                      onEdit={() => setModal({ type: 'edit', user })}
                      onReset={() => setModal({ type: 'reset', user })}
                      onDelete={() => setModal({ type: 'delete', user })}
                    />
                  </td>
                </tr>
              ))}
              {!loading && filteredUsers.length === 0 && (
                <tr>
                  <td colSpan={5}>No users match the selected filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {modal?.type === 'create' && (
        <UserFormModal
          title="Create user"
          mode="create"
          onClose={() => setModal(null)}
          onSubmit={(payload) => handleCreate(payload as UserCreate)}
        />
      )}

      {modal?.type === 'edit' && (
        <UserFormModal
          title="Edit user"
          mode="edit"
          user={modal.user}
          onClose={() => setModal(null)}
          onSubmit={(payload) => handleUpdate(modal.user.id, payload as UserUpdate)}
        />
      )}

      {modal?.type === 'delete' && (
        <ConfirmModal
          title="Soft delete user"
          message={`Soft delete ${modal.user.email}? The backend keeps history and removes the account from normal flows.`}
          confirmLabel="Soft delete"
          onClose={() => setModal(null)}
          onConfirm={() => handleDelete(modal.user.id)}
        />
      )}

      {modal?.type === 'reset' && (
        <ResetPasswordModal
          user={modal.user}
          onClose={() => setModal(null)}
          onSubmit={(newPassword) => handleReset(modal.user.id, newPassword)}
        />
      )}
    </section>
  )
}

type AcademicKind = 'branches' | 'cycles' | 'tracks' | 'levels' | 'classes'
type AcademicRecord = Branch | Cycle | Track | Level | AcademicClass
type AcademicModalState =
  | { type: 'create'; kind: AcademicKind }
  | { type: 'edit'; kind: AcademicKind; record: AcademicRecord }
  | { type: 'delete'; kind: AcademicKind; record: AcademicRecord }
  | null

type AcademicFormState = {
  name: string
  cycle_number: string
  start_date: string
  end_date: string
  cycle_status: 'active' | 'closed'
  code: string
  track_number: string
  create_default_levels: boolean
  track_id: string
  level_number: string
  title: string
  duration_months: string
  branch_id: string
  cycle_id: string
  level_id: string
  instructor_id: string
  mentor_id: string
  schedule_text: string
  max_students: string
  class_type: 'online' | 'onsite'
  class_status: 'planned' | 'active' | 'completed' | 'cancelled'
}

const academicKinds: Array<{ key: AcademicKind; label: string }> = [
  { key: 'branches', label: 'Branches' },
  { key: 'cycles', label: 'Cycles' },
  { key: 'tracks', label: 'Tracks' },
  { key: 'levels', label: 'Levels' },
  { key: 'classes', label: 'Classes' },
]

const emptyAcademicForm: AcademicFormState = {
  name: '',
  cycle_number: '1',
  start_date: '',
  end_date: '',
  cycle_status: 'active',
  code: '',
  track_number: '1',
  create_default_levels: false,
  track_id: '',
  level_number: '1',
  title: '',
  duration_months: '2',
  branch_id: '',
  cycle_id: '',
  level_id: '',
  instructor_id: '',
  mentor_id: '',
  schedule_text: '',
  max_students: '25',
  class_type: 'online',
  class_status: 'planned',
}

function AdminAcademicExperience() {
  const [activeKind, setActiveKind] = useState<AcademicKind>('branches')
  const [branches, setBranches] = useState<Branch[]>([])
  const [cycles, setCycles] = useState<Cycle[]>([])
  const [tracks, setTracks] = useState<Track[]>([])
  const [levels, setLevels] = useState<Level[]>([])
  const [classes, setClasses] = useState<AcademicClass[]>([])
  const [users, setUsers] = useState<CurrentUser[]>([])
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [modal, setModal] = useState<AcademicModalState>(null)

  async function loadAcademicData() {
    setLoading(true)
    setMessage('')
    try {
      const [branchData, cycleData, trackData, levelData, classData, userData] = await Promise.all([
        listBranches(),
        listCycles(),
        listTracks(),
        listLevels(),
        listClasses(),
        listUsers(),
      ])
      setBranches(branchData.data)
      setCycles(cycleData.data)
      setTracks(trackData.data)
      setLevels(levelData.data)
      setClasses(classData.data)
      setUsers(userData.data)
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true

    async function loadInitialAcademicData() {
      try {
        const [branchData, cycleData, trackData, levelData, classData, userData] = await Promise.all([
          listBranches(),
          listCycles(),
          listTracks(),
          listLevels(),
          listClasses(),
          listUsers(),
        ])
        if (!mounted) {
          return
        }
        setBranches(branchData.data)
        setCycles(cycleData.data)
        setTracks(trackData.data)
        setLevels(levelData.data)
        setClasses(classData.data)
        setUsers(userData.data)
      } catch (error) {
        if (mounted) {
          setMessage(errorMessage(error))
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    void loadInitialAcademicData()

    return () => {
      mounted = false
    }
  }, [])

  const records = filterAcademicRecords(getAcademicRecords(activeKind, { branches, cycles, tracks, levels, classes }), query, statusFilter)
  const teachers = users.filter((user) => user.role === 'teacher' && user.teacher_profile)

  async function handleSave(kind: AcademicKind, mode: 'create' | 'edit', id: string | null, form: AcademicFormState) {
    if (kind === 'branches') {
      const payload = academicPayload(kind, form) as BranchCreate | BranchUpdate
      if (mode === 'create') {
        await createBranch(payload as BranchCreate)
      } else if (id) {
        await updateBranch(id, payload as BranchUpdate)
      }
    }

    if (kind === 'cycles') {
      const payload = academicPayload(kind, form) as CycleCreate | CycleUpdate
      if (mode === 'create') {
        await createCycle(payload as CycleCreate)
      } else if (id) {
        await updateCycle(id, payload as CycleUpdate)
      }
    }

    if (kind === 'tracks') {
      const payload = academicPayload(kind, form) as TrackCreate | TrackUpdate
      if (mode === 'create') {
        await createTrack(payload as TrackCreate)
      } else if (id) {
        await updateTrack(id, payload as TrackUpdate)
      }
    }

    if (kind === 'levels') {
      const payload = academicPayload(kind, form) as LevelCreate | LevelUpdate
      if (mode === 'create') {
        await createLevel(payload as LevelCreate)
      } else if (id) {
        await updateLevel(id, payload as LevelUpdate)
      }
    }

    if (kind === 'classes') {
      const payload = academicPayload(kind, form) as ClassCreate | ClassUpdate
      if (mode === 'create') {
        await createClass(payload as ClassCreate)
      } else if (id) {
        await updateClass(id, payload as ClassUpdate)
      }
    }

    setModal(null)
    await loadAcademicData()
  }

  async function handleDelete(kind: AcademicKind, id: string) {
    if (kind === 'branches') await deleteBranch(id)
    if (kind === 'cycles') await deleteCycle(id)
    if (kind === 'tracks') await deleteTrack(id)
    if (kind === 'levels') await deleteLevel(id)
    if (kind === 'classes') await deleteClass(id)
    setModal(null)
    await loadAcademicData()
  }

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}

      <section className="stats-grid" aria-label="Academic setup summary">
        <article className="stat-card"><span>Branches</span><strong>{loading ? '...' : branches.length}</strong><small>Campus and delivery locations</small></article>
        <article className="stat-card"><span>Cycles</span><strong>{loading ? '...' : cycles.length}</strong><small>{cycles.filter((item) => item.status === 'active').length} active</small></article>
        <article className="stat-card"><span>Tracks</span><strong>{loading ? '...' : tracks.length}</strong><small>Codes drive class format</small></article>
        <article className="stat-card"><span>Classes</span><strong>{loading ? '...' : classes.length}</strong><small>{classes.filter((item) => item.status === 'active').length} active</small></article>
      </section>

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div>
            <h2>Academic Setup</h2>
            <p>Manage branches, cycles, tracks, levels, and class structure.</p>
          </div>

          <div className="academic-tabs" role="tablist" aria-label="Academic setup screens">
            {academicKinds.map((kind) => (
              <button
                key={kind.key}
                type="button"
                className={activeKind === kind.key ? 'selected' : ''}
                onClick={() => {
                  setActiveKind(kind.key)
                  setStatusFilter('all')
                }}
              >
                {kind.label}
              </button>
            ))}
          </div>

          <div className="admin-toolbar academic-toolbar">
            <label>
              <span>Search</span>
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search current screen" />
            </label>
            <label>
              <span>Filter</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="all">All records</option>
                {activeKind === 'cycles' && <option value="active">Active cycles</option>}
                {activeKind === 'cycles' && <option value="closed">Closed cycles</option>}
                {activeKind === 'classes' && <option value="planned">Planned classes</option>}
                {activeKind === 'classes' && <option value="active">Active classes</option>}
                {activeKind === 'classes' && <option value="completed">Completed classes</option>}
                {activeKind === 'classes' && <option value="cancelled">Cancelled classes</option>}
                {activeKind === 'classes' && <option value="online">Online classes</option>}
                {activeKind === 'classes' && <option value="onsite">Onsite classes</option>}
                {activeKind === 'levels' && tracks.map((track) => <option key={track.id} value={track.id}>{track.name}</option>)}
              </select>
            </label>
            <button className="primary-button" type="button" onClick={() => setModal({ type: 'create', kind: activeKind })}>
              <Plus size={18} />
              Create {academicLabel(activeKind)}
            </button>
          </div>
        </div>

        <AcademicTable
          kind={activeKind}
          records={records}
          branches={branches}
          cycles={cycles}
          tracks={tracks}
          levels={levels}
          teachers={teachers}
          onEdit={(record) => setModal({ type: 'edit', kind: activeKind, record })}
          onDelete={(record) => setModal({ type: 'delete', kind: activeKind, record })}
        />
      </section>

      {(modal?.type === 'create' || modal?.type === 'edit') && (
        <AcademicFormModal
          mode={modal.type}
          kind={modal.kind}
          record={modal.type === 'edit' ? modal.record : undefined}
          branches={branches}
          cycles={cycles}
          tracks={tracks}
          levels={levels}
          teachers={teachers}
          onClose={() => setModal(null)}
          onSubmit={(form) => handleSave(modal.kind, modal.type, modal.type === 'edit' ? modal.record.id : null, form)}
        />
      )}

      {modal?.type === 'delete' && (
        <ConfirmModal
          title={`Delete ${academicLabel(modal.kind)}`}
          message={`Soft delete ${academicRecordName(modal.kind, modal.record)}? Related history remains in the backend.`}
          confirmLabel="Delete"
          onClose={() => setModal(null)}
          onConfirm={() => handleDelete(modal.kind, modal.record.id)}
        />
      )}
    </section>
  )
}

type EnrollmentModalState =
  | { type: 'enroll' }
  | { type: 'remove'; enrollment: Enrollment }
  | null

type EnrollmentFormState = {
  class_id: string
  student_id: string
}

function AdminEnrollmentExperience() {
  const [enrollments, setEnrollments] = useState<Enrollment[]>([])
  const [classes, setClasses] = useState<AcademicClass[]>([])
  const [branches, setBranches] = useState<Branch[]>([])
  const [cycles, setCycles] = useState<Cycle[]>([])
  const [tracks, setTracks] = useState<Track[]>([])
  const [levels, setLevels] = useState<Level[]>([])
  const [users, setUsers] = useState<CurrentUser[]>([])
  const [selectedClassId, setSelectedClassId] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'completed' | 'removed'>('all')
  const [branchFilter, setBranchFilter] = useState('all')
  const [cycleFilter, setCycleFilter] = useState('all')
  const [trackFilter, setTrackFilter] = useState('all')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [modal, setModal] = useState<EnrollmentModalState>(null)

  async function loadEnrollmentData() {
    setLoading(true)
    setMessage('')
    try {
      const [enrollmentData, classData, branchData, cycleData, trackData, levelData, userData] = await Promise.all([
        listEnrollments(),
        listClasses(),
        listBranches(),
        listCycles(),
        listTracks(),
        listLevels(),
        listUsers(),
      ])
      setEnrollments(enrollmentData.data)
      setClasses(classData.data)
      setBranches(branchData.data)
      setCycles(cycleData.data)
      setTracks(trackData.data)
      setLevels(levelData.data)
      setUsers(userData.data)
      setSelectedClassId((current) => current || classData.data[0]?.id || '')
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true

    async function loadInitialEnrollmentData() {
      try {
        const [enrollmentData, classData, branchData, cycleData, trackData, levelData, userData] = await Promise.all([
          listEnrollments(),
          listClasses(),
          listBranches(),
          listCycles(),
          listTracks(),
          listLevels(),
          listUsers(),
        ])
        if (!mounted) return
        setEnrollments(enrollmentData.data)
        setClasses(classData.data)
        setBranches(branchData.data)
        setCycles(cycleData.data)
        setTracks(trackData.data)
        setLevels(levelData.data)
        setUsers(userData.data)
        setSelectedClassId(classData.data[0]?.id || '')
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    void loadInitialEnrollmentData()

    return () => {
      mounted = false
    }
  }, [])

  const selectedClass = classes.find((item) => item.id === selectedClassId) ?? classes[0]
  const activeCount = selectedClass ? activeEnrollmentCount(enrollments, selectedClass.id) : 0
  const classEnrollments = selectedClass ? enrollments.filter((item) => item.class_id === selectedClass.id) : []
  const filteredEnrollments = enrollments.filter((item) => {
    const academicClass = classes.find((classItem) => classItem.id === item.class_id)
    const normalizedQuery = query.trim().toLowerCase()
    const textMatches =
      !normalizedQuery ||
      `${item.student_code} ${item.student_full_name} ${item.class_code} ${item.track_name}`.toLowerCase().includes(normalizedQuery)
    const statusMatches = statusFilter === 'all' || item.status === statusFilter
    const branchMatches = branchFilter === 'all' || academicClass?.branch_id === branchFilter
    const cycleMatches = cycleFilter === 'all' || academicClass?.cycle_id === cycleFilter
    const trackMatches = trackFilter === 'all' || academicClass?.track_id === trackFilter
    return textMatches && statusMatches && branchMatches && cycleMatches && trackMatches
  })
  const studentOptions = users.filter((user) => user.role === 'student' && user.student_profile)
  const teacherOptions = users.filter((user) => user.role === 'teacher' && user.teacher_profile)

  async function handleEnroll(payload: EnrollmentCreate) {
    await createEnrollment(payload)
    setModal(null)
    await loadEnrollmentData()
  }

  async function handleRemove(enrollmentId: string) {
    await removeEnrollment(enrollmentId)
    setModal(null)
    await loadEnrollmentData()
  }

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}

      <section className="stats-grid" aria-label="Enrollment summary">
        <article className="stat-card"><span>Total enrollments</span><strong>{loading ? '...' : enrollments.length}</strong><small>Includes removed history</small></article>
        <article className="stat-card"><span>Active enrollments</span><strong>{enrollments.filter((item) => item.status === 'active').length}</strong><small>Current students in classes</small></article>
        <article className="stat-card"><span>Selected class</span><strong>{selectedClass?.code ?? '...'}</strong><small>{selectedClass ? classStatusLine(selectedClass, activeCount) : 'Choose a class'}</small></article>
        <article className="stat-card"><span>Capacity</span><strong>{selectedClass ? `${activeCount}/${selectedClass.max_students}` : '...'}</strong><small>{selectedClass ? capacityStatus(activeCount, selectedClass.max_students) : 'No class selected'}</small></article>
      </section>

      <section className="class-info-panel">
        <div>
          <span className="eyebrow">Class roster view</span>
          <h2>{selectedClass?.code ?? 'Select a class'}</h2>
          <p>
            {selectedClass
              ? `${branchName(branches, selectedClass.branch_id)} / ${trackName(tracks, selectedClass.track_id)} / ${levelName(levels, selectedClass.level_id)}`
              : 'Class details will appear here.'}
          </p>
        </div>
        <div className="class-info-grid">
          <span><strong>Status</strong>{selectedClass?.status ?? '-'}</span>
          <span><strong>Instructor</strong>{selectedClass ? teacherName(teacherOptions, selectedClass.instructor_id) : '-'}</span>
          <span><strong>Mentor</strong>{selectedClass ? teacherName(teacherOptions, selectedClass.mentor_id) : '-'}</span>
          <span><strong>Capacity</strong>{selectedClass ? capacityStatus(activeCount, selectedClass.max_students) : '-'}</span>
        </div>
      </section>

      <section className="content-grid enrollment-grid">
        <div className="data-panel">
          <div className="panel-toolbar">
            <div>
              <h2>Enrollment List</h2>
              <p>Admin list from /api/enrollments with class, branch, cycle, track, and status filters.</p>
            </div>
            <div className="admin-toolbar enrollment-toolbar">
              <label><span>Search</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Student, code, class" /></label>
              <label><span>Status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}><option value="all">All statuses</option><option value="active">Active</option><option value="completed">Completed</option><option value="removed">Removed</option></select></label>
              <label><span>Branch</span><select value={branchFilter} onChange={(event) => setBranchFilter(event.target.value)}><option value="all">All branches</option>{branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label>
              <label><span>Cycle</span><select value={cycleFilter} onChange={(event) => setCycleFilter(event.target.value)}><option value="all">All cycles</option>{cycles.map((cycle) => <option key={cycle.id} value={cycle.id}>{cycle.name}</option>)}</select></label>
              <label><span>Track</span><select value={trackFilter} onChange={(event) => setTrackFilter(event.target.value)}><option value="all">All tracks</option>{tracks.map((track) => <option key={track.id} value={track.id}>{track.code} - {track.name}</option>)}</select></label>
              <button className="primary-button" type="button" onClick={() => setModal({ type: 'enroll' })}><Plus size={18} />Enroll student</button>
            </div>
          </div>
          <EnrollmentTable enrollments={filteredEnrollments} onRemove={(enrollment) => setModal({ type: 'remove', enrollment })} />
        </div>

        <aside className="workflow-panel">
          <div className="panel-heading">
            <Users size={22} />
            <div>
              <h2>Class Roster</h2>
              <p>{classEnrollments.filter((item) => item.status === 'active').length} active students</p>
            </div>
          </div>
          <label className="roster-selector">
            <span>Class selector</span>
            <select value={selectedClassId} onChange={(event) => setSelectedClassId(event.target.value)}>
              {classes.map((classItem) => (
                <option key={classItem.id} value={classItem.id}>{classItem.code}</option>
              ))}
            </select>
          </label>
          <div className="roster-list">
            {classEnrollments.map((enrollment) => (
              <article key={enrollment.id}>
                <strong>{enrollment.student_full_name}</strong>
                <span>{enrollment.student_code}</span>
                <StatusBadge value={enrollment.status} />
              </article>
            ))}
            {!classEnrollments.length && <span className="empty-text">No enrollments for this class yet.</span>}
          </div>
        </aside>
      </section>

      {modal?.type === 'enroll' && (
        <EnrollmentFormModal
          classes={classes}
          students={studentOptions}
          defaultClassId={selectedClass?.id ?? ''}
          onClose={() => setModal(null)}
          onSubmit={handleEnroll}
        />
      )}

      {modal?.type === 'remove' && (
        <ConfirmModal
          title="Remove enrollment"
          message={`Remove ${modal.enrollment.student_full_name} from ${modal.enrollment.class_code}? History will remain available to Admin.`}
          confirmLabel="Remove enrollment"
          onClose={() => setModal(null)}
          onConfirm={() => handleRemove(modal.enrollment.id)}
        />
      )}
    </section>
  )
}

function EnrollmentTable({
  enrollments,
  onRemove,
}: {
  enrollments: Enrollment[]
  onRemove: (enrollment: Enrollment) => void
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Student</th>
            <th>Class</th>
            <th>Structure</th>
            <th>Status</th>
            <th>Enrolled</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {enrollments.map((enrollment) => (
            <tr key={enrollment.id}>
              <td>{enrollment.student_full_name}<br /><small>{enrollment.student_code}</small></td>
              <td><span className="class-code">{enrollment.class_code}</span></td>
              <td>{enrollment.branch_name} / {enrollment.track_name} L{enrollment.level_number}<br /><small>{enrollment.cycle_name}</small></td>
              <td><StatusBadge value={enrollment.status} /></td>
              <td>{compactDate(enrollment.enrolled_at)}</td>
              <td><EnrollmentActionMenu canRemove={enrollment.status === 'active'} onRemove={() => onRemove(enrollment)} /></td>
            </tr>
          ))}
          {enrollments.length === 0 && (
            <tr>
              <td colSpan={6}>No enrollments match the selected filters.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

function EnrollmentActionMenu({ canRemove, onRemove }: { canRemove: boolean; onRemove: () => void }) {
  return (
    <details className="dropdown-menu row-menu">
      <summary aria-label="Enrollment row actions">
        <MoreHorizontal size={18} />
      </summary>
      <div className="dropdown-panel dropdown-panel-right">
        <button type="button" disabled={!canRemove} onClick={onRemove}>Remove enrollment</button>
        <button type="button">View class roster</button>
      </div>
    </details>
  )
}

function EnrollmentFormModal({
  classes,
  students,
  defaultClassId,
  onClose,
  onSubmit,
}: {
  classes: AcademicClass[]
  students: CurrentUser[]
  defaultClassId: string
  onClose: () => void
  onSubmit: (payload: EnrollmentCreate) => Promise<void>
}) {
  const [form, setForm] = useState<EnrollmentFormState>({
    class_id: defaultClassId || classes[0]?.id || '',
    student_id: students[0]?.student_profile?.id ?? '',
  })
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit(form)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal confirm-modal" role="dialog" aria-modal="true" aria-labelledby="enroll-title">
        <div className="modal-header">
          <div>
            <span className="eyebrow">Admin enrollment</span>
            <h2 id="enroll-title">Enroll student</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <label>
              <span>Class selector</span>
              <select value={form.class_id} onChange={(event) => setForm({ ...form, class_id: event.target.value })} required>
                {classes.map((classItem) => (
                  <option key={classItem.id} value={classItem.id}>{classItem.code} / {classItem.status}</option>
                ))}
              </select>
            </label>
            <label>
              <span>Student selector</span>
              <select value={form.student_id} onChange={(event) => setForm({ ...form, student_id: event.target.value })} required>
                {students.map((student) => (
                  <option key={student.student_profile?.id} value={student.student_profile?.id}>
                    {student.student_profile?.student_code} - {student.student_profile?.full_name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button className="primary-button" type="submit" disabled={submitting || !form.class_id || !form.student_id}>
              {submitting ? 'Enrolling...' : 'Enroll student'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

type MaterialModalState =
  | { type: 'create' }
  | { type: 'edit'; material: Material }
  | { type: 'delete'; material: Material }
  | null

type MaterialFormState = {
  class_id: string
  creator_id: string
  creator_role: MaterialCreatorRole
  title: string
  description: string
  material_type: MaterialType
  url: string
  is_active: boolean
}

const emptyMaterialForm: MaterialFormState = {
  class_id: '',
  creator_id: '',
  creator_role: 'instructor',
  title: '',
  description: '',
  material_type: 'pdf',
  url: '',
  is_active: true,
}

function LmsMaterialsExperience({ currentUser }: { currentUser: CurrentUser }) {
  const [materials, setMaterials] = useState<Material[]>([])
  const [classes, setClasses] = useState<AcademicClass[]>([])
  const [users, setUsers] = useState<CurrentUser[]>([])
  const [typeFilter, setTypeFilter] = useState<'all' | MaterialType>('all')
  const [creatorRoleFilter, setCreatorRoleFilter] = useState<'all' | MaterialCreatorRole>('all')
  const [classFilter, setClassFilter] = useState('all')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<MaterialModalState>(null)

  async function reloadMaterials() {
    setLoading(true)
    setMessage('')
    try {
      const [materialData, classData, userData] = await Promise.all([
        currentUser.role === 'student' ? listStudentMaterials() : listMaterials(),
        currentUser.role === 'student' ? null : listClasses(),
        currentUser.role === 'admin' ? listUsers() : null,
      ])
      setMaterials(materialData.data)
      setClasses(classData?.data ?? [])
      setUsers(userData?.data ?? [])
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true

    async function loadInitialMaterials() {
      try {
        const [materialData, classData, userData] = await Promise.all([
          currentUser.role === 'student' ? listStudentMaterials() : listMaterials(),
          currentUser.role === 'student' ? null : listClasses(),
          currentUser.role === 'admin' ? listUsers() : null,
        ])
        if (!mounted) return
        setMaterials(materialData.data)
        setClasses(classData?.data ?? [])
        setUsers(userData?.data ?? [])
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    void loadInitialMaterials()

    return () => {
      mounted = false
    }
  }, [currentUser.role])

  const filtered = materials.filter((material) => {
    const typeMatches = typeFilter === 'all' || material.material_type === typeFilter
    const roleMatches = creatorRoleFilter === 'all' || material.creator_role === creatorRoleFilter
    const classMatches = classFilter === 'all' || material.class_id === classFilter
    return typeMatches && roleMatches && classMatches
  })
  const teachers = users.filter((user) => user.role === 'teacher' && user.teacher_profile)

  async function handleSave(mode: 'create' | 'edit', id: string | null, form: MaterialFormState) {
    const payload = materialPayload(form, currentUser.role)
    if (mode === 'create') {
      await createMaterial(payload)
    } else if (id) {
      await updateMaterial(id, materialUpdatePayload(form))
    }
    setModal(null)
    await reloadMaterials()
  }

  async function handleDelete(id: string) {
    await deleteMaterial(id)
    setModal(null)
    await reloadMaterials()
  }

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}
      <section className="stats-grid" aria-label="Materials summary">
        <article className="stat-card"><span>Materials</span><strong>{loading ? '...' : materials.length}</strong><small>{currentUser.role === 'student' ? 'My active class' : 'Role-scoped list'}</small></article>
        <article className="stat-card"><span>PDF</span><strong>{materials.filter((item) => item.material_type === 'pdf').length}</strong><small>Reference material</small></article>
        <article className="stat-card"><span>Video</span><strong>{materials.filter((item) => item.material_type === 'video').length}</strong><small>External links</small></article>
        <article className="stat-card"><span>External files</span><strong>{materials.filter((item) => item.material_type === 'external_file').length}</strong><small>Shared resources</small></article>
      </section>

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div>
            <h2>{currentUser.role === 'student' ? 'My Materials' : 'Materials Table'}</h2>
            <p>{currentUser.role === 'student' ? 'Active materials for your class.' : 'Create and manage class material links.'}</p>
          </div>
          <div className="admin-toolbar lms-toolbar">
            <label><span>Material type</span><select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value as typeof typeFilter)}><option value="all">All types</option><option value="pdf">PDF</option><option value="video">Video</option><option value="external_file">External file</option></select></label>
            <label><span>Creator role</span><select value={creatorRoleFilter} onChange={(event) => setCreatorRoleFilter(event.target.value as typeof creatorRoleFilter)}><option value="all">Any role</option><option value="instructor">Instructor</option><option value="mentor">Mentor</option></select></label>
            <label><span>Class</span><select value={classFilter} onChange={(event) => setClassFilter(event.target.value)}><option value="all">All classes</option>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
            {currentUser.role !== 'student' && <button className="primary-button" type="button" onClick={() => setModal({ type: 'create' })}><Plus size={18} />Add material</button>}
          </div>
        </div>
        <MaterialTable materials={filtered} canManage={currentUser.role !== 'student'} onEdit={(material) => setModal({ type: 'edit', material })} onDelete={(material) => setModal({ type: 'delete', material })} />
      </section>

      {(modal?.type === 'create' || modal?.type === 'edit') && (
        <MaterialFormModal
          mode={modal.type}
          material={modal.type === 'edit' ? modal.material : undefined}
          classes={classes}
          teachers={teachers}
          currentUser={currentUser}
          onClose={() => setModal(null)}
          onSubmit={(form) => handleSave(modal.type, modal.type === 'edit' ? modal.material.id : null, form)}
        />
      )}
      {modal?.type === 'delete' && (
        <ConfirmModal
          title="Delete material"
          message={`Delete ${modal.material.title}? Students will no longer see this material.`}
          confirmLabel="Delete"
          onClose={() => setModal(null)}
          onConfirm={() => handleDelete(modal.material.id)}
        />
      )}
    </section>
  )
}

function MaterialTable({
  materials,
  canManage,
  onEdit,
  onDelete,
}: {
  materials: Material[]
  canManage: boolean
  onEdit: (material: Material) => void
  onDelete: (material: Material) => void
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Class</th>
            <th>Type</th>
            <th>Creator</th>
            <th>Link</th>
            {canManage && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {materials.map((material) => (
            <tr key={material.id}>
              <td>{material.title}<br /><small>{material.description || 'No description'}</small></td>
              <td><span className="class-code">{material.class_code}</span></td>
              <td><StatusBadge value={material.material_type.replaceAll('_', ' ')} /></td>
              <td>{material.creator_name}<br /><small>{material.creator_role}</small></td>
              <td><a href={material.url} target="_blank" rel="noreferrer">Open</a></td>
              {canManage && <td><LmsRowMenu actions={[{ label: 'Edit material', onClick: () => onEdit(material) }, { label: 'Delete material', onClick: () => onDelete(material) }]} /></td>}
            </tr>
          ))}
          {!materials.length && <tr><td colSpan={canManage ? 6 : 5}>No materials match the selected filters.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function MaterialFormModal({
  mode,
  material,
  classes,
  teachers,
  currentUser,
  onClose,
  onSubmit,
}: {
  mode: 'create' | 'edit'
  material?: Material
  classes: AcademicClass[]
  teachers: CurrentUser[]
  currentUser: CurrentUser
  onClose: () => void
  onSubmit: (form: MaterialFormState) => Promise<void>
}) {
  const [form, setForm] = useState<MaterialFormState>(() => materialFormFromRecord(material, classes, teachers, currentUser))
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit(form)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="material-title">
        <div className="modal-header">
          <div><span className="eyebrow">LMS content</span><h2 id="material-title">{mode === 'create' ? 'Add' : 'Edit'} material</h2></div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="form-grid-two">
              <label><span>Class</span><select value={form.class_id} onChange={(event) => setForm({ ...form, class_id: event.target.value })} disabled={mode === 'edit'} required>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
              <label><span>Material type</span><select value={form.material_type} onChange={(event) => setForm({ ...form, material_type: event.target.value as MaterialType })}><option value="pdf">PDF</option><option value="video">Video</option><option value="external_file">External file</option></select></label>
            </div>
            {currentUser.role === 'admin' && mode === 'create' && (
              <label><span>Creator</span><select value={form.creator_id} onChange={(event) => setForm({ ...form, creator_id: event.target.value })} required>{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>
            )}
            <label><span>Creator role</span><select value={form.creator_role} onChange={(event) => setForm({ ...form, creator_role: event.target.value as MaterialCreatorRole })}><option value="instructor">Instructor</option><option value="mentor">Mentor</option></select></label>
            <label><span>Title</span><input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required /></label>
            <label><span>Description</span><input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
            <label><span>URL</span><input type="url" value={form.url} onChange={(event) => setForm({ ...form, url: event.target.value })} required /></label>
            {mode === 'edit' && <label className="checkbox-row"><input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} /><span>Active</span></label>}
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting}>{submitting ? 'Saving...' : 'Save material'}</button></div>
        </form>
      </section>
    </div>
  )
}

type AssignmentModalState =
  | { type: 'create' }
  | { type: 'edit'; assignment: Assignment }
  | { type: 'delete'; assignment: Assignment }
  | { type: 'submit'; assignment: Assignment }
  | { type: 'review'; submission: ReviewTarget }
  | null

type AssignmentFormState = {
  class_id: string
  created_by_teacher_id: string
  title: string
  description: string
  requirement_url: string
  deadline: string
  max_grade: string
  is_active: boolean
}

type ReviewTarget = {
  id: string
  classId?: string
  assignmentTitle: string
  studentName: string
  studentCode: string
  classCode: string
  submissionUrl?: string
  requirementUrl?: string
  maxGrade: number
  submittedAt?: string
  reviewedAt?: string
  reviewedBy?: string | null
  grade: number | null
  feedback: string | null
  status: AssignmentSubmissionStatus
}

const emptyAssignmentForm: AssignmentFormState = {
  class_id: '',
  created_by_teacher_id: '',
  title: '',
  description: '',
  requirement_url: '',
  deadline: '',
  max_grade: '100',
  is_active: true,
}

function LmsAssignmentsExperience({ currentUser }: { currentUser: CurrentUser }) {
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [pending, setPending] = useState<PendingSubmission[]>([])
  const [reviewed, setReviewed] = useState<ReviewedSubmission[]>([])
  const [late, setLate] = useState<PendingSubmission[]>([])
  const [classes, setClasses] = useState<AcademicClass[]>([])
  const [users, setUsers] = useState<CurrentUser[]>([])
  const [assignmentStatusFilter, setAssignmentStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [submissionStatusFilter, setSubmissionStatusFilter] = useState<'all' | AssignmentSubmissionStatus>('all')
  const [classFilter, setClassFilter] = useState('all')
  const [creatorFilter, setCreatorFilter] = useState('all')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<AssignmentModalState>(null)

  async function reloadAssignments() {
    setLoading(true)
    setMessage('')
    try {
      const data = await loadAssignmentWorkspace(currentUser.role)
      setAssignments(data.assignments)
      setSubmissions(data.submissions)
      setPending(data.pending)
      setReviewed(data.reviewed)
      setLate(data.late)
      setClasses(data.classes)
      setUsers(data.users)
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true

    async function loadInitialAssignments() {
      try {
        const data = await loadAssignmentWorkspace(currentUser.role)
        if (!mounted) return
        setAssignments(data.assignments)
        setSubmissions(data.submissions)
        setPending(data.pending)
        setReviewed(data.reviewed)
        setLate(data.late)
        setClasses(data.classes)
        setUsers(data.users)
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    void loadInitialAssignments()

    return () => {
      mounted = false
    }
  }, [currentUser.role])

  const teachers = users.filter((user) => user.role === 'teacher' && user.teacher_profile)
  const filteredAssignments = assignments.filter((assignment) => {
    const classMatches = classFilter === 'all' || assignment.class_id === classFilter
    const creatorMatches = creatorFilter === 'all' || assignment.created_by_teacher_id === creatorFilter
    const statusMatches =
      assignmentStatusFilter === 'all' ||
      (assignmentStatusFilter === 'active' ? assignment.is_active : !assignment.is_active)
    return classMatches && creatorMatches && statusMatches
  })
  const pendingTargets = currentUser.role === 'admin'
    ? submissions.filter((submission) => submission.status === 'submitted').map((submission) => submissionTargetFromAdmin(submission, assignments))
    : pending.map(reviewTargetFromPending)
  const lateTargets = currentUser.role === 'admin'
    ? submissions.filter((submission) => submission.status === 'late').map((submission) => submissionTargetFromAdmin(submission, assignments))
    : late.map(reviewTargetFromPending)
  const reviewedTargets = currentUser.role === 'admin'
    ? submissions.filter((submission) => ['reviewed', 'rejected'].includes(submission.status)).map((submission) => submissionTargetFromAdmin(submission, assignments))
    : reviewed.map(reviewTargetFromReviewed)
  const visiblePending = filterReviewTargets(pendingTargets, classFilter, submissionStatusFilter)
  const visibleLate = filterReviewTargets(lateTargets, classFilter, submissionStatusFilter)
  const visibleReviewed = filterReviewTargets(reviewedTargets, classFilter, submissionStatusFilter)

  async function handleSave(mode: 'create' | 'edit', id: string | null, form: AssignmentFormState) {
    if (mode === 'create') {
      await createAssignment(assignmentPayload(form, currentUser.role))
    } else if (id) {
      await updateAssignment(id, assignmentUpdatePayload(form))
    }
    setModal(null)
    await reloadAssignments()
  }

  async function handleDelete(id: string) {
    await deleteAssignment(id)
    setModal(null)
    await reloadAssignments()
  }

  async function handleSubmitAssignment(assignmentId: string, submissionUrl: string) {
    await submitAssignment(assignmentId, { submission_url: submissionUrl })
    setModal(null)
    await reloadAssignments()
  }

  async function handleReviewSubmission(target: ReviewTarget, grade: number, feedback: string, reviewerId: string) {
    await reviewSubmission(target.id, {
      grade,
      feedback: feedback || null,
      reviewed_by_teacher_id: currentUser.role === 'admin' ? reviewerId : null,
    })
    setModal(null)
    await reloadAssignments()
  }

  async function handleRejectSubmission(target: ReviewTarget, feedback: string, reviewerId: string) {
    await rejectSubmission(target.id, {
      feedback: feedback || null,
      reviewed_by_teacher_id: currentUser.role === 'admin' ? reviewerId : null,
    })
    setModal(null)
    await reloadAssignments()
  }

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}
      <section className="stats-grid" aria-label="Assignments summary">
        <article className="stat-card"><span>Assignments</span><strong>{loading ? '...' : assignments.length}</strong><small>{currentUser.role === 'student' ? 'My active class' : 'Created for classes'}</small></article>
        <article className="stat-card"><span>Pending reviews</span><strong>{visiblePending.length}</strong><small>Submitted work</small></article>
        <article className="stat-card"><span>Late submissions</span><strong>{visibleLate.length}</strong><small>Needs decision</small></article>
        <article className="stat-card"><span>Reviewed</span><strong>{visibleReviewed.length}</strong><small>Graded or rejected</small></article>
      </section>

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div>
            <h2>{currentUser.role === 'student' ? 'My Assignments' : 'Assignment Table'}</h2>
            <p>{currentUser.role === 'student' ? 'Submit work and track deadlines for your active class.' : 'Create assignments and monitor submission status.'}</p>
          </div>
          <div className="admin-toolbar assignment-toolbar">
            <label><span>Class</span><select value={classFilter} onChange={(event) => setClassFilter(event.target.value)}><option value="all">All classes</option>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
            {currentUser.role === 'admin' && <label><span>Teacher</span><select value={creatorFilter} onChange={(event) => setCreatorFilter(event.target.value)}><option value="all">All creators</option>{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>}
            <label><span>Assignment status</span><select value={assignmentStatusFilter} onChange={(event) => setAssignmentStatusFilter(event.target.value as typeof assignmentStatusFilter)}><option value="all">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select></label>
            {currentUser.role !== 'student' && <button className="primary-button" type="button" onClick={() => setModal({ type: 'create' })}><Plus size={18} />Add assignment</button>}
          </div>
        </div>
        <AssignmentTable
          assignments={filteredAssignments}
          currentUser={currentUser}
          onEdit={(assignment) => setModal({ type: 'edit', assignment })}
          onDelete={(assignment) => setModal({ type: 'delete', assignment })}
          onSubmit={(assignment) => setModal({ type: 'submit', assignment })}
        />
      </section>

      {currentUser.role === 'student' ? (
        <section className="data-panel admin-users-panel">
          <div className="panel-toolbar">
            <div>
              <h2>My Submissions</h2>
              <p>Submission history, grades, and feedback.</p>
            </div>
            <label className="compact-filter"><span>Submission status</span><select value={submissionStatusFilter} onChange={(event) => setSubmissionStatusFilter(event.target.value as typeof submissionStatusFilter)}><option value="all">All statuses</option>{submissionStatusOptions.map((status) => <option key={status} value={status}>{titleCase(status)}</option>)}</select></label>
          </div>
          <StudentSubmissionTable submissions={submissions.filter((submission) => submissionStatusFilter === 'all' || submission.status === submissionStatusFilter)} />
        </section>
      ) : (
        <section className="submission-panels">
          <div className="submission-filter-row">
            <label><span>Submission status</span><select value={submissionStatusFilter} onChange={(event) => setSubmissionStatusFilter(event.target.value as typeof submissionStatusFilter)}><option value="all">All statuses</option>{submissionStatusOptions.map((status) => <option key={status} value={status}>{titleCase(status)}</option>)}</select></label>
          </div>
          <SubmissionQueuePanel title="Pending Reviews" description="Submitted assignments waiting for grading." targets={visiblePending} onReview={(submission) => setModal({ type: 'review', submission })} />
          <SubmissionQueuePanel title="Reviewed Submissions" description="Graded and rejected work with feedback." targets={visibleReviewed} reviewed onReview={(submission) => setModal({ type: 'review', submission })} />
          <SubmissionQueuePanel title="Late Submissions" description="Late work can be reviewed or rejected." targets={visibleLate} allowReject onReview={(submission) => setModal({ type: 'review', submission })} />
        </section>
      )}

      {(modal?.type === 'create' || modal?.type === 'edit') && (
        <AssignmentFormModal
          mode={modal.type}
          assignment={modal.type === 'edit' ? modal.assignment : undefined}
          classes={classes}
          teachers={teachers}
          currentUser={currentUser}
          onClose={() => setModal(null)}
          onSubmit={(form) => handleSave(modal.type, modal.type === 'edit' ? modal.assignment.id : null, form)}
        />
      )}
      {modal?.type === 'delete' && (
        <ConfirmModal
          title="Delete assignment"
          message={`Delete ${modal.assignment.title}? Existing submissions remain in history.`}
          confirmLabel="Delete"
          onClose={() => setModal(null)}
          onConfirm={() => handleDelete(modal.assignment.id)}
        />
      )}
      {modal?.type === 'submit' && (
        <SubmitAssignmentModal
          assignment={modal.assignment}
          onClose={() => setModal(null)}
          onSubmit={(submissionUrl) => handleSubmitAssignment(modal.assignment.id, submissionUrl)}
        />
      )}
      {modal?.type === 'review' && (
        <ReviewSubmissionModal
          target={modal.submission}
          currentUser={currentUser}
          teachers={teachers}
          onClose={() => setModal(null)}
          onReview={(grade, feedback, reviewerId) => handleReviewSubmission(modal.submission, grade, feedback, reviewerId)}
          onReject={(feedback, reviewerId) => handleRejectSubmission(modal.submission, feedback, reviewerId)}
        />
      )}
    </section>
  )
}

function AssignmentTable({
  assignments,
  currentUser,
  onEdit,
  onDelete,
  onSubmit,
}: {
  assignments: Assignment[]
  currentUser: CurrentUser
  onEdit: (assignment: Assignment) => void
  onDelete: (assignment: Assignment) => void
  onSubmit: (assignment: Assignment) => void
}) {
  const canManage = currentUser.role !== 'student'

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Assignment</th>
            <th>Class</th>
            <th>Teacher</th>
            <th>Deadline</th>
            <th>Max grade</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {assignments.map((assignment) => (
            <tr key={assignment.id}>
              <td>{assignment.title}<br /><small>{assignment.description || 'No description'}</small></td>
              <td><span className="class-code">{assignment.class_code}</span></td>
              <td>{assignment.created_by_teacher_name}</td>
              <td>{formatDateTime(assignment.deadline)}</td>
              <td>{assignment.max_grade}</td>
              <td><StatusBadge value={assignment.is_active ? 'Active' : 'Inactive'} /></td>
              <td>
                <LmsRowMenu
                  actions={[
                    { label: 'Open requirement', onClick: () => window.open(assignment.requirement_url, '_blank', 'noopener,noreferrer') },
                    ...(currentUser.role === 'student' ? [{ label: 'Submit assignment', onClick: () => onSubmit(assignment) }] : []),
                    ...(canManage ? [{ label: 'Edit assignment', onClick: () => onEdit(assignment) }, { label: 'Delete assignment', onClick: () => onDelete(assignment) }] : []),
                  ]}
                />
              </td>
            </tr>
          ))}
          {!assignments.length && <tr><td colSpan={7}>No assignments match the selected filters.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function StudentSubmissionTable({ submissions }: { submissions: Submission[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Assignment</th>
            <th>Class</th>
            <th>Status</th>
            <th>Submitted</th>
            <th>Grade</th>
            <th>Feedback</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {submissions.map((submission) => (
            <tr key={submission.id}>
              <td>{submission.assignment_title}</td>
              <td><span className="class-code">{submission.class_code}</span></td>
              <td><StatusBadge value={titleCase(submission.status)} /></td>
              <td>{formatDateTime(submission.submitted_at)}</td>
              <td>{submission.grade ?? 'Not graded'}</td>
              <td>{submission.feedback || 'No feedback'}</td>
              <td><LmsRowMenu actions={[{ label: 'Open submission', onClick: () => window.open(submission.submission_url, '_blank', 'noopener,noreferrer') }]} /></td>
            </tr>
          ))}
          {!submissions.length && <tr><td colSpan={7}>No submissions match the selected filters.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function SubmissionQueuePanel({
  title,
  description,
  targets,
  reviewed = false,
  allowReject = false,
  onReview,
}: {
  title: string
  description: string
  targets: ReviewTarget[]
  reviewed?: boolean
  allowReject?: boolean
  onReview: (target: ReviewTarget) => void
}) {
  return (
    <section className="data-panel admin-users-panel">
      <div className="panel-toolbar">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Assignment</th>
              <th>Student</th>
              <th>Class</th>
              <th>{reviewed ? 'Reviewed' : 'Submitted'}</th>
              <th>Grade</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {targets.map((target) => (
              <tr key={target.id}>
                <td>{target.assignmentTitle}<br /><small>{target.requirementUrl ? <a href={target.requirementUrl} target="_blank" rel="noreferrer">Requirement</a> : 'Requirement link unavailable'}</small></td>
                <td>{target.studentName}<br /><small>{target.studentCode}</small></td>
                <td><span className="class-code">{target.classCode}</span></td>
                <td>{formatDateTime(reviewed ? target.reviewedAt : target.submittedAt)}</td>
                <td>{target.grade === null ? `0 / ${target.maxGrade}` : `${target.grade} / ${target.maxGrade}`}</td>
                <td><StatusBadge value={titleCase(target.status)} /></td>
                <td>
                  <LmsRowMenu
                    actions={[
                      ...(target.submissionUrl ? [{ label: 'Open submission', onClick: () => window.open(target.submissionUrl, '_blank', 'noopener,noreferrer') }] : []),
                      { label: reviewed ? 'Update review' : 'Review submission', onClick: () => onReview(target) },
                      ...(allowReject ? [{ label: 'Review / reject late', onClick: () => onReview(target) }] : []),
                    ]}
                  />
                </td>
              </tr>
            ))}
            {!targets.length && <tr><td colSpan={7}>No submissions match the selected filters.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function AssignmentFormModal({
  mode,
  assignment,
  classes,
  teachers,
  currentUser,
  onClose,
  onSubmit,
}: {
  mode: 'create' | 'edit'
  assignment?: Assignment
  classes: AcademicClass[]
  teachers: CurrentUser[]
  currentUser: CurrentUser
  onClose: () => void
  onSubmit: (form: AssignmentFormState) => Promise<void>
}) {
  const [form, setForm] = useState<AssignmentFormState>(() => assignmentFormFromRecord(assignment, classes, teachers))
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit(form)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="assignment-title">
        <div className="modal-header">
          <div><span className="eyebrow">LMS assignments</span><h2 id="assignment-title">{mode === 'create' ? 'Add' : 'Edit'} assignment</h2></div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="form-grid-two">
              <label><span>Class</span><select value={form.class_id} onChange={(event) => setForm({ ...form, class_id: event.target.value })} disabled={mode === 'edit'} required>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
              {currentUser.role === 'admin' && mode === 'create' && <label><span>Teacher</span><select value={form.created_by_teacher_id} onChange={(event) => setForm({ ...form, created_by_teacher_id: event.target.value })} required>{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>}
            </div>
            <label><span>Title</span><input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required /></label>
            <label><span>Description</span><textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} rows={3} /></label>
            <label><span>Requirement URL</span><input type="url" value={form.requirement_url} onChange={(event) => setForm({ ...form, requirement_url: event.target.value })} required /></label>
            <div className="form-grid-two">
              <label><span>Deadline</span><input type="datetime-local" value={form.deadline} onChange={(event) => setForm({ ...form, deadline: event.target.value })} required /></label>
              <label><span>Max grade</span><input type="number" min="1" step="0.5" value={form.max_grade} onChange={(event) => setForm({ ...form, max_grade: event.target.value })} required /></label>
            </div>
            {mode === 'edit' && <label className="checkbox-row"><input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} /><span>Active</span></label>}
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting}>{submitting ? 'Saving...' : 'Save assignment'}</button></div>
        </form>
      </section>
    </div>
  )
}

function SubmitAssignmentModal({
  assignment,
  onClose,
  onSubmit,
}: {
  assignment: Assignment
  onClose: () => void
  onSubmit: (submissionUrl: string) => Promise<void>
}) {
  const [submissionUrl, setSubmissionUrl] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit(submissionUrl)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="submit-title">
        <div className="modal-header">
          <div><span className="eyebrow">Student assignment</span><h2 id="submit-title">Submit assignment</h2></div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="class-code-guide">
              <strong>{assignment.title}</strong>
              <span><code>{assignment.class_code}</code> deadline {formatDateTime(assignment.deadline)}.</span>
            </div>
            <label><span>Submission URL</span><input type="url" value={submissionUrl} onChange={(event) => setSubmissionUrl(event.target.value)} required /></label>
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting}>{submitting ? 'Submitting...' : 'Submit assignment'}</button></div>
        </form>
      </section>
    </div>
  )
}

function ReviewSubmissionModal({
  target,
  currentUser,
  teachers,
  onClose,
  onReview,
  onReject,
}: {
  target: ReviewTarget
  currentUser: CurrentUser
  teachers: CurrentUser[]
  onClose: () => void
  onReview: (grade: number, feedback: string, reviewerId: string) => Promise<void>
  onReject: (feedback: string, reviewerId: string) => Promise<void>
}) {
  const [grade, setGrade] = useState(target.grade?.toString() ?? '')
  const [feedback, setFeedback] = useState(target.feedback ?? '')
  const [reviewerId, setReviewerId] = useState(teachers[0]?.teacher_profile?.id ?? '')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState<'review' | 'reject' | null>(null)
  const needsReviewer = currentUser.role === 'admin'

  async function handleReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting('review')
    setMessage('')
    try {
      await onReview(Number(grade), feedback, reviewerId)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(null)
    }
  }

  async function handleRejectLate() {
    setSubmitting('reject')
    setMessage('')
    try {
      await onReject(feedback, reviewerId)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(null)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="review-title">
        <div className="modal-header">
          <div><span className="eyebrow">Submission review</span><h2 id="review-title">Review submission</h2></div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button>
        </div>
        <form onSubmit={handleReview}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="class-code-guide">
              <strong>{target.assignmentTitle}</strong>
              <span>{target.studentName} / <code>{target.classCode}</code> / max grade {target.maxGrade}</span>
            </div>
            {needsReviewer && <label><span>Reviewer</span><select value={reviewerId} onChange={(event) => setReviewerId(event.target.value)} required>{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>}
            <div className="form-grid-two">
              <label><span>Grade</span><input type="number" min="0" max={target.maxGrade} step="0.5" value={grade} onChange={(event) => setGrade(event.target.value)} required /></label>
              <label><span>Submission status</span><select value={target.status} disabled>{submissionStatusOptions.map((status) => <option key={status} value={status}>{titleCase(status)}</option>)}</select></label>
            </div>
            <label><span>Feedback</span><textarea value={feedback} onChange={(event) => setFeedback(event.target.value)} rows={4} /></label>
          </div>
          <div className="modal-actions split-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button className="danger-button" type="button" onClick={handleRejectLate} disabled={submitting !== null || target.status !== 'late' || (needsReviewer && !reviewerId)}>{submitting === 'reject' ? 'Rejecting...' : 'Reject late submission'}</button>
            <button className="primary-button" type="submit" disabled={submitting !== null || !grade || (needsReviewer && !reviewerId)}>{submitting === 'review' ? 'Reviewing...' : 'Review'}</button>
          </div>
        </form>
      </section>
    </div>
  )
}

type StudentOption = {
  id: string
  code: string
  name: string
}

type AttendanceModalState =
  | { type: 'manual' }
  | { type: 'edit-record'; record: AttendanceRecord }
  | null

function AttendanceExperience({ currentUser }: { currentUser: CurrentUser }) {
  const [sessions, setSessions] = useState<AttendanceSession[]>([])
  const [records, setRecords] = useState<AttendanceRecord[]>([])
  const [classes, setClasses] = useState<AcademicClass[]>([])
  const [users, setUsers] = useState<CurrentUser[]>([])
  const [selectedClassId, setSelectedClassId] = useState('all')
  const [selectedSessionId, setSelectedSessionId] = useState('')
  const [sessionTypeFilter, setSessionTypeFilter] = useState<'all' | AttendanceSessionType>('all')
  const [statusFilter, setStatusFilter] = useState<'all' | AttendanceStatus>('all')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<AttendanceModalState>(null)

  async function reloadAttendance() {
    setLoading(true)
    setMessage('')
    try {
      if (currentUser.role === 'student') {
        const data = await listStudentAttendance()
        setRecords(data.data)
        setSessions([])
        setClasses([])
        setUsers([])
      } else {
        const [sessionData, classData, userData] = await Promise.all([
          listAttendanceSessions(),
          listClasses(),
          currentUser.role === 'admin' ? listUsers() : Promise.resolve({ data: [] as CurrentUser[] }),
        ])
        setSessions(sessionData.data)
        setClasses(classData.data)
        setUsers(userData.data)
        const nextSessionId = selectedSessionId || sessionData.data[0]?.id || ''
        setSelectedSessionId(nextSessionId)
        if (nextSessionId) {
          const recordData = await listAttendanceSessionRecords(nextSessionId)
          setRecords(recordData.data)
        } else {
          setRecords([])
        }
      }
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true

    async function loadInitialAttendance() {
      try {
        if (currentUser.role === 'student') {
          const data = await listStudentAttendance()
          if (!mounted) return
          setRecords(data.data)
        } else {
          const [sessionData, classData, userData] = await Promise.all([
            listAttendanceSessions(),
            listClasses(),
            currentUser.role === 'admin' ? listUsers() : Promise.resolve({ data: [] as CurrentUser[] }),
          ])
          if (!mounted) return
          setSessions(sessionData.data)
          setClasses(classData.data)
          setUsers(userData.data)
          const firstSessionId = sessionData.data[0]?.id ?? ''
          setSelectedSessionId(firstSessionId)
          if (firstSessionId) {
            const recordData = await listAttendanceSessionRecords(firstSessionId)
            if (mounted) setRecords(recordData.data)
          }
        }
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    void loadInitialAttendance()

    return () => {
      mounted = false
    }
  }, [currentUser.role])

  async function handleSessionChange(sessionId: string) {
    setSelectedSessionId(sessionId)
    if (!sessionId) {
      setRecords([])
      return
    }
    try {
      const data = await listAttendanceSessionRecords(sessionId)
      setRecords(data.data)
    } catch (error) {
      setMessage(errorMessage(error))
    }
  }

  async function handleRecordUpdate(record: AttendanceRecord, status: AttendanceStatus) {
    await updateAttendanceRecord(record.id, { status })
    setModal(null)
    if (selectedSessionId) {
      const data = await listAttendanceSessionRecords(selectedSessionId)
      setRecords(data.data)
    }
  }

  const teachers = users.filter((user) => user.role === 'teacher' && user.teacher_profile)
  const visibleSessions = sessions.filter((session) => {
    const classMatches = selectedClassId === 'all' || session.class_id === selectedClassId
    const typeMatches = sessionTypeFilter === 'all' || session.session_type === sessionTypeFilter
    return classMatches && typeMatches
  })
  const visibleRecords = records.filter((record) => statusFilter === 'all' || record.status === statusFilter)

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}
      <section className="stats-grid" aria-label="Attendance summary">
        <article className="stat-card"><span>Sessions</span><strong>{loading ? '...' : sessions.length || (currentUser.role === 'student' ? 'My' : 0)}</strong><small>{currentUser.role === 'student' ? 'Attendance records' : 'Tracked sessions'}</small></article>
        <article className="stat-card"><span>Present</span><strong>{records.filter((record) => record.status === 'present').length}</strong><small>Full attendance credit</small></article>
        <article className="stat-card"><span>Late</span><strong>{records.filter((record) => record.status === 'late').length}</strong><small>Partial attendance credit</small></article>
        <article className="stat-card"><span>Absent</span><strong>{records.filter((record) => record.status === 'absent').length}</strong><small>No attendance credit</small></article>
      </section>

      {currentUser.role !== 'student' && (
        <>
          <section className="data-panel admin-users-panel">
            <div className="panel-toolbar">
              <div><h2>Attendance Sessions</h2><p>Create manual sessions, upload CSV attendance, and inspect session records.</p></div>
              <div className="admin-toolbar attendance-toolbar">
                <label><span>Class</span><select value={selectedClassId} onChange={(event) => setSelectedClassId(event.target.value)}><option value="all">All classes</option>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
                <label><span>Session type</span><select value={sessionTypeFilter} onChange={(event) => setSessionTypeFilter(event.target.value as typeof sessionTypeFilter)}><option value="all">All types</option><option value="instructor">Instructor</option><option value="mentor">Mentor</option></select></label>
                <button className="primary-button" type="button" onClick={() => setModal({ type: 'manual' })}><Plus size={18} />Manual entry</button>
              </div>
            </div>
            <AttendanceSessionsTable sessions={visibleSessions} onOpenRecords={handleSessionChange} />
          </section>

          <AttendanceCsvPanel classes={classes} teachers={teachers} currentUser={currentUser} onUploaded={reloadAttendance} />
        </>
      )}

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div><h2>{currentUser.role === 'student' ? 'My Attendance' : 'Attendance Records Editor'}</h2><p>{currentUser.role === 'student' ? 'Your attendance record and earned attendance grade.' : 'Edit attendance status from the selected session.'}</p></div>
          <div className="admin-toolbar record-toolbar">
            {currentUser.role !== 'student' && <label><span>Session</span><select value={selectedSessionId} onChange={(event) => handleSessionChange(event.target.value)}>{sessions.map((session) => <option key={session.id} value={session.id}>{session.class_code} / {titleCase(session.session_type)} / {session.session_date}</option>)}</select></label>}
            <label><span>Attendance status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}><option value="all">All statuses</option><option value="present">Present</option><option value="late">Late</option><option value="absent">Absent</option></select></label>
          </div>
        </div>
        <AttendanceRecordsTable records={visibleRecords} canEdit={currentUser.role !== 'student'} onEdit={(record) => setModal({ type: 'edit-record', record })} />
      </section>

      {modal?.type === 'manual' && (
        <ManualAttendanceModal currentUser={currentUser} classes={classes} teachers={teachers} onClose={() => setModal(null)} onCreated={async () => { setModal(null); await reloadAttendance() }} />
      )}
      {modal?.type === 'edit-record' && (
        <AttendanceRecordEditModal record={modal.record} onClose={() => setModal(null)} onSubmit={(status) => handleRecordUpdate(modal.record, status)} />
      )}
    </section>
  )
}

function AttendanceSessionsTable({ sessions, onOpenRecords }: { sessions: AttendanceSession[]; onOpenRecords: (sessionId: string) => void }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Class</th><th>Teacher</th><th>Type</th><th>Date</th><th>Source</th><th>Actions</th></tr></thead>
        <tbody>
          {sessions.map((session) => (
            <tr key={session.id}>
              <td><span className="class-code">{session.class_code}</span></td>
              <td>{session.teacher_name}</td>
              <td><StatusBadge value={titleCase(session.session_type)} /></td>
              <td>{session.session_date}</td>
              <td>{titleCase(session.source_type)}</td>
              <td><LmsRowMenu actions={[{ label: 'Open records', onClick: () => onOpenRecords(session.id) }]} /></td>
            </tr>
          ))}
          {!sessions.length && <tr><td colSpan={6}>No attendance sessions match the selected filters.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function AttendanceRecordsTable({ records, canEdit, onEdit }: { records: AttendanceRecord[]; canEdit: boolean; onEdit: (record: AttendanceRecord) => void }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Student</th><th>Status</th><th>Earned grade</th><th>Max grade</th><th>Grade entry</th>{canEdit && <th>Actions</th>}</tr></thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id}>
              <td>{record.student_name}<br /><small>{record.student_code}</small></td>
              <td><StatusBadge value={titleCase(record.status)} /></td>
              <td>{record.earned_grade}</td>
              <td>{record.max_grade}</td>
              <td>{record.grade_entry_id ? 'Created' : 'Pending'}</td>
              {canEdit && <td><LmsRowMenu actions={[{ label: 'Edit status', onClick: () => onEdit(record) }]} /></td>}
            </tr>
          ))}
          {!records.length && <tr><td colSpan={canEdit ? 6 : 5}>No attendance records match the selected filters.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function AttendanceCsvPanel({ classes, teachers, currentUser, onUploaded }: { classes: AcademicClass[]; teachers: CurrentUser[]; currentUser: CurrentUser; onUploaded: () => Promise<void> }) {
  const [classId, setClassId] = useState(classes[0]?.id ?? '')
  const [teacherId, setTeacherId] = useState(teachers[0]?.teacher_profile?.id ?? '')
  const [sessionType, setSessionType] = useState<AttendanceSessionType>('instructor')
  const [sessionDate, setSessionDate] = useState(todayInput())
  const [file, setFile] = useState<File | null>(null)
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const selectedClassId = classId || classes[0]?.id || ''
  const selectedTeacherId = teacherId || teachers[0]?.teacher_profile?.id || ''

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file) return
    setSubmitting(true)
    setMessage('')
    try {
      const response = await uploadAttendanceCsv({ class_id: selectedClassId, teacher_id: currentUser.role === 'admin' ? selectedTeacherId : null, session_type: sessionType, session_date: sessionDate, file })
      setMessage(uploadSummary(response.data))
      await onUploaded()
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="data-panel workflow-panel">
      <div className="panel-heading"><FileText size={20} /><div><h2>Attendance CSV Upload</h2><p>Upload rows with student code and attendance status.</p></div></div>
      {message && <div className="form-message">{message}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-grid-two">
          <label><span>Class</span><select value={selectedClassId} onChange={(event) => setClassId(event.target.value)} required>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
          <label><span>Session type</span><select value={sessionType} onChange={(event) => setSessionType(event.target.value as AttendanceSessionType)}><option value="instructor">Instructor</option><option value="mentor">Mentor</option></select></label>
        </div>
        {currentUser.role === 'admin' && <label><span>Teacher</span><select value={selectedTeacherId} onChange={(event) => setTeacherId(event.target.value)} required>{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>}
        <div className="form-grid-two">
          <label><span>Session date</span><input type="date" value={sessionDate} onChange={(event) => setSessionDate(event.target.value)} required /></label>
          <label><span>CSV file</span><input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0] ?? null)} required /></label>
        </div>
        <div className="csv-actions">
          <button className="primary-button" type="submit" disabled={submitting || !file}>{submitting ? 'Uploading...' : 'Upload CSV'}</button>
          <LmsRowMenu actions={[{ label: 'Clear selected file', onClick: () => setFile(null) }, { label: 'Use selected class', onClick: () => setMessage(`Selected class is ready for ${sessionType} CSV upload.`) }]} />
        </div>
      </form>
    </section>
  )
}

function ManualAttendanceModal({ currentUser, classes, teachers, onClose, onCreated }: { currentUser: CurrentUser; classes: AcademicClass[]; teachers: CurrentUser[]; onClose: () => void; onCreated: () => Promise<void> }) {
  const [classId, setClassId] = useState(classes[0]?.id ?? '')
  const [teacherId, setTeacherId] = useState(teachers[0]?.teacher_profile?.id ?? '')
  const [sessionType, setSessionType] = useState<AttendanceSessionType>('instructor')
  const [sessionDate, setSessionDate] = useState(todayInput())
  const [students, setStudents] = useState<StudentOption[]>([])
  const [studentId, setStudentId] = useState('')
  const [status, setStatus] = useState<AttendanceStatus>('present')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let mounted = true

    async function loadStudents() {
      if (!classId) return
      try {
        const options = currentUser.role === 'admin'
          ? await studentOptionsForAdminClass(classId)
          : await studentOptionsForTeacherClass(classId)
        if (!mounted) return
        setStudents(options)
        setStudentId(options[0]?.id ?? '')
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      }
    }

    void loadStudents()
    return () => {
      mounted = false
    }
  }, [classId, currentUser.role])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await createManualAttendance({
        class_id: classId,
        teacher_id: currentUser.role === 'admin' ? teacherId : null,
        session_type: sessionType,
        session_date: sessionDate,
        records: [{ student_id: studentId, status }],
      })
      await onCreated()
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="manual-attendance-title">
        <div className="modal-header"><div><span className="eyebrow">Attendance</span><h2 id="manual-attendance-title">Manual attendance entry</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button></div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="form-grid-two">
              <label><span>Class</span><select value={classId} onChange={(event) => setClassId(event.target.value)} required>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
              <label><span>Session type</span><select value={sessionType} onChange={(event) => setSessionType(event.target.value as AttendanceSessionType)}><option value="instructor">Instructor</option><option value="mentor">Mentor</option></select></label>
            </div>
            {currentUser.role === 'admin' && <label><span>Teacher</span><select value={teacherId} onChange={(event) => setTeacherId(event.target.value)} required>{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>}
            <div className="form-grid-two">
              <label><span>Session date</span><input type="date" value={sessionDate} onChange={(event) => setSessionDate(event.target.value)} required /></label>
              <label><span>Student</span><select value={studentId} onChange={(event) => setStudentId(event.target.value)} required>{students.map((student) => <option key={student.id} value={student.id}>{student.code} - {student.name}</option>)}</select></label>
            </div>
            <label><span>Attendance status</span><select value={status} onChange={(event) => setStatus(event.target.value as AttendanceStatus)}><option value="present">Present</option><option value="late">Late</option><option value="absent">Absent</option></select></label>
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting || !studentId}>{submitting ? 'Saving...' : 'Save attendance'}</button></div>
        </form>
      </section>
    </div>
  )
}

function AttendanceRecordEditModal({ record, onClose, onSubmit }: { record: AttendanceRecord; onClose: () => void; onSubmit: (status: AttendanceStatus) => Promise<void> }) {
  const [status, setStatus] = useState<AttendanceStatus>(record.status)
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit(status)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="attendance-edit-title">
        <div className="modal-header"><div><span className="eyebrow">Attendance editor</span><h2 id="attendance-edit-title">Edit attendance status</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button></div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="class-code-guide"><strong>{record.student_name}</strong><span>{record.student_code} / current status {titleCase(record.status)}</span></div>
            <label><span>Attendance status</span><select value={status} onChange={(event) => setStatus(event.target.value as AttendanceStatus)}><option value="present">Present</option><option value="late">Late</option><option value="absent">Absent</option></select></label>
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting}>{submitting ? 'Saving...' : 'Save status'}</button></div>
        </form>
      </section>
    </div>
  )
}

type QuizModalState =
  | { type: 'manual' }
  | { type: 'edit-result'; result: QuizResult }
  | null

function QuizzesExperience({ currentUser }: { currentUser: CurrentUser }) {
  const [quizzes, setQuizzes] = useState<Quiz[]>([])
  const [results, setResults] = useState<QuizResult[]>([])
  const [classes, setClasses] = useState<AcademicClass[]>([])
  const [users, setUsers] = useState<CurrentUser[]>([])
  const [selectedClassId, setSelectedClassId] = useState('all')
  const [selectedQuizId, setSelectedQuizId] = useState('')
  const [sourceFilter, setSourceFilter] = useState<'all' | 'manual' | 'csv_upload'>('all')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<QuizModalState>(null)

  async function reloadQuizzes() {
    setLoading(true)
    setMessage('')
    try {
      if (currentUser.role === 'student') {
        const resultData = await listStudentQuizzes()
        setResults(resultData.data)
        setQuizzes([])
        setClasses([])
        setUsers([])
      } else {
        const [quizData, classData, userData] = await Promise.all([
          listQuizzes(),
          listClasses(),
          currentUser.role === 'admin' ? listUsers() : Promise.resolve({ data: [] as CurrentUser[] }),
        ])
        setQuizzes(quizData.data)
        setClasses(classData.data)
        setUsers(userData.data)
        const nextQuizId = selectedQuizId || quizData.data[0]?.id || ''
        setSelectedQuizId(nextQuizId)
        if (nextQuizId) {
          const resultData = await listQuizResults(nextQuizId)
          setResults(resultData.data)
        } else {
          setResults([])
        }
      }
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true

    async function loadInitialQuizzes() {
      try {
        if (currentUser.role === 'student') {
          const resultData = await listStudentQuizzes()
          if (mounted) setResults(resultData.data)
        } else {
          const [quizData, classData, userData] = await Promise.all([
            listQuizzes(),
            listClasses(),
            currentUser.role === 'admin' ? listUsers() : Promise.resolve({ data: [] as CurrentUser[] }),
          ])
          if (!mounted) return
          setQuizzes(quizData.data)
          setClasses(classData.data)
          setUsers(userData.data)
          const firstQuizId = quizData.data[0]?.id ?? ''
          setSelectedQuizId(firstQuizId)
          if (firstQuizId) {
            const resultData = await listQuizResults(firstQuizId)
            if (mounted) setResults(resultData.data)
          }
        }
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    void loadInitialQuizzes()

    return () => {
      mounted = false
    }
  }, [currentUser.role])

  async function handleQuizChange(quizId: string) {
    setSelectedQuizId(quizId)
    if (!quizId) {
      setResults([])
      return
    }
    try {
      const data = await listQuizResults(quizId)
      setResults(data.data)
    } catch (error) {
      setMessage(errorMessage(error))
    }
  }

  async function handleResultUpdate(result: QuizResult, earnedGrade: number) {
    await updateQuizResult(result.id, { earned_grade: earnedGrade })
    setModal(null)
    if (selectedQuizId) {
      const data = await listQuizResults(selectedQuizId)
      setResults(data.data)
    }
  }

  const teachers = users.filter((user) => user.role === 'teacher' && user.teacher_profile)
  const visibleQuizzes = quizzes.filter((quiz) => {
    const classMatches = selectedClassId === 'all' || quiz.class_id === selectedClassId
    const sourceMatches = sourceFilter === 'all' || quiz.source_type === sourceFilter
    return classMatches && sourceMatches
  })

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}
      <section className="stats-grid" aria-label="Quiz summary">
        <article className="stat-card"><span>Quizzes</span><strong>{loading ? '...' : quizzes.length || (currentUser.role === 'student' ? 'My' : 0)}</strong><small>{currentUser.role === 'student' ? 'Published results' : 'Quiz sessions'}</small></article>
        <article className="stat-card"><span>Results</span><strong>{results.length}</strong><small>Visible quiz grades</small></article>
        <article className="stat-card"><span>Average</span><strong>{results.length ? formatPercent((results.reduce((sum, result) => sum + result.earned_grade / result.max_grade, 0) / results.length) * 100) : '0%'}</strong><small>Current table</small></article>
        <article className="stat-card"><span>Corrections</span><strong>{results.filter((result) => result.grade_entry_id).length}</strong><small>Grade ledger entries</small></article>
      </section>

      {currentUser.role !== 'student' && (
        <>
          <section className="data-panel admin-users-panel">
            <div className="panel-toolbar">
              <div><h2>Quizzes Table</h2><p>Create quiz results manually, upload CSV files, and open result records.</p></div>
              <div className="admin-toolbar quiz-toolbar">
                <label><span>Class</span><select value={selectedClassId} onChange={(event) => setSelectedClassId(event.target.value)}><option value="all">All classes</option>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
                <label><span>CSV source</span><select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value as typeof sourceFilter)}><option value="all">All sources</option><option value="manual">Manual</option><option value="csv_upload">CSV upload</option></select></label>
                <button className="primary-button" type="button" onClick={() => setModal({ type: 'manual' })}><Plus size={18} />Manual quiz</button>
              </div>
            </div>
            <QuizzesTable quizzes={visibleQuizzes} onOpenResults={handleQuizChange} />
          </section>

          <QuizCsvPanel classes={classes} teachers={teachers} currentUser={currentUser} onUploaded={reloadQuizzes} />
        </>
      )}

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div><h2>{currentUser.role === 'student' ? 'My Quizzes' : 'Quiz Results Table'}</h2><p>{currentUser.role === 'student' ? 'Your quiz grades and maximum scores.' : 'Edit earned grades for the selected quiz.'}</p></div>
          {currentUser.role !== 'student' && <label className="compact-filter"><span>Quiz selector</span><select value={selectedQuizId} onChange={(event) => handleQuizChange(event.target.value)}>{quizzes.map((quiz) => <option key={quiz.id} value={quiz.id}>{quiz.title} / {quiz.class_code}</option>)}</select></label>}
        </div>
        <QuizResultsTable results={results} quizzes={quizzes} canEdit={currentUser.role !== 'student'} onEdit={(result) => setModal({ type: 'edit-result', result })} />
      </section>

      {modal?.type === 'manual' && <ManualQuizModal currentUser={currentUser} classes={classes} teachers={teachers} onClose={() => setModal(null)} onCreated={async () => { setModal(null); await reloadQuizzes() }} />}
      {modal?.type === 'edit-result' && <QuizResultEditModal result={modal.result} onClose={() => setModal(null)} onSubmit={(earnedGrade) => handleResultUpdate(modal.result, earnedGrade)} />}
    </section>
  )
}

function QuizzesTable({ quizzes, onOpenResults }: { quizzes: Quiz[]; onOpenResults: (quizId: string) => void }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Quiz</th><th>Class</th><th>Teacher</th><th>Date</th><th>Max grade</th><th>Source</th><th>Actions</th></tr></thead>
        <tbody>
          {quizzes.map((quiz) => (
            <tr key={quiz.id}>
              <td>{quiz.title}<br /><small>{quiz.description || 'No description'}</small></td>
              <td><span className="class-code">{quiz.class_code}</span></td>
              <td>{quiz.teacher_name}</td>
              <td>{quiz.quiz_date}</td>
              <td>{quiz.max_grade}</td>
              <td>{titleCase(quiz.source_type)}</td>
              <td><LmsRowMenu actions={[{ label: 'Open results', onClick: () => onOpenResults(quiz.id) }]} /></td>
            </tr>
          ))}
          {!quizzes.length && <tr><td colSpan={7}>No quizzes match the selected filters.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function QuizResultsTable({ results, quizzes, canEdit, onEdit }: { results: QuizResult[]; quizzes: Quiz[]; canEdit: boolean; onEdit: (result: QuizResult) => void }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Student</th><th>Quiz</th><th>Earned</th><th>Max</th><th>Progress</th><th>Grade entry</th>{canEdit && <th>Actions</th>}</tr></thead>
        <tbody>
          {results.map((result) => {
            const quiz = quizzes.find((item) => item.id === result.quiz_id)
            return (
              <tr key={result.id}>
                <td>{result.student_name}<br /><small>{result.student_code}</small></td>
                <td>{quiz?.title ?? result.quiz_id}</td>
                <td>{result.earned_grade}</td>
                <td>{result.max_grade}</td>
                <td><StatusBadge value={formatPercent((result.earned_grade / result.max_grade) * 100)} /></td>
                <td>{result.grade_entry_id ? 'Created' : 'Pending'}</td>
                {canEdit && <td><LmsRowMenu actions={[{ label: 'Edit result', onClick: () => onEdit(result) }]} /></td>}
              </tr>
            )
          })}
          {!results.length && <tr><td colSpan={canEdit ? 7 : 6}>No quiz results match the selected filters.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function QuizCsvPanel({ classes, teachers, currentUser, onUploaded }: { classes: AcademicClass[]; teachers: CurrentUser[]; currentUser: CurrentUser; onUploaded: () => Promise<void> }) {
  const [classId, setClassId] = useState(classes[0]?.id ?? '')
  const [teacherId, setTeacherId] = useState(teachers[0]?.teacher_profile?.id ?? '')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [quizDate, setQuizDate] = useState(todayInput())
  const [maxGrade, setMaxGrade] = useState('10')
  const [file, setFile] = useState<File | null>(null)
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const selectedClassId = classId || classes[0]?.id || ''
  const selectedTeacherId = teacherId || teachers[0]?.teacher_profile?.id || ''

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file) return
    setSubmitting(true)
    setMessage('')
    try {
      const response = await uploadQuizCsv({ class_id: selectedClassId, teacher_id: currentUser.role === 'admin' ? selectedTeacherId : null, title, description: description || null, quiz_date: quizDate, max_grade: Number(maxGrade), file })
      setMessage(uploadSummary(response.data))
      await onUploaded()
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="data-panel workflow-panel">
      <div className="panel-heading"><FileCheck2 size={20} /><div><h2>Quiz CSV Upload</h2><p>Upload rows with student code, earned grade, and max grade.</p></div></div>
      {message && <div className="form-message">{message}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-grid-two">
          <label><span>Class</span><select value={selectedClassId} onChange={(event) => setClassId(event.target.value)} required>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
          <label><span>Quiz date</span><input type="date" value={quizDate} onChange={(event) => setQuizDate(event.target.value)} required /></label>
        </div>
        {currentUser.role === 'admin' && <label><span>Teacher</span><select value={selectedTeacherId} onChange={(event) => setTeacherId(event.target.value)} required>{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>}
        <div className="form-grid-two">
          <label><span>Quiz title</span><input value={title} onChange={(event) => setTitle(event.target.value)} required /></label>
          <label><span>Max grade</span><input type="number" min="1" step="0.5" value={maxGrade} onChange={(event) => setMaxGrade(event.target.value)} required /></label>
        </div>
        <label><span>Description</span><input value={description} onChange={(event) => setDescription(event.target.value)} /></label>
        <div className="form-grid-two">
          <label><span>CSV file</span><input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0] ?? null)} required /></label>
          <div className="csv-actions"><button className="primary-button" type="submit" disabled={submitting || !file}>{submitting ? 'Uploading...' : 'Upload CSV'}</button><LmsRowMenu actions={[{ label: 'Clear selected file', onClick: () => setFile(null) }, { label: 'Use selected quiz setup', onClick: () => setMessage(`CSV setup ready for ${title || 'new quiz'}.`) }]} /></div>
        </div>
      </form>
    </section>
  )
}

function ManualQuizModal({ currentUser, classes, teachers, onClose, onCreated }: { currentUser: CurrentUser; classes: AcademicClass[]; teachers: CurrentUser[]; onClose: () => void; onCreated: () => Promise<void> }) {
  const [classId, setClassId] = useState(classes[0]?.id ?? '')
  const [teacherId, setTeacherId] = useState(teachers[0]?.teacher_profile?.id ?? '')
  const [students, setStudents] = useState<StudentOption[]>([])
  const [studentId, setStudentId] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [quizDate, setQuizDate] = useState(todayInput())
  const [maxGrade, setMaxGrade] = useState('10')
  const [earnedGrade, setEarnedGrade] = useState('10')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let mounted = true

    async function loadStudents() {
      if (!classId) return
      try {
        const options = currentUser.role === 'admin'
          ? await studentOptionsForAdminClass(classId)
          : await studentOptionsForTeacherClass(classId)
        if (!mounted) return
        setStudents(options)
        setStudentId(options[0]?.id ?? '')
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      }
    }

    void loadStudents()
    return () => {
      mounted = false
    }
  }, [classId, currentUser.role])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await createManualQuiz({
        class_id: classId,
        teacher_id: currentUser.role === 'admin' ? teacherId : null,
        title,
        description: description || null,
        quiz_date: quizDate,
        max_grade: Number(maxGrade),
        results: [{ student_id: studentId, earned_grade: Number(earnedGrade) }],
      })
      await onCreated()
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="manual-quiz-title">
        <div className="modal-header"><div><span className="eyebrow">Quizzes</span><h2 id="manual-quiz-title">Manual quiz result entry</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button></div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="form-grid-two">
              <label><span>Class</span><select value={classId} onChange={(event) => setClassId(event.target.value)} required>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
              <label><span>Quiz date</span><input type="date" value={quizDate} onChange={(event) => setQuizDate(event.target.value)} required /></label>
            </div>
            {currentUser.role === 'admin' && <label><span>Teacher</span><select value={teacherId} onChange={(event) => setTeacherId(event.target.value)} required>{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>}
            <label><span>Quiz title</span><input value={title} onChange={(event) => setTitle(event.target.value)} required /></label>
            <label><span>Description</span><input value={description} onChange={(event) => setDescription(event.target.value)} /></label>
            <div className="form-grid-two">
              <label><span>Student</span><select value={studentId} onChange={(event) => setStudentId(event.target.value)} required>{students.map((student) => <option key={student.id} value={student.id}>{student.code} - {student.name}</option>)}</select></label>
              <label><span>Max grade</span><input type="number" min="1" step="0.5" value={maxGrade} onChange={(event) => setMaxGrade(event.target.value)} required /></label>
            </div>
            <label><span>Earned grade</span><input type="number" min="0" max={maxGrade} step="0.5" value={earnedGrade} onChange={(event) => setEarnedGrade(event.target.value)} required /></label>
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting || !studentId}>{submitting ? 'Saving...' : 'Save quiz result'}</button></div>
        </form>
      </section>
    </div>
  )
}

function QuizResultEditModal({ result, onClose, onSubmit }: { result: QuizResult; onClose: () => void; onSubmit: (earnedGrade: number) => Promise<void> }) {
  const [earnedGrade, setEarnedGrade] = useState(String(result.earned_grade))
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit(Number(earnedGrade))
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="quiz-result-edit-title">
        <div className="modal-header"><div><span className="eyebrow">Quiz editor</span><h2 id="quiz-result-edit-title">Edit quiz result</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button></div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="class-code-guide"><strong>{result.student_name}</strong><span>{result.student_code} / max grade {result.max_grade}</span></div>
            <label><span>Earned grade</span><input type="number" min="0" max={result.max_grade} step="0.5" value={earnedGrade} onChange={(event) => setEarnedGrade(event.target.value)} required /></label>
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting}>{submitting ? 'Saving...' : 'Save result'}</button></div>
        </form>
      </section>
    </div>
  )
}

type GradebookModalState =
  | { type: 'correction'; entry: GradeEntry }
  | { type: 'bonus' }
  | null

const gradeCategories: GradeCategory[] = ['assignment', 'attendance', 'quiz', 'bonus', 'correction']
const gradeSources: GradeSourceType[] = ['manual', 'csv_upload', 'system_bonus', 'correction']

function GradebookExperience({ currentUser }: { currentUser: CurrentUser }) {
  const [entries, setEntries] = useState<GradeEntry[]>([])
  const [corrections, setCorrections] = useState<CorrectionHistory[]>([])
  const [bonusEntries, setBonusEntries] = useState<BonusEntry[]>([])
  const [classes, setClasses] = useState<AcademicClass[]>([])
  const [categoryFilter, setCategoryFilter] = useState<'all' | GradeCategory>('all')
  const [sourceFilter, setSourceFilter] = useState<'all' | GradeSourceType>('all')
  const [classFilter, setClassFilter] = useState('all')
  const [studentFilter, setStudentFilter] = useState('all')
  const [teacherFilter, setTeacherFilter] = useState('all')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<GradebookModalState>(null)

  async function reloadGradebook(nextClassFilter = classFilter) {
    setLoading(true)
    setMessage('')
    try {
      const data = await loadGradebookWorkspace(currentUser.role, nextClassFilter)
      setEntries(data.entries)
      setCorrections(data.corrections)
      setBonusEntries(data.bonusEntries)
      setClasses(data.classes)
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true

    async function loadInitialGradebook() {
      try {
        const data = await loadGradebookWorkspace(currentUser.role, 'all')
        if (!mounted) return
        setEntries(data.entries)
        setCorrections(data.corrections)
        setBonusEntries(data.bonusEntries)
        setClasses(data.classes)
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    void loadInitialGradebook()

    return () => {
      mounted = false
    }
  }, [currentUser.role])

  async function handleClassFilter(value: string) {
    setClassFilter(value)
    setStudentFilter('all')
    await reloadGradebook(value)
  }

  async function handleCorrection(entry: GradeEntry, earnedGrade: number, reason: string) {
    await createCorrection(entry.id, { earned_grade: earnedGrade, reason })
    setModal(null)
    await reloadGradebook()
  }

  async function handleBonus(payload: { classId: string; studentId: string; reason: string }) {
    await createBonus({ class_id: payload.classId, student_id: payload.studentId, reason: payload.reason || null })
    setModal(null)
    await reloadGradebook()
  }

  const studentOptions = uniqueEntryOptions(entries, 'student')
  const teacherOptions = uniqueEntryOptions(entries, 'teacher')
  const visibleEntries = entries.filter((entry) => {
    const categoryMatches = categoryFilter === 'all' || entry.category === categoryFilter
    const sourceMatches = sourceFilter === 'all' || entry.source_type === sourceFilter
    const classMatches = classFilter === 'all' || entry.class_id === classFilter
    const studentMatches = studentFilter === 'all' || entry.student_id === studentFilter
    const teacherMatches = teacherFilter === 'all' || entry.teacher_id === teacherFilter
    return categoryMatches && sourceMatches && classMatches && studentMatches && teacherMatches
  })
  const correctionEntries = entries.filter((entry) => entry.category === 'correction')
  const totalEarned = visibleEntries.reduce((sum, entry) => sum + entry.earned_grade, 0)
  const totalMax = visibleEntries.reduce((sum, entry) => sum + entry.max_grade, 0)

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}
      <section className="stats-grid" aria-label="Gradebook summary">
        <article className="stat-card"><span>Grade entries</span><strong>{loading ? '...' : entries.length}</strong><small>{currentUser.role === 'student' ? 'My grade history' : 'Role-scoped ledger'}</small></article>
        <article className="stat-card"><span>Corrections</span><strong>{corrections.length || correctionEntries.length}</strong><small>Audit history</small></article>
        <article className="stat-card"><span>Bonus</span><strong>{bonusEntries.length}</strong><small>Weekly bonus tracking</small></article>
        <article className="stat-card"><span>Visible score</span><strong>{totalMax ? formatPercent((totalEarned / totalMax) * 100) : 'Ledger'}</strong><small>Filtered rows</small></article>
      </section>

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div>
            <h2>{currentUser.role === 'student' ? 'Student Grade History' : 'Gradebook Table'}</h2>
            <p>{currentUser.role === 'student' ? 'Your assignment, attendance, quiz, bonus, and correction history.' : 'Audit grade entries and create corrections without mutating originals.'}</p>
          </div>
          <div className="admin-toolbar gradebook-toolbar">
            <label><span>Category</span><select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value as typeof categoryFilter)}><option value="all">All categories</option>{gradeCategories.map((category) => <option key={category} value={category}>{titleCase(category)}</option>)}</select></label>
            <label><span>Source type</span><select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value as typeof sourceFilter)}><option value="all">All sources</option>{gradeSources.map((source) => <option key={source} value={source}>{titleCase(source)}</option>)}</select></label>
            <label><span>Class</span><select value={classFilter} onChange={(event) => handleClassFilter(event.target.value)}><option value="all">All classes</option>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
            <label><span>Student</span><select value={studentFilter} onChange={(event) => setStudentFilter(event.target.value)}><option value="all">All students</option>{studentOptions.map((student) => <option key={student.id} value={student.id}>{student.label}</option>)}</select></label>
            {currentUser.role !== 'student' && <label><span>Teacher</span><select value={teacherFilter} onChange={(event) => setTeacherFilter(event.target.value)}><option value="all">All teachers</option>{teacherOptions.map((teacher) => <option key={teacher.id} value={teacher.id}>{teacher.label}</option>)}</select></label>}
          </div>
        </div>
        <GradebookTable entries={visibleEntries} canCorrect={currentUser.role !== 'student'} onCorrect={(entry) => setModal({ type: 'correction', entry })} />
      </section>

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div><h2>Corrections History</h2><p>Correction entries with original grade context and required reasons.</p></div>
        </div>
        <CorrectionsHistoryTable corrections={corrections} correctionEntries={correctionEntries} />
      </section>

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div><h2>Bonus Management</h2><p>{currentUser.role === 'student' ? 'Bonus entries applied to your class.' : 'Give weekly bonus entries and track remaining allowance.'}</p></div>
          {currentUser.role !== 'student' && <button className="primary-button" type="button" onClick={() => setModal({ type: 'bonus' })}><Plus size={18} />Give bonus</button>}
        </div>
        <BonusTable bonusEntries={bonusEntries.filter((entry) => classFilter === 'all' || entry.class_id === classFilter)} />
      </section>

      {modal?.type === 'correction' && (
        <CorrectionModal entry={modal.entry} onClose={() => setModal(null)} onSubmit={(earnedGrade, reason) => handleCorrection(modal.entry, earnedGrade, reason)} />
      )}
      {modal?.type === 'bonus' && (
        <BonusModal currentUser={currentUser} classes={classes} onClose={() => setModal(null)} onSubmit={handleBonus} />
      )}
    </section>
  )
}

function GradebookTable({ entries, canCorrect, onCorrect }: { entries: GradeEntry[]; canCorrect: boolean; onCorrect: (entry: GradeEntry) => void }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Student</th><th>Class</th><th>Teacher</th><th>Category</th><th>Score</th><th>Source</th><th>Created</th><th>Actions</th></tr></thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.id}>
              <td>{entry.student_name}<br /><small>{entry.student_code}</small></td>
              <td><span className="class-code">{entry.class_code}</span></td>
              <td>{entry.teacher_name ?? 'Academy'}</td>
              <td><StatusBadge value={titleCase(entry.category)} /></td>
              <td>{entry.earned_grade} / {entry.max_grade}</td>
              <td>{titleCase(entry.source_type)}</td>
              <td>{formatDateTime(entry.created_at)}</td>
              <td>
                <LmsRowMenu
                  actions={[
                    ...(canCorrect && entry.category !== 'correction' ? [{ label: 'Create correction', onClick: () => onCorrect(entry) }] : []),
                    { label: 'Copy entry id', onClick: () => void navigator.clipboard?.writeText(entry.id) },
                  ]}
                />
              </td>
            </tr>
          ))}
          {!entries.length && <tr><td colSpan={8}>No grade entries match the selected filters.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function CorrectionsHistoryTable({ corrections, correctionEntries }: { corrections: CorrectionHistory[]; correctionEntries: GradeEntry[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Student</th><th>Class</th><th>Original</th><th>Correction</th><th>Reason</th><th>Corrected by</th><th>Date</th></tr></thead>
        <tbody>
          {corrections.map((correction) => (
            <tr key={correction.correction_id}>
              <td>{correction.student_name}<br /><small>{correction.student_code}</small></td>
              <td><span className="class-code">{correction.class_code}</span></td>
              <td>{titleCase(correction.original_category)}<br /><small>{correction.original_earned_grade} / {correction.original_max_grade}</small></td>
              <td>{correction.correction_earned_grade}</td>
              <td>{correction.correction_reason}</td>
              <td>{correction.corrected_by}</td>
              <td>{formatDateTime(correction.corrected_at)}</td>
            </tr>
          ))}
          {!corrections.length && correctionEntries.map((entry) => (
            <tr key={entry.id}>
              <td>{entry.student_name}<br /><small>{entry.student_code}</small></td>
              <td><span className="class-code">{entry.class_code}</span></td>
              <td>{entry.related_entry_id ?? 'Original entry'}</td>
              <td>{entry.earned_grade}</td>
              <td>{entry.reason}</td>
              <td>{entry.teacher_name ?? 'Academy'}</td>
              <td>{formatDateTime(entry.created_at)}</td>
            </tr>
          ))}
          {!corrections.length && !correctionEntries.length && <tr><td colSpan={7}>No corrections are available yet.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function BonusTable({ bonusEntries }: { bonusEntries: BonusEntry[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Student</th><th>Class</th><th>Bonus</th><th>Reason</th><th>Weekly count</th><th>Remaining</th><th>Created</th></tr></thead>
        <tbody>
          {bonusEntries.map((entry) => (
            <tr key={entry.grade_entry_id}>
              <td>{entry.student_name}<br /><small>{entry.student_code}</small></td>
              <td><span className="class-code">{entry.class_code}</span></td>
              <td>{entry.earned_grade}</td>
              <td>{entry.reason}</td>
              <td>{entry.weekly_bonus_count}</td>
              <td><StatusBadge value={`${entry.weekly_bonus_remaining} left`} /></td>
              <td>{formatDateTime(entry.created_at)}</td>
            </tr>
          ))}
          {!bonusEntries.length && <tr><td colSpan={7}>No bonus entries match the selected filters.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function CorrectionModal({ entry, onClose, onSubmit }: { entry: GradeEntry; onClose: () => void; onSubmit: (earnedGrade: number, reason: string) => Promise<void> }) {
  const [earnedGrade, setEarnedGrade] = useState(String(entry.earned_grade))
  const [reason, setReason] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit(Number(earnedGrade), reason)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="correction-title">
        <div className="modal-header"><div><span className="eyebrow">Grade correction</span><h2 id="correction-title">Create correction</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button></div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="class-code-guide">
              <strong>{entry.student_name} / {titleCase(entry.category)}</strong>
              <span><code>{entry.class_code}</code> original score {entry.earned_grade} / {entry.max_grade}, source {titleCase(entry.source_type)}.</span>
            </div>
            <label><span>Correction amount</span><input type="number" step="0.5" value={earnedGrade} onChange={(event) => setEarnedGrade(event.target.value)} required /></label>
            <label><span>Reason</span><textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={4} maxLength={500} required /></label>
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting || !reason.trim()}>{submitting ? 'Saving...' : 'Create correction'}</button></div>
        </form>
      </section>
    </div>
  )
}

function BonusModal({ currentUser, classes, onClose, onSubmit }: { currentUser: CurrentUser; classes: AcademicClass[]; onClose: () => void; onSubmit: (payload: { classId: string; studentId: string; reason: string }) => Promise<void> }) {
  const [classId, setClassId] = useState(classes[0]?.id ?? '')
  const [students, setStudents] = useState<StudentOption[]>([])
  const [studentId, setStudentId] = useState('')
  const [reason, setReason] = useState('Bonus')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let mounted = true

    async function loadStudents() {
      if (!classId) return
      try {
        const options = currentUser.role === 'admin'
          ? await studentOptionsForAdminClass(classId)
          : await studentOptionsForTeacherClass(classId)
        if (!mounted) return
        setStudents(options)
        setStudentId(options[0]?.id ?? '')
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      }
    }

    void loadStudents()
    return () => {
      mounted = false
    }
  }, [classId, currentUser.role])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit({ classId, studentId, reason })
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="bonus-title">
        <div className="modal-header"><div><span className="eyebrow">Bonus management</span><h2 id="bonus-title">Give bonus</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button></div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="form-grid-two">
              <label><span>Class</span><select value={classId} onChange={(event) => setClassId(event.target.value)} required>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
              <label><span>Student</span><select value={studentId} onChange={(event) => setStudentId(event.target.value)} required>{students.map((student) => <option key={student.id} value={student.id}>{student.code} - {student.name}</option>)}</select></label>
            </div>
            <label><span>Reason</span><textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={3} maxLength={500} /></label>
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting || !studentId}>{submitting ? 'Saving...' : 'Give bonus'}</button></div>
        </form>
      </section>
    </div>
  )
}

function ProgressRankingExperience({ currentUser }: { currentUser: CurrentUser }) {
  const [classes, setClasses] = useState<AcademicClass[]>([])
  const [tracks, setTracks] = useState<Track[]>([])
  const [users, setUsers] = useState<CurrentUser[]>([])
  const [classProgress, setClassProgress] = useState<ClassProgress | null>(null)
  const [studentProgress, setStudentProgress] = useState<StudentProgress | null>(null)
  const [teacherProgress, setTeacherProgress] = useState<TeacherProgress | null>(null)
  const [snapshots, setSnapshots] = useState<ProgressSnapshot[]>([])
  const [classRanking, setClassRanking] = useState<RankingItem[]>([])
  const [trackRanking, setTrackRanking] = useState<RankingItem[]>([])
  const [top3, setTop3] = useState<RankingItem[]>([])
  const [classId, setClassId] = useState('')
  const [trackId, setTrackId] = useState('')
  const [studentId, setStudentId] = useState('')
  const [teacherId, setTeacherId] = useState('')
  const [weekFilter, setWeekFilter] = useState('all')
  const [yearFilter, setYearFilter] = useState('all')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true

    async function loadInitialProgress() {
      try {
        if (currentUser.role === 'student') {
          const [progressData, topData] = await Promise.all([getMyProgress(), getMyTop3Ranking()])
          if (!mounted) return
          setStudentProgress(progressData.data)
          setTop3(topData.data)
          return
        }

        const [classData, trackData, userData] = await Promise.all([
          listClasses(),
          currentUser.role === 'admin' ? listTracks() : Promise.resolve({ data: [] as Track[] }),
          currentUser.role === 'admin' ? listUsers() : Promise.resolve({ data: [] as CurrentUser[] }),
        ])
        if (!mounted) return
        const firstClassId = classData.data[0]?.id ?? ''
        const firstTrackId = trackData.data[0]?.id ?? ''
        const firstTeacherId = userData.data.find((user) => user.teacher_profile)?.teacher_profile?.id ?? ''
        setClasses(classData.data)
        setTracks(trackData.data)
        setUsers(userData.data)
        setClassId(firstClassId)
        setTrackId(firstTrackId)
        setTeacherId(firstTeacherId)
        if (firstClassId) {
          const [progressData, rankingData, snapshotData] = await Promise.all([
            currentUser.role === 'teacher' ? getTeacherClassProgress(firstClassId) : getClassProgress(firstClassId),
            currentUser.role === 'teacher' ? getTeacherClassRanking(firstClassId) : getClassRanking(firstClassId),
            currentUser.role === 'admin' ? listClassProgressSnapshots(firstClassId) : Promise.resolve({ data: [] as ProgressSnapshot[] }),
          ])
          if (!mounted) return
          setClassProgress(progressData.data)
          setClassRanking(rankingData.data)
          setSnapshots(snapshotData.data)
          setStudentId(progressData.data.students[0]?.student_id ?? '')
          setStudentProgress(progressData.data.students[0] ?? null)
        }
        if (currentUser.role === 'admin' && firstTrackId) {
          const rankingData = await getTrackRanking(firstTrackId)
          if (mounted) setTrackRanking(rankingData.data)
        }
        if (currentUser.role === 'admin' && firstTeacherId) {
          const teacherData = await getTeacherProgress(firstTeacherId)
          if (mounted) setTeacherProgress(teacherData.data)
        }
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    void loadInitialProgress()

    return () => {
      mounted = false
    }
  }, [currentUser.role])

  async function handleClassChange(nextClassId: string) {
    setClassId(nextClassId)
    setMessage('')
    try {
      const [progressData, rankingData, snapshotData] = await Promise.all([
        currentUser.role === 'teacher' ? getTeacherClassProgress(nextClassId) : getClassProgress(nextClassId),
        currentUser.role === 'teacher' ? getTeacherClassRanking(nextClassId) : getClassRanking(nextClassId),
        currentUser.role === 'admin' ? listClassProgressSnapshots(nextClassId) : Promise.resolve({ data: [] as ProgressSnapshot[] }),
      ])
      setClassProgress(progressData.data)
      setClassRanking(rankingData.data)
      setSnapshots(snapshotData.data)
      const firstStudent = progressData.data.students[0] ?? null
      setStudentId(firstStudent?.student_id ?? '')
      setStudentProgress(firstStudent)
    } catch (error) {
      setMessage(errorMessage(error))
    }
  }

  async function handleStudentChange(nextStudentId: string) {
    setStudentId(nextStudentId)
    if (!nextStudentId) {
      setStudentProgress(null)
      return
    }
    try {
      if (currentUser.role === 'admin') {
        const progressData = await getStudentProgress(nextStudentId)
        setStudentProgress(progressData.data)
      } else {
        setStudentProgress(classProgress?.students.find((student) => student.student_id === nextStudentId) ?? null)
      }
    } catch (error) {
      setMessage(errorMessage(error))
    }
  }

  async function handleTeacherChange(nextTeacherId: string) {
    setTeacherId(nextTeacherId)
    if (!nextTeacherId) return
    try {
      const data = await getTeacherProgress(nextTeacherId)
      setTeacherProgress(data.data)
    } catch (error) {
      setMessage(errorMessage(error))
    }
  }

  async function handleTrackChange(nextTrackId: string) {
    setTrackId(nextTrackId)
    if (!nextTrackId) return
    try {
      const data = await getTrackRanking(nextTrackId)
      setTrackRanking(data.data)
    } catch (error) {
      setMessage(errorMessage(error))
    }
  }

  async function handleCreateSnapshot() {
    if (!classId) return
    try {
      const response = currentUser.role === 'teacher'
        ? await createTeacherClassProgressSnapshots(classId)
        : await createClassProgressSnapshots(classId)
      setSnapshots(response.data)
      setMessage(`${response.data.length} progress snapshot rows created.`)
    } catch (error) {
      setMessage(errorMessage(error))
    }
  }

  const teachers = users.filter((user) => user.teacher_profile)
  const snapshotWeeks = Array.from(new Set(snapshots.map((snapshot) => String(snapshot.week_number))))
  const snapshotYears = Array.from(new Set(snapshots.map((snapshot) => String(snapshot.year))))
  const visibleSnapshots = snapshots.filter((snapshot) => {
    const weekMatches = weekFilter === 'all' || String(snapshot.week_number) === weekFilter
    const yearMatches = yearFilter === 'all' || String(snapshot.year) === yearFilter
    return weekMatches && yearMatches
  })

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}
      <section className="stats-grid" aria-label="Progress summary">
        <article className="stat-card"><span>{currentUser.role === 'student' ? 'My progress' : 'Class progress'}</span><strong>{loading ? '...' : formatProgress(currentUser.role === 'student' ? studentProgress?.final_progress : classProgress?.class_progress)}</strong><small>Weighted final progress</small></article>
        <article className="stat-card"><span>Students</span><strong>{classProgress?.student_count ?? (studentProgress ? 1 : 0)}</strong><small>Current scope</small></article>
        <article className="stat-card"><span>Ranking rows</span><strong>{currentUser.role === 'student' ? top3.length : classRanking.length}</strong><small>{currentUser.role === 'student' ? 'Top 3' : 'Class ranking'}</small></article>
        <article className="stat-card"><span>Snapshots</span><strong>{visibleSnapshots.length}</strong><small>Historical rows</small></article>
      </section>

      {currentUser.role !== 'student' && (
        <section className="data-panel admin-users-panel">
          <div className="panel-toolbar">
            <div><h2>{currentUser.role === 'admin' ? 'Class Progress' : 'Assigned Class Progress'}</h2><p>Review weighted progress by class and student.</p></div>
            <div className="admin-toolbar outcomes-toolbar">
              <label><span>Class</span><select value={classId} onChange={(event) => handleClassChange(event.target.value)}>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
              <label><span>Student</span><select value={studentId} onChange={(event) => handleStudentChange(event.target.value)}>{classProgress?.students.map((student) => <option key={student.student_id} value={student.student_id}>{student.student_code} - {student.student_name}</option>)}</select></label>
              {currentUser.role === 'admin' && <label><span>Teacher</span><select value={teacherId} onChange={(event) => handleTeacherChange(event.target.value)}>{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>}
              <button className="primary-button" type="button" onClick={handleCreateSnapshot}>Create snapshot</button>
            </div>
          </div>
          <ProgressTable students={classProgress?.students ?? []} />
        </section>
      )}

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div><h2>{currentUser.role === 'student' ? 'My Progress' : 'Student Progress'}</h2><p>Attendance, quiz, assignment, bonus, and final progress split.</p></div>
        </div>
        <ProgressDetail progress={studentProgress} />
      </section>

      {currentUser.role === 'admin' && (
        <section className="data-panel admin-users-panel">
          <div className="panel-toolbar">
            <div><h2>Teacher Progress</h2><p>Instructor and mentor progress across assigned classes.</p></div>
          </div>
          <TeacherProgressPanel progress={teacherProgress} />
        </section>
      )}

      <section className="data-panel admin-users-panel">
        <div className="panel-toolbar">
          <div><h2>{currentUser.role === 'student' ? 'Top 3 Ranking' : 'Class Ranking'}</h2><p>Ranking is ordered by final progress, with ties sharing rank.</p></div>
          {currentUser.role !== 'student' && <label className="compact-filter"><span>Class selector</span><select value={classId} onChange={(event) => handleClassChange(event.target.value)}>{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>}
        </div>
        <RankingTable ranking={currentUser.role === 'student' ? top3 : classRanking} />
      </section>

      {currentUser.role === 'admin' && (
        <>
          <section className="data-panel admin-users-panel">
            <div className="panel-toolbar">
              <div><h2>Track Ranking</h2><p>Compare active students across classes in a track.</p></div>
              <label className="compact-filter"><span>Track selector</span><select value={trackId} onChange={(event) => handleTrackChange(event.target.value)}>{tracks.map((track) => <option key={track.id} value={track.id}>{track.code} - {track.name}</option>)}</select></label>
            </div>
            <RankingTable ranking={trackRanking} />
          </section>

          <section className="data-panel admin-users-panel">
            <div className="panel-toolbar">
              <div><h2>Snapshot History</h2><p>Filter immutable progress snapshots by week and year.</p></div>
              <div className="admin-toolbar snapshot-toolbar">
                <label><span>Week</span><select value={weekFilter} onChange={(event) => setWeekFilter(event.target.value)}><option value="all">All weeks</option>{snapshotWeeks.map((week) => <option key={week} value={week}>Week {week}</option>)}</select></label>
                <label><span>Year</span><select value={yearFilter} onChange={(event) => setYearFilter(event.target.value)}><option value="all">All years</option>{snapshotYears.map((year) => <option key={year} value={year}>{year}</option>)}</select></label>
              </div>
            </div>
            <SnapshotTable snapshots={visibleSnapshots} />
          </section>
        </>
      )}
    </section>
  )
}

function ProgressTable({ students }: { students: StudentProgress[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Student</th><th>Class</th><th>Attendance</th><th>Quiz</th><th>Assignment</th><th>Bonus</th><th>Final</th></tr></thead>
        <tbody>
          {students.map((student) => (
            <tr key={student.student_id}>
              <td>{student.student_name}<br /><small>{student.student_code}</small></td>
              <td><span className="class-code">{student.class_code}</span></td>
              <td>{formatProgress(student.attendance_progress)}</td>
              <td>{formatProgress(student.quiz_progress)}</td>
              <td>{formatProgress(student.assignment_progress)}</td>
              <td>{formatProgress(student.bonus_progress)}</td>
              <td><StatusBadge value={formatProgress(student.final_progress)} /></td>
            </tr>
          ))}
          {!students.length && <tr><td colSpan={7}>No progress rows are available for this class.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function ProgressDetail({ progress }: { progress: StudentProgress | null }) {
  if (!progress) {
    return <p className="empty-text">No student progress is available for the current selection.</p>
  }

  return (
    <div className="progress-detail-grid">
      <span><strong>Student</strong>{progress.student_code} - {progress.student_name}</span>
      <span><strong>Class</strong>{progress.class_code}</span>
      <span><strong>Attendance</strong>{formatProgress(progress.attendance_progress)}</span>
      <span><strong>Quiz</strong>{formatProgress(progress.quiz_progress)}</span>
      <span><strong>Assignment</strong>{formatProgress(progress.assignment_progress)}</span>
      <span><strong>Bonus</strong>{formatProgress(progress.bonus_progress)}</span>
      <span><strong>Final</strong>{formatProgress(progress.final_progress)}</span>
    </div>
  )
}

function TeacherProgressPanel({ progress }: { progress: TeacherProgress | null }) {
  if (!progress) {
    return <p className="empty-text">Select a teacher to view progress.</p>
  }

  return (
    <>
      <div className="progress-detail-grid">
        <span><strong>Teacher</strong>{progress.teacher_name}</span>
        <span><strong>Instructor progress</strong>{formatProgress(progress.instructor_progress)}</span>
        <span><strong>Mentor progress</strong>{formatProgress(progress.mentor_progress)}</span>
      </div>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Class</th><th>Role</th><th>Progress</th></tr></thead>
          <tbody>
            {progress.assigned_classes.map((item) => (
              <tr key={`${item.class_id}-${item.role}`}>
                <td><span className="class-code">{item.class_code}</span></td>
                <td>{titleCase(item.role)}</td>
                <td>{formatProgress(item.class_progress)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

function RankingTable({ ranking }: { ranking: RankingItem[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Rank</th><th>Student</th><th>Class</th><th>Attendance</th><th>Quiz</th><th>Assignment</th><th>Bonus</th><th>Final</th></tr></thead>
        <tbody>
          {ranking.map((item) => (
            <tr key={`${item.rank}-${item.student_id}-${item.class_id}`}>
              <td><StatusBadge value={`#${item.rank}`} /></td>
              <td>{item.student_name}<br /><small>{item.student_code}</small></td>
              <td><span className="class-code">{item.class_code}</span></td>
              <td>{formatProgress(item.attendance_progress)}</td>
              <td>{formatProgress(item.quiz_progress)}</td>
              <td>{formatProgress(item.assignment_progress)}</td>
              <td>{formatProgress(item.bonus_progress)}</td>
              <td>{formatProgress(item.final_progress)}</td>
            </tr>
          ))}
          {!ranking.length && <tr><td colSpan={8}>No ranking rows are available for this selection.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function SnapshotTable({ snapshots }: { snapshots: ProgressSnapshot[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Student</th><th>Class</th><th>Week</th><th>Year</th><th>Attendance</th><th>Quiz</th><th>Assignment</th><th>Bonus</th><th>Final</th></tr></thead>
        <tbody>
          {snapshots.map((snapshot) => (
            <tr key={snapshot.id}>
              <td>{snapshot.student_name}<br /><small>{snapshot.student_code}</small></td>
              <td><span className="class-code">{snapshot.class_code}</span></td>
              <td>Week {snapshot.week_number}</td>
              <td>{snapshot.year}</td>
              <td>{formatProgress(snapshot.attendance_progress)}</td>
              <td>{formatProgress(snapshot.quiz_progress)}</td>
              <td>{formatProgress(snapshot.assignment_progress)}</td>
              <td>{formatProgress(snapshot.bonus_progress)}</td>
              <td>{formatProgress(snapshot.final_progress)}</td>
            </tr>
          ))}
          {!snapshots.length && <tr><td colSpan={9}>No snapshots match the selected week and year.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

type FinalProjectModalState =
  | { type: 'submit'; project: FinalProject | null }
  | { type: 'review'; project: FinalProject }
  | null

const finalProjectStatuses: FinalProjectStatus[] = ['pending', 'approved', 'rejected']

function FinalProjectsExperience({ currentUser }: { currentUser: CurrentUser }) {
  const [projects, setProjects] = useState<FinalProject[]>([])
  const [myProject, setMyProject] = useState<FinalProject | null>(null)
  const [classes, setClasses] = useState<AcademicClass[]>([])
  const [tracks, setTracks] = useState<Track[]>([])
  const [classId, setClassId] = useState('all')
  const [trackId, setTrackId] = useState('all')
  const [statusFilter, setStatusFilter] = useState<'all' | FinalProjectStatus>('all')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<FinalProjectModalState>(null)

  async function reloadProjects(nextClassId = classId) {
    setLoading(true)
    setMessage('')
    try {
      if (currentUser.role === 'student') {
        const project = await loadStudentFinalProject()
        setMyProject(project)
        setProjects(project ? [project] : [])
      } else {
        const data = await loadFinalProjectWorkspace(currentUser.role, nextClassId)
        setProjects(data.projects)
        setClasses(data.classes)
        setTracks(data.tracks)
        if (currentUser.role === 'teacher' && !nextClassId && data.classes[0]?.id) {
          setClassId(data.classes[0].id)
        }
      }
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true

    async function loadInitialProjects() {
      try {
        if (currentUser.role === 'student') {
          const project = await loadStudentFinalProject()
          if (!mounted) return
          setMyProject(project)
          setProjects(project ? [project] : [])
        } else {
          const data = await loadFinalProjectWorkspace(currentUser.role, '')
          if (!mounted) return
          setProjects(data.projects)
          setClasses(data.classes)
          setTracks(data.tracks)
          setClassId(currentUser.role === 'teacher' ? data.classes[0]?.id ?? '' : 'all')
        }
      } catch (error) {
        if (mounted) setMessage(errorMessage(error))
      } finally {
        if (mounted) setLoading(false)
      }
    }

    void loadInitialProjects()

    return () => {
      mounted = false
    }
  }, [currentUser.role])

  async function handleClassChange(nextClassId: string) {
    setClassId(nextClassId)
    if (currentUser.role === 'teacher') {
      await reloadProjects(nextClassId)
    }
  }

  async function handleStudentSubmit(projectLink: string) {
    if (myProject) {
      await updateMyFinalProject({ project_link: projectLink })
    } else {
      await submitMyFinalProject({ project_link: projectLink })
    }
    setModal(null)
    await reloadProjects()
  }

  async function handleReview(project: FinalProject, payload: FinalProjectReview) {
    await reviewFinalProject(project.final_project_id, payload)
    setModal(null)
    await reloadProjects()
  }

  const classTrackLookup = new Map(classes.map((item) => [item.id, item.track_id]))
  const visibleProjects = projects.filter((project) => {
    const classMatches = classId === 'all' || project.class_id === classId
    const trackMatches = trackId === 'all' || classTrackLookup.get(project.class_id) === trackId
    const statusMatches = statusFilter === 'all' || project.status === statusFilter
    return classMatches && trackMatches && statusMatches
  })

  return (
    <section className="admin-stack">
      {message && <div className="form-message">{message}</div>}
      <section className="stats-grid" aria-label="Final project summary">
        <article className="stat-card"><span>Projects</span><strong>{loading ? '...' : projects.length}</strong><small>{currentUser.role === 'student' ? 'My submission' : 'Current queue'}</small></article>
        <article className="stat-card"><span>Pending</span><strong>{projects.filter((project) => project.status === 'pending').length}</strong><small>Needs review</small></article>
        <article className="stat-card"><span>Approved</span><strong>{projects.filter((project) => project.status === 'approved').length}</strong><small>Reviewed</small></article>
        <article className="stat-card"><span>Rejected</span><strong>{projects.filter((project) => project.status === 'rejected').length}</strong><small>Feedback attached</small></article>
      </section>

      {currentUser.role === 'student' ? (
        <section className="data-panel admin-users-panel">
          <div className="panel-toolbar">
            <div><h2>Final Project Submission</h2><p>Submit or update your pending final project link.</p></div>
            <button className="primary-button" type="button" onClick={() => setModal({ type: 'submit', project: myProject })}>{myProject ? 'Update project' : 'Submit project'}</button>
          </div>
          <FinalProjectsTable projects={visibleProjects} canReview={false} onReview={() => undefined} />
        </section>
      ) : (
        <section className="data-panel admin-users-panel">
          <div className="panel-toolbar">
            <div><h2>{currentUser.role === 'admin' ? 'Final Project Review Queue' : 'Final Projects for Assigned Classes'}</h2><p>{currentUser.role === 'admin' ? 'Review pending submissions and record approval or rejection.' : 'Read-only project submissions for selected assigned class.'}</p></div>
            <div className="admin-toolbar projects-toolbar">
              <label><span>Class</span><select value={classId} onChange={(event) => handleClassChange(event.target.value)}>{currentUser.role === 'admin' && <option value="all">All classes</option>}{classes.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
              {currentUser.role === 'admin' && <label><span>Track</span><select value={trackId} onChange={(event) => setTrackId(event.target.value)}><option value="all">All tracks</option>{tracks.map((track) => <option key={track.id} value={track.id}>{track.code} - {track.name}</option>)}</select></label>}
              <label><span>Final project status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}><option value="all">All statuses</option>{finalProjectStatuses.map((status) => <option key={status} value={status}>{titleCase(status)}</option>)}</select></label>
            </div>
          </div>
          <FinalProjectsTable projects={visibleProjects} canReview={currentUser.role === 'admin'} onReview={(project) => setModal({ type: 'review', project })} />
        </section>
      )}

      {modal?.type === 'submit' && (
        <FinalProjectSubmitModal project={modal.project} onClose={() => setModal(null)} onSubmit={handleStudentSubmit} />
      )}
      {modal?.type === 'review' && (
        <FinalProjectReviewModal project={modal.project} onClose={() => setModal(null)} onSubmit={(payload) => handleReview(modal.project, payload)} />
      )}
    </section>
  )
}

function FinalProjectsTable({ projects, canReview, onReview }: { projects: FinalProject[]; canReview: boolean; onReview: (project: FinalProject) => void }) {
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Student</th><th>Class</th><th>Level</th><th>Project</th><th>Status</th><th>Grade</th><th>Feedback</th><th>Actions</th></tr></thead>
        <tbody>
          {projects.map((project) => (
            <tr key={project.final_project_id}>
              <td>{project.student_name}<br /><small>{project.student_code}</small></td>
              <td><span className="class-code">{project.class_code}</span></td>
              <td>Level {project.level_number}</td>
              <td><a href={project.project_link} target="_blank" rel="noreferrer">Open project</a></td>
              <td><StatusBadge value={titleCase(project.status)} /></td>
              <td>{project.grade ?? 'Not graded'}</td>
              <td>{project.feedback || 'No feedback'}</td>
              <td>
                <LmsRowMenu
                  actions={[
                    { label: 'Open project', onClick: () => window.open(project.project_link, '_blank', 'noopener,noreferrer') },
                    ...(canReview ? [{ label: 'Review actions', onClick: () => onReview(project) }] : []),
                  ]}
                />
              </td>
            </tr>
          ))}
          {!projects.length && <tr><td colSpan={8}>No final projects match the selected filters.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function FinalProjectSubmitModal({ project, onClose, onSubmit }: { project: FinalProject | null; onClose: () => void; onSubmit: (projectLink: string) => Promise<void> }) {
  const [projectLink, setProjectLink] = useState(project?.project_link ?? '')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit(projectLink)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="project-submit-title">
        <div className="modal-header"><div><span className="eyebrow">Final project</span><h2 id="project-submit-title">{project ? 'Update' : 'Submit'} final project</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button></div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            {project && <div className="class-code-guide"><strong>Current status: {titleCase(project.status)}</strong><span>Pending submissions can be updated before review.</span></div>}
            <label><span>Project link</span><input type="url" value={projectLink} onChange={(event) => setProjectLink(event.target.value)} required /></label>
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting}>{submitting ? 'Saving...' : 'Save project'}</button></div>
        </form>
      </section>
    </div>
  )
}

function FinalProjectReviewModal({ project, onClose, onSubmit }: { project: FinalProject; onClose: () => void; onSubmit: (payload: FinalProjectReview) => Promise<void> }) {
  const [status, setStatus] = useState<FinalProjectStatus>(project.status === 'rejected' ? 'rejected' : 'approved')
  const [grade, setGrade] = useState(project.grade?.toString() ?? '')
  const [feedback, setFeedback] = useState(project.feedback ?? '')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit({ status, grade: grade ? Number(grade) : null, feedback: feedback || null })
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="project-review-title">
        <div className="modal-header"><div><span className="eyebrow">Review actions</span><h2 id="project-review-title">Review final project</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close modal"><X size={20} /></button></div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <div className="class-code-guide"><strong>{project.student_name}</strong><span><code>{project.class_code}</code> Level {project.level_number} / submitted {formatDateTime(project.submitted_at)}.</span></div>
            <label><span>Review action</span><select value={status} onChange={(event) => setStatus(event.target.value as FinalProjectStatus)}><option value="approved">Approve</option><option value="rejected">Reject</option></select></label>
            <div className="form-grid-two">
              <label><span>Grade</span><input type="number" min="0" step="0.5" value={grade} onChange={(event) => setGrade(event.target.value)} /></label>
              <label><span>Final project status</span><select value={status} onChange={(event) => setStatus(event.target.value as FinalProjectStatus)}><option value="approved">Approved</option><option value="rejected">Rejected</option></select></label>
            </div>
            <label><span>Feedback</span><textarea value={feedback} onChange={(event) => setFeedback(event.target.value)} rows={4} /></label>
          </div>
          <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={submitting}>{submitting ? 'Saving...' : 'Save review'}</button></div>
        </form>
      </section>
    </div>
  )
}

function AcademicTable({
  kind,
  records,
  branches,
  cycles,
  tracks,
  levels,
  teachers,
  onEdit,
  onDelete,
}: {
  kind: AcademicKind
  records: AcademicRecord[]
  branches: Branch[]
  cycles: Cycle[]
  tracks: Track[]
  levels: Level[]
  teachers: CurrentUser[]
  onEdit: (record: AcademicRecord) => void
  onDelete: (record: AcademicRecord) => void
}) {
  const columns = academicColumns(kind)

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((column) => <th key={column}>{column}</th>)}
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id}>
              {columns.map((column) => (
                <td key={column}>{academicCell(kind, column, record, { branches, cycles, tracks, levels, teachers })}</td>
              ))}
              <td>
                <AcademicActionMenu onEdit={() => onEdit(record)} onDelete={() => onDelete(record)} />
              </td>
            </tr>
          ))}
          {records.length === 0 && (
            <tr>
              <td colSpan={columns.length + 1}>No {academicLabel(kind).toLowerCase()} records match the current filters.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

function AcademicFormModal({
  mode,
  kind,
  record,
  branches,
  cycles,
  tracks,
  levels,
  teachers,
  onClose,
  onSubmit,
}: {
  mode: 'create' | 'edit'
  kind: AcademicKind
  record?: AcademicRecord
  branches: Branch[]
  cycles: Cycle[]
  tracks: Track[]
  levels: Level[]
  teachers: CurrentUser[]
  onClose: () => void
  onSubmit: (form: AcademicFormState) => Promise<void>
}) {
  const [form, setForm] = useState<AcademicFormState>(() => academicFormFromRecord(kind, record, { branches, cycles, tracks, levels, teachers }))
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const selectedTrack = tracks.find((track) => track.id === form.track_id)
  const visibleLevels = levels.filter((level) => !form.track_id || level.track_id === form.track_id)
  const classCodeExample = `${selectedTrack?.code ?? 'BE'}${form.class_type === 'online' ? '1' : '5'}001`

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit(form)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="academic-form-title">
        <div className="modal-header">
          <div>
            <span className="eyebrow">Academic setup</span>
            <h2 id="academic-form-title">{mode === 'create' ? 'Create' : 'Edit'} {academicLabel(kind)}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <AcademicFields
              kind={kind}
              form={form}
              setForm={setForm}
              branches={branches}
              cycles={cycles}
              tracks={tracks}
              levels={visibleLevels}
              teachers={teachers}
              classCodeExample={classCodeExample}
            />
          </div>
          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

function AcademicFields({
  kind,
  form,
  setForm,
  branches,
  cycles,
  tracks,
  levels,
  teachers,
  classCodeExample,
}: {
  kind: AcademicKind
  form: AcademicFormState
  setForm: (form: AcademicFormState) => void
  branches: Branch[]
  cycles: Cycle[]
  tracks: Track[]
  levels: Level[]
  teachers: CurrentUser[]
  classCodeExample: string
}) {
  if (kind === 'branches') {
    return (
      <label>
        <span>Branch name</span>
        <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
      </label>
    )
  }

  if (kind === 'cycles') {
    return (
      <>
        <div className="form-grid-two">
          <label><span>Cycle number</span><input type="number" min="1" value={form.cycle_number} onChange={(event) => setForm({ ...form, cycle_number: event.target.value })} required /></label>
          <label><span>Status</span><select value={form.cycle_status} onChange={(event) => setForm({ ...form, cycle_status: event.target.value as AcademicFormState['cycle_status'] })}><option value="active">Active</option><option value="closed">Closed</option></select></label>
        </div>
        <label><span>Cycle name</span><input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required /></label>
        <div className="form-grid-two">
          <label><span>Start date</span><input type="date" value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} required /></label>
          <label><span>End date</span><input type="date" value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} required /></label>
        </div>
      </>
    )
  }

  if (kind === 'tracks') {
    return (
      <>
        <div className="form-grid-two">
          <label><span>Track code</span><input maxLength={2} value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value.toUpperCase() })} placeholder="BE" required /></label>
          <label><span>Track number</span><input type="number" min="1" value={form.track_number} onChange={(event) => setForm({ ...form, track_number: event.target.value })} required /></label>
        </div>
        <label><span>Track name</span><input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required /></label>
        <label className="checkbox-row">
          <input type="checkbox" checked={form.create_default_levels} onChange={(event) => setForm({ ...form, create_default_levels: event.target.checked })} />
          <span>Create default levels 1, 2, and 3</span>
        </label>
      </>
    )
  }

  if (kind === 'levels') {
    return (
      <>
        <label><span>Track</span><select value={form.track_id} onChange={(event) => setForm({ ...form, track_id: event.target.value })} required>{optionPlaceholder('Select track')}{tracks.map((track) => <option key={track.id} value={track.id}>{track.code} - {track.name}</option>)}</select></label>
        <div className="form-grid-two">
          <label><span>Level number</span><select value={form.level_number} onChange={(event) => setForm({ ...form, level_number: event.target.value })}><option value="1">Level 1</option><option value="2">Level 2</option><option value="3">Level 3</option></select></label>
          <label><span>Duration months</span><input type="number" min="1" value={form.duration_months} onChange={(event) => setForm({ ...form, duration_months: event.target.value })} required /></label>
        </div>
        <label><span>Title</span><input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required /></label>
      </>
    )
  }

  return (
    <>
      <div className="class-code-guide">
        <strong>Class code format</strong>
        <span><code>{classCodeExample}</code> uses track code + type digit + sequence. Online uses 1, onsite uses 5.</span>
      </div>
      <div className="form-grid-two">
        <label><span>Class code</span><input value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value.toUpperCase() })} placeholder={classCodeExample} minLength={6} maxLength={6} required /></label>
        <label><span>Class type</span><select value={form.class_type} onChange={(event) => setForm({ ...form, class_type: event.target.value as AcademicFormState['class_type'] })}><option value="online">Online</option><option value="onsite">Onsite</option></select></label>
      </div>
      <div className="form-grid-two">
        <label><span>Branch</span><select value={form.branch_id} onChange={(event) => setForm({ ...form, branch_id: event.target.value })} required>{optionPlaceholder('Select branch')}{branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label>
        <label><span>Cycle</span><select value={form.cycle_id} onChange={(event) => setForm({ ...form, cycle_id: event.target.value })} required>{optionPlaceholder('Select cycle')}{cycles.map((cycle) => <option key={cycle.id} value={cycle.id}>{cycle.name}</option>)}</select></label>
      </div>
      <div className="form-grid-two">
        <label><span>Track</span><select value={form.track_id} onChange={(event) => setForm({ ...form, track_id: event.target.value, level_id: '' })} required>{optionPlaceholder('Select track')}{tracks.map((track) => <option key={track.id} value={track.id}>{track.code} - {track.name}</option>)}</select></label>
        <label><span>Level</span><select value={form.level_id} onChange={(event) => setForm({ ...form, level_id: event.target.value })} required>{optionPlaceholder('Select level')}{levels.map((level) => <option key={level.id} value={level.id}>Level {level.level_number} - {level.title}</option>)}</select></label>
      </div>
      <div className="form-grid-two">
        <label><span>Instructor</span><select value={form.instructor_id} onChange={(event) => setForm({ ...form, instructor_id: event.target.value })} required>{optionPlaceholder('Select instructor')}{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>
        <label><span>Mentor</span><select value={form.mentor_id} onChange={(event) => setForm({ ...form, mentor_id: event.target.value })} required>{optionPlaceholder('Select mentor')}{teachers.map((teacher) => <option key={teacher.teacher_profile?.id} value={teacher.teacher_profile?.id}>{teacher.teacher_profile?.full_name}</option>)}</select></label>
      </div>
      <label><span>Schedule text</span><input value={form.schedule_text} onChange={(event) => setForm({ ...form, schedule_text: event.target.value })} placeholder="Sun/Tue 7:00 PM" required /></label>
      <div className="form-grid-two">
        <label><span>Max students</span><input type="number" min="1" max="25" value={form.max_students} onChange={(event) => setForm({ ...form, max_students: event.target.value })} required /></label>
        <label><span>Status</span><select value={form.class_status} onChange={(event) => setForm({ ...form, class_status: event.target.value as AcademicFormState['class_status'] })}><option value="planned">Planned</option><option value="active">Active</option><option value="completed">Completed</option><option value="cancelled">Cancelled</option></select></label>
      </div>
      <div className="form-grid-two">
        <label><span>Start date</span><input type="date" value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} required /></label>
        <label><span>End date</span><input type="date" value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} required /></label>
      </div>
    </>
  )
}

function UserFormModal({
  title,
  mode,
  user,
  onClose,
  onSubmit,
}: {
  title: string
  mode: 'create' | 'edit'
  user?: CurrentUser
  onClose: () => void
  onSubmit: (payload: UserCreate | UserUpdate) => Promise<void>
}) {
  const [form, setForm] = useState<UserFormState>(() => userFormFromUser(user))
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')

    try {
      await onSubmit(mode === 'create' ? createPayloadFromForm(form) : updatePayloadFromForm(form))
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
      return
    }

    setSubmitting(false)
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal admin-modal" role="dialog" aria-modal="true" aria-labelledby="user-form-title">
        <div className="modal-header">
          <div>
            <span className="eyebrow">Admin user workflow</span>
            <h2 id="user-form-title">{title}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <label>
              <span>Email</span>
              <input
                type="email"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
                required
              />
            </label>

            {mode === 'create' && (
              <label>
                <span>Temporary password</span>
                <input
                  type="password"
                  value={form.password}
                  onChange={(event) => setForm({ ...form, password: event.target.value })}
                  minLength={8}
                  required
                />
              </label>
            )}

            <div className="form-grid-two">
              <label>
                <span>Role</span>
                <select
                  value={form.role}
                  onChange={(event) => setForm({ ...form, role: event.target.value as Role })}
                  disabled={mode === 'edit'}
                >
                  <option value="admin">Admin</option>
                  <option value="teacher">Teacher</option>
                  <option value="student">Student</option>
                </select>
              </label>
              <label>
                <span>Status</span>
                <select
                  value={form.is_active ? 'active' : 'inactive'}
                  onChange={(event) => setForm({ ...form, is_active: event.target.value === 'active' })}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </label>
            </div>

            <RoleProfileFields form={form} onChange={setForm} />
          </div>
          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? 'Saving...' : 'Save user'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

function RoleProfileFields({ form, onChange }: { form: UserFormState; onChange: (form: UserFormState) => void }) {
  if (form.role === 'admin') {
    return (
      <label>
        <span>Admin full name</span>
        <input
          value={form.full_name}
          onChange={(event) => onChange({ ...form, full_name: event.target.value })}
          required
        />
      </label>
    )
  }

  if (form.role === 'teacher') {
    return (
      <>
        <div className="form-grid-two">
          <label>
            <span>Teacher code</span>
            <input
              value={form.teacher_code}
              onChange={(event) => onChange({ ...form, teacher_code: event.target.value })}
              required
            />
          </label>
          <label>
            <span>Teacher type</span>
            <select
              value={form.teacher_type}
              onChange={(event) => onChange({ ...form, teacher_type: event.target.value as UserFormState['teacher_type'] })}
            >
              <option value="instructor">Instructor</option>
              <option value="mentor">Mentor</option>
              <option value="instructor_and_mentor">Instructor and mentor</option>
            </select>
          </label>
        </div>
        <label>
          <span>Teacher full name</span>
          <input
            value={form.full_name}
            onChange={(event) => onChange({ ...form, full_name: event.target.value })}
            required
          />
        </label>
        <label>
          <span>Phone number</span>
          <input value={form.phone_number} onChange={(event) => onChange({ ...form, phone_number: event.target.value })} />
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.is_team_leader}
            onChange={(event) => onChange({ ...form, is_team_leader: event.target.checked })}
          />
          <span>Team leader</span>
        </label>
      </>
    )
  }

  return (
    <>
      <div className="form-grid-two">
        <label>
          <span>Student code</span>
          <input
            value={form.student_code}
            onChange={(event) => onChange({ ...form, student_code: event.target.value })}
            required
          />
        </label>
        <label>
          <span>Student status</span>
          <select
            value={form.student_status}
            onChange={(event) => onChange({ ...form, student_status: event.target.value as UserFormState['student_status'] })}
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
            <option value="dropped">Dropped</option>
            <option value="graduated">Graduated</option>
          </select>
        </label>
      </div>
      <label>
        <span>Student full name</span>
        <input
          value={form.full_name}
          onChange={(event) => onChange({ ...form, full_name: event.target.value })}
          required
        />
      </label>
      <label>
        <span>Phone number</span>
        <input value={form.phone_number} onChange={(event) => onChange({ ...form, phone_number: event.target.value })} />
      </label>
    </>
  )
}

function ConfirmModal({
  title,
  message,
  confirmLabel,
  onClose,
  onConfirm,
}: {
  title: string
  message: string
  confirmLabel: string
  onClose: () => void
  onConfirm: () => Promise<void>
}) {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleConfirm() {
    setSubmitting(true)
    setError('')
    try {
      await onConfirm()
    } catch (caught) {
      setError(errorMessage(caught))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal confirm-modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
        <div className="modal-header">
          <div>
            <span className="eyebrow">Confirmation</span>
            <h2 id="confirm-title">{title}</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>
        <div className="modal-body">
          {error && <div className="form-message">{error}</div>}
          <p>{message}</p>
        </div>
        <div className="modal-actions">
          <button type="button" onClick={onClose}>Cancel</button>
          <button className="danger-button" type="button" onClick={handleConfirm} disabled={submitting}>
            {submitting ? 'Working...' : confirmLabel}
          </button>
        </div>
      </section>
    </div>
  )
}

function ResetPasswordModal({
  user,
  onClose,
  onSubmit,
}: {
  user: CurrentUser
  onClose: () => void
  onSubmit: (newPassword: string) => Promise<void>
}) {
  const [newPassword, setNewPassword] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setMessage('')
    try {
      await onSubmit(newPassword)
    } catch (error) {
      setMessage(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal confirm-modal" role="dialog" aria-modal="true" aria-labelledby="reset-title">
        <div className="modal-header">
          <div>
            <span className="eyebrow">Admin only</span>
            <h2 id="reset-title">Reset password</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-form">
            {message && <div className="form-message">{message}</div>}
            <p>Reset password for {user.email}. The user will be forced to change it after login.</p>
            <label>
              <span>New password</span>
              <input
                type="password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                minLength={8}
                required
              />
            </label>
          </div>
          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? 'Resetting...' : 'Reset password'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

function AdminUserActionMenu({
  onEdit,
  onReset,
  onDelete,
}: {
  onEdit: () => void
  onReset: () => void
  onDelete: () => void
}) {
  return (
    <details className="dropdown-menu row-menu">
      <summary aria-label="User row actions">
        <MoreHorizontal size={18} />
      </summary>
      <div className="dropdown-panel dropdown-panel-right">
        <button type="button" onClick={onEdit}>Edit user</button>
        <button type="button" onClick={onReset}>Reset password</button>
        <button type="button" onClick={onDelete}>Soft delete</button>
      </div>
    </details>
  )
}

function AcademicActionMenu({ onEdit, onDelete }: { onEdit: () => void; onDelete: () => void }) {
  return (
    <details className="dropdown-menu row-menu">
      <summary aria-label="Academic row actions">
        <MoreHorizontal size={18} />
      </summary>
      <div className="dropdown-panel dropdown-panel-right">
        <button type="button" onClick={onEdit}>Edit</button>
        <button type="button" onClick={onDelete}>Delete</button>
      </div>
    </details>
  )
}

function getAcademicRecords(kind: AcademicKind, data: {
  branches: Branch[]
  cycles: Cycle[]
  tracks: Track[]
  levels: Level[]
  classes: AcademicClass[]
}) {
  if (kind === 'branches') return data.branches
  if (kind === 'cycles') return data.cycles
  if (kind === 'tracks') return data.tracks
  if (kind === 'levels') return data.levels
  return data.classes
}

function filterAcademicRecords(records: AcademicRecord[], query: string, filter: string) {
  const normalizedQuery = query.trim().toLowerCase()
  return records.filter((record) => {
    const textMatches = !normalizedQuery || JSON.stringify(record).toLowerCase().includes(normalizedQuery)
    const filterMatches =
      filter === 'all' ||
      ('status' in record && record.status === filter) ||
      ('class_type' in record && record.class_type === filter) ||
      ('track_id' in record && record.track_id === filter)
    return textMatches && filterMatches
  })
}

function academicColumns(kind: AcademicKind) {
  if (kind === 'branches') return ['Name', 'Created']
  if (kind === 'cycles') return ['Cycle', 'Dates', 'Status']
  if (kind === 'tracks') return ['Code', 'Name', 'Levels']
  if (kind === 'levels') return ['Track', 'Level', 'Duration']
  return ['Code', 'Structure', 'Team', 'Status']
}

function academicCell(
  kind: AcademicKind,
  column: string,
  record: AcademicRecord,
  lookups: { branches: Branch[]; cycles: Cycle[]; tracks: Track[]; levels: Level[]; teachers: CurrentUser[] },
) {
  if (kind === 'branches') {
    const branch = record as Branch
    if (column === 'Name') return branch.name
    return compactDate(branch.created_at)
  }

  if (kind === 'cycles') {
    const cycle = record as Cycle
    if (column === 'Cycle') return `${cycle.cycle_number} - ${cycle.name}`
    if (column === 'Dates') return `${cycle.start_date} to ${cycle.end_date}`
    return <StatusBadge value={cycle.status} />
  }

  if (kind === 'tracks') {
    const track = record as Track
    if (column === 'Code') return <span className="class-code">{track.code}</span>
    if (column === 'Name') return `${track.name} / #${track.track_number}`
    return `${track.levels?.length ?? 0} levels`
  }

  if (kind === 'levels') {
    const level = record as Level
    if (column === 'Track') return trackName(lookups.tracks, level.track_id)
    if (column === 'Level') return `Level ${level.level_number} - ${level.title}`
    return `${level.duration_months} months`
  }

  const academicClass = record as AcademicClass
  if (column === 'Code') return <span className="class-code">{academicClass.code}</span>
  if (column === 'Structure') {
    return `${branchName(lookups.branches, academicClass.branch_id)} / ${trackName(lookups.tracks, academicClass.track_id)} / ${levelName(lookups.levels, academicClass.level_id)}`
  }
  if (column === 'Team') {
    return `${teacherName(lookups.teachers, academicClass.instructor_id)} / ${teacherName(lookups.teachers, academicClass.mentor_id)}`
  }
  return <StatusBadge value={`${academicClass.status} ${academicClass.class_type}`} />
}

function academicFormFromRecord(
  kind: AcademicKind,
  record: AcademicRecord | undefined,
  lookups: { branches: Branch[]; cycles: Cycle[]; tracks: Track[]; levels: Level[]; teachers: CurrentUser[] },
): AcademicFormState {
  const defaults = {
    ...emptyAcademicForm,
    branch_id: lookups.branches[0]?.id ?? '',
    cycle_id: lookups.cycles[0]?.id ?? '',
    track_id: lookups.tracks[0]?.id ?? '',
    level_id: lookups.levels[0]?.id ?? '',
    instructor_id: lookups.teachers[0]?.teacher_profile?.id ?? '',
    mentor_id: lookups.teachers[0]?.teacher_profile?.id ?? '',
  }

  if (!record) return defaults

  if (kind === 'branches') {
    return { ...defaults, name: (record as Branch).name }
  }

  if (kind === 'cycles') {
    const cycle = record as Cycle
    return {
      ...defaults,
      name: cycle.name,
      cycle_number: String(cycle.cycle_number),
      start_date: cycle.start_date,
      end_date: cycle.end_date,
      cycle_status: cycle.status,
    }
  }

  if (kind === 'tracks') {
    const track = record as Track
    return {
      ...defaults,
      name: track.name,
      code: track.code,
      track_number: String(track.track_number),
    }
  }

  if (kind === 'levels') {
    const level = record as Level
    return {
      ...defaults,
      track_id: level.track_id,
      level_number: String(level.level_number),
      title: level.title,
      duration_months: String(level.duration_months),
    }
  }

  const academicClass = record as AcademicClass
  return {
    ...defaults,
    code: academicClass.code,
    branch_id: academicClass.branch_id,
    cycle_id: academicClass.cycle_id,
    track_id: academicClass.track_id,
    level_id: academicClass.level_id,
    instructor_id: academicClass.instructor_id,
    mentor_id: academicClass.mentor_id,
    schedule_text: academicClass.schedule_text,
    max_students: String(academicClass.max_students),
    class_type: academicClass.class_type,
    class_status: academicClass.status,
    start_date: academicClass.start_date,
    end_date: academicClass.end_date,
  }
}

function academicPayload(kind: AcademicKind, form: AcademicFormState) {
  if (kind === 'branches') return { name: form.name }
  if (kind === 'cycles') {
    return {
      cycle_number: Number(form.cycle_number),
      name: form.name,
      start_date: form.start_date,
      end_date: form.end_date,
      status: form.cycle_status,
    }
  }
  if (kind === 'tracks') {
    return {
      code: form.code,
      name: form.name,
      track_number: Number(form.track_number),
      create_default_levels: form.create_default_levels,
    }
  }
  if (kind === 'levels') {
    return {
      track_id: form.track_id,
      level_number: Number(form.level_number),
      title: form.title,
      duration_months: Number(form.duration_months),
    }
  }
  return {
    code: form.code,
    branch_id: form.branch_id,
    cycle_id: form.cycle_id,
    track_id: form.track_id,
    level_id: form.level_id,
    instructor_id: form.instructor_id,
    mentor_id: form.mentor_id,
    schedule_text: form.schedule_text,
    max_students: Number(form.max_students),
    class_type: form.class_type,
    start_date: form.start_date,
    end_date: form.end_date,
    status: form.class_status,
  }
}

function academicLabel(kind: AcademicKind) {
  const labels: Record<AcademicKind, string> = {
    branches: 'Branch',
    cycles: 'Cycle',
    tracks: 'Track',
    levels: 'Level',
    classes: 'Class',
  }
  return labels[kind]
}

function academicRecordName(kind: AcademicKind, record: AcademicRecord) {
  if (kind === 'branches') return (record as Branch).name
  if (kind === 'cycles') return (record as Cycle).name
  if (kind === 'tracks') return (record as Track).name
  if (kind === 'levels') return (record as Level).title
  return (record as AcademicClass).code
}

function optionPlaceholder(label: string) {
  return <option value="">{label}</option>
}

function compactDate(value: string) {
  return value.slice(0, 10)
}

function activeEnrollmentCount(enrollments: Enrollment[], classId: string) {
  return enrollments.filter((enrollment) => enrollment.class_id === classId && enrollment.status === 'active').length
}

function capacityStatus(activeCount: number, maxStudents: number) {
  if (activeCount >= maxStudents) return 'Full'
  if (activeCount >= Math.floor(maxStudents * 0.85)) return 'Near capacity'
  return 'Available'
}

function classStatusLine(academicClass: AcademicClass, activeCount: number) {
  return `${academicClass.status} / ${capacityStatus(activeCount, academicClass.max_students)}`
}

function branchName(branches: Branch[], id: string) {
  return branches.find((branch) => branch.id === id)?.name ?? 'Unknown branch'
}

function trackName(tracks: Track[], id: string) {
  const track = tracks.find((item) => item.id === id)
  return track ? `${track.code} ${track.name}` : 'Unknown track'
}

function levelName(levels: Level[], id: string) {
  const level = levels.find((item) => item.id === id)
  return level ? `L${level.level_number}` : 'Unknown level'
}

function teacherName(users: CurrentUser[], teacherProfileId: string) {
  return users.find((user) => user.teacher_profile?.id === teacherProfileId)?.teacher_profile?.full_name ?? 'Unknown teacher'
}

function userFormFromUser(user?: CurrentUser): UserFormState {
  if (!user) {
    return emptyUserForm
  }

  if (user.role === 'admin') {
    return {
      ...emptyUserForm,
      email: user.email,
      role: user.role,
      is_active: user.is_active,
      full_name: user.admin_profile?.full_name ?? '',
    }
  }

  if (user.role === 'teacher') {
    return {
      ...emptyUserForm,
      email: user.email,
      role: user.role,
      is_active: user.is_active,
      full_name: user.teacher_profile?.full_name ?? '',
      phone_number: user.teacher_profile?.phone_number ?? '',
      teacher_code: user.teacher_profile?.teacher_code ?? '',
      teacher_type: user.teacher_profile?.teacher_type ?? 'instructor',
      is_team_leader: user.teacher_profile?.is_team_leader ?? false,
    }
  }

  return {
    ...emptyUserForm,
    email: user.email,
    role: user.role,
    is_active: user.is_active,
    full_name: user.student_profile?.full_name ?? '',
    phone_number: user.student_profile?.phone_number ?? '',
    student_code: user.student_profile?.student_code ?? '',
    student_status: user.student_profile?.status ?? 'active',
  }
}

function createPayloadFromForm(form: UserFormState): UserCreate {
  const base = {
    email: form.email,
    password: form.password,
    role: form.role,
  }

  if (form.role === 'admin') {
    return {
      ...base,
      admin_profile: { full_name: form.full_name },
      teacher_profile: null,
      student_profile: null,
    }
  }

  if (form.role === 'teacher') {
    return {
      ...base,
      admin_profile: null,
      teacher_profile: {
        teacher_code: form.teacher_code,
        full_name: form.full_name,
        phone_number: form.phone_number || null,
        teacher_type: form.teacher_type,
        is_team_leader: form.is_team_leader,
      },
      student_profile: null,
    }
  }

  return {
    ...base,
    admin_profile: null,
    teacher_profile: null,
    student_profile: {
      student_code: form.student_code,
      full_name: form.full_name,
      phone_number: form.phone_number || null,
      status: form.student_status,
    },
  }
}

function updatePayloadFromForm(form: UserFormState): UserUpdate {
  const base = {
    email: form.email,
    is_active: form.is_active,
  }

  if (form.role === 'admin') {
    return {
      ...base,
      admin_profile: { full_name: form.full_name },
    }
  }

  if (form.role === 'teacher') {
    return {
      ...base,
      teacher_profile: {
        teacher_code: form.teacher_code,
        full_name: form.full_name,
        phone_number: form.phone_number || null,
        teacher_type: form.teacher_type,
        is_team_leader: form.is_team_leader,
      },
    }
  }

  return {
    ...base,
    student_profile: {
      student_code: form.student_code,
      full_name: form.full_name,
      phone_number: form.phone_number || null,
      status: form.student_status,
    },
  }
}

const submissionStatusOptions: AssignmentSubmissionStatus[] = ['submitted', 'reviewed', 'late', 'replaced', 'rejected']

function materialFormFromRecord(
  material: Material | undefined,
  classes: AcademicClass[],
  teachers: CurrentUser[],
  currentUser: CurrentUser,
): MaterialFormState {
  const firstClass = classes[0]?.id ?? ''
  const firstTeacher = teachers[0]?.teacher_profile?.id ?? ''
  const ownTeacher = currentUser.teacher_profile?.id ?? ''

  if (!material) {
    return {
      ...emptyMaterialForm,
      class_id: firstClass,
      creator_id: currentUser.role === 'admin' ? firstTeacher : ownTeacher,
    }
  }

  return {
    class_id: material.class_id,
    creator_id: material.creator_id,
    creator_role: material.creator_role,
    title: material.title,
    description: material.description ?? '',
    material_type: material.material_type,
    url: material.url,
    is_active: true,
  }
}

function materialPayload(form: MaterialFormState, role: Role): MaterialCreate {
  return {
    class_id: form.class_id,
    creator_id: role === 'admin' ? form.creator_id : null,
    creator_role: form.creator_role,
    title: form.title,
    description: form.description || null,
    material_type: form.material_type,
    url: form.url,
  }
}

function materialUpdatePayload(form: MaterialFormState): MaterialUpdate {
  return {
    creator_role: form.creator_role,
    title: form.title,
    description: form.description || null,
    material_type: form.material_type,
    url: form.url,
    is_active: form.is_active,
  }
}

type AssignmentWorkspaceData = {
  assignments: Assignment[]
  submissions: Submission[]
  pending: PendingSubmission[]
  reviewed: ReviewedSubmission[]
  late: PendingSubmission[]
  classes: AcademicClass[]
  users: CurrentUser[]
}

async function loadAssignmentWorkspace(role: Role): Promise<AssignmentWorkspaceData> {
  if (role === 'student') {
    const [assignmentData, submissionData] = await Promise.all([
      listStudentAssignments(),
      listStudentSubmissions(),
    ])
    return {
      assignments: assignmentData.data,
      submissions: submissionData.data,
      pending: [],
      reviewed: [],
      late: [],
      classes: [],
      users: [],
    }
  }

  if (role === 'admin') {
    const [assignmentData, submissionData, classData, userData] = await Promise.all([
      listAssignments(),
      listAssignmentSubmissions(),
      listClasses(),
      listUsers(),
    ])
    return {
      assignments: assignmentData.data,
      submissions: submissionData.data,
      pending: [],
      reviewed: [],
      late: [],
      classes: classData.data,
      users: userData.data,
    }
  }

  const [assignmentData, pendingData, reviewedData, lateData, classData] = await Promise.all([
    listAssignments(),
    listPendingAssignments(),
    listReviewedAssignments(),
    listLateAssignments(),
    listClasses(),
  ])
  return {
    assignments: assignmentData.data,
    submissions: [],
    pending: pendingData.data,
    reviewed: reviewedData.data,
    late: lateData.data,
    classes: classData.data,
    users: [],
  }
}

function assignmentFormFromRecord(
  assignment: Assignment | undefined,
  classes: AcademicClass[],
  teachers: CurrentUser[],
): AssignmentFormState {
  if (!assignment) {
    return {
      ...emptyAssignmentForm,
      class_id: classes[0]?.id ?? '',
      created_by_teacher_id: teachers[0]?.teacher_profile?.id ?? '',
    }
  }

  return {
    class_id: assignment.class_id,
    created_by_teacher_id: assignment.created_by_teacher_id,
    title: assignment.title,
    description: assignment.description ?? '',
    requirement_url: assignment.requirement_url,
    deadline: toDatetimeInput(assignment.deadline),
    max_grade: String(assignment.max_grade),
    is_active: assignment.is_active,
  }
}

function assignmentPayload(form: AssignmentFormState, role: Role): AssignmentCreate {
  return {
    class_id: form.class_id,
    created_by_teacher_id: role === 'admin' ? form.created_by_teacher_id : null,
    title: form.title,
    description: form.description || null,
    requirement_url: form.requirement_url,
    deadline: new Date(form.deadline).toISOString(),
    max_grade: Number(form.max_grade),
  }
}

function assignmentUpdatePayload(form: AssignmentFormState): AssignmentUpdate {
  return {
    title: form.title,
    description: form.description || null,
    requirement_url: form.requirement_url,
    deadline: new Date(form.deadline).toISOString(),
    max_grade: Number(form.max_grade),
    is_active: form.is_active,
  }
}

function submissionTargetFromAdmin(submission: Submission, assignments: Assignment[]): ReviewTarget {
  const assignment = assignments.find((item) => item.id === submission.assignment_id)
  return {
    id: submission.id,
    classId: submission.class_id,
    assignmentTitle: submission.assignment_title,
    studentName: submission.student_full_name,
    studentCode: submission.student_code,
    classCode: submission.class_code,
    submissionUrl: submission.submission_url,
    maxGrade: assignment?.max_grade ?? submission.grade ?? 0,
    submittedAt: submission.submitted_at,
    reviewedAt: submission.reviewed_at ?? undefined,
    reviewedBy: submission.reviewed_by_teacher,
    grade: submission.grade,
    feedback: submission.feedback,
    status: submission.status,
  }
}

function reviewTargetFromPending(submission: PendingSubmission): ReviewTarget {
  return {
    id: submission.submission_id,
    classId: submission.class_id,
    assignmentTitle: submission.assignment_title,
    studentName: submission.student_full_name,
    studentCode: submission.student_code,
    classCode: submission.class_code,
    submissionUrl: submission.submission_url,
    requirementUrl: submission.requirement_url,
    maxGrade: submission.assignment_max_grade,
    submittedAt: submission.submitted_at,
    grade: null,
    feedback: null,
    status: submission.status,
  }
}

function reviewTargetFromReviewed(submission: ReviewedSubmission): ReviewTarget {
  return {
    id: submission.submission_id,
    assignmentTitle: submission.assignment_title,
    studentName: submission.student_name,
    studentCode: submission.student_code,
    classCode: submission.class_code,
    maxGrade: submission.assignment_max_grade,
    reviewedAt: submission.reviewed_at,
    reviewedBy: submission.reviewed_by_teacher,
    grade: submission.grade,
    feedback: submission.feedback,
    status: 'reviewed',
  }
}

function filterReviewTargets(
  targets: ReviewTarget[],
  classFilter: string,
  statusFilter: 'all' | AssignmentSubmissionStatus,
) {
  return targets.filter((target) => {
    const classMatches = classFilter === 'all' || !target.classId || target.classId === classFilter
    const statusMatches = statusFilter === 'all' || target.status === statusFilter
    return classMatches && statusMatches
  })
}

function toDatetimeInput(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  const offset = date.getTimezoneOffset()
  const local = new Date(date.getTime() - offset * 60_000)
  return local.toISOString().slice(0, 16)
}

function formatDateTime(value?: string) {
  if (!value) {
    return 'Not set'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function todayInput() {
  return new Date().toISOString().slice(0, 10)
}

async function studentOptionsForAdminClass(classId: string): Promise<StudentOption[]> {
  const response = await listEnrollments()
  return response.data
    .filter((enrollment) => enrollment.class_id === classId && enrollment.status === 'active')
    .map((enrollment) => ({
      id: enrollment.student_id,
      code: enrollment.student_code,
      name: enrollment.student_full_name,
    }))
}

async function studentOptionsForTeacherClass(classId: string): Promise<StudentOption[]> {
  const response = await listTeacherClassStudents(classId)
  return response.data.map((student) => ({
    id: student.student_id,
    code: student.student_code,
    name: student.student_full_name,
  }))
}

function uploadSummary(result: { success_count: number; error_count: number; total_rows: number }) {
  return `${result.success_count} of ${result.total_rows} rows imported. ${result.error_count} row${result.error_count === 1 ? '' : 's'} need attention.`
}

type GradebookWorkspaceData = {
  entries: GradeEntry[]
  corrections: CorrectionHistory[]
  bonusEntries: BonusEntry[]
  classes: AcademicClass[]
}

async function loadGradebookWorkspace(role: Role, classId: string): Promise<GradebookWorkspaceData> {
  if (role === 'student') {
    const [entryData, bonusData] = await Promise.all([
      listStudentGradeEntries(),
      listStudentBonus(),
    ])
    return {
      entries: entryData.data,
      corrections: [],
      bonusEntries: bonusData.data,
      classes: [],
    }
  }

  if (role === 'teacher' && classId !== 'all') {
    const [entryData, bonusData, correctionData, classData] = await Promise.all([
      listTeacherClassGradeEntries(classId),
      listTeacherClassBonus(classId),
      listTeacherCorrectionsHistory(),
      listClasses(),
    ])
    return {
      entries: entryData.data,
      corrections: correctionData.data,
      bonusEntries: bonusData.data,
      classes: classData.data,
    }
  }

  const [entryData, bonusData, correctionData, classData] = await Promise.all([
    listGradeEntries(),
    listBonus(),
    role === 'admin' ? listAdminCorrectionsHistory() : listTeacherCorrectionsHistory(),
    listClasses(),
  ])
  return {
    entries: entryData.data,
    corrections: correctionData.data,
    bonusEntries: bonusData.data,
    classes: classData.data,
  }
}

function uniqueEntryOptions(entries: GradeEntry[], kind: 'student' | 'teacher') {
  const options = new Map<string, string>()
  for (const entry of entries) {
    if (kind === 'student') {
      options.set(entry.student_id, `${entry.student_code} - ${entry.student_name}`)
    } else if (entry.teacher_id && entry.teacher_name) {
      options.set(entry.teacher_id, entry.teacher_name)
    }
  }
  return Array.from(options, ([id, label]) => ({ id, label }))
}

type FinalProjectWorkspaceData = {
  projects: FinalProject[]
  classes: AcademicClass[]
  tracks: Track[]
}

async function loadFinalProjectWorkspace(role: Role, classId: string): Promise<FinalProjectWorkspaceData> {
  const [classData, trackData] = await Promise.all([
    listClasses(),
    role === 'admin' ? listTracks() : Promise.resolve({ data: [] as Track[] }),
  ])

  if (role === 'teacher') {
    const selectedClassId = classId || classData.data[0]?.id || ''
    const projectData = selectedClassId
      ? await listTeacherClassFinalProjects(selectedClassId)
      : { data: [] as FinalProject[] }
    return {
      projects: projectData.data,
      classes: classData.data,
      tracks: [],
    }
  }

  const projectData = await listFinalProjects()
  return {
    projects: projectData.data,
    classes: classData.data,
    tracks: trackData.data,
  }
}

async function loadStudentFinalProject() {
  try {
    const response = await getMyFinalProject()
    return response.data
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null
    }
    throw error
  }
}

function formatProgress(value?: number | null) {
  return typeof value === 'number' ? formatPercent(value) : '0%'
}

function countUsers(users: CurrentUser[], role: Role) {
  return users.filter((user) => user.role === role).length
}

function profileSummary(user: CurrentUser) {
  if (user.admin_profile) {
    return user.admin_profile.full_name
  }

  if (user.teacher_profile) {
    return `${user.teacher_profile.full_name} / ${user.teacher_profile.teacher_type.replaceAll('_', ' ')}`
  }

  if (user.student_profile) {
    return `${user.student_profile.full_name} / ${user.student_profile.student_code}`
  }

  return 'No profile'
}

function userStatus(user: CurrentUser) {
  if (!user.is_active) {
    return 'Inactive'
  }

  if (user.must_change_password) {
    return 'Must change password'
  }

  return 'Active'
}

function titleCase(value: string) {
  return value.slice(0, 1).toUpperCase() + value.slice(1).replaceAll('_', ' ')
}

function formatPercent(value: number) {
  return `${Math.round(value * 10) / 10}%`
}

function AuthLoadingScreen() {
  return (
    <main className="auth-shell">
      <section className="auth-card compact">
        <div className="brand large">
          <div className="brand-mark">ICA</div>
          <div>
            <strong>ICA Academy</strong>
            <span>CRM / LMS</span>
          </div>
        </div>
        <div className="loading-line" />
        <p>Checking your secure session...</p>
      </section>
    </main>
  )
}

function LoginScreen({
  message,
  onAuthenticated,
  onMessage,
}: {
  message: string
  onAuthenticated: () => Promise<void>
  onMessage: (message: string) => void
}) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    onMessage('')

    try {
      await login({ email, password })
      await onAuthenticated()
    } catch (error) {
      onMessage(errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="auth-heading">
          <div className="brand large">
            <div className="brand-mark">ICA</div>
            <div>
              <strong>ICA Academy</strong>
              <span>CRM / LMS</span>
            </div>
          </div>
          <div>
            <span className="eyebrow">Secure workspace</span>
            <h1>Sign in</h1>
            <p>Use your academy account to open the Admin, Teacher, or Student dashboard.</p>
          </div>
        </div>

        {message && <div className="form-message">{message}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>Email</span>
            <input
              autoComplete="email"
              placeholder="name@ica.eg"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label>
            <span>Password</span>
            <input
              autoComplete="current-password"
              placeholder="Enter your password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>

          <button className="primary-button full-width" type="submit" disabled={submitting}>
            {submitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        {import.meta.env.DEV && (
          <div className="seed-note">
            <strong>Development seed note</strong>
            <span>Default backend admin: admin@ica.eg / Admin@123456</span>
          </div>
        )}
      </section>
    </main>
  )
}

function ForceChangePasswordScreen({
  user,
  onComplete,
}: {
  user: CurrentUser
  onComplete: () => void
}) {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')

    if (newPassword !== confirmPassword) {
      setMessage('New password and confirmation do not match.')
      return
    }

    setSubmitting(true)
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      onComplete()
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="auth-heading">
          <div className="brand large">
            <div className="brand-mark">ICA</div>
            <div>
              <strong>ICA Academy</strong>
              <span>CRM / LMS</span>
            </div>
          </div>
          <div>
            <span className="eyebrow">Required security step</span>
            <h1>Change password</h1>
            <p>{displayNameFor(user)} must set a new password before entering the dashboard.</p>
          </div>
        </div>

        {message && <div className="form-message">{message}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>Current password</span>
            <input
              autoComplete="current-password"
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>

          <label>
            <span>New password</span>
            <input
              autoComplete="new-password"
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>

          <label>
            <span>Confirm new password</span>
            <input
              autoComplete="new-password"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>

          <button className="primary-button full-width" type="submit" disabled={submitting}>
            {submitting ? 'Updating password...' : 'Update password'}
          </button>
        </form>
      </section>
    </main>
  )
}

function StatusBadge({ value }: { value: string }) {
  const tone = value.toLowerCase().includes('low') || value.toLowerCase().includes('critical')
    ? 'danger'
    : value.toLowerCase().includes('pending') || value.toLowerCase().includes('warning')
      ? 'warning'
      : 'success'

  return <span className={`status-badge ${tone}`}>{value}</span>
}

function ActionMenu({ actions }: { actions: string[] }) {
  return (
    <details className="dropdown-menu row-menu">
      <summary aria-label="Row actions">
        <MoreHorizontal size={18} />
      </summary>
      <div className="dropdown-panel dropdown-panel-right">
        {actions.map((action) => (
          <button key={action} type="button">
            {action}
          </button>
        ))}
      </div>
    </details>
  )
}

function LmsRowMenu({ actions }: { actions: Array<{ label: string; onClick: () => void }> }) {
  return (
    <details className="dropdown-menu row-menu">
      <summary aria-label="Row actions">
        <MoreHorizontal size={18} />
      </summary>
      <div className="dropdown-panel dropdown-panel-right">
        {actions.map((action) => (
          <button key={action.label} type="button" onClick={action.onClick}>
            {action.label}
          </button>
        ))}
      </div>
    </details>
  )
}

export default App
