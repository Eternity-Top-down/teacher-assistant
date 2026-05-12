<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.mjs?url'
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

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerUrl

const teacher = ref(null)
const route = ref(window.location.hash || '#/one-on-one')
const loading = ref(false)
const message = ref('')
const authMode = ref('login')

const oneStudents = ref([])
const currentStudent = ref(null)
const feedbacks = ref([])
const feedbackSearchResults = ref([])
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
const showClassModal = ref(false)
const showBulkModal = ref(false)
const showEveningStudentModal = ref(false)
const showMonthlyModal = ref(false)
const isEditingEveningDetail = ref(false)
const editingClass = ref(null)
const aiSettings = ref(null)
const visionSettings = ref(null)
const styleExamples = ref([])
const detailStyleExample = ref(null)
const isEditingStyleExample = ref(false)
const showAccountMenu = ref(false)
const showApiOnboarding = ref(false)
const showSettingsGuide = ref(false)
const showFeedbackStyleModal = ref(false)
const showMaterialsModal = ref(false)
const materialInput = ref(null)
const materialImages = ref([])
const materialAnalysis = ref(null)
const materialsAnalyzing = ref(false)
const materialsConverting = ref(false)
const classroomContentMode = ref('qa')
const feedbackEmphasis = ref('')
const feedbackDraftStatus = ref('')
const hasSavedFeedbackDraft = ref(false)
const styleExamplePage = ref(1)
const feedbackStyleExamplePage = ref(1)
const feedbackSearchForm = reactive(defaultFeedbackSearchRange())
const studentHistoryFilter = reactive({ start_date: '', end_date: '' })
const feedbackPanels = reactive(defaultFeedbackPanels())

const API_ONBOARDING_SEEN_KEY = 'api_onboarding_seen_v1'
const SETTINGS_GUIDE_SEEN_KEY = 'settings_guide_seen_v1'
const MAX_MATERIAL_IMAGES = 9
const MAX_MATERIAL_IMAGE_SIZE = 8 * 1024 * 1024
const MAX_MATERIAL_PDF_SIZE = 25 * 1024 * 1024
const MAX_PDF_RENDER_WIDTH = 1500
const MATERIAL_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MATERIAL_PDF_TYPE = 'application/pdf'
const MATERIAL_ACCEPT_TYPES = [...MATERIAL_IMAGE_TYPES, MATERIAL_PDF_TYPE].join(',')
const MATERIALS_MODAL_VISIBLE_WIDTH = 168
const MATERIALS_MODAL_VISIBLE_HEIGHT = 96
const STYLE_EXAMPLE_PAGE_SIZE = 5
const MAX_ENABLED_STYLE_EXAMPLES = 5
const CLASSROOM_CONTENT_MODES = [
  { value: 'qa', label: '问答模式' },
  { value: 'free', label: '自由模式' },
]
const QA_FIELDS = [
  {
    key: 'lesson',
    formField: 'lesson_summary',
    title: '1. 本节课主要学了什么？',
    example: '例如：学习了一元一次方程的去括号、移项和合并同类项，重点练了应用题列方程。',
  },
  {
    key: 'performance',
    formField: 'performance_summary',
    title: '2. 学生课堂表现和掌握情况如何？',
    example: '例如：听课比较专注，基础计算掌握较好，但应用题读题和等量关系寻找还需要提醒。',
  },
  {
    key: 'advice',
    formField: 'advice_summary',
    title: '3. 课后建议重点是什么？',
    example: '例如：建议课后把今天错的应用题重新整理一遍，先标出关键词，再写等量关系。',
  },
  {
    key: 'homework',
    formField: 'homework_plan',
    title: '4. 作业安排是什么？',
    example: '例如：完成讲义第 3 页 1-6 题，错题整理到错题本，下节课检查。',
  },
]

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
  base_url: 'https://api.deepseek.com',
  model: 'deepseek-v4-flash',
  api_key: '',
  clear_api_key: false,
})
const visionSettingsForm = reactive({
  provider: 'doubao_v',
  base_url: 'https://ark.cn-beijing.volces.com/api/v3',
  model: 'doubao-1.5-vision-pro-32k',
  api_key: '',
  clear_api_key: false,
})
const styleExampleForm = reactive({ title: '', content: '', enabled: true })
const inlineStyleExampleForm = reactive({ title: '', content: '', enabled: true })
const styleExampleEditForm = reactive({ title: '', content: '', enabled: true })
const qaAnswers = reactive(defaultQaAnswers())
const materialsModalFrame = reactive({ left: 160, top: 80, width: 760, height: 680 })
const materialsModalDrag = reactive({ active: false, startX: 0, startY: 0, startLeft: 0, startTop: 0, startWidth: 0, startHeight: 0, mode: '' })
const settingsPanels = reactive({
  feedback_ai: true,
  vision_ai: false,
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
    hint: '适合长上下文材料整理，也可用于生成自然、完整的反馈正文。需要视觉输入时建议切到图片识别模型里的 Kimi K2.5。',
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

const VISION_PRESETS = {
  doubao_v: {
    label: '火山方舟 - 豆包视觉理解（推荐，有免费额度）',
    base_url: 'https://ark.cn-beijing.volces.com/api/v3',
    model: 'doubao-1.5-vision-pro-32k',
    hint: '适合课堂图片理解，多数新账号可在火山方舟领取免费推理额度。若控制台要求推理接入点，请把模型名改成 ep-... 接入点 ID。',
    api_key_url: 'https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey',
    docs_url: 'https://www.volcengine.com/docs/82379/1168048',
  },
  qwen_vl: {
    label: '阿里云百炼 - 通义千问视觉/OCR',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen-vl-ocr-latest',
    hint: '适合讲义、试卷、表格、手写和错题图片识别；可选 qwen-vl-ocr、qwen3-vl-flash、qwen3-vl-plus。',
    api_key_url: 'https://bailian.console.aliyun.com/?tab=model#/api-key',
    docs_url: 'https://www.alibabacloud.com/help/zh/doc-detail/2845564.html',
  },
  kimi: {
    label: 'Kimi / Moonshot 视觉模型',
    base_url: 'https://api.moonshot.ai/v1',
    model: 'kimi-k2.5',
    hint: '适合长上下文、多图课堂材料理解；也可按 Kimi 官方视觉模型列表填写。',
    api_key_url: 'https://platform.moonshot.ai/console/api-keys',
    docs_url: 'https://platform.moonshot.ai/docs/guide/use-kimi-vision-model',
  },
  zhipu_v: {
    label: '智谱 AI - GLM 视觉模型',
    base_url: 'https://open.bigmodel.cn/api/paas/v4',
    model: 'glm-4.6v-flash',
    hint: '适合图片理解、视觉总结和教育课件类场景；如需更高质量可按账号权限改用 glm-4v-plus-0111。',
    api_key_url: 'https://bigmodel.cn/usercenter/proj-mgmt/apikeys',
    docs_url: 'https://docs.bigmodel.cn/cn/guide/models/free/glm-4.6v-flash',
  },
  deepseek: {
    label: 'DeepSeek（通常不推荐用于图片识别）',
    base_url: 'https://api.deepseek.com',
    model: 'deepseek-v4-flash',
    hint: 'DeepSeek 常用于文本生成；请确认当前模型是否支持图片输入。课堂资料识别需要视觉/多模态模型。',
    api_key_url: 'https://platform.deepseek.com/api_keys',
    docs_url: 'https://api-docs.deepseek.com/',
  },
  custom: { label: '自定义兼容接口', base_url: '', model: '', hint: '用于其他 OpenAI-compatible 多模态供应商。', api_key_url: '', docs_url: '' },
}

const isAuthed = computed(() => Boolean(teacher.value))
const teacherInitial = computed(() => (teacher.value?.email || 'T').slice(0, 1).toUpperCase())
const selectedAIPreset = computed(() => AI_PRESETS[aiSettingsForm.provider] || AI_PRESETS.custom)
const selectedVisionPreset = computed(() => VISION_PRESETS[visionSettingsForm.provider] || VISION_PRESETS.custom)
const currentView = computed(() => {
  if (!isAuthed.value) return 'auth'
  if (route.value === '#/settings') return 'settings'
  if (route.value === '#/one-on-one/feedbacks') return 'one-feedback-search'
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
  enabledStyleExampleCount.value
    ? `已启用 ${enabledStyleExampleCount.value} / ${MAX_ENABLED_STYLE_EXAMPLES} 条样例，将按个人风格生成`
    : '暂无启用样例，将按标准结构生成'
)
const styleExampleTotalPages = computed(() => totalPages(styleExamples.value.length))
const feedbackStyleExampleTotalPages = computed(() => totalPages(styleExamples.value.length))
const paginatedStyleExamples = computed(() => pageItems(styleExamples.value, styleExamplePage.value))
const paginatedFeedbackStyleExamples = computed(() => pageItems(styleExamples.value, feedbackStyleExamplePage.value))
const materialStatus = computed(() => {
  if (materialsConverting.value) return '正在转换 PDF 页面...'
  if (materialsAnalyzing.value) return '正在识别课堂资料...'
  if (materialAnalysis.value) return `已识别 ${materialImages.value.length} 个资料页面，可填入课堂学习内容`
  if (materialImages.value.length) return `已选择 ${materialImages.value.length} / ${MAX_MATERIAL_IMAGES} 个资料页面，支持图片和 PDF`
  return '可上传图片或 PDF，Word 请先导出为 PDF 后上传'
})
const materialsModalStyle = computed(() => ({
  left: `${materialsModalFrame.left}px`,
  top: `${materialsModalFrame.top}px`,
  width: `${materialsModalFrame.width}px`,
  height: `${materialsModalFrame.height}px`,
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
    draft: true,
    final: true,
  }
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
  settingsPanels.vision_ai = panel === 'vision_ai'
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
  Object.assign(qaAnswers, defaultQaAnswers())
  classroomContentMode.value = 'qa'
  feedbackEmphasis.value = ''
  clearMaterialImages()
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

function hasQaAnswers() {
  return QA_FIELDS.some((field) => qaAnswers[field.key]?.trim())
}

function currentFeedbackDraftKey() {
  if (!teacher.value?.id || !currentStudent.value?.id) return ''
  return `one_feedback_draft:${teacher.value.id}:${currentStudent.value.id}`
}

function feedbackDraftHasContent(draft) {
  return Boolean(
    hasFeedbackDraft(draft?.feedback || {}) ||
      draft?.material_analysis ||
      Object.values(draft?.qa_answers || {}).some((value) => String(value || '').trim()) ||
      draft?.emphasis_summary?.trim()
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
    content_mode: classroomContentMode.value,
    qa_answers: { ...qaAnswers },
    emphasis_summary: feedbackEmphasis.value,
    material_analysis: materialAnalysis.value,
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
  Object.assign(qaAnswers, defaultQaAnswers(), draft.qa_answers || {})
  classroomContentMode.value = draft.content_mode === 'free' ? 'free' : 'qa'
  feedbackEmphasis.value = draft.emphasis_summary || ''
  clearMaterialImages()
  materialAnalysis.value = draft.material_analysis || null
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
    maybeShowApiOnboarding()
  } catch (error) {
    showMessage(error.message || 'AI 初稿生成失败，请检查模型配置后重试')
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

function applyVisionPreset() {
  const preset = VISION_PRESETS[visionSettingsForm.provider]
  if (!preset || visionSettingsForm.provider === 'custom') return
  visionSettingsForm.base_url = preset.base_url
  visionSettingsForm.model = preset.model
}

function assignAISettings(settings) {
  aiSettings.value = settings
  aiSettingsForm.provider = settings?.provider || 'deepseek'
  aiSettingsForm.base_url = settings?.base_url || AI_PRESETS.deepseek.base_url
  aiSettingsForm.model = settings?.model || AI_PRESETS.deepseek.model
  aiSettingsForm.api_key = ''
  aiSettingsForm.clear_api_key = false
}

function assignVisionSettings(settings) {
  visionSettings.value = settings
  visionSettingsForm.provider = settings?.provider || 'doubao_v'
  visionSettingsForm.base_url = settings?.base_url || VISION_PRESETS.doubao_v.base_url
  visionSettingsForm.model = settings?.model || VISION_PRESETS.doubao_v.model
  visionSettingsForm.api_key = ''
  visionSettingsForm.clear_api_key = false
}

async function loadAISettings() {
  const data = await request('/settings/ai')
  assignAISettings(data.settings)
}

async function loadVisionSettings() {
  const data = await request('/settings/vision')
  assignVisionSettings(data.settings)
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

async function saveVisionSettings() {
  if (!visionSettingsForm.base_url.trim()) return showMessage('请填写图片识别模型的 Base URL')
  if (!visionSettingsForm.model.trim()) return showMessage('请填写图片识别模型名')
  loading.value = true
  try {
    const data = await request('/settings/vision', {
      method: 'PUT',
      body: JSON.stringify(visionSettingsForm),
    })
    assignVisionSettings(data.settings)
    showMessage('图片识别模型配置已保存')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function testVisionSettings() {
  if (!visionSettingsForm.base_url.trim()) return showMessage('请填写图片识别模型的 Base URL')
  if (!visionSettingsForm.model.trim()) return showMessage('请填写图片识别模型名')
  loading.value = true
  try {
    const data = await request('/settings/vision/test', {
      method: 'POST',
      body: JSON.stringify({
        provider: visionSettingsForm.provider,
        base_url: visionSettingsForm.base_url,
        model: visionSettingsForm.model,
        api_key: visionSettingsForm.api_key,
      }),
    })
    showMessage(data.message || '图片识别模型连接成功')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function clearVisionKey() {
  if (!window.confirm('确定清除已保存的图片识别模型 API Key 吗？清除后将无法识别课堂图片。')) return
  visionSettingsForm.api_key = ''
  visionSettingsForm.clear_api_key = true
  await saveVisionSettings()
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

function clearStudentHistoryFilter() {
  studentHistoryFilter.start_date = ''
  studentHistoryFilter.end_date = ''
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

async function openMaterialsModal() {
  showMaterialsModal.value = true
  await resizeAllTextareas()
}

function closeMaterialsModal() {
  showMaterialsModal.value = false
}

function closeCreateFeedback() {
  if ((hasFeedbackDraft(feedbackForm) || hasQaAnswers() || feedbackEmphasis.value.trim()) && !window.confirm('这条反馈还没有保存，确定关闭吗？')) return
  showFeedbackStyleModal.value = false
  showMaterialsModal.value = false
  showCreateModal.value = false
  resetFeedbackForm()
}

function closeMonthlyModal() {
  if (
    (monthlyForm.homework_summary.trim() || monthlyForm.ai_draft.trim() || monthlyForm.final_feedback.trim()) &&
    !window.confirm('这条月度反馈还没有保存，确定关闭吗？')
  ) {
    return
  }
  showMonthlyModal.value = false
  resetMonthlyForm()
}

function setClassroomContentMode(mode) {
  classroomContentMode.value = mode
  openFeedbackPanel('content')
  resizeAllTextareas()
  saveFeedbackDraft()
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

function appendMergedText(field, text) {
  const value = String(text || '').trim()
  if (!value) return
  const current = String(feedbackForm[field] || '').trim()
  if (current.includes(value)) return
  feedbackForm[field] = [current, value].filter(Boolean).join('\n')
}

function qaFieldValue(field) {
  return qaAnswerToBullets(qaAnswers[field.key]) || feedbackForm[field.formField]
}

function qaInputForGenerate() {
  return QA_FIELDS.reduce((payload, field) => {
    payload[field.formField] = qaFieldValue(field)
    return payload
  }, {})
}

function convertQaToFree() {
  if (!hasQaAnswers()) return showMessage('请先填写问答内容')
  QA_FIELDS.forEach((field) => {
    appendMergedText(field.formField, qaAnswerToBullets(qaAnswers[field.key]))
  })
  classroomContentMode.value = 'free'
  openFeedbackPanel('content')
  resizeAllTextareas()
  saveFeedbackDraft()
  showMessage('已整理到自由模式，可继续修改完善')
}

function appendText(field, text) {
  if (!text.trim()) return
  feedbackForm[field] = [feedbackForm[field], text.trim()].filter(Boolean).join('\n')
}

function formatFileSize(size) {
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)}MB`
  return `${Math.max(1, Math.round(size / 1024))}KB`
}

function clearMaterialInput() {
  if (materialInput.value) materialInput.value.value = ''
}

function removeMaterialImage(index) {
  const [removed] = materialImages.value.splice(index, 1)
  if (removed?.preview_url) URL.revokeObjectURL(removed.preview_url)
  materialAnalysis.value = null
  clearMaterialInput()
}

function clearMaterialImages() {
  materialImages.value.forEach((image) => {
    if (image.preview_url) URL.revokeObjectURL(image.preview_url)
  })
  materialImages.value = []
  materialAnalysis.value = null
  clearMaterialInput()
}

function isPdfFile(file) {
  return file.type === MATERIAL_PDF_TYPE || file.name.toLowerCase().endsWith('.pdf')
}

function isWordFile(file) {
  const name = file.name.toLowerCase()
  return (
    name.endsWith('.doc') ||
    name.endsWith('.docx') ||
    file.type === 'application/msword' ||
    file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  )
}

function materialPageItem(file, source = '图片') {
  return {
    id: `${Date.now()}-${file.name}-${Math.random()}`,
    file,
    preview_url: URL.createObjectURL(file),
    source,
  }
}

function canvasToBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob)
      else reject(new Error('PDF 页面转换失败，请重试'))
    }, 'image/png')
  })
}

async function renderPdfPages(file, limit) {
  if (file.size > MAX_MATERIAL_PDF_SIZE) {
    showMessage(`${file.name} 超过 25MB，请压缩或拆分后上传`)
    return []
  }
  const pdf = await pdfjsLib.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise
  const pageCount = Math.min(pdf.numPages, limit)
  const pages = []
  const baseName = file.name.replace(/\.pdf$/i, '')

  for (let pageNumber = 1; pageNumber <= pageCount; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber)
    const viewport = page.getViewport({ scale: 1 })
    const scale = Math.min(2, Math.max(1.1, MAX_PDF_RENDER_WIDTH / viewport.width))
    const scaledViewport = page.getViewport({ scale })
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')
    canvas.width = Math.floor(scaledViewport.width)
    canvas.height = Math.floor(scaledViewport.height)
    await page.render({ canvasContext: context, viewport: scaledViewport }).promise
    const blob = await canvasToBlob(canvas)
    if (blob.size > MAX_MATERIAL_IMAGE_SIZE) {
      showMessage(`${file.name} 第 ${pageNumber} 页转换后超过 8MB，已跳过`)
      continue
    }
    const imageFile = new File([blob], `${baseName}-第${pageNumber}页.png`, { type: 'image/png' })
    pages.push(materialPageItem(imageFile, `${file.name} 第 ${pageNumber} 页`))
  }

  if (pdf.numPages > limit) showMessage(`${file.name} 页数较多，已保留前 ${limit} 页`)
  return pages
}

async function handleMaterialFiles(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  if (materialImages.value.length >= MAX_MATERIAL_IMAGES) {
    showMessage(`一次最多上传 ${MAX_MATERIAL_IMAGES} 个课堂资料页面`)
    clearMaterialInput()
    return
  }

  const accepted = []
  materialsConverting.value = true
  try {
    for (const file of files) {
      const availableSlots = MAX_MATERIAL_IMAGES - materialImages.value.length - accepted.length
      if (availableSlots <= 0) {
        showMessage(`已保留前 ${MAX_MATERIAL_IMAGES} 个资料页面`)
        break
      }
      if (isWordFile(file)) {
        showMessage(`${file.name} 暂不支持直接上传，请先导出为 PDF 后上传`)
        continue
      }
      if (isPdfFile(file)) {
        accepted.push(...(await renderPdfPages(file, availableSlots)))
        continue
      }
      if (!MATERIAL_IMAGE_TYPES.includes(file.type)) {
        showMessage('只支持 JPG、PNG、WEBP 图片和 PDF 文件')
        continue
      }
      if (file.size > MAX_MATERIAL_IMAGE_SIZE) {
        showMessage(`${file.name} 超过 8MB，请压缩后再上传`)
        continue
      }
      accepted.push(materialPageItem(file))
    }
  } catch (error) {
    showMessage(error.message)
  } finally {
    materialsConverting.value = false
    clearMaterialInput()
  }

  if (accepted.length) {
    materialImages.value = [...materialImages.value, ...accepted]
    materialAnalysis.value = null
    saveFeedbackDraft()
  }
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const value = String(reader.result || '')
      resolve(value.includes(',') ? value.split(',')[1] : value)
    }
    reader.onerror = () => reject(new Error(`${file.name} 读取失败，请重新选择`))
    reader.readAsDataURL(file)
  })
}

function clampMaterialsModalFrame() {
  const minLeft = Math.min(8, MATERIALS_MODAL_VISIBLE_WIDTH - materialsModalFrame.width)
  const maxLeft = Math.max(8, window.innerWidth - MATERIALS_MODAL_VISIBLE_WIDTH)
  const minTop = Math.min(8, MATERIALS_MODAL_VISIBLE_HEIGHT - materialsModalFrame.height)
  const maxTop = Math.max(8, window.innerHeight - MATERIALS_MODAL_VISIBLE_HEIGHT)
  materialsModalFrame.left = Math.min(Math.max(minLeft, materialsModalFrame.left), maxLeft)
  materialsModalFrame.top = Math.min(Math.max(minTop, materialsModalFrame.top), maxTop)
}

function startMaterialsModalMove(event, mode) {
  if (event.button !== undefined && event.button !== 0) return
  materialsModalDrag.active = true
  materialsModalDrag.mode = mode
  materialsModalDrag.startX = event.clientX
  materialsModalDrag.startY = event.clientY
  materialsModalDrag.startLeft = materialsModalFrame.left
  materialsModalDrag.startTop = materialsModalFrame.top
  materialsModalDrag.startWidth = materialsModalFrame.width
  materialsModalDrag.startHeight = materialsModalFrame.height
  window.addEventListener('pointermove', moveMaterialsModal)
  window.addEventListener('pointerup', stopMaterialsModalMove, { once: true })
}

function moveMaterialsModal(event) {
  if (!materialsModalDrag.active) return
  const deltaX = event.clientX - materialsModalDrag.startX
  const deltaY = event.clientY - materialsModalDrag.startY
  if (materialsModalDrag.mode === 'move') {
    materialsModalFrame.left = materialsModalDrag.startLeft + deltaX
    materialsModalFrame.top = materialsModalDrag.startTop + deltaY
  } else {
    materialsModalFrame.width = Math.min(window.innerWidth - 16, Math.max(520, materialsModalDrag.startWidth + deltaX))
    materialsModalFrame.height = Math.min(window.innerHeight - 16, Math.max(430, materialsModalDrag.startHeight + deltaY))
  }
  clampMaterialsModalFrame()
}

function stopMaterialsModalMove() {
  materialsModalDrag.active = false
  window.removeEventListener('pointermove', moveMaterialsModal)
}

async function analyzeMaterialImages() {
  if (!materialImages.value.length) return showMessage('请先选择课堂资料')
  materialsAnalyzing.value = true
  try {
    const images = await Promise.all(
      materialImages.value.map(async (item) => ({
        name: item.file.name,
        mime_type: item.file.type,
        data_base64: await fileToBase64(item.file),
      }))
    )
    materialAnalysis.value = await request(`/students/${currentStudent.value.id}/feedbacks/materials/analyze`, {
      method: 'POST',
      body: JSON.stringify({
        lesson_title: titleForGenerate(feedbackForm.lesson_title, feedbackForm.lesson_time),
        subject: currentStudent.value?.subject || '',
        images,
      }),
    })
    saveFeedbackDraft()
    showMessage('课堂资料已识别完成')
  } catch (error) {
    showMessage(error.message)
  } finally {
    materialsAnalyzing.value = false
  }
}

function applyMaterialAnalysis() {
  const suggestion = materialAnalysis.value?.lesson_summary_suggestion || ''
  if (!suggestion.trim()) return showMessage('暂无可填入的课堂学习内容')
  appendText('lesson_summary', suggestion)
  if (classroomContentMode.value === 'qa') {
    qaAnswers.lesson = [qaAnswers.lesson, suggestion.trim()].filter(Boolean).join('\n')
  }
  openFeedbackPanel('content')
  resizeAllTextareas()
  saveFeedbackDraft()
  showMessage('已填入课堂学习内容，可继续修改')
}

async function generateDraft() {
  if (!feedbackForm.lesson_title.trim()) return showMessage('请填写反馈标题')
  const contentPayload = classroomContentMode.value === 'qa' ? qaInputForGenerate() : {
    lesson_summary: feedbackForm.lesson_summary,
    performance_summary: feedbackForm.performance_summary,
    advice_summary: feedbackForm.advice_summary,
    homework_plan: feedbackForm.homework_plan,
  }
  if (classroomContentMode.value === 'qa') {
    const missingQuestion = QA_FIELDS.find((field) => !qaAnswers[field.key]?.trim())
    if (missingQuestion) return showMessage(`请先填写：${missingQuestion.title}`)
  }
  if (!contentPayload.lesson_summary.trim()) return showMessage('请填写课堂学习内容')
  if (classroomContentMode.value === 'qa') {
    QA_FIELDS.forEach((field) => {
      feedbackForm[field.formField] = contentPayload[field.formField]
    })
  }
  loading.value = true
  try {
    const data = await request(`/students/${currentStudent.value.id}/feedbacks/generate`, {
      method: 'POST',
      body: JSON.stringify({
        lesson_time: feedbackForm.lesson_time,
        lesson_title: titleForGenerate(feedbackForm.lesson_title, feedbackForm.lesson_time),
        ...contentPayload,
        emphasis_summary: feedbackEmphasis.value,
      }),
    })
    feedbackForm.ai_draft = data.draft
    feedbackForm.final_feedback = data.draft
    feedbackForm.lesson_title = titleForGenerate(feedbackForm.lesson_title, feedbackForm.lesson_time)
    feedbackPanels.draft = true
    feedbackPanels.final = true
    await resizeAllTextareas()
    saveFeedbackDraft()
    showMessage('AI 初稿已生成')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function saveFeedback() {
  if (!feedbackForm.final_feedback.trim()) return showMessage('请先生成或填写反馈内容')
  if (classroomContentMode.value === 'qa' && hasQaAnswers()) {
    const contentPayload = qaInputForGenerate()
    QA_FIELDS.forEach((field) => {
      feedbackForm[field.formField] = contentPayload[field.formField]
    })
  }
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
    if (currentView.value === 'one-feedback-search') await loadFeedbackSearchResults()
    if (currentView.value === 'one-student' || currentView.value === 'one-history') await loadOneStudentContext(true)
    if (currentView.value === 'evening') await loadEveningClasses()
    if (currentView.value === 'evening-class') await loadEveningClassContext()
    if (currentView.value === 'evening-student') await loadEveningStudentContext()
    if (currentView.value === 'settings') {
      await loadAISettings()
      await loadVisionSettings()
      await loadStyleExamples()
    }
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
          <p>把一对一课后反馈和晚辅月度作业反馈，整理进一个清晰、温暖、好维护的工作台。</p>
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
            <p class="eyebrow">{{ currentView === 'settings' ? '设置' : currentView.startsWith('evening') ? '晚辅' : '一对一' }}</p>
            <h2 v-if="currentView === 'one-list'">一对一学生</h2>
            <h2 v-else-if="currentView === 'one-feedback-search'">反馈查询</h2>
            <h2 v-else-if="currentView === 'settings'">AI 模型配置</h2>
            <h2 v-else-if="currentView === 'evening'">晚辅班级</h2>
            <h2 v-else-if="currentView === 'evening-class'">{{ currentClass?.name || '晚辅班级' }}</h2>
            <h2 v-else-if="currentView === 'evening-student'">{{ currentEveningStudent?.name || '晚辅学生' }}</h2>
            <h2 v-else>{{ currentStudent?.name || '一对一学生' }}</h2>
          </div>
          <button v-if="currentView === 'one-student' || currentView === 'one-history' || currentView === 'one-feedback-search'" class="ghost-btn" @click="go('#/one-on-one')">返回一对一</button>
          <button v-if="currentView === 'evening-class'" class="ghost-btn" @click="go('#/evening')">返回晚辅</button>
          <button v-if="currentView === 'evening-student'" class="ghost-btn" @click="go(`#/evening/classes/${currentEveningStudent?.class_id}`)">返回班级</button>
          <button v-if="currentView === 'settings'" class="ghost-btn" type="button" @click="openSettingsGuide">设置引导</button>
        </header>

        <section v-if="currentView === 'one-list'" class="dashboard-grid">
          <form class="paper-card student-form" @submit.prevent="createOneStudent">
            <h3>添加一对一学生</h3>
            <input v-model="oneStudentForm.name" placeholder="学生姓名" />
            <input v-model="oneStudentForm.grade" placeholder="年级，例如 初二" />
            <input v-model="oneStudentForm.subject" placeholder="科目，例如 数学" />
            <textarea v-model="oneStudentForm.note" class="auto-textarea" placeholder="备注" @input="autoResize"></textarea>
            <button class="primary-btn" :disabled="loading">添加到一对一</button>
            <button type="button" class="ghost-btn" @click="go('#/one-on-one/feedbacks')">反馈查询</button>
          </form>
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

        <section v-if="currentView === 'one-student' && currentStudent" class="student-home">
          <div class="paper-card profile-card">
            <h3>{{ currentStudent.name }}</h3>
            <p>{{ currentStudent.grade || '未填写年级' }} · {{ currentStudent.subject || '未填写科目' }}</p>
            <small>{{ currentStudent.note || '暂无备注' }}</small>
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

        <section v-if="currentView === 'evening'" class="dashboard-grid">
          <form class="paper-card student-form" @submit.prevent="createClassFromList">
            <h3>新建晚辅班级</h3>
            <input v-model="classForm.name" placeholder="班级名称，例如 周一晚辅班" />
            <textarea v-model="classForm.note" class="auto-textarea" placeholder="备注" @input="autoResize"></textarea>
            <button class="primary-btn" :disabled="loading">新建班级</button>
          </form>
          <div class="student-list">
            <article v-for="cls in eveningClasses" :key="cls.id" class="student-card" @click="go(`#/evening/classes/${cls.id}`)">
              <img class="card-sticker" :src="eveningStickerArt" alt="" aria-hidden="true" />
              <span class="avatar">班</span>
              <h3>{{ cls.name }}</h3>
              <p>{{ cls.note || '暂无备注' }}</p>
              <small>{{ cls.student_count }} 名学生</small>
            </article>
            <div v-if="!eveningClasses.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>还没有晚辅班级。</span></div>
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
              <img class="card-sticker" :src="eveningStickerArt" alt="" aria-hidden="true" />
              <span class="avatar">{{ student.name.slice(0, 1) }}</span><h3>{{ student.name }}</h3>
              <p>{{ student.grade || '未填年级' }} · {{ student.school || '未填学校' }}</p><small>{{ student.feedback_count }} 条月度反馈</small>
            </article>
            <div v-if="!eveningStudents.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>这个班级还没有学生。</span></div>
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
            <div v-if="!eveningFeedbacks.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>暂无月度反馈。</span></div>
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

          <form class="paper-card settings-card vision-settings-card" :class="{ collapsed: !settingsPanels.vision_ai }" @submit.prevent="saveVisionSettings">
            <button class="settings-accordion-header" type="button" @click="toggleSettingsPanel('vision_ai')">
              <span>
                <span class="eyebrow">Image Recognition</span>
                <strong>图片识别模型配置（视觉模型）</strong>
                <small>用于识别课堂讲义、板书、作业、错题照片，并提炼知识点和易错点。</small>
              </span>
              <span class="settings-header-side">
                <span class="settings-pill" :class="{ ok: visionSettings?.has_api_key }">{{ visionSettings?.has_api_key ? `已配置：${visionSettings.model}` : '可选 · 未配置' }}</span>
                <span class="settings-caret">{{ settingsPanels.vision_ai ? '收起' : '展开' }}</span>
              </span>
            </button>

            <div v-show="settingsPanels.vision_ai" class="settings-panel-body">
              <p class="settings-hint">视觉模型就是能看懂图片的 AI 模型。普通文本反馈模型可以写反馈，但图片识别这里需要填写支持图片输入的模型。</p>

              <label>推荐模型
                <select v-model="visionSettingsForm.provider" @change="applyVisionPreset">
                  <option v-for="(preset, key) in VISION_PRESETS" :key="key" :value="key">{{ preset.label }}</option>
                </select>
                <small>{{ selectedVisionPreset.hint }}</small>
              </label>
              <div class="preset-link-row">
                <a v-if="selectedVisionPreset.api_key_url" :href="selectedVisionPreset.api_key_url" target="_blank" rel="noreferrer">获取 API Key</a>
                <a v-if="selectedVisionPreset.docs_url" :href="selectedVisionPreset.docs_url" target="_blank" rel="noreferrer">查看接入文档</a>
              </div>

              <label>Base URL
                <input v-model="visionSettingsForm.base_url" placeholder="https://ark.cn-beijing.volces.com/api/v3" />
                <small>模型平台的 OpenAI-compatible 多模态接口地址。豆包常用 https://ark.cn-beijing.volces.com/api/v3。</small>
              </label>

              <label>模型名
                <input v-model="visionSettingsForm.model" placeholder="doubao-1.5-vision-pro-32k" />
                <small>示例：doubao-1.5-vision-pro-32k、ep-...、qwen3-vl-plus、qwen-vl-ocr-latest、kimi-k2.5、glm-4.6v-flash。</small>
              </label>

              <label>API Key
                <input v-model="visionSettingsForm.api_key" type="password" :placeholder="visionSettings?.has_api_key ? '已配置，留空则保留原 Key' : '粘贴图片识别模型的 API Key'" autocomplete="off" />
                <small>{{ visionSettings?.has_api_key ? '当前账号已有图片识别模型 API Key。填写新 Key 会覆盖旧 Key。' : '还没有保存图片识别模型 API Key，识别课堂图片前需要先配置。' }}</small>
              </label>

              <p v-if="visionSettingsForm.provider === 'deepseek'" class="settings-warning">DeepSeek 常用于文本生成；请确认当前模型是否支持图片输入。课堂资料识别需要视觉/多模态模型。</p>

              <div class="button-row danger-row">
                <div class="button-row">
                  <button type="button" class="ghost-btn" :disabled="loading" @click="testVisionSettings">测试视觉连接</button>
                  <button class="primary-btn" :disabled="loading">保存图片识别配置</button>
                </div>
                <button type="button" class="danger-btn" :disabled="loading || !visionSettings?.has_api_key" @click="clearVisionKey">清除 API Key</button>
              </div>
              <p class="settings-hint">测试会发送一张内置示例图片给模型，只用于确认它能读取图片，不会保存。</p>
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
        <p class="settings-hint">老师要使用“生成 AI 初稿”和课堂图片识别，需要先到设置页填写自己的模型 API Key。配置只保存在当前老师账号下，API Key 会加密保存。</p>
        <div class="guide-step-list">
          <article>
            <strong>1. 反馈生成模型是必配项</strong>
            <span>它负责根据课堂内容、学生表现、课后建议和作业安排，生成课后反馈初稿。</span>
          </article>
          <article>
            <strong>2. 图片识别模型是可选增强项</strong>
            <span>如果你想上传讲义、作业或错题照片来提炼课堂内容，再配置支持图片输入的视觉模型。</span>
          </article>
          <article>
            <strong>3. 个人风格样例可稍后补充</strong>
            <span>没有启用样例时按标准四段结构生成；启用样例后，AI 会更贴近你的表达习惯。</span>
          </article>
        </div>
        <div class="button-row danger-row">
          <button type="button" class="primary-btn" @click="goToApiSettingsFromOnboarding">去设置 API</button>
          <button type="button" class="ghost-btn" @click="closeApiOnboarding">知道了，稍后再说</button>
        </div>
      </article>
    </div>

    <div v-if="detailStyleExample" class="modal-mask">
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
            <input v-model="styleExampleEditForm.title" placeholder="例如：晨钰第3次数学课（4.26）" />
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
            <span>这是生成课后反馈初稿的核心配置。优先完成它，后面就能在学生页面生成反馈。</span>
          </article>
          <article>
            <strong>2. 按需配置图片识别模型</strong>
            <span>它只负责看图片、提炼课堂资料。不需要上传图片识别时，可以先跳过。</span>
          </article>
          <article>
            <strong>3. 可选配置个人风格样例</strong>
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
          <button type="button" class="ghost-btn" :disabled="loading" @click="openFeedbackStyleModal">{{ styleExamples.length ? '管理个人风格' : '个人风格' }}</button>
        </section>
        <section class="feedback-style-entry materials-entry">
          <div>
            <strong>课堂资料</strong>
            <small>{{ materialStatus }}</small>
          </div>
          <button type="button" class="ghost-btn" :disabled="loading" @click="openMaterialsModal">导入课堂资料</button>
        </section>
        <section class="feedback-panel classroom-content-panel" :class="{ collapsed: !feedbackPanels.content }">
          <button class="feedback-panel-header" type="button" @click="toggleFeedbackPanel('content')"><strong>课堂内容填写</strong><span>{{ feedbackPanels.content ? '收起' : '展开' }}</span></button>
          <div v-show="feedbackPanels.content" class="feedback-panel-body">
            <div class="mode-switch" role="tablist" aria-label="课堂内容填写模式">
              <button v-for="mode in CLASSROOM_CONTENT_MODES" :key="mode.value" type="button" :class="{ active: classroomContentMode === mode.value }" @click="setClassroomContentMode(mode.value)">{{ mode.label }}</button>
            </div>

            <div v-if="classroomContentMode === 'qa'" class="qa-mode-panel">
              <label v-for="field in QA_FIELDS" :key="field.key" class="qa-question">
                <span>{{ field.title }}</span>
                <small>{{ field.example }}</small>
                <textarea v-model="qaAnswers[field.key]" class="auto-textarea" placeholder="按课堂真实情况简单写几句即可" @input="autoResize"></textarea>
              </label>
              <div class="button-row">
                <button type="button" class="ghost-btn" :disabled="loading" @click="convertQaToFree">转为自由编辑</button>
              </div>
            </div>

            <div v-else class="free-mode-panel">
              <label>1. 课堂学习内容<textarea v-model="feedbackForm.lesson_summary" class="auto-textarea" placeholder="写本节课学习的知识点、题型、方法，方便 AI 整理成复习清单" @input="autoResize"></textarea></label>
              <label>2. 课堂表现与知识掌握情况<textarea v-model="feedbackForm.performance_summary" class="auto-textarea" placeholder="写学生状态、掌握得好的地方、需要关注的问题" @input="autoResize"></textarea></label>
              <label>3. 课后建议<textarea v-model="feedbackForm.advice_summary" class="auto-textarea" placeholder="写你想给学生/家长的具体建议，AI 会润色成可执行方案" @input="autoResize"></textarea></label>
              <label>4. 作业安排<textarea v-model="feedbackForm.homework_plan" class="auto-textarea" placeholder="严格填写本次需要布置给学生的作业，AI 只润色不新增" @input="autoResize"></textarea></label>
              <label>重点强调<textarea v-model="feedbackEmphasis" class="auto-textarea" placeholder="可选。比如希望反馈更突出学习习惯、错题复盘、课堂进步或家长配合方式" @input="autoResize"></textarea></label>
            </div>
          </div>
        </section>

        <section class="feedback-panel" :class="{ collapsed: !feedbackPanels.draft }">
          <button class="feedback-panel-header" type="button" @click="toggleFeedbackPanel('draft')"><strong>AI 初稿</strong><span>{{ feedbackPanels.draft ? '收起' : '展开' }}</span></button>
          <label v-show="feedbackPanels.draft"><textarea v-model="feedbackForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label>
        </section>

        <section class="feedback-panel" :class="{ collapsed: !feedbackPanels.final }">
          <button class="feedback-panel-header" type="button" @click="toggleFeedbackPanel('final')"><strong>最终反馈</strong><span>{{ feedbackPanels.final ? '收起' : '展开' }}</span></button>
          <label v-show="feedbackPanels.final"><textarea v-model="feedbackForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
        </section>

        <div class="button-row feedback-action-row"><button type="button" class="ghost-btn" :disabled="loading" @click="generateDraft">生成 AI 初稿</button><button type="button" class="ghost-btn" :disabled="loading" @click="copyFeedbackText(feedbackForm.final_feedback)">复制最终反馈</button><button class="primary-btn" :disabled="loading">保存最终反馈</button></div>
	      </form>

      <div v-if="showMaterialsModal" class="nested-modal-mask transparent-mask">
        <article class="paper-card modal-panel materials-floating-modal" :style="materialsModalStyle">
          <div class="modal-title draggable-title" @pointerdown="startMaterialsModalMove($event, 'move')">
            <div>
              <h3>课堂资料</h3>
              <small>{{ materialStatus }}</small>
            </div>
            <button type="button" class="icon-btn" @pointerdown.stop @click="closeMaterialsModal">×</button>
          </div>

          <div class="materials-header">
            <div>
              <strong>导入课堂资料</strong>
              <small>最多 {{ MAX_MATERIAL_IMAGES }} 个资料页面，支持 JPG、PNG、WEBP 和 PDF。Word 请先导出为 PDF 后上传。</small>
            </div>
          </div>

          <div class="materials-modal-body">
            <p class="materials-guide">上传课堂照片、试卷截图或 PDF 后，可以识别图片里的知识点、题型和易错点，并把提炼结果填入“课堂学习内容”，辅助后续生成课后反馈。浮窗可以拖到网页边缘半隐藏，方便一边对照资料一边填写。</p>

            <div v-if="materialImages.length" class="material-preview-grid">
              <article v-for="(image, index) in materialImages" :key="image.id" class="material-preview-item">
                <img :src="image.preview_url" alt="" />
                <div>
                  <strong>{{ image.file.name }}</strong>
                  <small>{{ image.source }} · {{ formatFileSize(image.file.size) }}</small>
                </div>
                <button type="button" class="icon-btn" :disabled="materialsAnalyzing || materialsConverting" @click="removeMaterialImage(index)">×</button>
              </article>
            </div>
            <p v-else class="settings-hint">还没有课堂资料。可以上传课堂照片、试卷截图，或直接选择 PDF。</p>

            <section v-if="materialAnalysis" class="analysis-result-panel">
              <div class="analysis-result-header">
                <strong>课堂资料提炼结果</strong>
                <button type="button" class="primary-btn" @click="applyMaterialAnalysis">填入课堂学习内容</button>
              </div>
              <p v-if="materialAnalysis.practice_summary">{{ materialAnalysis.practice_summary }}</p>
              <div class="analysis-columns">
                <div v-if="materialAnalysis.knowledge_points?.length">
                  <strong>知识点</strong>
                  <span v-for="item in materialAnalysis.knowledge_points" :key="item">{{ item }}</span>
                </div>
                <div v-if="materialAnalysis.question_types?.length">
                  <strong>题型</strong>
                  <span v-for="item in materialAnalysis.question_types" :key="item">{{ item }}</span>
                </div>
                <div v-if="materialAnalysis.weak_points?.length">
                  <strong>易错点/薄弱点</strong>
                  <span v-for="item in materialAnalysis.weak_points" :key="item">{{ item }}</span>
                </div>
              </div>
            </section>
          </div>

          <div class="button-row materials-action-row">
            <label class="file-picker-btn">
              选择图片/PDF
              <input ref="materialInput" type="file" :accept="MATERIAL_ACCEPT_TYPES" multiple @change="handleMaterialFiles" />
            </label>
            <button type="button" class="ghost-btn" :disabled="!materialImages.length || materialsAnalyzing || materialsConverting" @click="clearMaterialImages">清空</button>
            <button type="button" class="ghost-btn" :disabled="!materialImages.length || materialsAnalyzing || materialsConverting" @click="analyzeMaterialImages">
              {{ materialsConverting ? '正在转换 PDF...' : materialsAnalyzing ? '正在识别课堂资料...' : '识别并提炼课堂内容' }}
            </button>
          </div>

          <button class="resize-handle" type="button" aria-label="调整课堂资料浮窗大小" @pointerdown="startMaterialsModalMove($event, 'resize')"></button>
        </article>
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
          <p><strong>反馈标题：</strong>{{ detailFeedback.lesson_title || '未填写' }}</p><p><strong>上课时间：</strong>{{ detailFeedback.lesson_time }}</p><p><strong>课堂学习内容：</strong>{{ detailFeedback.lesson_summary }}</p><p><strong>课堂表现与知识掌握：</strong>{{ detailFeedback.performance_summary || '未填写' }}</p><p><strong>课后建议：</strong>{{ detailFeedback.advice_summary || '未填写' }}</p><p><strong>作业安排：</strong>{{ detailFeedback.homework_plan || '未填写' }}</p><h4>最终反馈</h4><pre>{{ detailFeedback.final_feedback }}</pre><details><summary>查看 AI 初稿</summary><pre>{{ detailFeedback.ai_draft }}</pre></details>
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
        <input v-model="oneStudentForm.name" placeholder="学生姓名" /><input v-model="oneStudentForm.grade" placeholder="年级" /><input v-model="oneStudentForm.subject" placeholder="科目" /><textarea v-model="oneStudentForm.note" class="auto-textarea" placeholder="备注" @input="autoResize"></textarea>
        <div class="button-row danger-row"><button class="primary-btn">保存学生信息</button><button type="button" class="danger-btn" @click="deleteOneStudent">删除学生</button></div>
      </form>
    </div>

    <div v-if="showClassModal" class="modal-mask">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveClass">
        <div class="modal-title"><h3>{{ editingClass ? '编辑班级' : '新建班级' }}</h3><button type="button" class="icon-btn" @click="showClassModal = false">×</button></div>
        <input v-model="classForm.name" placeholder="班级名称" /><textarea v-model="classForm.note" class="auto-textarea" placeholder="备注" @input="autoResize"></textarea>
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
        <input v-model="eveningStudentForm.name" placeholder="姓名" /><input v-model="eveningStudentForm.grade" placeholder="年级" /><input v-model="eveningStudentForm.school" placeholder="学校" /><textarea v-model="eveningStudentForm.note" class="auto-textarea" placeholder="备注" @input="autoResize"></textarea>
        <div class="button-row danger-row"><button class="primary-btn">保存学生信息</button><button type="button" class="danger-btn" @click="deleteEveningStudent">删除学生</button></div>
      </form>
    </div>

    <div v-if="showMonthlyModal" class="modal-mask">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="saveMonthlyFeedback">
        <div class="modal-title"><h3>新增月度反馈</h3><button type="button" class="icon-btn" @click="closeMonthlyModal">×</button></div>
        <label>反馈月份<input v-model="monthlyForm.feedback_month" type="month" /></label>
        <label>本月作业完成情况简述<textarea v-model="monthlyForm.homework_summary" class="auto-textarea" @input="autoResize"></textarea></label>
        <div class="button-row"><button type="button" class="ghost-btn" @click="generateMonthlyDraft">生成 AI 初稿</button><button class="primary-btn">保存月度反馈</button></div>
        <label>AI 初稿<textarea v-model="monthlyForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label><label>最终反馈<textarea v-model="monthlyForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
      </form>
    </div>

    <div v-if="eveningDetail" class="modal-mask">
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
