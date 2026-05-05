const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const FIELD_LABELS = {
  email: '邮箱',
  password: '密码',
  code: '验证码',
  name: '学生姓名',
  lesson_title: '反馈标题',
  lesson_time: '上课时间',
  lesson_summary: '课堂学习内容',
  performance_summary: '课堂表现与知识掌握情况',
  advice_summary: '课后建议',
  homework_plan: '作业安排',
  ai_draft: 'AI 初稿',
  final_feedback: '最终反馈',
  school: '学校',
  names_text: '学生名单',
  feedback_month: '反馈月份',
  homework_summary: '作业完成情况简述',
  provider: '模型供应商',
  base_url: 'Base URL',
  model: '模型名',
  api_key: 'API Key',
}

export function getToken() {
  return localStorage.getItem('teacher_token') || ''
}

export function setToken(token) {
  localStorage.setItem('teacher_token', token)
}

export function clearToken() {
  localStorage.removeItem('teacher_token')
}

function translateValidationError(error) {
  const field = error.loc?.[error.loc.length - 1]
  const label = FIELD_LABELS[field] || field || '表单内容'
  const type = error.type || ''

  if (type.includes('string_too_short')) return `${label}填写太短，请补充完整`
  if (type.includes('string_too_long')) return `${label}内容太长，请适当精简`
  if (type.includes('missing')) return `请填写${label}`
  if (type.includes('value_error')) return `${label}格式不正确`
  return `${label}填写不正确`
}

function formatErrorDetail(detail) {
  if (!detail) return '请求失败，请稍后重试'
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(translateValidationError).join('；')
  if (typeof detail === 'object') return detail.msg || JSON.stringify(detail)
  return String(detail)
}

export async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    })
  } catch (error) {
    throw new Error('无法连接后端服务，请确认后端正在运行')
  }

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(formatErrorDetail(data.detail))
  }
  return data
}
