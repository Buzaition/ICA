import type { TokenPair } from './types'

const accessTokenKey = 'ica.access_token'
const refreshTokenKey = 'ica.refresh_token'
const tokenTypeKey = 'ica.token_type'

let memoryTokens: TokenPair | null = null

function canUseLocalStorage() {
  try {
    return typeof window !== 'undefined' && Boolean(window.localStorage)
  } catch {
    return false
  }
}

export function getTokens(): TokenPair | null {
  if (!canUseLocalStorage()) {
    return memoryTokens
  }

  const accessToken = window.localStorage.getItem(accessTokenKey)
  const refreshToken = window.localStorage.getItem(refreshTokenKey)
  const tokenType = window.localStorage.getItem(tokenTypeKey) ?? 'bearer'

  if (!accessToken || !refreshToken) {
    return memoryTokens
  }

  return {
    access_token: accessToken,
    refresh_token: refreshToken,
    token_type: tokenType,
  }
}

export function setTokens(tokens: TokenPair) {
  memoryTokens = tokens

  if (!canUseLocalStorage()) {
    return
  }

  window.localStorage.setItem(accessTokenKey, tokens.access_token)
  window.localStorage.setItem(refreshTokenKey, tokens.refresh_token)
  window.localStorage.setItem(tokenTypeKey, tokens.token_type)
}

export function clearTokens() {
  memoryTokens = null

  if (!canUseLocalStorage()) {
    return
  }

  window.localStorage.removeItem(accessTokenKey)
  window.localStorage.removeItem(refreshTokenKey)
  window.localStorage.removeItem(tokenTypeKey)
}
