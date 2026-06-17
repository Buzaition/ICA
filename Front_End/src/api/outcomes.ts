import { apiRequest } from './client'
import type {
  ClassProgress,
  FinalProject,
  FinalProjectReview,
  FinalProjectSubmit,
  ProgressSnapshot,
  RankingItem,
  StudentProgress,
  TeacherProgress,
} from './types'

export function getMyProgress() {
  return apiRequest<StudentProgress>('/api/students/me/progress')
}

export function getTeacherClassProgress(classId: string) {
  return apiRequest<ClassProgress>(`/api/teachers/me/classes/${classId}/progress`)
}

export function createTeacherClassProgressSnapshots(classId: string) {
  return apiRequest<ProgressSnapshot[]>(`/api/teachers/me/classes/${classId}/progress-snapshots`, { method: 'POST' })
}

export function getStudentProgress(studentId: string) {
  return apiRequest<StudentProgress>(`/api/progress/students/${studentId}`)
}

export function getClassProgress(classId: string) {
  return apiRequest<ClassProgress>(`/api/progress/classes/${classId}`)
}

export function listClassProgressSnapshots(classId: string) {
  return apiRequest<ProgressSnapshot[]>(`/api/progress/classes/${classId}/snapshots`)
}

export function createClassProgressSnapshots(classId: string) {
  return apiRequest<ProgressSnapshot[]>(`/api/progress/classes/${classId}/snapshots`, { method: 'POST' })
}

export function getTeacherProgress(teacherId: string) {
  return apiRequest<TeacherProgress>(`/api/progress/teachers/${teacherId}`)
}

export function getMyTop3Ranking() {
  return apiRequest<RankingItem[]>('/api/students/me/ranking/top3')
}

export function getTeacherClassRanking(classId: string) {
  return apiRequest<RankingItem[]>(`/api/teachers/me/classes/${classId}/ranking`)
}

export function getClassRanking(classId: string) {
  return apiRequest<RankingItem[]>(`/api/ranking/classes/${classId}`)
}

export function getTrackRanking(trackId: string) {
  return apiRequest<RankingItem[]>(`/api/ranking/tracks/${trackId}`)
}

export function submitMyFinalProject(payload: FinalProjectSubmit) {
  return apiRequest<FinalProject>('/api/students/me/final-project', { method: 'POST', body: payload })
}

export function getMyFinalProject() {
  return apiRequest<FinalProject>('/api/students/me/final-project')
}

export function updateMyFinalProject(payload: FinalProjectSubmit) {
  return apiRequest<FinalProject>('/api/students/me/final-project', { method: 'PUT', body: payload })
}

export function listTeacherClassFinalProjects(classId: string) {
  return apiRequest<FinalProject[]>(`/api/teachers/me/classes/${classId}/final-projects`)
}

export function listFinalProjects() {
  return apiRequest<FinalProject[]>('/api/final-projects')
}

export function reviewFinalProject(id: string, payload: FinalProjectReview) {
  return apiRequest<FinalProject>(`/api/final-projects/${id}/review`, { method: 'POST', body: payload })
}
