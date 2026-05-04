<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { clearToken, request, setToken } from './api'

const teacher = ref(null)
const route = ref(window.location.hash || '#/one-on-one')
const loading = ref(false)
const message = ref('')
const authMode = ref('login')

const oneStudents = ref([])
const currentStudent = ref(null)
const feedbacks = ref([])
const detailFeedback = ref(null)
const showCreateModal = ref(false)
const showStudentModal = ref(false)
const showOneStudentEditModal = ref(false)
const isEditingDetail = ref(false)

const eveningClasses = ref([])
const currentClass = ref(null)
const eveningStudents = ref([])
const currentEveningStudent = ref(null)
const eveningFeedbacks = ref([])
const eveningDetail = ref(null)
const showClassModal = ref(false)
const showBulkModal = ref(false)
const showEveningStudentModal = ref(false)
const showMonthlyModal = ref(false)
const isEditingEveningDetail = ref(false)
const editingClass = ref(null)
const aiSettings = ref(null)
const showAccountMenu = ref(false)

const authForm = reactive({ email: '', password: '', confirmPassword: '', code: '' })
const oneStudentForm = reactive({ name: '', grade: '', subject: '', note: '' })
const feedbackForm = reactive(newFeedback())
const editForm = reactive(newFeedback())
const classForm = reactive({ name: '', note: '' })
const bulkForm = reactive({ names_text: '' })
const eveningStudentForm = reactive({ name: '', grade: '', school: '', note: '' })
const monthlyForm = reactive(newMonthlyFeedback())
const monthlyEditForm = reactive(newMonthlyFeedback())
const aiSettingsForm = reactive({
  provider: 'deepseek',
  base_url: 'https://api.deepseek.com/v1',
  model: 'deepseek-chat',
  api_key: '',
  clear_api_key: false,
})

const AI_PRESETS = {
  deepseek: { label: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  openai: { label: 'OpenAI', base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  qwen: { label: '通义千问', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
  zhipu: { label: '智谱 AI', base_url: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash' },
  custom: { label: '自定义兼容接口', base_url: '', model: '' },
}

const isAuthed = computed(() => Boolean(teacher.value))
const teacherInitial = computed(() => (teacher.value?.email || 'T').slice(0, 1).toUpperCase())
const currentView = computed(() => {
  if (!isAuthed.value) return 'auth'
  if (route.value === '#/settings') return 'settings'
  if (route.value.startsWith('#/evening/classes/')) return 'evening-class'
  if (route.value.startsWith('#/evening/students/')) return 'evening-student'
  if (route.value === '#/evening') return 'evening'
  if (route.value.includes('/history')) return 'one-history'
  if (route.value.startsWith('#/one-on-one/students/')) return 'one-student'
  return 'one-list'
})

function newFeedback() {
  return {
    lesson_time: new Date().toISOString().slice(0, 16),
    lesson_summary: '',
    performance_summary: '',
    ai_draft: '',
    final_feedback: '',
  }
}

function currentMonth() {
  return new Date().toISOString().slice(0, 7)
}

function newMonthlyFeedback() {
  return {
    feedback_month: currentMonth(),
    homework_summary: '',
    ai_draft: '',
    final_feedback: '',
  }
}

function showMessage(text) {
  message.value = text
  window.setTimeout(() => {
    if (message.value === text) message.value = ''
  }, 3200)
}

function go(path) {
  showAccountMenu.value = false
  window.location.hash = path
}

function closeAccountMenu() {
  showAccountMenu.value = false
}

function toggleAccountMenu() {
  showAccountMenu.value = !showAccountMenu.value
}

function shortText(text, length = 72) {
  if (!text) return '暂无内容'
  return text.length > length ? `${text.slice(0, length)}...` : text
}

function autoResize(event) {
  const textarea = event?.target
  if (!textarea) return
  textarea.style.height = 'auto'
  textarea.style.height = `${textarea.scrollHeight}px`
}

async function resizeAllTextareas() {
  await nextTick()
  document.querySelectorAll('textarea.auto-textarea').forEach((textarea) => {
    textarea.style.height = 'auto'
    textarea.style.height = `${textarea.scrollHeight}px`
  })
}

function assignFeedback(target, source) {
  target.lesson_time = source.lesson_time || newFeedback().lesson_time
  target.lesson_summary = source.lesson_summary || ''
  target.performance_summary = source.performance_summary || ''
  target.ai_draft = source.ai_draft || ''
  target.final_feedback = source.final_feedback || ''
}

function resetFeedbackForm() {
  assignFeedback(feedbackForm, newFeedback())
}

function assignMonthly(target, source) {
  target.feedback_month = source.feedback_month || currentMonth()
  target.homework_summary = source.homework_summary || ''
  target.ai_draft = source.ai_draft || ''
  target.final_feedback = source.final_feedback || ''
}

function resetMonthlyForm() {
  assignMonthly(monthlyForm, newMonthlyFeedback())
}

function routeId(index = 2) {
  return route.value.split('/')[index]
}

async function sendCode() {
  if (!authForm.email) return showMessage('请先填写邮箱')
  loading.value = true
  try {
    const data = await request('/auth/send-code', {
      method: 'POST',
      body: JSON.stringify({ email: authForm.email }),
    })
    showMessage(data.message)
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function register() {
  if (authForm.password !== authForm.confirmPassword) return showMessage('两次密码不一致')
  loading.value = true
  try {
    const data = await request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email: authForm.email, password: authForm.password, code: authForm.code }),
    })
    setToken(data.token)
    teacher.value = data.teacher
    go('#/one-on-one')
    await handleRoute()
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function login() {
  loading.value = true
  try {
    const data = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: authForm.email, password: authForm.password }),
    })
    setToken(data.token)
    teacher.value = data.teacher
    go('#/one-on-one')
    await handleRoute()
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

function logout() {
  showAccountMenu.value = false
  clearToken()
  teacher.value = null
  go('#/one-on-one')
}

async function loadMe() {
  try {
    const data = await request('/auth/me')
    teacher.value = data.teacher
  } catch {
    clearToken()
  }
}

function applyAIPreset() {
  const preset = AI_PRESETS[aiSettingsForm.provider]
  if (!preset || aiSettingsForm.provider === 'custom') return
  aiSettingsForm.base_url = preset.base_url
  aiSettingsForm.model = preset.model
}

function assignAISettings(settings) {
  aiSettings.value = settings
  aiSettingsForm.provider = settings?.provider || 'deepseek'
  aiSettingsForm.base_url = settings?.base_url || AI_PRESETS.deepseek.base_url
  aiSettingsForm.model = settings?.model || AI_PRESETS.deepseek.model
  aiSettingsForm.api_key = ''
  aiSettingsForm.clear_api_key = false
}

async function loadAISettings() {
  const data = await request('/settings/ai')
  assignAISettings(data.settings)
}

async function saveAISettings() {
  if (!aiSettingsForm.base_url.trim()) return showMessage('请填写 Base URL')
  if (!aiSettingsForm.model.trim()) return showMessage('请填写模型名')
  loading.value = true
  try {
    const data = await request('/settings/ai', {
      method: 'PUT',
      body: JSON.stringify(aiSettingsForm),
    })
    assignAISettings(data.settings)
    showMessage('AI 设置已保存')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function testAISettings() {
  if (!aiSettingsForm.base_url.trim()) return showMessage('请填写 Base URL')
  if (!aiSettingsForm.model.trim()) return showMessage('请填写模型名')
  loading.value = true
  try {
    const data = await request('/settings/ai/test', {
      method: 'POST',
      body: JSON.stringify({
        provider: aiSettingsForm.provider,
        base_url: aiSettingsForm.base_url,
        model: aiSettingsForm.model,
        api_key: aiSettingsForm.api_key,
      }),
    })
    showMessage(data.message || '连接成功，可以生成反馈')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function clearAIKey() {
  if (!window.confirm('确定清除已保存的 API Key 吗？清除后需要重新配置才能生成 AI 反馈。')) return
  aiSettingsForm.api_key = ''
  aiSettingsForm.clear_api_key = true
  await saveAISettings()
}

async function loadOneStudents() {
  const data = await request('/students')
  oneStudents.value = data.students
}

async function createOneStudent() {
  if (!oneStudentForm.name.trim()) return showMessage('请填写学生姓名')
  loading.value = true
  try {
    await request('/students', { method: 'POST', body: JSON.stringify(oneStudentForm) })
    Object.assign(oneStudentForm, { name: '', grade: '', subject: '', note: '' })
    await loadOneStudents()
    showMessage('学生已添加')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function loadOneStudentContext(loadFeedbacks = true) {
  const id = route.value.split('/')[3]
  if (!id) return
  const studentData = await request(`/students/${id}`)
  currentStudent.value = studentData.student
  if (loadFeedbacks) {
    const feedbackData = await request(`/students/${id}/feedbacks`)
    feedbacks.value = feedbackData.feedbacks
  }
}

function openOneStudentEdit() {
  Object.assign(oneStudentForm, currentStudent.value)
  showOneStudentEditModal.value = true
}

async function saveOneStudentEdit() {
  loading.value = true
  try {
    const data = await request(`/students/${currentStudent.value.id}`, {
      method: 'PUT',
      body: JSON.stringify(oneStudentForm),
    })
    currentStudent.value = data.student
    showOneStudentEditModal.value = false
    await loadOneStudents()
    showMessage('学生信息已更新')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function deleteOneStudent() {
  if (!window.confirm('确定删除该学生吗？该学生所有一对一反馈也会删除，且无法恢复。')) return
  loading.value = true
  try {
    await request(`/students/${currentStudent.value.id}`, { method: 'DELETE' })
    showOneStudentEditModal.value = false
    go('#/one-on-one')
    showMessage('学生已删除')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

function openCreateFeedback() {
  resetFeedbackForm()
  showCreateModal.value = true
  resizeAllTextareas()
}

function closeCreateFeedback() {
  showCreateModal.value = false
  resetFeedbackForm()
}

async function generateDraft() {
  if (!feedbackForm.lesson_summary.trim()) return showMessage('请填写课程内容简述')
  loading.value = true
  try {
    const data = await request(`/students/${currentStudent.value.id}/feedbacks/generate`, {
      method: 'POST',
      body: JSON.stringify({
        lesson_time: feedbackForm.lesson_time,
        lesson_summary: feedbackForm.lesson_summary,
        performance_summary: feedbackForm.performance_summary,
      }),
    })
    feedbackForm.ai_draft = data.draft
    feedbackForm.final_feedback = data.draft
    await resizeAllTextareas()
    showMessage('AI 初稿已生成')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function saveFeedback() {
  if (!feedbackForm.final_feedback.trim()) return showMessage('请先生成或填写反馈内容')
  loading.value = true
  try {
    await request(`/students/${currentStudent.value.id}/feedbacks`, {
      method: 'POST',
      body: JSON.stringify(feedbackForm),
    })
    closeCreateFeedback()
    await loadOneStudentContext(true)
    showMessage('反馈已保存')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function openFeedbackDetail(feedback) {
  loading.value = true
  try {
    const data = await request(`/feedbacks/${feedback.id}`)
    detailFeedback.value = data.feedback
    assignFeedback(editForm, data.feedback)
    isEditingDetail.value = false
    await resizeAllTextareas()
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

function closeFeedbackDetail() {
  detailFeedback.value = null
  isEditingDetail.value = false
}

async function saveFeedbackEdit() {
  loading.value = true
  try {
    const data = await request(`/feedbacks/${detailFeedback.value.id}`, {
      method: 'PUT',
      body: JSON.stringify(editForm),
    })
    detailFeedback.value = data.feedback
    isEditingDetail.value = false
    await loadOneStudentContext(true)
    showMessage('反馈已更新')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function deleteFeedback() {
  if (!window.confirm('确定删除这条反馈吗？删除后无法恢复。')) return
  loading.value = true
  try {
    await request(`/feedbacks/${detailFeedback.value.id}`, { method: 'DELETE' })
    closeFeedbackDetail()
    await loadOneStudentContext(true)
    showMessage('反馈已删除')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function loadEveningClasses() {
  const data = await request('/evening/classes')
  eveningClasses.value = data.classes
}

function openClassModal(cls = null) {
  editingClass.value = cls
  classForm.name = cls?.name || ''
  classForm.note = cls?.note || ''
  showClassModal.value = true
}

async function saveClass() {
  if (!classForm.name.trim()) return showMessage('请填写班级名称')
  loading.value = true
  try {
    if (editingClass.value) {
      await request(`/evening/classes/${editingClass.value.id}`, { method: 'PUT', body: JSON.stringify(classForm) })
    } else {
      await request('/evening/classes', { method: 'POST', body: JSON.stringify(classForm) })
    }
    showClassModal.value = false
    await loadEveningClasses()
    if (currentClass.value) await loadEveningClassContext()
    showMessage('班级已保存')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function createClassFromList() {
  editingClass.value = null
  await saveClass()
}

async function deleteClass() {
  if (!window.confirm('确定删除该晚辅班级吗？班级学生和月度反馈也会删除，且无法恢复。')) return
  loading.value = true
  try {
    await request(`/evening/classes/${currentClass.value.id}`, { method: 'DELETE' })
    showClassModal.value = false
    go('#/evening')
    showMessage('班级已删除')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function loadEveningClassContext() {
  const id = route.value.split('/')[3]
  const [classData, studentData] = await Promise.all([
    request(`/evening/classes/${id}`),
    request(`/evening/classes/${id}/students`),
  ])
  currentClass.value = classData.class
  eveningStudents.value = studentData.students
}

async function bulkCreateEveningStudents() {
  if (!bulkForm.names_text.trim()) return showMessage('请至少输入一名学生')
  loading.value = true
  try {
    const data = await request(`/evening/classes/${currentClass.value.id}/students/bulk`, {
      method: 'POST',
      body: JSON.stringify(bulkForm),
    })
    bulkForm.names_text = ''
    showBulkModal.value = false
    await loadEveningClassContext()
    showMessage(`已录入 ${data.created_count} 名学生`)
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function loadEveningStudentContext() {
  const id = route.value.split('/')[3]
  const [studentData, feedbackData] = await Promise.all([
    request(`/evening/students/${id}`),
    request(`/evening/students/${id}/monthly-feedbacks`),
  ])
  currentEveningStudent.value = studentData.student
  eveningFeedbacks.value = feedbackData.feedbacks
}

function openEveningStudentEdit() {
  Object.assign(eveningStudentForm, currentEveningStudent.value)
  showEveningStudentModal.value = true
}

async function saveEveningStudentEdit() {
  loading.value = true
  try {
    const data = await request(`/evening/students/${currentEveningStudent.value.id}`, {
      method: 'PUT',
      body: JSON.stringify(eveningStudentForm),
    })
    currentEveningStudent.value = data.student
    showEveningStudentModal.value = false
    showMessage('晚辅学生信息已更新')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function deleteEveningStudent() {
  if (!window.confirm('确定删除该晚辅学生吗？该学生月度反馈也会删除，且无法恢复。')) return
  loading.value = true
  try {
    await request(`/evening/students/${currentEveningStudent.value.id}`, { method: 'DELETE' })
    showEveningStudentModal.value = false
    go(`#/evening/classes/${currentEveningStudent.value.class_id}`)
    showMessage('晚辅学生已删除')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

function openMonthlyModal() {
  resetMonthlyForm()
  showMonthlyModal.value = true
  resizeAllTextareas()
}

async function generateMonthlyDraft() {
  if (!monthlyForm.homework_summary.trim()) return showMessage('请填写本月作业完成情况简述')
  loading.value = true
  try {
    const data = await request(`/evening/students/${currentEveningStudent.value.id}/monthly-feedbacks/generate`, {
      method: 'POST',
      body: JSON.stringify({
        feedback_month: monthlyForm.feedback_month,
        homework_summary: monthlyForm.homework_summary,
      }),
    })
    monthlyForm.ai_draft = data.draft
    monthlyForm.final_feedback = data.draft
    await resizeAllTextareas()
    showMessage('AI 初稿已生成')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function saveMonthlyFeedback() {
  if (!monthlyForm.final_feedback.trim()) return showMessage('请先生成或填写反馈内容')
  loading.value = true
  try {
    await request(`/evening/students/${currentEveningStudent.value.id}/monthly-feedbacks`, {
      method: 'POST',
      body: JSON.stringify(monthlyForm),
    })
    showMonthlyModal.value = false
    await loadEveningStudentContext()
    showMessage('月度反馈已保存')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

function openEveningDetail(feedback) {
  eveningDetail.value = feedback
  assignMonthly(monthlyEditForm, feedback)
  isEditingEveningDetail.value = false
  resizeAllTextareas()
}

async function saveEveningDetailEdit() {
  loading.value = true
  try {
    const data = await request(`/evening/monthly-feedbacks/${eveningDetail.value.id}`, {
      method: 'PUT',
      body: JSON.stringify(monthlyEditForm),
    })
    eveningDetail.value = data.feedback
    isEditingEveningDetail.value = false
    await loadEveningStudentContext()
    showMessage('月度反馈已更新')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function deleteEveningFeedback() {
  if (!window.confirm('确定删除这条月度反馈吗？删除后无法恢复。')) return
  loading.value = true
  try {
    await request(`/evening/monthly-feedbacks/${eveningDetail.value.id}`, { method: 'DELETE' })
    eveningDetail.value = null
    await loadEveningStudentContext()
    showMessage('月度反馈已删除')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function handleRoute() {
  showAccountMenu.value = false
  route.value = window.location.hash || '#/one-on-one'
  detailFeedback.value = null
  eveningDetail.value = null
  if (!isAuthed.value) return
  try {
    if (currentView.value === 'one-list') await loadOneStudents()
    if (currentView.value === 'one-student' || currentView.value === 'one-history') await loadOneStudentContext(true)
    if (currentView.value === 'evening') await loadEveningClasses()
    if (currentView.value === 'evening-class') await loadEveningClassContext()
    if (currentView.value === 'evening-student') await loadEveningStudentContext()
    if (currentView.value === 'settings') await loadAISettings()
  } catch (error) {
    showMessage(error.message)
    if (currentView.value.toString().startsWith('evening')) go('#/evening')
    else go('#/one-on-one')
  }
}

window.addEventListener('hashchange', handleRoute)

onMounted(async () => {
  if (!window.location.hash || window.location.hash === '#/students') go('#/one-on-one')
  await loadMe()
  await handleRoute()
})
</script>

<template>
  <main class="page-shell" @click="closeAccountMenu">
    <section v-if="currentView === 'auth'" class="auth-page">
      <div class="auth-illustration">
        <div class="doodle-sky" aria-hidden="true">
          <span>☀</span><span>✦</span><span>☁</span>
        </div>
        <p class="eyebrow">Teacher Assistant</p>
        <h1>教师工作记录助手</h1>
        <p>一对一课后反馈和晚辅月度作业反馈，都放进同一个清晰的工作台。</p>
        <div class="doodle-board"><span class="line-icon book"></span><strong>今日小目标</strong><em>记录学生成长</em></div>
        <div class="doodle-row" aria-hidden="true"><span>✎</span><span>▤</span><span>♡</span><span>☆</span></div>
      </div>
      <form class="paper-card auth-card" @submit.prevent="authMode === 'login' ? login() : register()">
        <div class="paper-clip" aria-hidden="true"></div>
        <div class="tabs">
          <button type="button" :class="{ active: authMode === 'login' }" @click="authMode = 'login'">登录</button>
          <button type="button" :class="{ active: authMode === 'register' }" @click="authMode = 'register'">注册</button>
        </div>
        <label>邮箱<input v-model="authForm.email" type="email" placeholder="teacher@qq.com" required /></label>
        <label>密码<input v-model="authForm.password" type="password" placeholder="至少 6 位" required /></label>
        <template v-if="authMode === 'register'">
          <label>确认密码<input v-model="authForm.confirmPassword" type="password" required /></label>
          <label class="code-line">验证码<span><input v-model="authForm.code" placeholder="6 位验证码" required /><button type="button" class="ghost-btn" :disabled="loading" @click="sendCode">发送</button></span></label>
        </template>
        <button class="primary-btn" :disabled="loading">{{ authMode === 'login' ? '进入工作台' : '创建老师账号' }}</button>
      </form>
    </section>

    <section v-else class="app-layout">
      <aside class="sidebar">
        <div class="brand"><span class="logo-mark"></span><strong>教师助手</strong></div>
        <div class="side-doodle" aria-hidden="true"><span class="mini-pencil"></span><span>✦</span><span class="mini-book"></span></div>
        <nav class="module-nav" aria-label="业务导航">
          <button class="nav-button" :class="{ active: currentView.startsWith('one') }" @click="go('#/one-on-one')">一对一</button>
          <button class="nav-button" :class="{ active: currentView.startsWith('evening') }" @click="go('#/evening')">晚辅</button>
        </nav>
        <div class="account-area" @click.stop>
          <button class="account-button" type="button" :class="{ active: showAccountMenu || currentView === 'settings' }" @click="toggleAccountMenu">
            <span class="account-avatar">{{ teacherInitial }}</span>
            <span class="account-meta"><strong>已登录账号</strong><small>{{ teacher?.email }}</small></span>
            <span class="account-caret">⌄</span>
          </button>
          <div v-if="showAccountMenu" class="account-menu">
            <button type="button" @click="go('#/settings')">设置</button>
            <button type="button" class="danger-menu-item" @click="logout">退出登录</button>
          </div>
        </div>
      </aside>

      <section class="content">
        <header class="top-banner">
          <div>
            <p class="eyebrow">{{ currentView === 'settings' ? '设置' : currentView.startsWith('evening') ? '晚辅' : '一对一' }}</p>
            <h2 v-if="currentView === 'one-list'">一对一学生</h2>
            <h2 v-else-if="currentView === 'settings'">AI 模型配置</h2>
            <h2 v-else-if="currentView === 'evening'">晚辅班级</h2>
            <h2 v-else-if="currentView === 'evening-class'">{{ currentClass?.name || '晚辅班级' }}</h2>
            <h2 v-else-if="currentView === 'evening-student'">{{ currentEveningStudent?.name || '晚辅学生' }}</h2>
            <h2 v-else>{{ currentStudent?.name || '一对一学生' }}</h2>
          </div>
          <button v-if="currentView === 'one-student' || currentView === 'one-history'" class="ghost-btn" @click="go('#/one-on-one')">返回一对一</button>
          <button v-if="currentView === 'evening-class'" class="ghost-btn" @click="go('#/evening')">返回晚辅</button>
          <button v-if="currentView === 'evening-student'" class="ghost-btn" @click="go(`#/evening/classes/${currentEveningStudent?.class_id}`)">返回班级</button>
        </header>

        <section v-if="currentView === 'one-list'" class="dashboard-grid">
          <form class="paper-card student-form" @submit.prevent="createOneStudent">
            <h3>添加一对一学生</h3>
            <input v-model="oneStudentForm.name" placeholder="学生姓名" />
            <input v-model="oneStudentForm.grade" placeholder="年级，例如 初二" />
            <input v-model="oneStudentForm.subject" placeholder="科目，例如 数学" />
            <textarea v-model="oneStudentForm.note" class="auto-textarea" placeholder="备注" @input="autoResize"></textarea>
            <button class="primary-btn" :disabled="loading">添加到一对一</button>
          </form>
          <div class="student-list">
            <article v-for="student in oneStudents" :key="student.id" class="student-card" @click="go(`#/one-on-one/students/${student.id}`)">
              <span class="avatar">{{ student.name.slice(0, 1) }}</span>
              <h3>{{ student.name }}</h3>
              <p>{{ student.grade || '未填写年级' }} · {{ student.subject || '未填写科目' }}</p>
              <small>{{ student.feedback_count }} 条一对一记录</small>
            </article>
            <div v-if="oneStudents.length === 0" class="empty-state">还没有一对一学生。</div>
          </div>
        </section>

        <section v-if="currentView === 'one-student' && currentStudent" class="student-home">
          <div class="paper-card profile-card">
            <h3>{{ currentStudent.name }}</h3>
            <p>{{ currentStudent.grade || '未填写年级' }} · {{ currentStudent.subject || '未填写科目' }}</p>
            <small>{{ currentStudent.note || '暂无备注' }}</small>
            <div class="button-row"><button class="ghost-btn" @click="openOneStudentEdit">编辑学生信息</button></div>
          </div>
          <div class="action-grid">
            <button class="action-card" type="button" @click="openCreateFeedback"><span class="line-icon pencil"></span><strong>新增课后反馈</strong><small>记录本次课程，生成并修改反馈正文</small></button>
            <button class="action-card" type="button" @click="go(`#/one-on-one/students/${currentStudent.id}/history`)"><span class="line-icon notebook"></span><strong>查看历史反馈</strong><small>共 {{ feedbacks.length }} 条记录</small></button>
          </div>
          <article v-if="feedbacks[0]" class="paper-card recent-card"><p class="eyebrow">最近一次反馈</p><h3>{{ feedbacks[0].lesson_time }}</h3><p>{{ shortText(feedbacks[0].final_feedback, 120) }}</p></article>
        </section>

        <section v-if="currentView === 'one-history' && currentStudent" class="history-page">
          <div class="history-header"><div><p class="eyebrow">一对一历史反馈</p><h3>{{ currentStudent.name }} 的记录</h3></div><button class="primary-btn" @click="openCreateFeedback">新增反馈</button></div>
          <div class="history-list">
            <button v-for="feedback in feedbacks" :key="feedback.id" class="history-card" type="button" @click="openFeedbackDetail(feedback)"><strong>{{ feedback.lesson_time }}</strong><span>{{ shortText(feedback.lesson_summary, 64) }}</span><small>{{ shortText(feedback.final_feedback, 110) }}</small></button>
            <div v-if="!feedbacks.length" class="empty-state">暂无反馈记录。</div>
          </div>
        </section>

        <section v-if="currentView === 'evening'" class="dashboard-grid">
          <form class="paper-card student-form" @submit.prevent="createClassFromList">
            <h3>新建晚辅班级</h3>
            <input v-model="classForm.name" placeholder="班级名称，例如 周一晚辅班" />
            <textarea v-model="classForm.note" class="auto-textarea" placeholder="备注" @input="autoResize"></textarea>
            <button class="primary-btn" :disabled="loading">新建班级</button>
          </form>
          <div class="student-list">
            <article v-for="cls in eveningClasses" :key="cls.id" class="student-card" @click="go(`#/evening/classes/${cls.id}`)">
              <span class="avatar">班</span>
              <h3>{{ cls.name }}</h3>
              <p>{{ cls.note || '暂无备注' }}</p>
              <small>{{ cls.student_count }} 名学生</small>
            </article>
            <div v-if="!eveningClasses.length" class="empty-state">还没有晚辅班级。</div>
          </div>
        </section>

        <section v-if="currentView === 'evening-class' && currentClass" class="student-home">
          <div class="paper-card profile-card">
            <h3>{{ currentClass.name }}</h3><small>{{ currentClass.note || '暂无备注' }}</small>
            <div class="button-row"><button class="ghost-btn" @click="openClassModal(currentClass)">编辑班级</button><button class="danger-btn" @click="deleteClass">删除班级</button></div>
          </div>
          <div class="button-row"><button class="primary-btn" @click="showBulkModal = true; resizeAllTextareas()">批量录入学生</button></div>
          <div class="student-list">
            <article v-for="student in eveningStudents" :key="student.id" class="student-card" @click="go(`#/evening/students/${student.id}`)">
              <span class="avatar">{{ student.name.slice(0, 1) }}</span><h3>{{ student.name }}</h3>
              <p>{{ student.grade || '未填年级' }} · {{ student.school || '未填学校' }}</p><small>{{ student.feedback_count }} 条月度反馈</small>
            </article>
            <div v-if="!eveningStudents.length" class="empty-state">这个班级还没有学生。</div>
          </div>
        </section>

        <section v-if="currentView === 'evening-student' && currentEveningStudent" class="history-page">
          <div class="paper-card profile-card">
            <h3>{{ currentEveningStudent.name }}</h3><p>{{ currentEveningStudent.grade || '未填年级' }} · {{ currentEveningStudent.school || '未填学校' }}</p><small>{{ currentEveningStudent.note || '暂无备注' }}</small>
            <div class="button-row"><button class="ghost-btn" @click="openEveningStudentEdit">编辑学生信息</button><button class="primary-btn" @click="openMonthlyModal">新增月度反馈</button></div>
          </div>
          <div class="history-list">
            <button v-for="feedback in eveningFeedbacks" :key="feedback.id" class="history-card" @click="openEveningDetail(feedback)">
              <strong>{{ feedback.feedback_month }}</strong><span>{{ shortText(feedback.homework_summary, 72) }}</span><small>{{ shortText(feedback.final_feedback, 120) }}</small>
            </button>
            <div v-if="!eveningFeedbacks.length" class="empty-state">暂无月度反馈。</div>
          </div>
        </section>

        <section v-if="currentView === 'settings'" class="settings-page">
          <form class="paper-card settings-card" @submit.prevent="saveAISettings">
            <div>
              <p class="eyebrow">AI Provider</p>
              <h3>使用你自己的模型 API</h3>
              <p class="settings-hint">这里保存的是当前老师账号自己的 AI 配置。API Key 会加密保存在本地数据库里，不会显示明文。</p>
            </div>

            <label>模型供应商
              <select v-model="aiSettingsForm.provider" @change="applyAIPreset">
                <option v-for="(preset, key) in AI_PRESETS" :key="key" :value="key">{{ preset.label }}</option>
              </select>
            </label>

            <label>Base URL
              <input v-model="aiSettingsForm.base_url" placeholder="https://api.deepseek.com/v1" />
              <small>模型平台的 OpenAI-compatible 接口地址。</small>
            </label>

            <label>模型名
              <input v-model="aiSettingsForm.model" placeholder="deepseek-chat" />
              <small>例如 DeepSeek 常用 deepseek-chat，OpenAI 可用 gpt-4o-mini。</small>
            </label>

            <label>API Key
              <input v-model="aiSettingsForm.api_key" type="password" :placeholder="aiSettings?.has_api_key ? '已配置，留空则保留原 Key' : '粘贴你的 API Key'" autocomplete="off" />
              <small>{{ aiSettings?.has_api_key ? '当前账号已有 API Key。填写新 Key 会覆盖旧 Key。' : '还没有保存 API Key，生成反馈前需要先配置。' }}</small>
            </label>

            <div class="settings-status" :class="{ ok: aiSettings?.has_api_key }">
              {{ aiSettings?.has_api_key ? `已配置：${aiSettings.model}` : '未配置 API Key' }}
            </div>

            <div class="button-row danger-row">
              <div class="button-row">
                <button type="button" class="ghost-btn" :disabled="loading" @click="testAISettings">测试连接</button>
                <button class="primary-btn" :disabled="loading">保存配置</button>
              </div>
              <button type="button" class="danger-btn" :disabled="loading || !aiSettings?.has_api_key" @click="clearAIKey">清除 API Key</button>
            </div>
          </form>
        </section>
      </section>
    </section>

    <div v-if="showCreateModal" class="modal-mask" @click.self="showCreateModal = false">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveFeedback">
        <div class="modal-title"><h3>新增课后反馈</h3><button type="button" class="icon-btn" @click="closeCreateFeedback">×</button></div>
        <label>上课时间<input v-model="feedbackForm.lesson_time" type="datetime-local" /></label>
        <label>课程内容简述<textarea v-model="feedbackForm.lesson_summary" class="auto-textarea" @input="autoResize"></textarea></label>
        <label>课堂表现简述<textarea v-model="feedbackForm.performance_summary" class="auto-textarea" @input="autoResize"></textarea></label>
        <div class="button-row"><button type="button" class="ghost-btn" :disabled="loading" @click="generateDraft">生成 AI 初稿</button><button class="primary-btn" :disabled="loading">保存最终反馈</button></div>
        <label>AI 初稿<textarea v-model="feedbackForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label>
        <label>最终反馈<textarea v-model="feedbackForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
      </form>
    </div>

    <div v-if="detailFeedback" class="modal-mask" @click.self="closeFeedbackDetail">
      <article class="paper-card modal-panel feedback-detail-modal">
        <div class="modal-title"><h3>反馈详情</h3><button type="button" class="icon-btn" @click="closeFeedbackDetail">×</button></div>
        <template v-if="!isEditingDetail">
          <p><strong>上课时间：</strong>{{ detailFeedback.lesson_time }}</p><p><strong>课程内容：</strong>{{ detailFeedback.lesson_summary }}</p><p><strong>课堂表现：</strong>{{ detailFeedback.performance_summary || '未填写' }}</p><h4>最终反馈</h4><pre>{{ detailFeedback.final_feedback }}</pre><details><summary>查看 AI 初稿</summary><pre>{{ detailFeedback.ai_draft }}</pre></details>
          <div class="button-row danger-row"><button class="ghost-btn" @click="isEditingDetail = true; assignFeedback(editForm, detailFeedback); resizeAllTextareas()">编辑反馈</button><button class="danger-btn" @click="deleteFeedback">删除反馈</button></div>
        </template>
        <form v-else class="feedback-editor" @submit.prevent="saveFeedbackEdit">
          <label>上课时间<input v-model="editForm.lesson_time" type="datetime-local" /></label><label>课程内容简述<textarea v-model="editForm.lesson_summary" class="auto-textarea" @input="autoResize"></textarea></label><label>课堂表现简述<textarea v-model="editForm.performance_summary" class="auto-textarea" @input="autoResize"></textarea></label><label>AI 初稿<textarea v-model="editForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label><label>最终反馈<textarea v-model="editForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
          <div class="button-row"><button class="primary-btn">保存修改</button><button class="ghost-btn" type="button" @click="isEditingDetail = false">取消</button></div>
        </form>
      </article>
    </div>

    <div v-if="showOneStudentEditModal" class="modal-mask" @click.self="showOneStudentEditModal = false">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveOneStudentEdit">
        <div class="modal-title"><h3>编辑一对一学生</h3><button type="button" class="icon-btn" @click="showOneStudentEditModal = false">×</button></div>
        <input v-model="oneStudentForm.name" placeholder="学生姓名" /><input v-model="oneStudentForm.grade" placeholder="年级" /><input v-model="oneStudentForm.subject" placeholder="科目" /><textarea v-model="oneStudentForm.note" class="auto-textarea" placeholder="备注" @input="autoResize"></textarea>
        <div class="button-row danger-row"><button class="primary-btn">保存学生信息</button><button type="button" class="danger-btn" @click="deleteOneStudent">删除学生</button></div>
      </form>
    </div>

    <div v-if="showClassModal" class="modal-mask" @click.self="showClassModal = false">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveClass">
        <div class="modal-title"><h3>{{ editingClass ? '编辑班级' : '新建班级' }}</h3><button type="button" class="icon-btn" @click="showClassModal = false">×</button></div>
        <input v-model="classForm.name" placeholder="班级名称" /><textarea v-model="classForm.note" class="auto-textarea" placeholder="备注" @input="autoResize"></textarea>
        <button class="primary-btn">保存班级</button>
      </form>
    </div>

    <div v-if="showBulkModal" class="modal-mask" @click.self="showBulkModal = false">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="bulkCreateEveningStudents">
        <div class="modal-title"><h3>批量录入学生</h3><button type="button" class="icon-btn" @click="showBulkModal = false">×</button></div>
        <label>学生名单<textarea v-model="bulkForm.names_text" class="auto-textarea final-text" placeholder="一行一个姓名" @input="autoResize"></textarea></label>
        <button class="primary-btn">录入学生</button>
      </form>
    </div>

    <div v-if="showEveningStudentModal" class="modal-mask" @click.self="showEveningStudentModal = false">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveEveningStudentEdit">
        <div class="modal-title"><h3>编辑晚辅学生</h3><button type="button" class="icon-btn" @click="showEveningStudentModal = false">×</button></div>
        <input v-model="eveningStudentForm.name" placeholder="姓名" /><input v-model="eveningStudentForm.grade" placeholder="年级" /><input v-model="eveningStudentForm.school" placeholder="学校" /><textarea v-model="eveningStudentForm.note" class="auto-textarea" placeholder="备注" @input="autoResize"></textarea>
        <div class="button-row danger-row"><button class="primary-btn">保存学生信息</button><button type="button" class="danger-btn" @click="deleteEveningStudent">删除学生</button></div>
      </form>
    </div>

    <div v-if="showMonthlyModal" class="modal-mask" @click.self="showMonthlyModal = false">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveMonthlyFeedback">
        <div class="modal-title"><h3>新增月度反馈</h3><button type="button" class="icon-btn" @click="showMonthlyModal = false">×</button></div>
        <label>反馈月份<input v-model="monthlyForm.feedback_month" type="month" /></label>
        <label>本月作业完成情况简述<textarea v-model="monthlyForm.homework_summary" class="auto-textarea" @input="autoResize"></textarea></label>
        <div class="button-row"><button type="button" class="ghost-btn" @click="generateMonthlyDraft">生成 AI 初稿</button><button class="primary-btn">保存月度反馈</button></div>
        <label>AI 初稿<textarea v-model="monthlyForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label><label>最终反馈<textarea v-model="monthlyForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
      </form>
    </div>

    <div v-if="eveningDetail" class="modal-mask" @click.self="eveningDetail = null">
      <article class="paper-card modal-panel feedback-detail-modal">
        <div class="modal-title"><h3>月度反馈详情</h3><button type="button" class="icon-btn" @click="eveningDetail = null">×</button></div>
        <template v-if="!isEditingEveningDetail">
          <p><strong>月份：</strong>{{ eveningDetail.feedback_month }}</p><p><strong>作业情况：</strong>{{ eveningDetail.homework_summary }}</p><h4>最终反馈</h4><pre>{{ eveningDetail.final_feedback }}</pre><details><summary>查看 AI 初稿</summary><pre>{{ eveningDetail.ai_draft }}</pre></details>
          <div class="button-row danger-row"><button class="ghost-btn" @click="isEditingEveningDetail = true; assignMonthly(monthlyEditForm, eveningDetail); resizeAllTextareas()">编辑反馈</button><button class="danger-btn" @click="deleteEveningFeedback">删除反馈</button></div>
        </template>
        <form v-else class="feedback-editor" @submit.prevent="saveEveningDetailEdit">
          <label>反馈月份<input v-model="monthlyEditForm.feedback_month" type="month" /></label><label>本月作业完成情况简述<textarea v-model="monthlyEditForm.homework_summary" class="auto-textarea" @input="autoResize"></textarea></label><label>AI 初稿<textarea v-model="monthlyEditForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label><label>最终反馈<textarea v-model="monthlyEditForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
          <div class="button-row"><button class="primary-btn">保存修改</button><button type="button" class="ghost-btn" @click="isEditingEveningDetail = false">取消</button></div>
        </form>
      </article>
    </div>

    <div v-if="message" class="toast">{{ message }}</div>
  </main>
</template>
