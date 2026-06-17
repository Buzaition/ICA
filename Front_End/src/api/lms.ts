import { apiRequest } from './client'
import type {
  Assignment,
  AssignmentCreate,
  AssignmentUpdate,
  Material,
  MaterialCreate,
  MaterialUpdate,
  PendingSubmission,
  ReviewedSubmission,
  Submission,
  SubmissionCreate,
  SubmissionReject,
  SubmissionReview,
} from './types'

export function listMaterials() {
  return apiRequest<Material[]>('/api/materials')
}

export function createMaterial(payload: MaterialCreate) {
  return apiRequest<Material>('/api/materials', { method: 'POST', body: payload })
}

export function updateMaterial(id: string, payload: MaterialUpdate) {
  return apiRequest<Material>(`/api/materials/${id}`, { method: 'PUT', body: payload })
}

export function deleteMaterial(id: string) {
  return apiRequest<Record<string, never>>(`/api/materials/${id}`, { method: 'DELETE' })
}

export function listStudentMaterials() {
  return apiRequest<Material[]>('/api/students/me/materials')
}

export function listTeacherClassMaterials(classId: string) {
  return apiRequest<Material[]>(`/api/teachers/me/classes/${classId}/materials`)
}

export function listAssignments() {
  return apiRequest<Assignment[]>('/api/assignments')
}

export function createAssignment(payload: AssignmentCreate) {
  return apiRequest<Assignment>('/api/assignments', { method: 'POST', body: payload })
}

export function updateAssignment(id: string, payload: AssignmentUpdate) {
  return apiRequest<Assignment>(`/api/assignments/${id}`, { method: 'PUT', body: payload })
}

export function deleteAssignment(id: string) {
  return apiRequest<Record<string, never>>(`/api/assignments/${id}`, { method: 'DELETE' })
}

export function listStudentAssignments() {
  return apiRequest<Assignment[]>('/api/students/me/assignments')
}

export function submitAssignment(assignmentId: string, payload: SubmissionCreate) {
  return apiRequest<Submission>(`/api/assignments/${assignmentId}/submit`, { method: 'POST', body: payload })
}

export function listStudentSubmissions() {
  return apiRequest<Submission[]>('/api/students/me/submissions')
}

export function listTeacherClassAssignments(classId: string) {
  return apiRequest<Assignment[]>(`/api/teachers/me/classes/${classId}/assignments`)
}

export function listPendingAssignments() {
  return apiRequest<PendingSubmission[]>('/api/teachers/me/assignments/pending')
}

export function listReviewedAssignments() {
  return apiRequest<ReviewedSubmission[]>('/api/teachers/me/assignments/reviewed')
}

export function listLateAssignments() {
  return apiRequest<PendingSubmission[]>('/api/teachers/me/assignments/late')
}

export function listAssignmentSubmissions() {
  return apiRequest<Submission[]>('/api/assignment-submissions')
}

export function reviewSubmission(submissionId: string, payload: SubmissionReview) {
  return apiRequest<Submission>(`/api/assignment-submissions/${submissionId}/review`, {
    method: 'POST',
    body: payload,
  })
}

export function rejectSubmission(submissionId: string, payload: SubmissionReject) {
  return apiRequest<Submission>(`/api/assignment-submissions/${submissionId}/reject`, {
    method: 'POST',
    body: payload,
  })
}
