import { apiRequest } from './client'
import type {
  AttendanceRecord,
  AttendanceRecordUpdate,
  AttendanceSession,
  AttendanceSessionType,
  AttendanceSubmissionResult,
  ManualAttendanceCreate,
  ManualQuizCreate,
  Quiz,
  QuizResult,
  QuizResultUpdate,
  QuizSubmissionResult,
} from './types'

export function createManualAttendance(payload: ManualAttendanceCreate) {
  return apiRequest<AttendanceSubmissionResult>('/api/attendance/manual', { method: 'POST', body: payload })
}

export function uploadAttendanceCsv(payload: {
  class_id: string
  session_type: AttendanceSessionType
  session_date: string
  teacher_id?: string | null
  file: File
}) {
  const form = new FormData()
  form.set('class_id', payload.class_id)
  form.set('session_type', payload.session_type)
  form.set('session_date', payload.session_date)
  if (payload.teacher_id) form.set('teacher_id', payload.teacher_id)
  form.set('file', payload.file)
  return apiRequest<AttendanceSubmissionResult>('/api/attendance/upload-csv', { method: 'POST', body: form })
}

export function listAttendanceSessions() {
  return apiRequest<AttendanceSession[]>('/api/attendance/sessions')
}

export function listAttendanceSessionRecords(sessionId: string) {
  return apiRequest<AttendanceRecord[]>(`/api/attendance/sessions/${sessionId}/records`)
}

export function updateAttendanceRecord(id: string, payload: AttendanceRecordUpdate) {
  return apiRequest<AttendanceRecord>(`/api/attendance/records/${id}`, { method: 'PUT', body: payload })
}

export function listAllAttendanceRecords() {
  return apiRequest<AttendanceRecord[]>('/api/attendance')
}

export function listStudentAttendance() {
  return apiRequest<AttendanceRecord[]>('/api/students/me/attendance')
}

export function listTeacherClassAttendance(classId: string) {
  return apiRequest<AttendanceSession[]>(`/api/teachers/me/classes/${classId}/attendance`)
}

export function createManualQuiz(payload: ManualQuizCreate) {
  return apiRequest<QuizSubmissionResult>('/api/quizzes/manual', { method: 'POST', body: payload })
}

export function uploadQuizCsv(payload: {
  class_id: string
  title: string
  quiz_date: string
  max_grade: number
  description?: string | null
  teacher_id?: string | null
  file: File
}) {
  const form = new FormData()
  form.set('class_id', payload.class_id)
  form.set('title', payload.title)
  form.set('quiz_date', payload.quiz_date)
  form.set('max_grade', String(payload.max_grade))
  if (payload.description) form.set('description', payload.description)
  if (payload.teacher_id) form.set('teacher_id', payload.teacher_id)
  form.set('file', payload.file)
  return apiRequest<QuizSubmissionResult>('/api/quizzes/upload-csv', { method: 'POST', body: form })
}

export function listQuizzes() {
  return apiRequest<Quiz[]>('/api/quizzes')
}

export function listQuizResults(quizId: string) {
  return apiRequest<QuizResult[]>(`/api/quizzes/${quizId}/results`)
}

export function updateQuizResult(id: string, payload: QuizResultUpdate) {
  return apiRequest<QuizResult>(`/api/quiz-results/${id}`, { method: 'PUT', body: payload })
}

export function listAllQuizResults() {
  return apiRequest<QuizResult[]>('/api/quiz-results')
}

export function listTeacherClassQuizzes(classId: string) {
  return apiRequest<Quiz[]>(`/api/teachers/me/classes/${classId}/quizzes`)
}

export function listStudentQuizzes() {
  return apiRequest<QuizResult[]>('/api/students/me/quizzes')
}
