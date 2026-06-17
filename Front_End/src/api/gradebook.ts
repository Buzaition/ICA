import { apiRequest } from './client'
import type {
  BonusCreate,
  BonusEntry,
  CorrectionCreate,
  CorrectionHistory,
  GradeEntry,
} from './types'

export function listGradeEntries() {
  return apiRequest<GradeEntry[]>('/api/grade-entries')
}

export function getGradeEntry(id: string) {
  return apiRequest<GradeEntry>(`/api/grade-entries/${id}`)
}

export function createCorrection(gradeEntryId: string, payload: CorrectionCreate) {
  return apiRequest<GradeEntry>(`/api/grade-entries/${gradeEntryId}/corrections`, {
    method: 'POST',
    body: payload,
  })
}

export function listCorrectionsForEntry(gradeEntryId: string) {
  return apiRequest<GradeEntry[]>(`/api/grade-entries/${gradeEntryId}/corrections`)
}

export function listStudentGradeEntries() {
  return apiRequest<GradeEntry[]>('/api/students/me/grade-entries')
}

export function listTeacherClassGradeEntries(classId: string) {
  return apiRequest<GradeEntry[]>(`/api/teachers/me/classes/${classId}/grade-entries`)
}

export function listTeacherCorrectionsHistory() {
  return apiRequest<CorrectionHistory[]>('/api/teachers/me/corrections-history')
}

export function listAdminCorrectionsHistory() {
  return apiRequest<CorrectionHistory[]>('/api/admin/corrections-history')
}

export function createBonus(payload: BonusCreate) {
  return apiRequest<BonusEntry>('/api/bonus', { method: 'POST', body: payload })
}

export function listBonus() {
  return apiRequest<BonusEntry[]>('/api/bonus')
}

export function listStudentBonus() {
  return apiRequest<BonusEntry[]>('/api/students/me/bonus')
}

export function listTeacherClassBonus(classId: string) {
  return apiRequest<BonusEntry[]>(`/api/teachers/me/classes/${classId}/bonus`)
}
