<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { clearToken, request, setToken } from './api'

const teacher = ref(null)
const students = ref([])
const currentStudent = ref(null)
const feedbacks = ref([])
const selectedFeedback = ref(null)
const loading = ref(false)
const message = ref('')
const authMode = ref('login')
const route = ref(window.location.hash || '#/students')

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

const feedbackForm = reactive({
  lesson_time: new Date().toISOString().slice(0, 16),
  lesson_summary: '',
  performance_summary: '',
  ai_draft: '',
  final_feedback: '',
})

const isAuthed = computed(() => Boolean(teacher.value))
const currentView = computed(() => {
  if (!isAuthed.value) return 'auth'
  if (route.value.startsWith('#/students/')) return 'student'
  return 'students'
})

function showMessage(text) {
  message.value = text
  window.setTimeout(() => {
    if (message.value === text) message.value = ''
  }, 2800)
}

function go(path) {
  window.location.hash = path
}

function resetFeedbackForm() {
  feedbackForm.lesson_time = new Date().toISOString().slice(0, 16)
  feedbackForm.lesson_summary = ''
  feedbackForm.performance_summary = ''
  feedbackForm.ai_draft = ''
  feedbackForm.final_feedback = ''
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

async function loadStudentPage() {
  const id = route.value.split('/')[2]
  if (!id || !isAuthed.value) return
  try {
    const [studentData, feedbackData] = await Promise.all([
      request(`/students/${id}`),
      request(`/students/${id}/feedbacks`),
    ])
    currentStudent.value = studentData.student
    feedbacks.value = feedbackData.feedbacks
    selectedFeedback.value = feedbackData.feedbacks[0] || null
    resetFeedbackForm()
  } catch (error) {
    showMessage(error.message)
    go('#/students')
  }
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
    const data = await request(`/students/${currentStudent.value.id}/feedbacks`, {
      method: 'POST',
      body: JSON.stringify(feedbackForm),
    })
    feedbacks.value = [data.feedback, ...feedbacks.value]
    selectedFeedback.value = data.feedback
    resetFeedbackForm()
    showMessage('反馈已保存')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

window.addEventListener('hashchange', async () => {
  route.value = window.location.hash || '#/students'
  if (route.value.startsWith('#/students/')) await loadStudentPage()
})

onMounted(async () => {
  if (!window.location.hash) go('#/students')
  await loadMe()
  if (route.value.startsWith('#/students/')) await loadStudentPage()
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
        <button class="nav-button active" @click="go('#/students')">学生列表</button>
        <button class="nav-button" @click="logout">退出登录</button>
        <div class="teacher-note">{{ teacher?.email }}</div>
      </aside>

      <section class="content">
        <header class="top-banner">
          <div>
            <p class="eyebrow">一对一辅导记录</p>
            <h2>{{ currentView === 'student' ? currentStudent?.name || '学生页面' : '我的学生' }}</h2>
          </div>
          <button v-if="currentView === 'student'" class="ghost-btn" @click="go('#/students')">返回列表</button>
        </header>

        <section v-if="currentView === 'students'" class="dashboard-grid">
          <form class="paper-card student-form" @submit.prevent="createStudent">
            <h3>添加学生</h3>
            <input v-model="studentForm.name" placeholder="学生姓名" />
            <input v-model="studentForm.grade" placeholder="年级，例如 初二" />
            <input v-model="studentForm.subject" placeholder="科目，例如 数学" />
            <textarea v-model="studentForm.note" placeholder="备注，例如 学习特点、家长期望"></textarea>
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

        <section v-if="currentView === 'student' && currentStudent" class="student-page">
          <div class="paper-card profile-card">
            <h3>{{ currentStudent.name }}</h3>
            <p>{{ currentStudent.grade || '未填写年级' }} · {{ currentStudent.subject || '未填写科目' }}</p>
            <small>{{ currentStudent.note || '暂无备注' }}</small>
          </div>

          <form class="paper-card feedback-editor" @submit.prevent="saveFeedback">
            <h3>新增课后反馈</h3>
            <label>上课时间<input v-model="feedbackForm.lesson_time" type="datetime-local" /></label>
            <label>课程内容简述<textarea v-model="feedbackForm.lesson_summary" placeholder="例如：今天讲了二次函数顶点式，学生对配方法还需要巩固。"></textarea></label>
            <label>课堂表现简述<textarea v-model="feedbackForm.performance_summary" placeholder="例如：课堂参与积极，但遇到综合题会有些犹豫。"></textarea></label>
            <div class="button-row">
              <button type="button" class="ghost-btn" :disabled="loading" @click="generateDraft">生成 AI 初稿</button>
              <button class="primary-btn" :disabled="loading">保存最终反馈</button>
            </div>
            <label>AI 初稿<textarea v-model="feedbackForm.ai_draft" class="large-text"></textarea></label>
            <label>最终反馈<textarea v-model="feedbackForm.final_feedback" class="large-text"></textarea></label>
          </form>

          <aside class="paper-card history-panel">
            <h3>历史反馈</h3>
            <button
              v-for="feedback in feedbacks"
              :key="feedback.id"
              class="history-item"
              type="button"
              @click="selectedFeedback = feedback"
            >
              <strong>{{ feedback.lesson_time }}</strong>
              <span>{{ feedback.lesson_summary.slice(0, 32) }}</span>
            </button>
            <div v-if="!feedbacks.length" class="empty-state small">暂无反馈记录</div>
          </aside>

          <article v-if="selectedFeedback" class="paper-card feedback-detail">
            <h3>反馈详情</h3>
            <p><strong>课程内容：</strong>{{ selectedFeedback.lesson_summary }}</p>
            <p><strong>课堂表现：</strong>{{ selectedFeedback.performance_summary || '未填写' }}</p>
            <pre>{{ selectedFeedback.final_feedback }}</pre>
          </article>
        </section>
      </section>
    </section>

    <div v-if="message" class="toast">{{ message }}</div>
  </main>
</template>
