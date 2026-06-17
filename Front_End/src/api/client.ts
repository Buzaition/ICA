import { clearTokens, getTokens, setTokens } from './tokenStorage'
import type { ApiEnvelope, ApiErrorPayload, RefreshRequest, TokenPair } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: unknown
  auth?: boolean
  retryOnUnauthorized?: boolean
}

export class ApiError extends Error {
  status: number
  errors: unknown[]

  constructor(payload: ApiErrorPayload) {
    super(payload.message)
    this.name = 'ApiError'
    this.status = payload.status
    this.errors = payload.errors
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<ApiEnvelope<T>> {
  const { retryOnUnauthorized = true } = options
  const response = await send(path, options)

  if (response.status !== 401 || !retryOnUnauthorized || path === '/api/auth/refresh') {
    return parseResponse<T>(response)
  }

  const refreshed = await tryRefreshTokens()
  if (!refreshed) {
    throw new ApiError({
      success: false,
      message: 'Your session expired. Please sign in again.',
      errors: [],
      status: 401,
    })
  }

  return parseResponse<T>(await send(path, { ...options, retryOnUnauthorized: false }))
}

async function send(path: string, options: RequestOptions): Promise<Response> {
  const headers = new Headers()
  headers.set('Accept', 'application/json')
  const isFormData = options.body instanceof FormData
  const requestBody: BodyInit | undefined = options.body == null
    ? undefined
    : isFormData
      ? options.body as FormData
      : JSON.stringify(options.body)

  if (options.body !== undefined && !isFormData) {
    headers.set('Content-Type', 'application/json')
  }

  if (options.auth !== false) {
    const tokens = getTokens()
    if (tokens?.access_token) {
      headers.set('Authorization', `Bearer ${tokens.access_token}`)
    }
  }

  const request = {
    method: options.method ?? 'GET',
    headers,
    body: requestBody,
  }

  try {
    return await fetch(apiUrl(path), request)
  } catch (error) {
    if (API_BASE_URL && isLocalFrontend()) {
      return fetch(path, request)
    }
    throw error
  }
}

function apiUrl(path: string) {
  if (/^https?:\/\//i.test(path)) {
    return path
  }

  return `${API_BASE_URL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`
}

async function parseResponse<T>(response: Response): Promise<ApiEnvelope<T>> {
  const payload = await readJson(response)

  if (!response.ok || payload?.success === false) {
    throw new ApiError({
      success: false,
      message: typeof payload?.message === 'string' ? payload.message : 'Request failed',
      errors: Array.isArray(payload?.errors) ? payload.errors : [],
      status: response.status,
    })
  }

  return {
    success: payload?.success !== false,
    message: typeof payload?.message === 'string' ? payload.message : 'Operation completed',
    data: (payload?.data ?? {}) as T,
    errors: Array.isArray(payload?.errors) ? payload.errors : [],
  }
}

async function readJson(response: Response): Promise<Record<string, unknown> | null> {
  const text = await response.text()
  if (!text) {
    return null
  }

  try {
    return JSON.parse(text) as Record<string, unknown>
  } catch {
    return {
      success: false,
      message: text || 'The server returned an invalid JSON response.',
      errors: [],
    }
  }
}

function isLocalFrontend() {
  return ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname)
}

async function tryRefreshTokens() {
  const tokens = getTokens()
  if (!tokens?.refresh_token) {
    clearTokens()
    return false
  }

  try {
    const envelope = await apiRequest<TokenPair>('/api/auth/refresh', {
      method: 'POST',
      body: { refresh_token: tokens.refresh_token } satisfies RefreshRequest,
      auth: false,
      retryOnUnauthorized: false,
    })
    setTokens(envelope.data)
    return true
  } catch {
    clearTokens()
    return false
  }
}
