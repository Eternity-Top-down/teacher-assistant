const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const FIELD_LABELS = {
  email: '邮箱',
  password: '密码',
  code: '验证码',
  name: '学生姓名',
  lesson_title: '反馈标题',
  lesson_time: '上课时间',
  raw_lesson_note: '本节课原始记录',
  lesson_summary: '课堂学习内容',
  performance_summary: '课堂表现与知识掌握情况',
  advice_summary: '课后建议',
  homework_plan: '作业安排',
  ai_draft: 'AI 初稿',
  final_feedback: '最终反馈',
  school: '学校',
  subject: '学科',
  names_text: '学生名单',
  period_type: '反馈类型',
  period_value: '反馈时间',
  homework_summary: '作业完成情况简述',
  provider: '模型供应商',
  base_url: 'Base URL',
  model: '模型名',
  api_key: 'API Key',
  model_type: '模型类型',
  config_id: '模型配置',
  title: '样例标题',
  content: '反馈样例',
  enabled: '启用状态',
  feedback_type: '样例类型',
  term_label: '学期 / 阶段',
  owner_name: '负责人 / 老师',
  export_subject: '导出科目',
  document_title: 'Word 标题',
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
    throw new Error('无法连接后端服务，或本次请求已超时/被中断，请确认后端正在运行后重试')
  }

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(formatErrorDetail(data.detail))
  }
  return data
}

export async function downloadRequest(path, options = {}) {
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
    throw new Error('无法连接后端服务，或本次请求已超时/被中断，请确认后端正在运行后重试')
  }

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(formatErrorDetail(data.detail))
  }
  return {
    blob: await response.blob(),
    filename: parseDownloadFilename(response.headers.get('Content-Disposition') || ''),
  }
}

function parseDownloadFilename(disposition) {
  const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  if (encoded) return decodeURIComponent(encoded)
  const plain = disposition.match(/filename="?([^";]+)"?/i)?.[1]
  return plain || ''
}
