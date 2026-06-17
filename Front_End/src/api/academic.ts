import { apiRequest } from './client'
import type {
  AcademicClass,
  Branch,
  BranchCreate,
  BranchUpdate,
  ClassCreate,
  ClassUpdate,
  Cycle,
  CycleCreate,
  CycleUpdate,
  Level,
  LevelCreate,
  LevelUpdate,
  Track,
  TrackCreate,
  TrackUpdate,
} from './types'

export function listBranches() {
  return apiRequest<Branch[]>('/api/branches')
}

export function createBranch(payload: BranchCreate) {
  return apiRequest<Branch>('/api/branches', { method: 'POST', body: payload })
}

export function updateBranch(id: string, payload: BranchUpdate) {
  return apiRequest<Branch>(`/api/branches/${id}`, { method: 'PUT', body: payload })
}

export function deleteBranch(id: string) {
  return apiRequest<Record<string, never>>(`/api/branches/${id}`, { method: 'DELETE' })
}

export function listCycles() {
  return apiRequest<Cycle[]>('/api/cycles')
}

export function createCycle(payload: CycleCreate) {
  return apiRequest<Cycle>('/api/cycles', { method: 'POST', body: payload })
}

export function updateCycle(id: string, payload: CycleUpdate) {
  return apiRequest<Cycle>(`/api/cycles/${id}`, { method: 'PUT', body: payload })
}

export function deleteCycle(id: string) {
  return apiRequest<Record<string, never>>(`/api/cycles/${id}`, { method: 'DELETE' })
}

export function listTracks() {
  return apiRequest<Track[]>('/api/tracks')
}

export function createTrack(payload: TrackCreate) {
  return apiRequest<Track>('/api/tracks', { method: 'POST', body: payload })
}

export function updateTrack(id: string, payload: TrackUpdate) {
  return apiRequest<Track>(`/api/tracks/${id}`, { method: 'PUT', body: payload })
}

export function deleteTrack(id: string) {
  return apiRequest<Record<string, never>>(`/api/tracks/${id}`, { method: 'DELETE' })
}

export function listLevels() {
  return apiRequest<Level[]>('/api/levels')
}

export function createLevel(payload: LevelCreate) {
  return apiRequest<Level>('/api/levels', { method: 'POST', body: payload })
}

export function updateLevel(id: string, payload: LevelUpdate) {
  return apiRequest<Level>(`/api/levels/${id}`, { method: 'PUT', body: payload })
}

export function deleteLevel(id: string) {
  return apiRequest<Record<string, never>>(`/api/levels/${id}`, { method: 'DELETE' })
}

export function listClasses() {
  return apiRequest<AcademicClass[]>('/api/classes')
}

export function createClass(payload: ClassCreate) {
  return apiRequest<AcademicClass>('/api/classes', { method: 'POST', body: payload })
}

export function updateClass(id: string, payload: ClassUpdate) {
  return apiRequest<AcademicClass>(`/api/classes/${id}`, { method: 'PUT', body: payload })
}

export function deleteClass(id: string) {
  return apiRequest<Record<string, never>>(`/api/classes/${id}`, { method: 'DELETE' })
}
