<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { clearToken, request, setToken } from './api'

const teacher = ref(null)
const students = ref([])
const currentStudent = ref(null)
const feedbacks = ref([])
const detailFeedback = ref(null)
const loading = ref(false)
const message = ref('')
const authMode = ref('login')
const route = ref(window.location.hash || '#/students')
const showCreateModal = ref(false)
const isEditingDetail = ref(false)

const authForm = reactive({
  email: '',
  password: '',
  confirmPassword: '',
  code: '',
})

const studentForm = reactive({
  name: '',
  grade: '',
  subject: '',
  note: '',
})

const feedbackForm = reactive(newFeedback())
const editForm = reactive(newFeedback())

const isAuthed = computed(() => Boolean(teacher.value))
const currentView = computed(() => {
  if (!isAuthed.value) return 'auth'
  if (route.value.includes('/history')) return 'history'
  if (route.value.startsWith('#/students/')) return 'student'
  return 'students'
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

function assignForm(target, source) {
  target.lesson_time = source.lesson_time || new Date().toISOString().slice(0, 16)
  target.lesson_summary = source.lesson_summary || ''
  target.performance_summary = source.performance_summary || ''
  target.ai_draft = source.ai_draft || ''
  target.final_feedback = source.final_feedback || ''
}

function resetFeedbackForm() {
  assignForm(feedbackForm, newFeedback())
}

function showMessage(text) {
  message.value = text
  window.setTimeout(() => {
    if (message.value === text) message.value = ''
  }, 3200)
}

function go(path) {
  window.location.hash = path
}

function currentStudentId() {
  return route.value.split('/')[2]
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
      body: JSON.stringify({
        email: authForm.email,
        password: authForm.password,
        code: authForm.code,
      }),
    })
    setToken(data.token)
    teacher.value = data.teacher
    await loadStudents()
    go('#/students')
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
    await loadStudents()
    go('#/students')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

function logout() {
  clearToken()
  teacher.value = null
  students.value = []
  currentStudent.value = null
  feedbacks.value = []
  detailFeedback.value = null
  go('#/students')
}

async function loadMe() {
  try {
    const data = await request('/auth/me')
    teacher.value = data.teacher
    await loadStudents()
  } catch {
    clearToken()
  }
}

async function loadStudents() {
  const data = await request('/students')
  students.value = data.students
}

async function createStudent() {
  if (!studentForm.name.trim()) return showMessage('请填写学生姓名')
  loading.value = true
  try {
    await request('/students', {
      method: 'POST',
      body: JSON.stringify(studentForm),
    })
    studentForm.name = ''
    studentForm.grade = ''
    studentForm.subject = ''
    studentForm.note = ''
    await loadStudents()
    showMessage('学生已添加')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function loadStudentContext(loadFeedbacks = false) {
  const id = currentStudentId()
  if (!id || !isAuthed.value) return
  try {
    const studentData = await request(`/students/${id}`)
    currentStudent.value = studentData.student
    if (loadFeedbacks) {
      const feedbackData = await request(`/students/${id}/feedbacks`)
      feedbacks.value = feedbackData.feedbacks
    }
  } catch (error) {
    showMessage(error.message)
    go('#/students')
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
    await loadStudentContext(true)
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
    assignForm(editForm, data.feedback)
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
    await loadStudentContext(true)
    await resizeAllTextareas()
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
    await loadStudentContext(true)
    showMessage('反馈已删除')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function handleRoute() {
  route.value = window.location.hash || '#/students'
  detailFeedback.value = null
  showCreateModal.value = false
  if (!isAuthed.value) return
  if (currentView.value === 'students') {
    await loadStudents()
  } else if (currentView.value === 'student') {
    await loadStudentContext(true)
  } else if (currentView.value === 'history') {
    await loadStudentContext(true)
  }
}

window.addEventListener('hashchange', handleRoute)

onMounted(async () => {
  if (!window.location.hash) go('#/students')
  await loadMe()
  await handleRoute()
})
</script>

<template>
  <main class="page-shell">
    <section v-if="currentView === 'auth'" class="auth-page">
      <div class="auth-illustration">
        <p class="eyebrow">Teacher Assistant</p>
        <h1>一对一课后反馈助手</h1>
        <p>把课堂记录变成清晰、温暖、专业的家长反馈，让每一次辅导都有迹可循。</p>
        <div class="doodle-board">
          <span>📚</span>
          <strong>今日小目标</strong>
          <em>记录学生成长</em>
        </div>
      </div>

      <form class="paper-card auth-card" @submit.prevent="authMode === 'login' ? login() : register()">
        <div class="tabs">
          <button type="button" :class="{ active: authMode === 'login' }" @click="authMode = 'login'">登录</button>
          <button type="button" :class="{ active: authMode === 'register' }" @click="authMode = 'register'">注册</button>
        </div>
        <label>邮箱<input v-model="authForm.email" type="email" placeholder="teacher@qq.com" required /></label>
        <label>密码<input v-model="authForm.password" type="password" placeholder="至少 6 位" required /></label>
        <template v-if="authMode === 'register'">
          <label>确认密码<input v-model="authForm.confirmPassword" type="password" required /></label>
          <label class="code-line">验证码
            <span>
              <input v-model="authForm.code" placeholder="6 位验证码" required />
              <button type="button" class="ghost-btn" :disabled="loading" @click="sendCode">发送</button>
            </span>
          </label>
        </template>
        <button class="primary-btn" :disabled="loading">{{ authMode === 'login' ? '进入学生手账' : '创建老师账号' }}</button>
      </form>
    </section>

    <section v-else class="app-layout">
      <aside class="sidebar">
        <div class="brand"><span>🍎</span><strong>反馈助手</strong></div>
        <button class="nav-button" :class="{ active: currentView === 'students' }" @click="go('#/students')">学生列表</button>
        <button class="nav-button" @click="logout">退出登录</button>
        <div class="teacher-note">{{ teacher?.email }}</div>
      </aside>

      <section class="content">
        <header class="top-banner">
          <div>
            <p class="eyebrow">一对一辅导记录</p>
            <h2>{{ currentView === 'students' ? '我的学生' : currentStudent?.name || '学生页面' }}</h2>
          </div>
          <button v-if="currentView !== 'students'" class="ghost-btn" @click="go('#/students')">返回列表</button>
        </header>

        <section v-if="currentView === 'students'" class="dashboard-grid">
          <form class="paper-card student-form" @submit.prevent="createStudent">
            <h3>添加学生</h3>
            <input v-model="studentForm.name" placeholder="学生姓名" />
            <input v-model="studentForm.grade" placeholder="年级，例如 初二" />
            <input v-model="studentForm.subject" placeholder="科目，例如 数学" />
            <textarea v-model="studentForm.note" class="auto-textarea" placeholder="备注，例如 学习特点、家长期望" @input="autoResize"></textarea>
            <button class="primary-btn" :disabled="loading">添加到我的学生</button>
          </form>

          <div class="student-list">
            <article
              v-for="student in students"
              :key="student.id"
              class="student-card"
              @click="go(`#/students/${student.id}`)"
            >
              <span class="avatar">{{ student.name.slice(0, 1) }}</span>
              <h3>{{ student.name }}</h3>
              <p>{{ student.grade || '未填写年级' }} · {{ student.subject || '未填写科目' }}</p>
              <small>{{ student.feedback_count }} 条反馈记录</small>
            </article>
            <div v-if="students.length === 0" class="empty-state">还没有学生，先添加第一位学生吧。</div>
          </div>
        </section>

        <section v-if="currentView === 'student' && currentStudent" class="student-home">
          <div class="paper-card profile-card">
            <h3>{{ currentStudent.name }}</h3>
            <p>{{ currentStudent.grade || '未填写年级' }} · {{ currentStudent.subject || '未填写科目' }}</p>
            <small>{{ currentStudent.note || '暂无备注' }}</small>
          </div>

          <div class="action-grid">
            <button class="action-card" type="button" @click="openCreateFeedback">
              <span>✏️</span>
              <strong>新增课后反馈</strong>
              <small>记录本次课程，生成并修改反馈正文</small>
            </button>
            <button class="action-card" type="button" @click="go(`#/students/${currentStudent.id}/history`)">
              <span>📚</span>
              <strong>查看历史反馈</strong>
              <small>共 {{ feedbacks.length }} 条记录，可查看、编辑、删除</small>
            </button>
          </div>

          <article v-if="feedbacks[0]" class="paper-card recent-card">
            <p class="eyebrow">最近一次反馈</p>
            <h3>{{ feedbacks[0].lesson_time }}</h3>
            <p>{{ shortText(feedbacks[0].final_feedback, 120) }}</p>
          </article>
        </section>

        <section v-if="currentView === 'history' && currentStudent" class="history-page">
          <div class="history-header">
            <div>
              <p class="eyebrow">历史反馈</p>
              <h3>{{ currentStudent.name }} 的反馈记录</h3>
            </div>
            <button class="primary-btn" type="button" @click="openCreateFeedback">新增反馈</button>
          </div>

          <div class="history-list">
            <button
              v-for="feedback in feedbacks"
              :key="feedback.id"
              class="history-card"
              type="button"
              @click="openFeedbackDetail(feedback)"
            >
              <strong>{{ feedback.lesson_time }}</strong>
              <span>{{ shortText(feedback.lesson_summary, 64) }}</span>
              <small>{{ shortText(feedback.final_feedback, 110) }}</small>
            </button>
            <div v-if="!feedbacks.length" class="empty-state">暂无反馈记录，可以先新增一条课后反馈。</div>
          </div>
        </section>
      </section>
    </section>

    <div v-if="showCreateModal" class="modal-mask" @click.self="closeCreateFeedback">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveFeedback">
        <div class="modal-title">
          <h3>新增课后反馈</h3>
          <button type="button" class="icon-btn" @click="closeCreateFeedback">×</button>
        </div>
        <label>上课时间<input v-model="feedbackForm.lesson_time" type="datetime-local" /></label>
        <label>课程内容简述<textarea v-model="feedbackForm.lesson_summary" class="auto-textarea" placeholder="例如：今天讲了二次函数顶点式，学生对配方法还需要巩固。" @input="autoResize"></textarea></label>
        <label>课堂表现简述<textarea v-model="feedbackForm.performance_summary" class="auto-textarea" placeholder="例如：课堂参与积极，但遇到综合题会有些犹豫。" @input="autoResize"></textarea></label>
        <div class="button-row">
          <button type="button" class="ghost-btn" :disabled="loading" @click="generateDraft">生成 AI 初稿</button>
          <button class="primary-btn" :disabled="loading">保存最终反馈</button>
        </div>
        <label>AI 初稿<textarea v-model="feedbackForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label>
        <label>最终反馈<textarea v-model="feedbackForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
      </form>
    </div>

    <div v-if="detailFeedback" class="modal-mask" @click.self="closeFeedbackDetail">
      <article class="paper-card modal-panel feedback-detail-modal">
        <div class="modal-title">
          <h3>反馈详情</h3>
          <button type="button" class="icon-btn" @click="closeFeedbackDetail">×</button>
        </div>

        <template v-if="!isEditingDetail">
          <p><strong>上课时间：</strong>{{ detailFeedback.lesson_time }}</p>
          <p><strong>课程内容：</strong>{{ detailFeedback.lesson_summary }}</p>
          <p><strong>课堂表现：</strong>{{ detailFeedback.performance_summary || '未填写' }}</p>
          <h4>最终反馈</h4>
          <pre>{{ detailFeedback.final_feedback }}</pre>
          <details>
            <summary>查看 AI 初稿</summary>
            <pre>{{ detailFeedback.ai_draft }}</pre>
          </details>
          <div class="button-row danger-row">
            <button class="ghost-btn" type="button" @click="isEditingDetail = true; assignForm(editForm, detailFeedback); resizeAllTextareas()">编辑反馈</button>
            <button class="danger-btn" type="button" @click="deleteFeedback">删除反馈</button>
          </div>
        </template>

        <form v-else class="feedback-editor" @submit.prevent="saveFeedbackEdit">
          <label>上课时间<input v-model="editForm.lesson_time" type="datetime-local" /></label>
          <label>课程内容简述<textarea v-model="editForm.lesson_summary" class="auto-textarea" @input="autoResize"></textarea></label>
          <label>课堂表现简述<textarea v-model="editForm.performance_summary" class="auto-textarea" @input="autoResize"></textarea></label>
          <label>AI 初稿<textarea v-model="editForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label>
          <label>最终反馈<textarea v-model="editForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
          <div class="button-row">
            <button class="primary-btn" :disabled="loading">保存修改</button>
            <button class="ghost-btn" type="button" @click="isEditingDetail = false">取消</button>
          </div>
        </form>
      </article>
    </div>

    <div v-if="message" class="toast">{{ message }}</div>
  </main>
</template>
