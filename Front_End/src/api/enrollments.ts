import { apiRequest } from './client'
import type { Enrollment, EnrollmentCreate, TeacherClassStudent } from './types'

export function listEnrollments() {
  return apiRequest<Enrollment[]>('/api/enrollments')
}

export function createEnrollment(payload: EnrollmentCreate) {
  return apiRequest<Enrollment>('/api/enrollments', {
    method: 'POST',
    body: payload,
  })
}

export function getEnrollment(id: string) {
  return apiRequest<Enrollment>(`/api/enrollments/${id}`)
}

export function removeEnrollment(id: string) {
  return apiRequest<Record<string, never>>(`/api/enrollments/${id}`, {
    method: 'DELETE',
  })
}

export function listTeacherClassStudents(classId: string) {
  return apiRequest<TeacherClassStudent[]>(`/api/teachers/me/classes/${classId}/students`)
}

export function getStudentActiveClass() {
  return apiRequest<Enrollment>('/api/students/me/class')
}
