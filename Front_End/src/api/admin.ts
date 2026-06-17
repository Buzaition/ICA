import { apiRequest } from './client'
import type {
  AdminDashboard,
  AdminNotification,
  CurrentUser,
  ResetPasswordRequest,
  UnreadCount,
  UserCreate,
  UserUpdate,
} from './types'

export function getAdminDashboard() {
  return apiRequest<AdminDashboard>('/api/admin/dashboard')
}

export function listUsers() {
  return apiRequest<CurrentUser[]>('/api/users')
}

export function createUser(payload: UserCreate) {
  return apiRequest<CurrentUser>('/api/users', {
    method: 'POST',
    body: payload,
  })
}

export function updateUser(userId: string, payload: UserUpdate) {
  return apiRequest<CurrentUser>(`/api/users/${userId}`, {
    method: 'PUT',
    body: payload,
  })
}

export function deleteUser(userId: string) {
  return apiRequest<Record<string, never>>(`/api/users/${userId}`, {
    method: 'DELETE',
  })
}

export function resetUserPassword(payload: ResetPasswordRequest) {
  return apiRequest<Record<string, never>>('/api/auth/reset-password', {
    method: 'POST',
    body: payload,
  })
}

export function listAdminNotifications() {
  return apiRequest<AdminNotification[]>('/api/admin/notifications')
}

export function getAdminUnreadCount() {
  return apiRequest<UnreadCount>('/api/admin/notifications/unread-count')
}
