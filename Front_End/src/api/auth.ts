import { apiRequest } from './client'
import { clearTokens, getTokens, setTokens } from './tokenStorage'
import type {
  ChangePasswordRequest,
  CurrentUser,
  LoginRequest,
  LogoutRequest,
  ResetPasswordRequest,
  TokenPair,
} from './types'

export async function login(payload: LoginRequest) {
  const envelope = await apiRequest<TokenPair>('/api/auth/login', {
    method: 'POST',
    body: payload,
    auth: false,
  })
  setTokens(envelope.data)
  return envelope
}

export async function refreshToken() {
  const tokens = getTokens()
  if (!tokens?.refresh_token) {
    throw new Error('No refresh token is available.')
  }

  const envelope = await apiRequest<TokenPair>('/api/auth/refresh', {
    method: 'POST',
    body: { refresh_token: tokens.refresh_token },
    auth: false,
  })
  setTokens(envelope.data)
  return envelope
}

export async function logout() {
  const tokens = getTokens()

  try {
    if (tokens?.refresh_token) {
      await apiRequest<Record<string, never>>('/api/auth/logout', {
        method: 'POST',
        body: { refresh_token: tokens.refresh_token } satisfies LogoutRequest,
      })
    }
  } finally {
    clearTokens()
  }
}

export async function changePassword(payload: ChangePasswordRequest) {
  const envelope = await apiRequest<Record<string, never>>('/api/auth/change-password', {
    method: 'POST',
    body: payload,
  })
  clearTokens()
  return envelope
}

export async function resetPassword(payload: ResetPasswordRequest) {
  return apiRequest<Record<string, never>>('/api/auth/reset-password', {
    method: 'POST',
    body: payload,
  })
}

export async function getCurrentUser() {
  return apiRequest<CurrentUser>('/api/auth/me')
}

export { getTokens }
