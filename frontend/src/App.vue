<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { clearToken, request, setToken } from './api'
import authHeroArt from './assets/illustrations/auth-hero-crayon.png'
import dashboardBannerArt from './assets/illustrations/dashboard-banner.jpg'
import emptyStateArt from './assets/illustrations/empty-state.jpg'
import eveningStickerArt from './assets/illustrations/evening-sticker.jpg'
import createFeedbackArt from './assets/illustrations/create-feedback-crayon.png'
import copyFeedbackArt from './assets/illustrations/copy-feedback-crayon.png'
import historyFeedbackArt from './assets/illustrations/history-feedback-crayon.png'
import oneOnOneStickerArt from './assets/illustrations/one-on-one-sticker.jpg'
import sidebarCampusArt from './assets/illustrations/sidebar-campus-crayon.png'
import sidebarDoodleArt from './assets/illustrations/sidebar-doodle-crayon.png'
import sidebarLogoArt from './assets/illustrations/sidebar-logo-crayon.png'

const teacher = ref(null)
const route = ref(window.location.hash || '#/one-on-one')
const loading = ref(false)
const message = ref('')
const authMode = ref('login')

const oneStudents = ref([])
const currentStudent = ref(null)
const feedbacks = ref([])
const feedbackSearchResults = ref([])
const eveningFeedbackSearchResults = ref([])
const detailFeedback = ref(null)
const showCreateModal = ref(false)
const showStudentModal = ref(false)
const showOneStudentEditModal = ref(false)
const isEditingDetail = ref(false)
const copiedFeedbackId = ref(null)

const eveningClasses = ref([])
const currentClass = ref(null)
const eveningStudents = ref([])
const currentEveningStudent = ref(null)
const eveningFeedbacks = ref([])
const eveningDetail = ref(null)
const groupClasses = ref([])
const currentGroupClass = ref(null)
const showClassModal = ref(false)
const showGroupClassModal = ref(false)
const showBulkModal = ref(false)
const showEveningStudentModal = ref(false)
const showMonthlyModal = ref(false)
const isEditingEveningDetail = ref(false)
const editingClass = ref(null)
const editingGroupClass = ref(null)
const aiSettings = ref(null)
const styleExamples = ref([])
const detailStyleExample = ref(null)
const isEditingStyleExample = ref(false)
const showAccountMenu = ref(false)
const showApiOnboarding = ref(false)
const showSettingsGuide = ref(false)
const showFeedbackStyleModal = ref(false)
const showWritingReference = ref(false)
const rawLessonNote = ref('')
const hasOrganizedLessonNote = ref(false)
const rawLessonNoteDirty = ref(false)
const organizeMissingFields = ref([])
const useStyleExamplesForDraft = ref(true)
const feedbackDraftStatus = ref('')
const hasSavedFeedbackDraft = ref(false)
const styleExamplePage = ref(1)
const feedbackStyleExamplePage = ref(1)
const feedbackSearchForm = reactive(defaultFeedbackSearchRange())
const eveningFeedbackSearchForm = reactive(defaultEveningSearchRange())
const studentHistoryFilter = reactive({ start_date: '', end_date: '' })
const feedbackPanels = reactive(defaultFeedbackPanels())

const API_ONBOARDING_SEEN_KEY = 'api_onboarding_seen_v1'
const SETTINGS_GUIDE_SEEN_KEY = 'settings_guide_seen_v1'
const WRITING_REFERENCE_VISIBLE_WIDTH = 132
const WRITING_REFERENCE_VISIBLE_HEIGHT = 76
const STYLE_EXAMPLE_PAGE_SIZE = 5
const MAX_ENABLED_STYLE_EXAMPLES = 5
const EVENING_PERIOD_TYPES = [
  { value: 'day', label: '按天' },
  { value: 'week', label: '按周' },
  { value: 'month', label: '按月' },
]
const FEEDBACK_CORE_FIELDS = [
  {
    formField: 'lesson_summary',
    title: '1. 课堂学习内容',
    placeholder: '写本节课学习、复习或检测的知识点、题型、方法和练习内容',
  },
  {
    formField: 'performance_summary',
    title: '2. 课堂表现与知识掌握情况',
    placeholder: '写上课状态、练习完成情况、掌握得好的地方和还不熟的知识点',
  },
  {
    formField: 'advice_summary',
    title: '3. 课后建议',
    placeholder: '写老师真实提出的建议、提醒或改进方向，例如复盘错题、注意审题、计算不要跳步',
  },
  {
    formField: 'homework_plan',
    title: '4. 作业安排',
    placeholder: '严格写本次实际布置的具体任务；没有作业请写“无”或“本次无额外作业”',
  },
]
const FIELD_TITLES = FEEDBACK_CORE_FIELDS.reduce((payload, field) => {
  payload[field.formField] = field.title
  return payload
}, {})
const WRITING_REFERENCE_SECTIONS = [
  {
    title: '课堂学习内容',
    guide: '写本节课学习、复习、检测了什么内容。',
    sample: '本节课复习了不等式和因式分解，涉及不等式运算、不等式组解集、一次函数图像与不等式关系、提公因式法、平方差公式和完全平方公式。',
  },
  {
    title: '课堂表现与知识掌握情况',
    guide: '写学生本节课上课状态、课堂练习完成情况和知识点掌握情况。',
    sample: '学生A听课认真，做题专注，比之前更愿意主动思考和提问；基础计算速度有进步，但一次函数图像理解、公式法应用和不等式变号规则还需要巩固。',
  },
  {
    title: '课后建议',
    guide: '写老师明确提出的建议、提醒、改进方向或习惯要求，不要让 AI 自行替你判断。',
    sample: '建议课后继续巩固基础题型，加强一次函数图像理解，做题时一步步计算，避免跳步。',
  },
  {
    title: '作业安排',
    guide: '严格按照实际布置的具体任务填写，不新增、不扩写；复习、预习、订正、带资料都可以是作业。',
    sample: '复习本节课讲过的不等式和因式分解内容；预习学校正在学的分式内容；下节课带半期试卷用于分析错题。',
  },
]

const authForm = reactive({ email: '', password: '', confirmPassword: '', code: '' })
const oneStudentForm = reactive({ name: '', grade: '', subject: '' })
const feedbackForm = reactive(newFeedback())
const editForm = reactive(newFeedback())
const classForm = reactive({ name: '' })
const groupClassForm = reactive({ name: '' })
const bulkForm = reactive({ names_text: '' })
const eveningStudentForm = reactive({ name: '', grade: '', school: '' })
const monthlyForm = reactive(newMonthlyFeedback())
const monthlyEditForm = reactive(newMonthlyFeedback())
const aiSettingsForm = reactive({
  provider: 'deepseek',
  base_url: 'https://api.deepseek.com',
  model: 'deepseek-v4-flash',
  api_key: '',
  clear_api_key: false,
})
const styleExampleForm = reactive({ title: '', content: '', enabled: true })
const inlineStyleExampleForm = reactive({ title: '', content: '', enabled: true })
const styleExampleEditForm = reactive({ title: '', content: '', enabled: true })
const legacyQaAnswers = reactive(defaultQaAnswers())
const writingReferenceFrame = reactive({ left: 220, top: 110, width: 560, height: 520 })
const writingReferenceDrag = reactive({ active: false, startX: 0, startY: 0, startLeft: 0, startTop: 0, startWidth: 0, startHeight: 0, mode: '' })
const settingsPanels = reactive({
  feedback_ai: false,
  style_examples: false,
})

const AI_PRESETS = {
  deepseek: {
    label: 'DeepSeek（推荐）',
    base_url: 'https://api.deepseek.com',
    model: 'deepseek-v4-flash',
    hint: '适合生成课后反馈初稿，中文表达稳定，性价比较高。deepseek-chat 将退役，新配置建议使用 deepseek-v4-flash。',
    api_key_url: 'https://platform.deepseek.com/api_keys',
    docs_url: 'https://api-docs.deepseek.com/',
  },
  qwen: {
    label: '阿里云百炼 - 通义千问',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen3.6-plus',
    hint: '适合中国大陆用户，中文反馈、总结和润色场景都比较顺手。若账号暂未开放新模型，可改用 qwen-plus。',
    api_key_url: 'https://bailian.console.aliyun.com/?tab=model#/api-key',
    docs_url: 'https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope',
  },
  kimi: {
    label: 'Kimi / Moonshot',
    base_url: 'https://api.moonshot.ai/v1',
    model: 'kimi-k2.6',
    hint: '适合长上下文课堂记录整理，也可用于生成自然、完整的反馈正文。',
    api_key_url: 'https://platform.moonshot.ai/console/api-keys',
    docs_url: 'https://platform.moonshot.ai/docs/overview',
  },
  zhipu: {
    label: '智谱 AI',
    base_url: 'https://open.bigmodel.cn/api/paas/v4',
    model: 'glm-4-flash-250414',
    hint: '适合中文反馈生成和日常教育文本润色；如账号支持更新的 GLM 系列，可按控制台模型名替换。',
    api_key_url: 'https://bigmodel.cn/usercenter/proj-mgmt/apikeys',
    docs_url: 'https://docs.bigmodel.cn/cn/guide/develop/openai/introduction',
  },
  openai: {
    label: 'OpenAI',
    base_url: 'https://api.openai.com/v1',
    model: 'gpt-5.4-mini',
    hint: '适合高质量文本生成；请确认网络、账号和付款方式可用。若账号暂未开放，可改用 gpt-4.1-mini。',
    api_key_url: 'https://platform.openai.com/api-keys',
    docs_url: 'https://platform.openai.com/docs/models/gpt-5.4-mini',
  },
  custom: { label: '自定义兼容接口', base_url: '', model: '', hint: '用于其他 OpenAI-compatible 文本生成模型。', api_key_url: '', docs_url: '' },
}

const isAuthed = computed(() => Boolean(teacher.value))
const teacherInitial = computed(() => (teacher.value?.email || 'T').slice(0, 1).toUpperCase())
const selectedAIPreset = computed(() => AI_PRESETS[aiSettingsForm.provider] || AI_PRESETS.custom)
const currentView = computed(() => {
  if (!isAuthed.value) return 'auth'
  if (route.value === '#/settings') return 'settings'
  if (route.value === '#/one-on-one/feedbacks') return 'one-feedback-search'
  if (route.value === '#/evening/feedbacks') return 'evening-feedback-search'
  if (route.value === '#/group-classes/feedbacks') return 'group-feedback-search'
  if (route.value.startsWith('#/group-classes/classes/')) return 'group-class'
  if (route.value === '#/group-classes') return 'group-classes'
  if (route.value.startsWith('#/evening/classes/')) return 'evening-class'
  if (route.value.startsWith('#/evening/students/')) return 'evening-student'
  if (route.value === '#/evening') return 'evening'
  if (route.value.includes('/history')) return 'one-history'
  if (route.value.startsWith('#/one-on-one/students/')) return 'one-student'
  return 'one-list'
})
const filteredStudentFeedbacks = computed(() =>
  feedbacks.value.filter((feedback) => isDateInRange(feedback.lesson_time, studentHistoryFilter.start_date, studentHistoryFilter.end_date))
)
const enabledStyleExamples = computed(() => styleExamples.value.filter((example) => example.enabled))
const enabledStyleExampleCount = computed(() => enabledStyleExamples.value.length)
const styleGenerationStatus = computed(() =>
  enabledStyleExampleCount.value && !useStyleExamplesForDraft.value
    ? '本次已停用个人风格，将按标准结构生成'
    : enabledStyleExampleCount.value
    ? `已启用 ${enabledStyleExampleCount.value} / ${MAX_ENABLED_STYLE_EXAMPLES} 条样例，将按个人风格生成`
    : '暂无启用样例，将按标准结构生成'
)
const styleExampleTotalPages = computed(() => totalPages(styleExamples.value.length))
const feedbackStyleExampleTotalPages = computed(() => totalPages(styleExamples.value.length))
const paginatedStyleExamples = computed(() => pageItems(styleExamples.value, styleExamplePage.value))
const paginatedFeedbackStyleExamples = computed(() => pageItems(styleExamples.value, feedbackStyleExamplePage.value))
const missingFeedbackFields = computed(() => FEEDBACK_CORE_FIELDS.filter((field) => !String(feedbackForm[field.formField] || '').trim()).map((field) => field.formField))
const blockingMissingFields = computed(() => [...new Set([...organizeMissingFields.value, ...missingFeedbackFields.value])])
const canGenerateFeedback = computed(() => blockingMissingFields.value.length === 0)
const missingFieldText = computed(() => blockingMissingFields.value.map((field) => FIELD_TITLES[field] || field).join('、'))
const eveningFeedbackStudentOptions = computed(() => {
  if (eveningStudents.value.length) return eveningStudents.value
  if (eveningDetail.value?.student_id) {
    return [{
      id: eveningDetail.value.student_id,
      name: eveningDetail.value.student_name || currentEveningStudent.value?.name || '当前学生',
    }]
  }
  return currentEveningStudent.value ? [currentEveningStudent.value] : []
})
const writingReferenceStyle = computed(() => ({
  left: `${writingReferenceFrame.left}px`,
  top: `${writingReferenceFrame.top}px`,
  width: `${writingReferenceFrame.width}px`,
  height: `${writingReferenceFrame.height}px`,
}))

function newFeedback() {
  return {
    lesson_title: '',
    lesson_time: new Date().toISOString().slice(0, 16),
    lesson_summary: '',
    performance_summary: '',
    advice_summary: '',
    homework_plan: '',
    ai_draft: '',
    final_feedback: '',
  }
}

function defaultQaAnswers() {
  return {
    lesson: '',
    performance: '',
    advice: '',
    homework: '',
  }
}

function currentMonth() {
  return new Date().toISOString().slice(0, 7)
}

function currentWeek() {
  const date = new Date()
  const day = date.getDay() || 7
  date.setDate(date.getDate() + 4 - day)
  const yearStart = new Date(date.getFullYear(), 0, 1)
  const week = Math.ceil((((date - yearStart) / 86400000) + 1) / 7)
  return `${date.getFullYear()}-W${String(week).padStart(2, '0')}`
}

function currentDateInput() {
  return dateInputValue(new Date())
}

function dateInputValue(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function defaultFeedbackSearchRange() {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - 30)
  return {
    start_date: dateInputValue(start),
    end_date: dateInputValue(end),
  }
}

function monthInputValue(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  return `${year}-${month}`
}

function defaultMonthlySearchRange() {
  const end = new Date()
  const start = new Date(end.getFullYear(), end.getMonth() - 2, 1)
  return {
    start_date: monthInputValue(start),
    end_date: monthInputValue(end),
  }
}

function defaultEveningSearchRange() {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - 90)
  return {
    start_date: dateInputValue(start),
    end_date: dateInputValue(end),
    period_type: '',
  }
}

function defaultPeriodValue(type) {
  if (type === 'day') return currentDateInput()
  if (type === 'week') return currentWeek()
  return currentMonth()
}

function periodInputType(type) {
  if (type === 'day') return 'date'
  if (type === 'week') return 'week'
  return 'month'
}

function periodFieldLabel(type) {
  if (type === 'day') return '反馈日期'
  if (type === 'week') return '反馈周次'
  return '反馈月份'
}

function periodTypeLabel(type) {
  return EVENING_PERIOD_TYPES.find((item) => item.value === type)?.label || '按月'
}

function totalPages(total) {
  return Math.max(1, Math.ceil(total / STYLE_EXAMPLE_PAGE_SIZE))
}

function pageItems(items, page) {
  const start = (page - 1) * STYLE_EXAMPLE_PAGE_SIZE
  return items.slice(start, start + STYLE_EXAMPLE_PAGE_SIZE)
}

function clampStyleExamplePages() {
  styleExamplePage.value = Math.min(styleExamplePage.value, styleExampleTotalPages.value)
  feedbackStyleExamplePage.value = Math.min(feedbackStyleExamplePage.value, feedbackStyleExampleTotalPages.value)
}

function setStyleExamplePage(page, target = 'settings') {
  const total = target === 'feedback' ? feedbackStyleExampleTotalPages.value : styleExampleTotalPages.value
  const next = Math.min(Math.max(1, page), total)
  if (target === 'feedback') {
    feedbackStyleExamplePage.value = next
  } else {
    styleExamplePage.value = next
  }
}

function defaultFeedbackPanels() {
  return {
    content: true,
    draft: false,
    final: true,
  }
}

function newMonthlyFeedback() {
  return {
    student_id: '',
    period_type: 'month',
    period_value: currentMonth(),
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

function markApiOnboardingSeen() {
  localStorage.setItem(API_ONBOARDING_SEEN_KEY, '1')
}

function maybeShowApiOnboarding() {
  if (!isAuthed.value || localStorage.getItem(API_ONBOARDING_SEEN_KEY)) return
  showApiOnboarding.value = true
}

function closeApiOnboarding() {
  markApiOnboardingSeen()
  showApiOnboarding.value = false
}

function goToApiSettingsFromOnboarding() {
  markApiOnboardingSeen()
  showApiOnboarding.value = false
  openSettingsPanel('feedback_ai')
  go('#/settings')
}

function toggleSettingsPanel(panel) {
  settingsPanels[panel] = !settingsPanels[panel]
}

function openSettingsPanel(panel) {
  settingsPanels.feedback_ai = panel === 'feedback_ai'
  settingsPanels.style_examples = panel === 'style_examples'
}

function openSettingsGuide() {
  showSettingsGuide.value = true
}

function closeSettingsGuide() {
  localStorage.setItem(SETTINGS_GUIDE_SEEN_KEY, '1')
  showSettingsGuide.value = false
}

function goToFeedbackSettingsFromGuide() {
  localStorage.setItem(SETTINGS_GUIDE_SEEN_KEY, '1')
  showSettingsGuide.value = false
  openSettingsPanel('feedback_ai')
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

function studentDisplayName(fullName = '') {
  const name = fullName.trim()
  if (!name) return name
  if ([...name].every((char) => /[\u4e00-\u9fff]/.test(char))) {
    if (name.length === 2) return name.slice(1)
    if (name.length >= 3) return name.slice(-2)
  }
  return name
}

function lessonDateLabel(lessonTime) {
  const value = new Date(lessonTime)
  if (Number.isNaN(value.getTime())) return ''
  return `${value.getMonth() + 1}.${value.getDate()}`
}

function stripTitleDate(title) {
  return title.trim().replace(/（\d{1,2}\.\d{1,2}）$/, '')
}

function titleForGenerate(title, lessonTime) {
  const date = lessonDateLabel(lessonTime)
  const base = stripTitleDate(title)
  return date ? `${base}（${date}）` : base
}

function defaultStyleExampleTitle() {
  const title = titleForGenerate(feedbackForm.lesson_title, feedbackForm.lesson_time)
  return title || '一对一课后反馈样例'
}

function lessonDateValue(lessonTime) {
  const raw = String(lessonTime || '').replace(' ', 'T')
  return raw.slice(0, 10)
}

function isDateInRange(lessonTime, startDate, endDate) {
  const value = lessonDateValue(lessonTime)
  if (!value) return false
  if (startDate && value < startDate) return false
  if (endDate && value > endDate) return false
  return true
}

function searchRangeLabel(startDate, endDate) {
  if (startDate && endDate) return `${startDate} 至 ${endDate}`
  if (startDate) return `${startDate} 之后`
  if (endDate) return `${endDate} 之前`
  return '全部时间'
}

function resetFeedbackPanels() {
  Object.assign(feedbackPanels, defaultFeedbackPanels())
}

function toggleFeedbackPanel(panel) {
  feedbackPanels[panel] = !feedbackPanels[panel]
  resizeAllTextareas()
  saveFeedbackDraft()
}

function openFeedbackPanel(panel) {
  feedbackPanels[panel] = true
  resizeAllTextareas()
  saveFeedbackDraft()
}

function resizeTextarea(textarea) {
  const scrollContainer = textarea.closest('.modal-panel') || document.scrollingElement
  const scrollTop = scrollContainer?.scrollTop || 0
  textarea.style.height = 'auto'
  textarea.style.height = `${textarea.scrollHeight}px`
  if (scrollContainer) scrollContainer.scrollTop = scrollTop
}

function autoResize(event) {
  const textarea = event?.target
  if (!textarea) return
  resizeTextarea(textarea)
}

async function resizeAllTextareas() {
  await nextTick()
  document.querySelectorAll('textarea.auto-textarea').forEach((textarea) => {
    resizeTextarea(textarea)
  })
}

function assignFeedback(target, source) {
  target.lesson_title = source.lesson_title || ''
  target.lesson_time = source.lesson_time || newFeedback().lesson_time
  target.lesson_summary = source.lesson_summary || ''
  target.performance_summary = source.performance_summary || ''
  target.advice_summary = source.advice_summary || ''
  target.homework_plan = source.homework_plan || ''
  target.ai_draft = source.ai_draft || ''
  target.final_feedback = source.final_feedback || ''
}

function resetFeedbackForm() {
  assignFeedback(feedbackForm, newFeedback())
  Object.assign(legacyQaAnswers, defaultQaAnswers())
  rawLessonNote.value = ''
  hasOrganizedLessonNote.value = false
  rawLessonNoteDirty.value = false
  organizeMissingFields.value = []
  useStyleExamplesForDraft.value = true
  feedbackDraftStatus.value = ''
}

function hasFeedbackDraft(form) {
  return Boolean(
    form.lesson_summary?.trim() ||
      form.performance_summary?.trim() ||
      form.advice_summary?.trim() ||
      form.homework_plan?.trim() ||
      form.ai_draft?.trim() ||
      form.final_feedback?.trim()
  )
}

function currentFeedbackDraftKey() {
  if (!teacher.value?.id || !currentStudent.value?.id) return ''
  return `one_feedback_draft:${teacher.value.id}:${currentStudent.value.id}`
}

function feedbackDraftHasContent(draft) {
  return Boolean(
    hasFeedbackDraft(draft?.feedback || {}) ||
      draft?.raw_lesson_note?.trim() ||
      Object.values(draft?.qa_answers || {}).some((value) => String(value || '').trim())
  )
}

function readFeedbackDraft() {
  const key = currentFeedbackDraftKey()
  if (!key) return null
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function refreshFeedbackDraftState() {
  hasSavedFeedbackDraft.value = feedbackDraftHasContent(readFeedbackDraft())
}

function saveFeedbackDraft() {
  const key = currentFeedbackDraftKey()
  if (!key || !showCreateModal.value) return
  const draft = {
    feedback: { ...feedbackForm },
    feedback_panels: { ...feedbackPanels },
    raw_lesson_note: rawLessonNote.value,
    has_organized_lesson_note: hasOrganizedLessonNote.value,
    raw_lesson_note_dirty: rawLessonNoteDirty.value,
    missing_fields: [...organizeMissingFields.value],
    use_style_examples: useStyleExamplesForDraft.value,
    updated_at: new Date().toISOString(),
  }
  try {
    localStorage.setItem(key, JSON.stringify(draft))
    hasSavedFeedbackDraft.value = feedbackDraftHasContent(draft)
    feedbackDraftStatus.value = '草稿已自动保存'
  } catch {
    feedbackDraftStatus.value = '草稿保存失败，请先复制重要内容'
  }
}

function applyFeedbackDraft(draft) {
  if (!draft?.feedback) return
  assignFeedback(feedbackForm, draft.feedback)
  Object.assign(feedbackPanels, defaultFeedbackPanels(), draft.feedback_panels || {})
  Object.assign(legacyQaAnswers, defaultQaAnswers(), draft.qa_answers || {})
  rawLessonNote.value = draft.raw_lesson_note || ''
  hasOrganizedLessonNote.value = draft.has_organized_lesson_note === true
  rawLessonNoteDirty.value = draft.raw_lesson_note_dirty === true
  if (!rawLessonNote.value && Object.values(legacyQaAnswers).some((value) => String(value || '').trim())) {
    FEEDBACK_CORE_FIELDS.forEach((field) => {
      const legacyKey = field.formField.replace('_summary', '').replace('homework_plan', 'homework')
      const value = legacyQaAnswers[legacyKey]
      if (value && !feedbackForm[field.formField]) feedbackForm[field.formField] = qaAnswerToBullets(value)
    })
  }
  organizeMissingFields.value = Array.isArray(draft.missing_fields) ? draft.missing_fields : []
  useStyleExamplesForDraft.value = draft.use_style_examples !== false
  feedbackDraftStatus.value = '已恢复草稿'
  hasSavedFeedbackDraft.value = true
}

function clearFeedbackDraft() {
  const key = currentFeedbackDraftKey()
  if (!key) return
  localStorage.removeItem(key)
  hasSavedFeedbackDraft.value = false
  feedbackDraftStatus.value = ''
}

function clearCurrentFeedbackDraft() {
  if (!window.confirm('确定清除这名学生的未保存草稿吗？当前表单内容会保留，但刷新后不能再恢复这份草稿。')) return
  clearFeedbackDraft()
  showMessage('草稿已清除')
}

function assignMonthly(target, source) {
  target.student_id = source.student_id || currentEveningStudent.value?.id || ''
  target.period_type = source.period_type || 'month'
  target.period_value = source.period_value || source.feedback_month || defaultPeriodValue(target.period_type)
  target.homework_summary = source.homework_summary || ''
  target.ai_draft = source.ai_draft || ''
  target.final_feedback = source.final_feedback || ''
}

function resetMonthlyForm() {
  assignMonthly(monthlyForm, newMonthlyFeedback())
}

function setEveningFeedbackPeriodType(form, type) {
  form.period_type = type
  form.period_value = defaultPeriodValue(type)
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
    maybeShowApiOnboarding()
  } catch (error) {
    showMessage(error.message || 'AI 处理失败，请检查模型配置后重试')
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
    maybeShowApiOnboarding()
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

async function loadStyleExamples() {
  const data = await request('/settings/style-examples')
  styleExamples.value = data.examples
  clampStyleExamplePages()
}

async function saveAISettings() {
  if (!aiSettingsForm.base_url.trim()) return showMessage('请填写 Base URL')
  if (!aiSettingsForm.model.trim()) return showMessage('请填写模型名')
  loading.value = true
  try {
    const data = await request('/settings/ai', {
      method: 'PUT',
      body: JSON.stringify({
        provider: aiSettingsForm.provider,
        base_url: aiSettingsForm.base_url,
        model: aiSettingsForm.model,
        api_key: aiSettingsForm.api_key,
        clear_api_key: aiSettingsForm.clear_api_key,
      }),
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

async function createStyleExampleFromForm(form, successMessage = '风格样例已保存') {
  if (!form.content.trim()) return showMessage('请粘贴一段反馈样例')
  if (form.enabled && enabledStyleExampleCount.value >= MAX_ENABLED_STYLE_EXAMPLES) {
    return showMessage('最多启用 5 条风格样例参与生成，请先停用一条样例')
  }
  const title = form.title.trim() || (form === inlineStyleExampleForm ? defaultStyleExampleTitle() : '')
  loading.value = true
  try {
    await request('/settings/style-examples', {
      method: 'POST',
      body: JSON.stringify({
        title,
        content: form.content,
        enabled: form.enabled,
      }),
    })
    Object.assign(form, { title: '', content: '', enabled: true })
    await loadStyleExamples()
    showMessage(successMessage)
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function saveStyleExample() {
  await createStyleExampleFromForm(styleExampleForm)
}

async function saveInlineStyleExample() {
  await createStyleExampleFromForm(inlineStyleExampleForm, '风格样例已添加，可继续填写反馈')
}

function assignStyleExampleForm(form, example) {
  form.title = example?.title || ''
  form.content = example?.content || ''
  form.enabled = Boolean(example?.enabled)
}

function openStyleExampleDetail(example) {
  detailStyleExample.value = example
  isEditingStyleExample.value = false
}

function closeStyleExampleDetail() {
  detailStyleExample.value = null
  isEditingStyleExample.value = false
}

function startStyleExampleEdit() {
  assignStyleExampleForm(styleExampleEditForm, detailStyleExample.value)
  isEditingStyleExample.value = true
  resizeAllTextareas()
}

async function saveStyleExampleEdit() {
  if (!styleExampleEditForm.content.trim()) return showMessage('请粘贴一段反馈样例')
  if (
    styleExampleEditForm.enabled &&
    !detailStyleExample.value?.enabled &&
    enabledStyleExampleCount.value >= MAX_ENABLED_STYLE_EXAMPLES
  ) {
    return showMessage('最多启用 5 条风格样例参与生成，请先停用一条样例')
  }
  loading.value = true
  try {
    const data = await request(`/settings/style-examples/${detailStyleExample.value.id}`, {
      method: 'PUT',
      body: JSON.stringify(styleExampleEditForm),
    })
    await loadStyleExamples()
    detailStyleExample.value = data.example
    isEditingStyleExample.value = false
    showMessage('风格样例已更新')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function toggleStyleExample(example) {
  if (!example.enabled && enabledStyleExampleCount.value >= MAX_ENABLED_STYLE_EXAMPLES) {
    return showMessage('最多启用 5 条风格样例参与生成，请先停用一条样例')
  }
  loading.value = true
  try {
    await request(`/settings/style-examples/${example.id}`, {
      method: 'PUT',
      body: JSON.stringify({ ...example, enabled: !example.enabled }),
    })
    await loadStyleExamples()
    if (detailStyleExample.value?.id === example.id) {
      detailStyleExample.value = {
        ...detailStyleExample.value,
        enabled: !example.enabled,
      }
      if (isEditingStyleExample.value) styleExampleEditForm.enabled = !example.enabled
    }
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function deleteStyleExample(example) {
  if (!window.confirm('确定删除这条风格样例吗？')) return
  loading.value = true
  try {
    await request(`/settings/style-examples/${example.id}`, { method: 'DELETE' })
    await loadStyleExamples()
    if (detailStyleExample.value?.id === example.id) closeStyleExampleDetail()
    showMessage('风格样例已删除')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function loadOneStudents() {
  const data = await request('/students')
  oneStudents.value = data.students
}

function feedbackSearchQuery() {
  const params = new URLSearchParams()
  if (feedbackSearchForm.start_date) params.set('start_date', feedbackSearchForm.start_date)
  if (feedbackSearchForm.end_date) params.set('end_date', feedbackSearchForm.end_date)
  const query = params.toString()
  return query ? `/feedbacks?${query}` : '/feedbacks'
}

function eveningFeedbackSearchQuery() {
  const params = new URLSearchParams()
  if (eveningFeedbackSearchForm.start_date) params.set('start_date', eveningFeedbackSearchForm.start_date)
  if (eveningFeedbackSearchForm.end_date) params.set('end_date', eveningFeedbackSearchForm.end_date)
  if (eveningFeedbackSearchForm.period_type) params.set('period_type', eveningFeedbackSearchForm.period_type)
  const query = params.toString()
  return query ? `/evening/feedbacks?${query}` : '/evening/feedbacks'
}

async function loadFeedbackSearchResults() {
  loading.value = true
  try {
    const data = await request(feedbackSearchQuery())
    feedbackSearchResults.value = data.feedbacks
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function resetFeedbackSearch() {
  Object.assign(feedbackSearchForm, defaultFeedbackSearchRange())
  await loadFeedbackSearchResults()
}

async function loadEveningFeedbackSearchResults() {
  loading.value = true
  try {
    const data = await request(eveningFeedbackSearchQuery())
    eveningFeedbackSearchResults.value = data.feedbacks
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function resetEveningFeedbackSearch() {
  Object.assign(eveningFeedbackSearchForm, defaultEveningSearchRange())
  await loadEveningFeedbackSearchResults()
}

function clearStudentHistoryFilter() {
  studentHistoryFilter.start_date = ''
  studentHistoryFilter.end_date = ''
}

async function createOneStudent() {
  if (!oneStudentForm.name.trim()) return showMessage('请填写学生姓名')
  loading.value = true
  try {
    await request('/students', { method: 'POST', body: JSON.stringify({ ...oneStudentForm, note: '' }) })
    Object.assign(oneStudentForm, { name: '', grade: '', subject: '' })
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
  Object.assign(oneStudentForm, {
    name: currentStudent.value?.name || '',
    grade: currentStudent.value?.grade || '',
    subject: currentStudent.value?.subject || '',
  })
  showOneStudentEditModal.value = true
}

async function saveOneStudentEdit() {
  loading.value = true
  try {
    const data = await request(`/students/${currentStudent.value.id}`, {
      method: 'PUT',
      body: JSON.stringify({ ...oneStudentForm, note: '' }),
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

async function openCreateFeedback() {
  resetFeedbackForm()
  resetFeedbackPanels()
  const subject = currentStudent.value?.subject || '课程'
  const displayName = studentDisplayName(currentStudent.value?.name || '学生')
  feedbackForm.lesson_title = `${displayName}第${feedbacks.value.length + 1}次${subject}课`
  try {
    await loadStyleExamples()
  } catch (error) {
    showMessage(error.message)
  }
  const draft = readFeedbackDraft()
  if (feedbackDraftHasContent(draft) && window.confirm('检测到这名学生有未保存草稿，是否恢复？')) {
    applyFeedbackDraft(draft)
  } else {
    refreshFeedbackDraftState()
  }
  showCreateModal.value = true
  resizeAllTextareas()
}

async function openFeedbackStyleModal() {
  showFeedbackStyleModal.value = true
  try {
    await loadStyleExamples()
    await resizeAllTextareas()
  } catch (error) {
    showMessage(error.message)
  }
}

function closeFeedbackStyleModal() {
  showFeedbackStyleModal.value = false
}

function closeCreateFeedback() {
  if ((hasFeedbackDraft(feedbackForm) || rawLessonNote.value.trim()) && !window.confirm('这条反馈还没有保存，确定关闭吗？')) return
  showFeedbackStyleModal.value = false
  showWritingReference.value = false
  showCreateModal.value = false
  resetFeedbackForm()
}

function closeMonthlyModal() {
  if (
    (monthlyForm.homework_summary.trim() || monthlyForm.ai_draft.trim() || monthlyForm.final_feedback.trim()) &&
    !window.confirm('这条晚辅反馈还没有保存，确定关闭吗？')
  ) {
    return
  }
  showMonthlyModal.value = false
  resetMonthlyForm()
}

function normalizeQaAnswer(text) {
  return String(text || '')
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*[-*•]?\s*\d*[.、)]?\s*/, '').trim())
    .filter(Boolean)
}

function qaAnswerToBullets(text) {
  const lines = normalizeQaAnswer(text)
  return lines.map((line) => `- ${line}`).join('\n')
}

function clampWritingReferenceFrame() {
  const minLeft = Math.min(8, WRITING_REFERENCE_VISIBLE_WIDTH - writingReferenceFrame.width)
  const maxLeft = Math.max(8, window.innerWidth - WRITING_REFERENCE_VISIBLE_WIDTH)
  const minTop = Math.min(8, WRITING_REFERENCE_VISIBLE_HEIGHT - writingReferenceFrame.height)
  const maxTop = Math.max(8, window.innerHeight - WRITING_REFERENCE_VISIBLE_HEIGHT)
  writingReferenceFrame.left = Math.min(Math.max(minLeft, writingReferenceFrame.left), maxLeft)
  writingReferenceFrame.top = Math.min(Math.max(minTop, writingReferenceFrame.top), maxTop)
}

function toggleWritingReference() {
  showWritingReference.value = !showWritingReference.value
  if (showWritingReference.value) clampWritingReferenceFrame()
}

function startWritingReferenceMove(event, mode) {
  if (event.button !== undefined && event.button !== 0) return
  writingReferenceDrag.active = true
  writingReferenceDrag.mode = mode
  writingReferenceDrag.startX = event.clientX
  writingReferenceDrag.startY = event.clientY
  writingReferenceDrag.startLeft = writingReferenceFrame.left
  writingReferenceDrag.startTop = writingReferenceFrame.top
  writingReferenceDrag.startWidth = writingReferenceFrame.width
  writingReferenceDrag.startHeight = writingReferenceFrame.height
  window.addEventListener('pointermove', moveWritingReference)
  window.addEventListener('pointerup', stopWritingReferenceMove, { once: true })
}

function moveWritingReference(event) {
  if (!writingReferenceDrag.active) return
  const deltaX = event.clientX - writingReferenceDrag.startX
  const deltaY = event.clientY - writingReferenceDrag.startY
  if (writingReferenceDrag.mode === 'move') {
    writingReferenceFrame.left = writingReferenceDrag.startLeft + deltaX
    writingReferenceFrame.top = writingReferenceDrag.startTop + deltaY
  } else {
    writingReferenceFrame.width = Math.min(window.innerWidth - 16, Math.max(360, writingReferenceDrag.startWidth + deltaX))
    writingReferenceFrame.height = Math.min(window.innerHeight - 16, Math.max(320, writingReferenceDrag.startHeight + deltaY))
  }
  clampWritingReferenceFrame()
}

function stopWritingReferenceMove() {
  writingReferenceDrag.active = false
  window.removeEventListener('pointermove', moveWritingReference)
}

function isFieldMissing(field) {
  return blockingMissingFields.value.includes(field)
}

function fieldSupplementPrompt(field) {
  if (field === 'advice_summary') return '老师希望学生课后怎么做？请写你的真实建议方向。'
  if (field === 'homework_plan') return '本次实际布置了什么任务？没有作业请写“无”或“本次无额外作业”。'
  if (field === 'performance_summary') return '学生这节课表现和掌握情况如何？写状态、做题情况、掌握好的地方或卡住的地方。'
  return '本节课主要学了什么？写知识点、题型、方法或练习内容。'
}

function handleRawLessonNoteInput(event) {
  autoResize(event)
  if (hasOrganizedLessonNote.value) rawLessonNoteDirty.value = true
}

function clearOrganizedMissingField(field) {
  if (!String(feedbackForm[field] || '').trim()) return
  organizeMissingFields.value = organizeMissingFields.value.filter((item) => item !== field)
  saveFeedbackDraft()
}

async function organizeLessonNote() {
  if (!feedbackForm.lesson_title.trim()) return showMessage('请填写反馈标题')
  if (
    !rawLessonNote.value.trim() &&
    !feedbackForm.lesson_summary.trim() &&
    !feedbackForm.performance_summary.trim() &&
    !feedbackForm.advice_summary.trim() &&
    !feedbackForm.homework_plan.trim()
  ) {
    return showMessage('请先写本节课原始记录')
  }
  loading.value = true
  try {
    const data = await request(`/students/${currentStudent.value.id}/feedbacks/organize`, {
      method: 'POST',
      body: JSON.stringify({
        lesson_time: feedbackForm.lesson_time,
        lesson_title: titleForGenerate(feedbackForm.lesson_title, feedbackForm.lesson_time),
        raw_lesson_note: rawLessonNote.value,
        lesson_summary: feedbackForm.lesson_summary,
        performance_summary: feedbackForm.performance_summary,
        advice_summary: feedbackForm.advice_summary,
        homework_plan: feedbackForm.homework_plan,
      }),
    })
    feedbackForm.lesson_summary = data.lesson_summary || ''
    feedbackForm.performance_summary = data.performance_summary || ''
    feedbackForm.advice_summary = data.advice_summary || ''
    feedbackForm.homework_plan = data.homework_plan || ''
    organizeMissingFields.value = Array.isArray(data.missing_fields) ? data.missing_fields : []
    hasOrganizedLessonNote.value = true
    rawLessonNoteDirty.value = false
    openFeedbackPanel('content')
    await resizeAllTextareas()
    saveFeedbackDraft()
    showMessage(organizeMissingFields.value.length ? `还需补充：${missingFieldText.value}` : '课堂记录已整理完整，可以生成反馈')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function generateDraft() {
  if (!feedbackForm.lesson_title.trim()) return showMessage('请填写反馈标题')
  if (!canGenerateFeedback.value) return showMessage(`请先补充：${missingFieldText.value}`)
  const contentPayload = {
    lesson_summary: feedbackForm.lesson_summary,
    performance_summary: feedbackForm.performance_summary,
    advice_summary: feedbackForm.advice_summary,
    homework_plan: feedbackForm.homework_plan,
  }
  loading.value = true
  try {
    const data = await request(`/students/${currentStudent.value.id}/feedbacks/generate`, {
      method: 'POST',
      body: JSON.stringify({
        lesson_time: feedbackForm.lesson_time,
        lesson_title: titleForGenerate(feedbackForm.lesson_title, feedbackForm.lesson_time),
        ...contentPayload,
        use_style_examples: useStyleExamplesForDraft.value,
      }),
    })
    feedbackForm.ai_draft = data.draft
    feedbackForm.final_feedback = data.draft
    feedbackForm.lesson_title = titleForGenerate(feedbackForm.lesson_title, feedbackForm.lesson_time)
    feedbackPanels.final = true
    await resizeAllTextareas()
    saveFeedbackDraft()
    showMessage('反馈已生成，可直接修改或复制')
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
    feedbackForm.lesson_title = titleForGenerate(feedbackForm.lesson_title, feedbackForm.lesson_time)
    await request(`/students/${currentStudent.value.id}/feedbacks`, {
      method: 'POST',
      body: JSON.stringify(feedbackForm),
    })
    clearFeedbackDraft()
    showCreateModal.value = false
    resetFeedbackForm()
    await loadOneStudentContext(true)
    showMessage('反馈已保存')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

function fallbackCopyText(text) {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()
  const copied = document.execCommand('copy')
  document.body.removeChild(textarea)
  return copied
}

async function copyFeedbackText(text) {
  const content = String(text || '').trim()
  if (!content) {
    showMessage('请先生成或填写反馈内容')
    return false
  }
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(content)
    } else if (!fallbackCopyText(content)) {
      throw new Error('copy failed')
    }
    showMessage('最终反馈已复制')
    return true
  } catch {
    if (fallbackCopyText(content)) {
      showMessage('最终反馈已复制')
      return true
    }
    showMessage('复制失败，请手动选择复制')
    return false
  }
}

async function copyFeedbackCard(feedback) {
  const copied = await copyFeedbackText(feedback.final_feedback)
  if (!copied) return
  copiedFeedbackId.value = feedback.id
  window.setTimeout(() => {
    if (copiedFeedbackId.value === feedback.id) copiedFeedbackId.value = null
  }, 1800)
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
    if (currentView.value === 'one-feedback-search') await loadFeedbackSearchResults()
    else await loadOneStudentContext(true)
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
    if (currentView.value === 'one-feedback-search') await loadFeedbackSearchResults()
    else await loadOneStudentContext(true)
    showMessage('反馈已删除')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function addCurrentFeedbackAsStyleExample() {
  if (!detailFeedback.value) return
  const defaultTitle = detailFeedback.value.lesson_title || `${currentStudent.value?.name || '学生'} ${detailFeedback.value.lesson_time}`
  loading.value = true
  try {
    await request('/settings/style-examples/from-feedback', {
      method: 'POST',
      body: JSON.stringify({
        feedback_type: 'one_on_one',
        feedback_id: detailFeedback.value.id,
        title: defaultTitle,
      }),
    })
    await loadStyleExamples()
    showMessage('已设为个人风格样例')
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
  if (!window.confirm('确定删除该晚辅班级吗？班级学生和晚辅反馈也会删除，且无法恢复。')) return
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

async function loadGroupClasses() {
  const data = await request('/group-classes')
  groupClasses.value = data.classes
}

async function loadGroupClassContext() {
  const id = route.value.split('/')[3]
  if (!id) return
  const data = await request(`/group-classes/${id}`)
  currentGroupClass.value = data.class
}

function openGroupClassModal(cls = null) {
  editingGroupClass.value = cls
  groupClassForm.name = cls?.name || ''
  showGroupClassModal.value = true
}

async function saveGroupClass() {
  if (!groupClassForm.name.trim()) return showMessage('请填写班级名称')
  loading.value = true
  try {
    if (editingGroupClass.value) {
      await request(`/group-classes/${editingGroupClass.value.id}`, { method: 'PUT', body: JSON.stringify(groupClassForm) })
    } else {
      await request('/group-classes', { method: 'POST', body: JSON.stringify(groupClassForm) })
    }
    showGroupClassModal.value = false
    await loadGroupClasses()
    if (currentGroupClass.value) await loadGroupClassContext()
    Object.assign(groupClassForm, { name: '' })
    showMessage('班课班级已保存')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function createGroupClassFromList() {
  editingGroupClass.value = null
  await saveGroupClass()
}

async function deleteGroupClass() {
  if (!window.confirm('确定删除该班课班级吗？')) return
  loading.value = true
  try {
    await request(`/group-classes/${currentGroupClass.value.id}`, { method: 'DELETE' })
    showGroupClassModal.value = false
    go('#/group-classes')
    showMessage('班课班级已删除')
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
    request(`/evening/students/${id}/feedbacks`),
  ])
  currentEveningStudent.value = studentData.student
  eveningFeedbacks.value = feedbackData.feedbacks
}

function openEveningStudentEdit() {
  Object.assign(eveningStudentForm, {
    name: currentEveningStudent.value?.name || '',
    grade: currentEveningStudent.value?.grade || '',
    school: currentEveningStudent.value?.school || '',
  })
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
  if (!window.confirm('确定删除该晚辅学生吗？该学生晚辅反馈也会删除，且无法恢复。')) return
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

function openMonthlyModal(student = null) {
  resetMonthlyForm()
  const selectedStudent = student || currentEveningStudent.value || eveningStudents.value[0]
  monthlyForm.student_id = selectedStudent?.id || ''
  showMonthlyModal.value = true
  resizeAllTextareas()
}

async function generateMonthlyDraft() {
  if (!monthlyForm.student_id) return showMessage('请选择晚辅学生')
  if (!monthlyForm.period_value) return showMessage('请选择反馈时间')
  if (!monthlyForm.homework_summary.trim()) return showMessage('请填写作业完成情况简述')
  loading.value = true
  try {
    const classId = currentClass.value?.id || currentEveningStudent.value?.class_id
    const data = await request(`/evening/classes/${classId}/feedbacks/generate`, {
      method: 'POST',
      body: JSON.stringify({
        student_id: Number(monthlyForm.student_id),
        period_type: monthlyForm.period_type,
        period_value: monthlyForm.period_value,
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
  if (!monthlyForm.student_id) return showMessage('请选择晚辅学生')
  if (!monthlyForm.period_value) return showMessage('请选择反馈时间')
  if (!monthlyForm.final_feedback.trim()) return showMessage('请先生成或填写反馈内容')
  loading.value = true
  try {
    const classId = currentClass.value?.id || currentEveningStudent.value?.class_id
    await request(`/evening/classes/${classId}/feedbacks`, {
      method: 'POST',
      body: JSON.stringify({
        ...monthlyForm,
        student_id: Number(monthlyForm.student_id),
      }),
    })
    showMonthlyModal.value = false
    if (currentView.value === 'evening-student') {
      await loadEveningStudentContext()
    } else if (currentView.value === 'evening-class') {
      await loadEveningClassContext()
    }
    showMessage('晚辅反馈已保存')
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
  if (!monthlyEditForm.student_id) return showMessage('请选择晚辅学生')
  if (!monthlyEditForm.period_value) return showMessage('请选择反馈时间')
  loading.value = true
  try {
    const data = await request(`/evening/feedbacks/${eveningDetail.value.id}`, {
      method: 'PUT',
      body: JSON.stringify({
        ...monthlyEditForm,
        student_id: Number(monthlyEditForm.student_id),
      }),
    })
    eveningDetail.value = data.feedback
    isEditingEveningDetail.value = false
    if (currentView.value === 'evening-student') await loadEveningStudentContext()
    if (currentView.value === 'evening-feedback-search') await loadEveningFeedbackSearchResults()
    showMessage('晚辅反馈已更新')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function deleteEveningFeedback() {
  if (!window.confirm('确定删除这条晚辅反馈吗？删除后无法恢复。')) return
  loading.value = true
  try {
    await request(`/evening/feedbacks/${eveningDetail.value.id}`, { method: 'DELETE' })
    eveningDetail.value = null
    if (currentView.value === 'evening-student') await loadEveningStudentContext()
    if (currentView.value === 'evening-feedback-search') await loadEveningFeedbackSearchResults()
    showMessage('晚辅反馈已删除')
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
  currentGroupClass.value = null
  if (!isAuthed.value) return
  try {
    if (currentView.value === 'one-list') await loadOneStudents()
    if (currentView.value === 'one-feedback-search') await loadFeedbackSearchResults()
    if (currentView.value === 'one-student' || currentView.value === 'one-history') await loadOneStudentContext(true)
    if (currentView.value === 'evening-feedback-search') await loadEveningFeedbackSearchResults()
    if (currentView.value === 'group-classes') await loadGroupClasses()
    if (currentView.value === 'group-class') await loadGroupClassContext()
    if (currentView.value === 'evening') await loadEveningClasses()
    if (currentView.value === 'evening-class') await loadEveningClassContext()
    if (currentView.value === 'evening-student') await loadEveningStudentContext()
    if (currentView.value === 'settings') {
      await loadAISettings()
      await loadStyleExamples()
    }
  } catch (error) {
    showMessage(error.message)
    if (currentView.value === 'group-feedback-search') go('#/group-classes')
    else if (currentView.value.toString().startsWith('group')) go('#/group-classes')
    else if (currentView.value.toString().startsWith('evening')) go('#/evening')
    else go('#/one-on-one')
  }
}

window.addEventListener('hashchange', handleRoute)

onMounted(async () => {
  if (!window.location.hash || window.location.hash === '#/students') go('#/one-on-one')
  await loadMe()
  await handleRoute()
  maybeShowApiOnboarding()
})
</script>

<template>
  <main class="page-shell" @click="closeAccountMenu">
    <section v-if="currentView === 'auth'" class="auth-page">
      <div class="auth-illustration">
        <div class="auth-copy">
          <p class="eyebrow">Teacher Assistant</p>
          <h1>教师工作记录助手</h1>
          <p>把一对一课后反馈和晚辅反馈，整理进一个清晰、温暖、好维护的工作台。</p>
          <div class="doodle-row" aria-hidden="true"><span>✎</span><span>▤</span><span>♡</span><span>☆</span></div>
        </div>
        <div class="auth-art-panel" aria-hidden="true">
          <img class="auth-art" :src="authHeroArt" alt="" />
        </div>
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
        <div class="brand"><img class="brand-logo" :src="sidebarLogoArt" alt="" aria-hidden="true" /><strong>教师助手</strong></div>
        <img class="side-doodle-art" :src="sidebarDoodleArt" alt="" aria-hidden="true" />
        <nav class="module-nav" aria-label="业务导航">
          <button class="nav-button" :class="{ active: currentView.startsWith('one') }" @click="go('#/one-on-one')">一对一</button>
          <button class="nav-button" :class="{ active: currentView.startsWith('evening') }" @click="go('#/evening')">晚辅</button>
          <button class="nav-button" :class="{ active: currentView.startsWith('group') }" @click="go('#/group-classes')">班课</button>
        </nav>
        <img class="sidebar-art" :src="sidebarCampusArt" alt="" aria-hidden="true" />
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
          <img class="banner-art" :src="dashboardBannerArt" alt="" aria-hidden="true" />
          <div>
            <p class="eyebrow">{{ currentView === 'settings' ? '设置' : currentView.startsWith('group') ? '班课' : currentView.startsWith('evening') ? '晚辅' : '一对一' }}</p>
            <h2 v-if="currentView === 'one-list'">一对一学生</h2>
            <h2 v-else-if="currentView === 'one-feedback-search'">反馈查询</h2>
            <h2 v-else-if="currentView === 'evening-feedback-search'">晚辅反馈查询</h2>
            <h2 v-else-if="currentView === 'group-feedback-search'">班课反馈查询</h2>
            <h2 v-else-if="currentView === 'settings'">AI 模型配置</h2>
            <h2 v-else-if="currentView === 'group-classes'">班课班级</h2>
            <h2 v-else-if="currentView === 'group-class'">{{ currentGroupClass?.name || '班课班级' }}</h2>
            <h2 v-else-if="currentView === 'evening'">晚辅班级</h2>
            <h2 v-else-if="currentView === 'evening-class'">{{ currentClass?.name || '晚辅班级' }}</h2>
            <h2 v-else-if="currentView === 'evening-student'">{{ currentEveningStudent?.name || '晚辅学生' }}</h2>
            <h2 v-else>{{ currentStudent?.name || '一对一学生' }}</h2>
          </div>
          <button v-if="currentView === 'one-student' || currentView === 'one-history' || currentView === 'one-feedback-search'" class="ghost-btn" @click="go('#/one-on-one')">返回一对一</button>
          <button v-if="currentView === 'group-class' || currentView === 'group-feedback-search'" class="ghost-btn" @click="go('#/group-classes')">返回班课</button>
          <button v-if="currentView === 'evening-class' || currentView === 'evening-feedback-search'" class="ghost-btn" @click="go('#/evening')">返回晚辅</button>
          <button v-if="currentView === 'evening-student'" class="ghost-btn" @click="go(`#/evening/classes/${currentEveningStudent?.class_id}`)">返回班级</button>
          <button v-if="currentView === 'settings'" class="ghost-btn" type="button" @click="openSettingsGuide">设置引导</button>
        </header>

        <section v-if="currentView === 'one-list'" class="dashboard-grid module-home-grid">
          <div class="module-tool-column">
            <form class="paper-card student-form" @submit.prevent="createOneStudent">
              <h3>添加一对一学生</h3>
              <input v-model="oneStudentForm.name" placeholder="学生姓名" />
              <input v-model="oneStudentForm.grade" placeholder="年级，例如 初二" />
              <input v-model="oneStudentForm.subject" placeholder="科目，例如 数学" />
              <button class="primary-btn" :disabled="loading">添加到一对一</button>
            </form>
            <button class="side-tool-card" type="button" @click="go('#/one-on-one/feedbacks')"><strong>反馈查询</strong><small>按时间查看一对一反馈</small><span>查看 →</span></button>
          </div>
          <div class="student-list">
            <article v-for="student in oneStudents" :key="student.id" class="student-card" @click="go(`#/one-on-one/students/${student.id}`)">
              <img class="card-sticker" :src="oneOnOneStickerArt" alt="" aria-hidden="true" />
              <span class="avatar">{{ student.name.slice(0, 1) }}</span>
              <h3>{{ student.name }}</h3>
              <p>{{ student.grade || '未填写年级' }} · {{ student.subject || '未填写科目' }}</p>
              <small>{{ student.feedback_count }} 条一对一记录</small>
            </article>
            <div v-if="oneStudents.length === 0" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>还没有一对一学生。</span></div>
          </div>
        </section>

        <section v-if="currentView === 'one-feedback-search'" class="history-page">
          <form class="paper-card query-panel" @submit.prevent="loadFeedbackSearchResults">
            <div>
              <p class="eyebrow">Feedback Search</p>
              <h3>按时间查找一对一反馈</h3>
              <small>{{ searchRangeLabel(feedbackSearchForm.start_date, feedbackSearchForm.end_date) }} · {{ feedbackSearchResults.length }} 条结果</small>
            </div>
            <label>开始日期<input v-model="feedbackSearchForm.start_date" type="date" /></label>
            <label>结束日期<input v-model="feedbackSearchForm.end_date" type="date" /></label>
            <div class="button-row">
              <button class="primary-btn" :disabled="loading">查询</button>
              <button type="button" class="ghost-btn" :disabled="loading" @click="resetFeedbackSearch">最近 30 天</button>
              <button type="button" class="ghost-btn" :disabled="loading" @click="feedbackSearchForm.start_date = ''; feedbackSearchForm.end_date = ''; loadFeedbackSearchResults()">清空</button>
            </div>
          </form>
          <div class="history-list">
            <article v-for="feedback in feedbackSearchResults" :key="feedback.id" class="history-card feedback-card feedback-search-card">
              <button class="feedback-card-main" type="button" @click="openFeedbackDetail(feedback)">
                <strong>{{ feedback.student_name }} · {{ feedback.lesson_title || feedback.lesson_time }}</strong>
                <span>{{ feedback.lesson_time }} · {{ feedback.grade || '未填年级' }} · {{ feedback.subject || '未填科目' }}</span>
                <small>{{ shortText(feedback.lesson_summary, 72) }}</small>
                <small>{{ shortText(feedback.final_feedback, 130) }}</small>
              </button>
              <button class="copy-feedback-btn" :class="{ copied: copiedFeedbackId === feedback.id }" type="button" title="复制最终反馈" aria-label="复制最终反馈" @click.stop="copyFeedbackCard(feedback)">
                <img class="copy-feedback-icon" :src="copyFeedbackArt" alt="" aria-hidden="true" />
              </button>
            </article>
            <div v-if="!feedbackSearchResults.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>这个时间段暂无一对一反馈。</span></div>
          </div>
        </section>

        <section v-if="currentView === 'evening-feedback-search'" class="history-page">
          <form class="paper-card query-panel" @submit.prevent="loadEveningFeedbackSearchResults">
            <div>
              <p class="eyebrow">Evening Search</p>
              <h3>按时间查找晚辅反馈</h3>
              <small>{{ searchRangeLabel(eveningFeedbackSearchForm.start_date, eveningFeedbackSearchForm.end_date) }} · {{ eveningFeedbackSearchResults.length }} 条结果</small>
            </div>
            <label>反馈类型<select v-model="eveningFeedbackSearchForm.period_type"><option value="">全部</option><option v-for="type in EVENING_PERIOD_TYPES" :key="type.value" :value="type.value">{{ type.label }}</option></select></label>
            <label>开始日期<input v-model="eveningFeedbackSearchForm.start_date" type="date" /></label>
            <label>结束日期<input v-model="eveningFeedbackSearchForm.end_date" type="date" /></label>
            <div class="button-row">
              <button class="primary-btn" :disabled="loading">查询</button>
              <button type="button" class="ghost-btn" :disabled="loading" @click="resetEveningFeedbackSearch">最近 90 天</button>
              <button type="button" class="ghost-btn" :disabled="loading" @click="eveningFeedbackSearchForm.start_date = ''; eveningFeedbackSearchForm.end_date = ''; eveningFeedbackSearchForm.period_type = ''; loadEveningFeedbackSearchResults()">清空</button>
            </div>
          </form>
          <div class="history-list">
            <button v-for="feedback in eveningFeedbackSearchResults" :key="feedback.id" class="history-card" type="button" @click="openEveningDetail(feedback)">
              <strong>{{ feedback.student_name }} · {{ feedback.period_label }}</strong>
              <span>{{ periodTypeLabel(feedback.period_type) }} · {{ feedback.class_name }} · {{ feedback.grade || '未填年级' }} · {{ feedback.school || '未填学校' }}</span>
              <small>{{ shortText(feedback.homework_summary, 86) }}</small>
              <small>{{ shortText(feedback.final_feedback, 130) }}</small>
            </button>
            <div v-if="!eveningFeedbackSearchResults.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>这个时间段暂无晚辅反馈。</span></div>
          </div>
        </section>

        <section v-if="currentView === 'group-feedback-search'" class="history-page">
          <div class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>班课反馈功能后续补充，当前暂无可查询反馈。</span></div>
        </section>

        <section v-if="currentView === 'one-student' && currentStudent" class="student-home">
          <div class="paper-card profile-card">
            <h3>{{ currentStudent.name }}</h3>
            <p>{{ currentStudent.grade || '未填写年级' }} · {{ currentStudent.subject || '未填写科目' }}</p>
            <div class="button-row"><button class="ghost-btn" @click="openOneStudentEdit">编辑学生信息</button></div>
          </div>
          <div class="action-grid">
            <button class="action-card" type="button" @click="openCreateFeedback"><img class="action-illustration" :src="createFeedbackArt" alt="" aria-hidden="true" /><strong>新增课后反馈</strong><small>记录本次课程，生成并修改反馈正文</small></button>
            <button class="action-card" type="button" @click="go(`#/one-on-one/students/${currentStudent.id}/history`)"><img class="action-illustration" :src="historyFeedbackArt" alt="" aria-hidden="true" /><strong>查看历史反馈</strong><small>共 {{ feedbacks.length }} 条记录</small></button>
          </div>
          <article v-if="feedbacks[0]" class="history-card feedback-card recent-card">
            <button class="feedback-card-main" type="button" @click="openFeedbackDetail(feedbacks[0])"><p class="eyebrow">最近一次反馈</p><h3>{{ feedbacks[0].lesson_time }}</h3><p>{{ shortText(feedbacks[0].final_feedback, 120) }}</p></button>
            <button class="copy-feedback-btn" :class="{ copied: copiedFeedbackId === feedbacks[0].id }" type="button" title="复制最终反馈" aria-label="复制最终反馈" @click.stop="copyFeedbackCard(feedbacks[0])">
              <img class="copy-feedback-icon" :src="copyFeedbackArt" alt="" aria-hidden="true" />
            </button>
          </article>
        </section>

        <section v-if="currentView === 'one-history' && currentStudent" class="history-page">
          <div class="history-header"><div><p class="eyebrow">一对一历史反馈</p><h3>{{ currentStudent.name }} 的记录</h3></div><button class="primary-btn" @click="openCreateFeedback">新增反馈</button></div>
          <form class="paper-card query-panel student-history-filter" @submit.prevent>
            <div>
              <p class="eyebrow">Time Filter</p>
              <h3>按时间筛选</h3>
              <small>{{ searchRangeLabel(studentHistoryFilter.start_date, studentHistoryFilter.end_date) }} · {{ filteredStudentFeedbacks.length }} / {{ feedbacks.length }} 条</small>
            </div>
            <label>开始日期<input v-model="studentHistoryFilter.start_date" type="date" /></label>
            <label>结束日期<input v-model="studentHistoryFilter.end_date" type="date" /></label>
            <button type="button" class="ghost-btn" @click="clearStudentHistoryFilter">清空</button>
          </form>
          <div class="history-list">
            <article v-for="feedback in filteredStudentFeedbacks" :key="feedback.id" class="history-card feedback-card">
              <button class="feedback-card-main" type="button" @click="openFeedbackDetail(feedback)"><strong>{{ feedback.lesson_title || feedback.lesson_time }}</strong><span>{{ shortText(feedback.lesson_summary, 64) }}</span><small>{{ shortText(feedback.final_feedback, 110) }}</small></button>
              <button class="copy-feedback-btn" :class="{ copied: copiedFeedbackId === feedback.id }" type="button" title="复制最终反馈" aria-label="复制最终反馈" @click.stop="copyFeedbackCard(feedback)">
                <img class="copy-feedback-icon" :src="copyFeedbackArt" alt="" aria-hidden="true" />
              </button>
            </article>
            <div v-if="!feedbacks.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>暂无反馈记录。</span></div>
            <div v-else-if="!filteredStudentFeedbacks.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>该时间段暂无反馈记录。</span></div>
          </div>
        </section>

        <section v-if="currentView === 'group-classes'" class="dashboard-grid module-home-grid">
          <div class="module-tool-column">
            <form class="paper-card student-form" @submit.prevent="createGroupClassFromList">
              <h3>新建班课班级</h3>
              <input v-model="groupClassForm.name" placeholder="班级名称，例如 初三数学" />
              <button class="primary-btn" :disabled="loading">新建班级</button>
            </form>
            <button class="side-tool-card" type="button" @click="go('#/group-classes/feedbacks')"><strong>反馈查询</strong><small>班课反馈功能后续补充</small><span>查看 →</span></button>
          </div>
          <div class="student-list">
            <article v-for="cls in groupClasses" :key="cls.id" class="student-card" @click="go(`#/group-classes/classes/${cls.id}`)">
              <img class="card-sticker" :src="eveningStickerArt" alt="" aria-hidden="true" />
              <span class="avatar">课</span>
              <h3>{{ cls.name }}</h3>
              <small>班课班级</small>
            </article>
            <div v-if="!groupClasses.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>还没有班课班级。</span></div>
          </div>
        </section>

        <section v-if="currentView === 'group-class' && currentGroupClass" class="student-home">
          <div class="paper-card profile-card">
            <h3>{{ currentGroupClass.name }}</h3><small>班课班级</small>
            <div class="button-row"><button class="ghost-btn" @click="openGroupClassModal(currentGroupClass)">编辑班级</button><button class="danger-btn" @click="deleteGroupClass">删除班级</button></div>
          </div>
          <div class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>班课学生和反馈功能后续补充。</span></div>
        </section>

        <section v-if="currentView === 'evening'" class="dashboard-grid module-home-grid">
          <div class="module-tool-column">
            <form class="paper-card student-form" @submit.prevent="createClassFromList">
              <h3>新建晚辅班级</h3>
              <input v-model="classForm.name" placeholder="班级名称，例如 初三晚辅" />
              <button class="primary-btn" :disabled="loading">新建班级</button>
            </form>
            <button class="side-tool-card" type="button" @click="go('#/evening/feedbacks')"><strong>反馈查询</strong><small>按时间查看晚辅反馈</small><span>查看 →</span></button>
          </div>
          <div class="student-list">
            <article v-for="cls in eveningClasses" :key="cls.id" class="student-card" @click="go(`#/evening/classes/${cls.id}`)">
              <img class="card-sticker" :src="eveningStickerArt" alt="" aria-hidden="true" />
              <span class="avatar">班</span>
              <h3>{{ cls.name }}</h3>
              <small>{{ cls.student_count }} 名学生</small>
            </article>
            <div v-if="!eveningClasses.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>还没有晚辅班级。</span></div>
          </div>
        </section>

        <section v-if="currentView === 'evening-class' && currentClass" class="student-home">
          <div class="paper-card profile-card">
            <h3>{{ currentClass.name }}</h3><small>{{ eveningStudents.length }} 名学生</small>
            <div class="button-row"><button class="ghost-btn" @click="openClassModal(currentClass)">编辑班级</button><button class="danger-btn" @click="deleteClass">删除班级</button></div>
          </div>
          <div class="button-row"><button class="primary-btn" @click="openMonthlyModal()">新增晚辅反馈</button><button class="ghost-btn" @click="showBulkModal = true; resizeAllTextareas()">批量录入学生</button></div>
          <div class="student-list">
            <article v-for="student in eveningStudents" :key="student.id" class="student-card" @click="go(`#/evening/students/${student.id}`)">
              <img class="card-sticker" :src="eveningStickerArt" alt="" aria-hidden="true" />
              <span class="avatar">{{ student.name.slice(0, 1) }}</span><h3>{{ student.name }}</h3>
              <p>{{ student.grade || '未填年级' }} · {{ student.school || '未填学校' }}</p><small>{{ student.feedback_count }} 条晚辅反馈</small>
            </article>
            <div v-if="!eveningStudents.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>这个班级还没有学生。</span></div>
          </div>
        </section>

        <section v-if="currentView === 'evening-student' && currentEveningStudent" class="history-page">
          <div class="paper-card profile-card">
            <h3>{{ currentEveningStudent.name }}</h3><p>{{ currentEveningStudent.grade || '未填年级' }} · {{ currentEveningStudent.school || '未填学校' }}</p>
            <div class="button-row"><button class="ghost-btn" @click="openEveningStudentEdit">编辑学生信息</button><button class="primary-btn" @click="openMonthlyModal(currentEveningStudent)">新增晚辅反馈</button></div>
          </div>
          <div class="history-list">
            <button v-for="feedback in eveningFeedbacks" :key="feedback.id" class="history-card" @click="openEveningDetail(feedback)">
              <strong>{{ feedback.period_label }}</strong><span>{{ periodTypeLabel(feedback.period_type) }} · {{ shortText(feedback.homework_summary, 72) }}</span><small>{{ shortText(feedback.final_feedback, 120) }}</small>
            </button>
            <div v-if="!eveningFeedbacks.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>暂无晚辅反馈。</span></div>
          </div>
        </section>

        <section v-if="currentView === 'settings'" class="settings-page">
          <form class="paper-card settings-card" :class="{ collapsed: !settingsPanels.feedback_ai }" @submit.prevent="saveAISettings">
            <button class="settings-accordion-header" type="button" @click="toggleSettingsPanel('feedback_ai')">
              <span>
                <span class="eyebrow">Feedback Model</span>
                <strong>反馈生成模型配置</strong>
                <small>用于根据课堂内容、表现、建议和作业生成课后反馈初稿。</small>
              </span>
              <span class="settings-header-side">
                <span class="settings-pill" :class="{ ok: aiSettings?.has_api_key }">{{ aiSettings?.has_api_key ? `已配置：${aiSettings.model}` : '必配 · 未配置' }}</span>
                <span class="settings-caret">{{ settingsPanels.feedback_ai ? '收起' : '展开' }}</span>
              </span>
            </button>

            <div v-show="settingsPanels.feedback_ai" class="settings-panel-body">
              <p class="settings-hint">反馈生成模型主要负责把老师填写的课堂事实整理成可以发给家长的课后反馈。API Key 会加密保存在本地数据库里，不会显示明文。</p>

              <label>推荐模型
                <select v-model="aiSettingsForm.provider" @change="applyAIPreset">
                  <option v-for="(preset, key) in AI_PRESETS" :key="key" :value="key">{{ preset.label }}</option>
                </select>
                <small>{{ selectedAIPreset.hint }}</small>
              </label>
              <div class="preset-link-row">
                <a v-if="selectedAIPreset.api_key_url" :href="selectedAIPreset.api_key_url" target="_blank" rel="noreferrer">获取 API Key</a>
                <a v-if="selectedAIPreset.docs_url" :href="selectedAIPreset.docs_url" target="_blank" rel="noreferrer">查看接入文档</a>
              </div>

              <label>Base URL
                <input v-model="aiSettingsForm.base_url" placeholder="https://api.deepseek.com" />
                <small>模型平台的 OpenAI-compatible 接口地址。</small>
              </label>

              <label>模型名
                <input v-model="aiSettingsForm.model" placeholder="deepseek-v4-flash" />
                <small>示例：deepseek-v4-flash、qwen3.6-plus、kimi-k2.6、glm-4-flash-250414。</small>
              </label>

              <label>API Key
                <input v-model="aiSettingsForm.api_key" type="password" :placeholder="aiSettings?.has_api_key ? '已配置，留空则保留原 Key' : '粘贴你的 API Key'" autocomplete="off" />
                <small>{{ aiSettings?.has_api_key ? '当前账号已有 API Key。填写新 Key 会覆盖旧 Key。' : '还没有保存 API Key，生成反馈前需要先配置。' }}</small>
              </label>

              <div class="button-row danger-row">
                <div class="button-row">
                  <button type="button" class="ghost-btn" :disabled="loading" @click="testAISettings">测试连接</button>
                  <button class="primary-btn" :disabled="loading">保存反馈生成配置</button>
                </div>
                <button type="button" class="danger-btn" :disabled="loading || !aiSettings?.has_api_key" @click="clearAIKey">清除 API Key</button>
              </div>
            </div>
          </form>

          <form class="paper-card settings-card" :class="{ collapsed: !settingsPanels.style_examples }" @submit.prevent="saveStyleExample">
            <button class="settings-accordion-header" type="button" @click="toggleSettingsPanel('style_examples')">
              <span>
                <span class="eyebrow">Writing Style</span>
                <strong>个人反馈风格样例</strong>
                <small>可选配置，让生成出来的反馈更像你平时写给家长的表达。</small>
              </span>
              <span class="settings-header-side">
                <span class="settings-pill" :class="{ ok: enabledStyleExampleCount }">{{ styleExamples.length ? `${enabledStyleExampleCount} / ${MAX_ENABLED_STYLE_EXAMPLES} 启用 · ${styleExamples.length} 条` : '可选 · 暂无样例' }}</span>
                <span class="settings-caret">{{ settingsPanels.style_examples ? '收起' : '展开' }}</span>
              </span>
            </button>

            <div v-show="settingsPanels.style_examples" class="settings-panel-body">
              <p class="settings-hint">个人风格样例用于告诉 AI 你平时怎么写反馈。没有启用样例时，课后反馈会按标准四段结构输出；启用样例后，AI 会学习样例的语气、排版和详略，但不会复用样例里的学生事实。添加是保存样例，启用才会参与生成，最多启用 {{ MAX_ENABLED_STYLE_EXAMPLES }} 条。</p>

              <label>样例标题
                <input v-model="styleExampleForm.title" placeholder="例如：小明第3次数学课（5.12）" />
                <small>建议用“学生 + 第几次 + 科目 + 日期”，方便以后在样例库里找到对应课程。标题仅用于管理，AI 主要学习下方反馈正文。</small>
              </label>

              <label>反馈样例
                <textarea v-model="styleExampleForm.content" class="auto-textarea final-text" placeholder="粘贴一段你写过的完整反馈" @input="autoResize"></textarea>
                <small>AI 只学习这里的正文内容。若希望 AI 学习你的标题格式，请把标题行也一起粘贴到这里。</small>
              </label>

              <label class="check-row">
                <input v-model="styleExampleForm.enabled" type="checkbox" />
                <span>保存后立即启用，参与后续反馈生成</span>
              </label>

              <div class="button-row">
                <button class="primary-btn" :disabled="loading">保存风格样例</button>
              </div>

              <div class="style-example-list">
                <article v-for="example in paginatedStyleExamples" :key="example.id" class="style-example-item" role="button" tabindex="0" @click="openStyleExampleDetail(example)" @keydown.enter.prevent="openStyleExampleDetail(example)">
                  <div>
                    <strong>{{ example.title || '未命名样例' }}</strong>
                    <small>{{ example.enabled ? '生成时参考' : '已停用' }} · {{ shortText(example.content, 88) }}</small>
                  </div>
                  <div class="button-row">
                    <button type="button" class="ghost-btn" :disabled="loading" @click.stop="toggleStyleExample(example)">{{ example.enabled ? '停用' : '启用' }}</button>
                    <button type="button" class="danger-btn" :disabled="loading" @click.stop="deleteStyleExample(example)">删除</button>
                  </div>
                </article>
                <p v-if="!styleExamples.length" class="settings-hint">还没有风格样例。</p>
                <div v-if="styleExamples.length > STYLE_EXAMPLE_PAGE_SIZE" class="pagination-row">
                  <button type="button" class="ghost-btn" :disabled="styleExamplePage <= 1" @click="setStyleExamplePage(styleExamplePage - 1)">上一页</button>
                  <span>第 {{ styleExamplePage }} / {{ styleExampleTotalPages }} 页</span>
                  <button type="button" class="ghost-btn" :disabled="styleExamplePage >= styleExampleTotalPages" @click="setStyleExamplePage(styleExamplePage + 1)">下一页</button>
                </div>
              </div>
            </div>
          </form>
        </section>
      </section>
    </section>

    <div v-if="showApiOnboarding" class="modal-mask">
      <article class="paper-card modal-panel onboarding-panel">
        <div class="modal-title">
          <div>
            <p class="eyebrow">开始使用 AI 前</p>
            <h3>先配置你的模型 API</h3>
          </div>
          <button type="button" class="icon-btn" @click="closeApiOnboarding">×</button>
        </div>
        <p class="settings-hint">老师要使用课堂记录整理和反馈生成，需要先到设置页填写自己的模型 API Key。配置只保存在当前老师账号下，API Key 会加密保存。</p>
        <div class="guide-step-list">
          <article>
            <strong>1. 反馈生成模型是必配项</strong>
            <span>它负责把老师的原始课堂记录整理成四大板块，并生成课后反馈正文。</span>
          </article>
          <article>
            <strong>2. 个人风格样例可稍后补充</strong>
            <span>没有启用样例时按标准四段结构生成；启用样例后，AI 会更贴近你的表达习惯。</span>
          </article>
        </div>
        <div class="button-row danger-row">
          <button type="button" class="primary-btn" @click="goToApiSettingsFromOnboarding">去设置 API</button>
          <button type="button" class="ghost-btn" @click="closeApiOnboarding">知道了，稍后再说</button>
        </div>
      </article>
    </div>

    <div v-if="detailStyleExample" class="modal-mask style-example-detail-mask">
      <article class="paper-card modal-panel feedback-detail-modal style-example-detail-modal">
        <div class="modal-title">
          <div>
            <p class="eyebrow">个人风格样例</p>
            <h3>{{ detailStyleExample.title || '未命名样例' }}</h3>
          </div>
          <button type="button" class="icon-btn" @click="closeStyleExampleDetail">×</button>
        </div>

        <template v-if="!isEditingStyleExample">
          <div class="style-example-meta-row">
            <span :class="{ active: detailStyleExample.enabled }">{{ detailStyleExample.enabled ? '生成时参考' : '已停用' }}</span>
            <small>{{ detailStyleExample.source_type === 'manual' ? '手动添加' : '来自已保存反馈' }} · {{ detailStyleExample.updated_at || detailStyleExample.created_at }}</small>
          </div>
          <pre>{{ detailStyleExample.content }}</pre>
          <div class="button-row danger-row">
            <div class="button-row">
              <button type="button" class="ghost-btn" :disabled="loading" @click="startStyleExampleEdit">编辑样例</button>
              <button type="button" class="ghost-btn" :disabled="loading" @click="toggleStyleExample(detailStyleExample)">{{ detailStyleExample.enabled ? '停用' : '启用' }}</button>
            </div>
            <button type="button" class="danger-btn" :disabled="loading" @click="deleteStyleExample(detailStyleExample)">删除样例</button>
          </div>
        </template>

        <form v-else class="feedback-editor" @submit.prevent="saveStyleExampleEdit">
          <label>样例标题
            <input v-model="styleExampleEditForm.title" placeholder="例如：某学生第3次数学课（4.26）" />
            <small>标题只用于管理样例，不参与 AI 学习。</small>
          </label>
          <label>反馈样例
            <textarea v-model="styleExampleEditForm.content" class="auto-textarea final-text" @input="autoResize"></textarea>
            <small>AI 只学习这里的正文内容。若希望 AI 学习你的标题格式，请把标题行也一起粘贴到这里。</small>
          </label>
          <label class="check-row">
            <input v-model="styleExampleEditForm.enabled" type="checkbox" />
            <span>启用后参与后续反馈生成</span>
          </label>
          <div class="button-row">
            <button class="primary-btn" :disabled="loading">保存修改</button>
            <button type="button" class="ghost-btn" :disabled="loading" @click="isEditingStyleExample = false">取消</button>
          </div>
        </form>
      </article>
    </div>

    <div v-if="showSettingsGuide" class="modal-mask">
      <article class="paper-card modal-panel settings-guide-panel">
        <div class="modal-title">
          <div>
            <p class="eyebrow">设置引导</p>
            <h3>这三个设置分别做什么</h3>
          </div>
          <button type="button" class="icon-btn" @click="closeSettingsGuide">×</button>
        </div>
        <div class="guide-step-list">
          <article>
            <strong>1. 先配置反馈生成模型</strong>
            <span>这是整理课堂记录和生成课后反馈的核心配置。优先完成它，后面就能在学生页面生成反馈。</span>
          </article>
          <article>
            <strong>2. 可选配置个人风格样例</strong>
            <span>添加是保存样例，启用才会参与生成。没有启用样例时，反馈会按标准四段结构输出。</span>
          </article>
        </div>
        <div class="button-row danger-row">
          <button type="button" class="primary-btn" @click="goToFeedbackSettingsFromGuide">去配置反馈生成模型</button>
          <button type="button" class="ghost-btn" @click="closeSettingsGuide">知道了</button>
        </div>
      </article>
    </div>

    <div v-if="showCreateModal" class="modal-mask">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveFeedback" @input="saveFeedbackDraft" @change="saveFeedbackDraft">
        <div class="modal-title">
          <div>
            <h3>新增课后反馈</h3>
            <small class="draft-status">{{ feedbackDraftStatus || '草稿自动保存中' }}</small>
          </div>
          <div class="button-row">
            <button v-if="hasSavedFeedbackDraft" type="button" class="ghost-btn" @click="clearCurrentFeedbackDraft">清除草稿</button>
            <button type="button" class="icon-btn" @click="closeCreateFeedback">×</button>
          </div>
        </div>
        <label>上课时间<input v-model="feedbackForm.lesson_time" type="datetime-local" /></label>
        <label>反馈标题<input v-model="feedbackForm.lesson_title" placeholder="例如：小明第3次数学课，生成时会自动补上（5.5）" /></label>
        <section class="feedback-style-entry">
          <div>
            <strong>个人风格</strong>
            <small>{{ styleGenerationStatus }}</small>
          </div>
          <div class="button-row">
            <button v-if="enabledStyleExampleCount" type="button" class="ghost-btn" :disabled="loading" @click="useStyleExamplesForDraft = !useStyleExamplesForDraft; saveFeedbackDraft()">{{ useStyleExamplesForDraft ? '本次不用个人风格' : '使用个人风格' }}</button>
            <button type="button" class="ghost-btn" :disabled="loading" @click="openFeedbackStyleModal">{{ styleExamples.length ? '管理个人风格' : '个人风格' }}</button>
          </div>
        </section>
        <section class="feedback-panel classroom-content-panel" :class="{ collapsed: !feedbackPanels.content }">
          <div class="feedback-panel-header feedback-panel-header-actions">
            <button class="feedback-panel-toggle" type="button" @click="toggleFeedbackPanel('content')"><strong>课堂记录整理</strong><span>{{ feedbackPanels.content ? '收起' : '展开' }}</span></button>
            <button type="button" class="ghost-btn reference-toggle-btn" @click="toggleWritingReference">{{ showWritingReference ? '收起参考' : '填写参考' }}</button>
          </div>
          <div v-show="feedbackPanels.content" class="feedback-panel-body">
            <div class="qa-mode-panel quick-note-panel">
              <label class="qa-question">
                <span>本节课原始记录</span>
                <small>随便写：讲了什么、学生表现、哪里需要注意、布置了什么作业。建议和作业最好分开写，例如“建议：……；作业：……”。AI 会先整理分类，不会直接生成最终反馈。</small>
                <textarea v-model="rawLessonNote" class="auto-textarea large-text" placeholder="例如：今天讲了一次函数图像和解析式，图像题还可以，应用题找等量关系有点卡。建议：回去复盘今天错题。作业：完成讲义 3-5 题。" @input="handleRawLessonNoteInput"></textarea>
              </label>
              <p v-if="hasOrganizedLessonNote && rawLessonNoteDirty" class="settings-warning">原始记录已修改，建议重新整理后再生成。</p>
              <div v-if="hasOrganizedLessonNote" class="organized-field-grid">
                <label v-for="field in FEEDBACK_CORE_FIELDS" :key="field.formField" :class="{ 'field-missing': isFieldMissing(field.formField) }">
                  <span>{{ field.title }}</span>
                  <small v-if="isFieldMissing(field.formField)">{{ fieldSupplementPrompt(field.formField) }}</small>
                  <textarea v-model="feedbackForm[field.formField]" class="auto-textarea" :placeholder="field.placeholder" @input="autoResize($event); clearOrganizedMissingField(field.formField)"></textarea>
                </label>
              </div>
              <p v-if="hasOrganizedLessonNote && blockingMissingFields.length" class="settings-warning">还需补充：{{ missingFieldText }}。四大板块齐全后才能生成反馈。</p>
              <p v-if="hasOrganizedLessonNote && canGenerateFeedback" class="settings-hint">四大板块已整理完整，请确认内容无误后生成反馈。</p>
              <div class="button-row classroom-generate-row danger-row">
                <button type="button" class="ghost-btn" :disabled="loading" @click="organizeLessonNote">{{ hasOrganizedLessonNote ? '重新整理' : '整理课堂记录' }}</button>
                <button v-if="hasOrganizedLessonNote" type="button" class="primary-btn" :disabled="loading || !canGenerateFeedback" @click="generateDraft">生成反馈</button>
              </div>
            </div>
          </div>
        </section>

        <section class="feedback-panel" :class="{ collapsed: !feedbackPanels.draft }">
          <button class="feedback-panel-header" type="button" @click="toggleFeedbackPanel('draft')"><strong>查看 AI 初稿</strong><span>{{ feedbackPanels.draft ? '收起' : '展开' }}</span></button>
          <label v-show="feedbackPanels.draft"><textarea v-model="feedbackForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label>
        </section>

        <section class="feedback-panel" :class="{ collapsed: !feedbackPanels.final }">
          <button class="feedback-panel-header" type="button" @click="toggleFeedbackPanel('final')"><strong>最终反馈</strong><span>{{ feedbackPanels.final ? '收起' : '展开' }}</span></button>
          <label v-show="feedbackPanels.final"><textarea v-model="feedbackForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
        </section>

        <div class="button-row feedback-action-row"><button type="button" class="ghost-btn" :disabled="loading" @click="copyFeedbackText(feedbackForm.final_feedback)">复制最终反馈</button><button class="primary-btn" :disabled="loading">保存最终反馈</button></div>
	      </form>

      <div v-if="showWritingReference" class="nested-modal-mask transparent-mask writing-reference-mask">
        <aside class="paper-card modal-panel writing-reference-floating-modal" :style="writingReferenceStyle" aria-label="课堂记录填写参考">
          <div class="modal-title draggable-title" @pointerdown="startWritingReferenceMove($event, 'move')">
            <div>
              <h3>参考示例</h3>
              <small>可拖动、调整大小，也可以放到边角对照填写。</small>
            </div>
            <button type="button" class="icon-btn" @pointerdown.stop @click="showWritingReference = false">×</button>
          </div>
          <div class="writing-reference-body">
            <section v-for="item in WRITING_REFERENCE_SECTIONS" :key="item.title" class="writing-reference-section">
              <strong>{{ item.title }}</strong>
              <p>填写什么：{{ item.guide }}</p>
              <span>{{ item.sample }}</span>
            </section>
          </div>
          <button class="resize-handle" type="button" aria-label="调整参考示例浮窗大小" @pointerdown="startWritingReferenceMove($event, 'resize')"></button>
        </aside>
      </div>

      <div v-if="showFeedbackStyleModal" class="nested-modal-mask">
        <article class="paper-card modal-panel feedback-style-modal">
          <div class="modal-title">
            <div>
              <h3>个人风格</h3>
              <small>{{ styleGenerationStatus }}</small>
            </div>
            <button type="button" class="icon-btn" @click="closeFeedbackStyleModal">×</button>
          </div>

          <p class="guide-hint">未启用样例时，AI 会按标准四段结构输出：课堂学习内容、课堂表现与知识掌握情况、课后建议、作业安排。启用样例后，AI 会学习你的语气、排版、段落详略和表达习惯，但不会复用样例里的学生事实。</p>

          <div class="style-status-row">
            <strong>{{ styleGenerationStatus }}</strong>
            <small>样例库可保存多条，最多启用 {{ MAX_ENABLED_STYLE_EXAMPLES }} 条参与生成。</small>
          </div>

          <section class="inline-style-form">
            <strong>快捷添加样例</strong>
            <label>样例标题
              <input v-model="inlineStyleExampleForm.title" :placeholder="`例如：${defaultStyleExampleTitle()}`" />
              <small>建议用“学生 + 第几次 + 科目 + 日期”。留空时会用当前反馈标题，标题仅用于管理样例。</small>
            </label>
            <label>反馈样例
              <textarea v-model="inlineStyleExampleForm.content" class="auto-textarea large-text" placeholder="粘贴一段你写过的完整反馈" @input="autoResize"></textarea>
              <small>AI 只学习这里的正文内容。若希望 AI 学习你的标题格式，请把标题行也一起粘贴到这里。</small>
            </label>
            <label class="check-row">
              <input v-model="inlineStyleExampleForm.enabled" type="checkbox" />
              <span>添加后立即启用，参与本次生成</span>
            </label>
            <div class="button-row">
              <button type="button" class="primary-btn" :disabled="loading" @click="saveInlineStyleExample">添加风格样例</button>
            </div>
          </section>

          <section class="style-library-panel">
            <div class="style-library-header">
              <strong>样例库</strong>
              <small>{{ styleExamples.length ? `${styleExamples.length} 条样例` : '暂无样例' }}</small>
            </div>
            <div class="style-example-list">
              <article v-for="example in paginatedFeedbackStyleExamples" :key="example.id" class="style-example-item" role="button" tabindex="0" @click="openStyleExampleDetail(example)" @keydown.enter.prevent="openStyleExampleDetail(example)">
                <div>
                  <strong>{{ example.title || '未命名样例' }}</strong>
                  <small>{{ example.enabled ? '生成时参考' : '已停用' }} · {{ shortText(example.content, 88) }}</small>
                </div>
                <div class="button-row">
                  <button type="button" class="ghost-btn" :disabled="loading" @click.stop="toggleStyleExample(example)">{{ example.enabled ? '停用' : '启用' }}</button>
                  <button type="button" class="danger-btn" :disabled="loading" @click.stop="deleteStyleExample(example)">删除</button>
                </div>
              </article>
              <p v-if="!styleExamples.length" class="settings-hint">还没有风格样例，可以先在上方粘贴一段自己的反馈。</p>
              <div v-if="styleExamples.length > STYLE_EXAMPLE_PAGE_SIZE" class="pagination-row">
                <button type="button" class="ghost-btn" :disabled="feedbackStyleExamplePage <= 1" @click="setStyleExamplePage(feedbackStyleExamplePage - 1, 'feedback')">上一页</button>
                <span>第 {{ feedbackStyleExamplePage }} / {{ feedbackStyleExampleTotalPages }} 页</span>
                <button type="button" class="ghost-btn" :disabled="feedbackStyleExamplePage >= feedbackStyleExampleTotalPages" @click="setStyleExamplePage(feedbackStyleExamplePage + 1, 'feedback')">下一页</button>
              </div>
            </div>
          </section>
        </article>
      </div>
    </div>

    <div v-if="detailFeedback" class="modal-mask">
      <article class="paper-card modal-panel feedback-detail-modal">
        <div class="modal-title"><h3>反馈详情</h3><button type="button" class="icon-btn" @click="closeFeedbackDetail">×</button></div>
        <template v-if="!isEditingDetail">
          <p><strong>反馈标题：</strong>{{ detailFeedback.lesson_title || '未填写' }}</p><p><strong>上课时间：</strong>{{ detailFeedback.lesson_time }}</p><p><strong>课堂学习内容：</strong>{{ detailFeedback.lesson_summary }}</p><p><strong>课堂表现与知识掌握情况：</strong>{{ detailFeedback.performance_summary || '未填写' }}</p><p><strong>课后建议：</strong>{{ detailFeedback.advice_summary || '未填写' }}</p><p><strong>作业安排：</strong>{{ detailFeedback.homework_plan || '未填写' }}</p><h4>最终反馈</h4><pre>{{ detailFeedback.final_feedback }}</pre><details><summary>查看 AI 初稿</summary><pre>{{ detailFeedback.ai_draft }}</pre></details>
          <div class="button-row danger-row"><div class="button-row"><button class="ghost-btn" @click="isEditingDetail = true; assignFeedback(editForm, detailFeedback); resizeAllTextareas()">编辑反馈</button><button class="ghost-btn" @click="addCurrentFeedbackAsStyleExample">设为风格样例</button></div><button class="danger-btn" @click="deleteFeedback">删除反馈</button></div>
        </template>
        <form v-else class="feedback-editor" @submit.prevent="saveFeedbackEdit">
          <label>上课时间<input v-model="editForm.lesson_time" type="datetime-local" /></label><label>反馈标题<input v-model="editForm.lesson_title" /></label><label>1. 课堂学习内容<textarea v-model="editForm.lesson_summary" class="auto-textarea" @input="autoResize"></textarea></label><label>2. 课堂表现与知识掌握情况<textarea v-model="editForm.performance_summary" class="auto-textarea" @input="autoResize"></textarea></label><label>3. 课后建议<textarea v-model="editForm.advice_summary" class="auto-textarea" @input="autoResize"></textarea></label><label>4. 作业安排<textarea v-model="editForm.homework_plan" class="auto-textarea" @input="autoResize"></textarea></label><label>AI 初稿<textarea v-model="editForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label><label>最终反馈<textarea v-model="editForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
          <div class="button-row"><button class="primary-btn">保存修改</button><button class="ghost-btn" type="button" @click="isEditingDetail = false">取消</button></div>
        </form>
      </article>
    </div>

    <div v-if="showOneStudentEditModal" class="modal-mask">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveOneStudentEdit">
        <div class="modal-title"><h3>编辑一对一学生</h3><button type="button" class="icon-btn" @click="showOneStudentEditModal = false">×</button></div>
        <input v-model="oneStudentForm.name" placeholder="学生姓名" /><input v-model="oneStudentForm.grade" placeholder="年级" /><input v-model="oneStudentForm.subject" placeholder="科目" />
        <div class="button-row danger-row"><button class="primary-btn">保存学生信息</button><button type="button" class="danger-btn" @click="deleteOneStudent">删除学生</button></div>
      </form>
    </div>

    <div v-if="showClassModal" class="modal-mask">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveClass">
        <div class="modal-title"><h3>{{ editingClass ? '编辑班级' : '新建班级' }}</h3><button type="button" class="icon-btn" @click="showClassModal = false">×</button></div>
        <input v-model="classForm.name" placeholder="班级名称，例如 初三晚辅" />
        <button class="primary-btn">保存班级</button>
      </form>
    </div>

    <div v-if="showGroupClassModal" class="modal-mask">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveGroupClass">
        <div class="modal-title"><h3>{{ editingGroupClass ? '编辑班课班级' : '新建班课班级' }}</h3><button type="button" class="icon-btn" @click="showGroupClassModal = false">×</button></div>
        <input v-model="groupClassForm.name" placeholder="班级名称，例如 初三数学" />
        <button class="primary-btn">保存班级</button>
      </form>
    </div>

    <div v-if="showBulkModal" class="modal-mask">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="bulkCreateEveningStudents">
        <div class="modal-title"><h3>批量录入学生</h3><button type="button" class="icon-btn" @click="showBulkModal = false">×</button></div>
        <label>学生名单<textarea v-model="bulkForm.names_text" class="auto-textarea final-text" placeholder="一行一个姓名" @input="autoResize"></textarea></label>
        <button class="primary-btn">录入学生</button>
      </form>
    </div>

    <div v-if="showEveningStudentModal" class="modal-mask">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveEveningStudentEdit">
        <div class="modal-title"><h3>编辑晚辅学生</h3><button type="button" class="icon-btn" @click="showEveningStudentModal = false">×</button></div>
        <input v-model="eveningStudentForm.name" placeholder="姓名" /><input v-model="eveningStudentForm.grade" placeholder="年级" /><input v-model="eveningStudentForm.school" placeholder="学校" />
        <div class="button-row danger-row"><button class="primary-btn">保存学生信息</button><button type="button" class="danger-btn" @click="deleteEveningStudent">删除学生</button></div>
      </form>
    </div>

    <div v-if="showMonthlyModal" class="modal-mask">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveMonthlyFeedback">
        <div class="modal-title"><h3>新增晚辅反馈</h3><button type="button" class="icon-btn" @click="closeMonthlyModal">×</button></div>
        <label>晚辅学生<select v-model="monthlyForm.student_id"><option value="">请选择学生</option><option v-for="student in eveningFeedbackStudentOptions" :key="student.id" :value="student.id">{{ student.name }}</option></select></label>
        <label>反馈类型<select v-model="monthlyForm.period_type" @change="setEveningFeedbackPeriodType(monthlyForm, monthlyForm.period_type)"><option v-for="type in EVENING_PERIOD_TYPES" :key="type.value" :value="type.value">{{ type.label }}</option></select></label>
        <label>{{ periodFieldLabel(monthlyForm.period_type) }}<input v-model="monthlyForm.period_value" :type="periodInputType(monthlyForm.period_type)" /></label>
        <label>作业完成情况简述<textarea v-model="monthlyForm.homework_summary" class="auto-textarea" @input="autoResize"></textarea></label>
        <div class="button-row"><button type="button" class="ghost-btn" @click="generateMonthlyDraft">生成 AI 初稿</button><button class="primary-btn">保存晚辅反馈</button></div>
        <label>AI 初稿<textarea v-model="monthlyForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label><label>最终反馈<textarea v-model="monthlyForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
      </form>
    </div>

    <div v-if="eveningDetail" class="modal-mask">
      <article class="paper-card modal-panel feedback-detail-modal">
        <div class="modal-title"><h3>晚辅反馈详情</h3><button type="button" class="icon-btn" @click="eveningDetail = null">×</button></div>
        <template v-if="!isEditingEveningDetail">
          <p><strong>学生：</strong>{{ eveningDetail.student_name || currentEveningStudent?.name || '未填写' }}</p><p><strong>反馈类型：</strong>{{ periodTypeLabel(eveningDetail.period_type) }}</p><p><strong>反馈时间：</strong>{{ eveningDetail.period_label }}</p><p><strong>作业情况：</strong>{{ eveningDetail.homework_summary }}</p><h4>最终反馈</h4><pre>{{ eveningDetail.final_feedback }}</pre><details><summary>查看 AI 初稿</summary><pre>{{ eveningDetail.ai_draft }}</pre></details>
          <div class="button-row danger-row"><button class="ghost-btn" @click="isEditingEveningDetail = true; assignMonthly(monthlyEditForm, eveningDetail); resizeAllTextareas()">编辑反馈</button><button class="danger-btn" @click="deleteEveningFeedback">删除反馈</button></div>
        </template>
        <form v-else class="feedback-editor" @submit.prevent="saveEveningDetailEdit">
          <label>晚辅学生<select v-model="monthlyEditForm.student_id"><option v-for="student in eveningFeedbackStudentOptions" :key="student.id" :value="student.id">{{ student.name }}</option></select></label><label>反馈类型<select v-model="monthlyEditForm.period_type" @change="setEveningFeedbackPeriodType(monthlyEditForm, monthlyEditForm.period_type)"><option v-for="type in EVENING_PERIOD_TYPES" :key="type.value" :value="type.value">{{ type.label }}</option></select></label><label>{{ periodFieldLabel(monthlyEditForm.period_type) }}<input v-model="monthlyEditForm.period_value" :type="periodInputType(monthlyEditForm.period_type)" /></label><label>作业完成情况简述<textarea v-model="monthlyEditForm.homework_summary" class="auto-textarea" @input="autoResize"></textarea></label><label>AI 初稿<textarea v-model="monthlyEditForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label><label>最终反馈<textarea v-model="monthlyEditForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
          <div class="button-row"><button class="primary-btn">保存修改</button><button type="button" class="ghost-btn" @click="isEditingEveningDetail = false">取消</button></div>
        </form>
      </article>
    </div>

    <div v-if="message" class="toast">{{ message }}</div>
  </main>
</template>
