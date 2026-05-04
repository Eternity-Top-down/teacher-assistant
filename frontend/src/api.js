const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

export function getToken() {
  return localStorage.getItem('teacher_token') || ''
}

export function setToken(token) {
  localStorage.setItem('teacher_token', token)
}

export function clearToken() {
  localStorage.removeItem('teacher_token')
}

export async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || '请求失败，请稍后重试')
  }
  return data
}
