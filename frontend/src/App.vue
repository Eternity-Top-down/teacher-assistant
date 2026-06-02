<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { clearToken, downloadRequest, request, setToken } from './api'
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
const generatingMonthlyDraft = ref(false)
const generatingEveningBatch = ref(false)
const savingEveningBatch = ref(false)
const exportingEveningWord = ref(false)
const message = ref('')
const authMode = ref('login')

const oneStudents = ref([])
const currentStudent = ref(null)
const feedbacks = ref([])
const feedbackSearchResults = ref([])
const selectedFeedbackSearchIds = ref([])
const selectedStudentFeedbackIds = ref([])
const eveningFeedbackSearchResults = ref([])
const eveningFeedbackArchiveResults = ref([])
const selectedEveningArchiveKeys = ref([])
const selectedEveningFeedbackIds = ref([])
const showEveningFeedbackDetails = ref(false)
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
const eveningHistoryStudent = ref(null)
const eveningHistoryFeedbacks = ref([])
const loadingEveningHistory = ref(false)
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
const showAIConfigForm = ref(false)
const showEveningBatchWorkbench = ref(false)
const openEveningBatchAfterClassLoad = ref(false)
const showEveningExportModal = ref(false)
const activeStyleExampleType = ref('one_on_one')
const showWritingReference = ref(false)
const feedbackEntryMode = ref('raw')
const rawLessonNote = ref('')
const hasOrganizedLessonNote = ref(false)
const rawLessonNoteDirty = ref(false)
const organizeMissingFields = ref([])
const useStyleExamplesForDraft = ref(true)
const useStyleExamplesForMonthlyDraft = ref(true)
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
const EVENING_BATCH_DRAFT_PREFIX = 'evening_batch_draft_v1'
const WRITING_REFERENCE_VISIBLE_WIDTH = 132
const WRITING_REFERENCE_VISIBLE_HEIGHT = 76
const STYLE_EXAMPLE_PAGE_SIZE = 5
const MAX_ENABLED_STYLE_EXAMPLES = 5
const EVENING_PERIOD_TYPES = [
  { value: 'day', label: '按天' },
  { value: 'week', label: '按周' },
  { value: 'month', label: '按月' },
]
const COMMON_SUBJECTS = ['数学', '英语', '语文', '物理', '化学', '生物', '历史', '地理', '政治', '科学']
const EVENING_SUMMARY_PLACEHOLDER = '可写作业完成情况、晚辅纪律、做得好的地方、存在问题和建议。例如：作业完成不错，晚辅后半段有聊天，书写还需要更认真。'
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
const eveningBatchForm = reactive(newEveningBatchForm())
const eveningExportForm = reactive({ term_label: '', owner_name: '', export_subject: '', document_title: '', filename_base: '' })
const eveningExportSource = reactive({ mode: 'batch', class_id: null, class_name: '', period_type: '', period_value: '', count: 0 })
const eveningExportFilenameManuallyEdited = ref(false)
const editingEveningExportFilename = ref(false)
const eveningBatchRows = ref([])
const generationModelKey = ref('')
const settingsModelKey = ref('')
const aiSettingsForm = reactive({
  id: null,
  name: '',
  provider: 'deepseek',
  base_url: 'https://api.deepseek.com',
  model: 'deepseek-v4-pro',
  api_key: '',
  clear_api_key: false,
  make_active: true,
})
const styleExampleForm = reactive({ title: '', content: '', enabled: false })
const inlineStyleExampleForm = reactive({ title: '', content: '', enabled: false })
const styleExampleEditForm = reactive({ title: '', content: '', enabled: false })
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
    model: 'deepseek-v4-pro',
    hint: '使用 DeepSeek 官方 OpenAI-compatible 接入方式：Base URL 为 https://api.deepseek.com，模型名按当前平台默认配置使用 deepseek-v4-pro。',
    api_key_url: 'https://platform.deepseek.com/api_keys',
    docs_url: 'https://api-docs.deepseek.com/',
  },
  doubao: {
    label: '豆包 / 火山方舟',
    base_url: 'https://ark.cn-beijing.volces.com/api/v3',
    model: 'doubao-seed-2-0-pro-260215',
    hint: '使用火山方舟 OpenAI-compatible 接入方式；模型名需与控制台已开通模型或推理接入点保持一致。',
    api_key_url: 'https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey',
    docs_url: 'https://www.volcengine.com/docs/82379/1298459',
  },
  custom: { label: '自定义兼容接口', base_url: '', model: '', hint: '用于其他 OpenAI-compatible 文本生成模型。', api_key_url: '', docs_url: '' },
}

const isAuthed = computed(() => Boolean(teacher.value))
const teacherInitial = computed(() => (teacher.value?.email || 'T').slice(0, 1).toUpperCase())
const selectedAIPreset = computed(() => AI_PRESETS[aiSettingsForm.provider] || AI_PRESETS.custom)
const aiModelOptions = computed(() => aiSettings.value?.models || [])
const aiPersonalConfigs = computed(() => aiSettings.value?.configs || [])
const activeAIModel = computed(() => aiSettings.value?.active_model || null)
const aiTrialRemaining = computed(() => aiSettings.value?.trial_quota_remaining ?? 0)
const aiTrialTotal = computed(() => aiSettings.value?.trial_quota_total ?? 0)
const selectedGenerationModel = computed(() => aiModelOptions.value.find((model) => aiModelKey(model) === generationModelKey.value) || activeAIModel.value)
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
const selectedFeedbackSearchItems = computed(() =>
  feedbackSearchResults.value.filter((feedback) => selectedFeedbackSearchIds.value.includes(feedback.id))
)
const selectedStudentFeedbackItems = computed(() =>
  filteredStudentFeedbacks.value.filter((feedback) => selectedStudentFeedbackIds.value.includes(feedback.id))
)
const oneOnOneStyleExamples = computed(() => styleExamples.value.filter((example) => (example.feedback_type || 'one_on_one') === 'one_on_one'))
const eveningStyleExamples = computed(() => styleExamples.value.filter((example) => example.feedback_type === 'evening_feedback'))
const currentStyleExamples = computed(() =>
  activeStyleExampleType.value === 'evening_feedback' ? eveningStyleExamples.value : oneOnOneStyleExamples.value
)
const oneOnOneEnabledStyleExampleCount = computed(() => oneOnOneStyleExamples.value.filter((example) => example.enabled).length)
const eveningEnabledStyleExampleCount = computed(() => eveningStyleExamples.value.filter((example) => example.enabled).length)
function styleEnabledStatus(count, disabledText, standardText) {
  if (count && disabledText) return disabledText
  if (!count) return standardText
  if (count === 1) return '已选择 1 条样例参与生成'
  if (count <= 3) return `已选择 ${count} 条样例参与生成，建议优先选择你满意且愿意复用的反馈`
  return `已选择 ${count} 条样例参与生成，数量偏多时可能影响篇幅和语气稳定`
}

const styleGenerationStatus = computed(() =>
  styleEnabledStatus(
    oneOnOneEnabledStyleExampleCount.value,
    oneOnOneEnabledStyleExampleCount.value && !useStyleExamplesForDraft.value ? '本次已停用个人风格，将按标准结构生成' : '',
    '未启用样例，将按标准结构生成',
  )
)
const eveningStyleGenerationStatus = computed(() =>
  styleEnabledStatus(
    eveningEnabledStyleExampleCount.value,
    eveningEnabledStyleExampleCount.value && !useStyleExamplesForMonthlyDraft.value ? '本次已停用晚辅个人风格，将按标准晚辅写法生成' : '',
    '未启用晚辅样例，将按标准晚辅写法生成',
  )
)
const currentStyleGenerationStatus = computed(() =>
  activeStyleExampleType.value === 'evening_feedback' ? eveningStyleGenerationStatus.value : styleGenerationStatus.value
)
const styleExampleTotalPages = computed(() => totalPages(currentStyleExamples.value.length))
const feedbackStyleExampleTotalPages = computed(() => totalPages(currentStyleExamples.value.length))
const paginatedStyleExamples = computed(() => pageItems(currentStyleExamples.value, styleExamplePage.value))
const paginatedFeedbackStyleExamples = computed(() => pageItems(currentStyleExamples.value, feedbackStyleExamplePage.value))
const styleSettingsHint = computed(() =>
  activeStyleExampleType.value === 'evening_feedback'
    ? '当前管理晚辅反馈风格样例，只影响晚辅反馈生成。晚辅样例主要学习家长沟通语气、段落详略和作业完成反馈写法，不会影响一对一课后反馈。'
    : '当前管理一对一反馈风格样例，只影响一对一课后反馈生成。启用样例后，AI 会学习你的标题格式、四段课后反馈结构、语气和详略。'
)
const styleExampleTitlePlaceholder = computed(() =>
  activeStyleExampleType.value === 'evening_feedback' ? '例如：小明5月数学晚辅反馈' : '例如：小明第3次数学课（5.12）'
)
const styleExampleContentPlaceholder = computed(() =>
  activeStyleExampleType.value === 'evening_feedback'
    ? '例如：\n小明5月数学晚辅反馈\n\n本月晚辅中，小明的数学作业整体完成较认真，订正也比之前更及时……'
    : '例如：\n小明第3次数学课（5.12）\n\n📖1.课堂学习内容：\n本节课主要复习了一次函数图像与解析式……\n\n🌟2.课堂表现与知识掌握情况：\n……'
)
const styleExampleTitleAutoHelp = '这里只是样例库里的管理名称，不会被 AI 当成反馈标题学习；留空时会用反馈样例正文第一行。若标题不在正文第一行，请手动填写。'
const styleExampleTitleHelp = computed(() => styleExampleTitleAutoHelp)
const styleExampleContentHelp = computed(() =>
  activeStyleExampleType.value === 'evening_feedback'
    ? 'AI 只学习这里粘贴的晚辅反馈正文。若希望 AI 学习标题格式，请把标题行和正文一起放在这里；样例标题不会参与学习。'
    : 'AI 只学习这里粘贴的反馈正文。若希望 AI 学习标题格式，请把标题行和正文一起放在这里；样例标题不会参与学习。'
)
const styleExampleSelectionHelp = computed(() =>
  `样例库可以多保存；参与生成时建议只启用 1-3 条你满意且愿意复用的反馈，最多 ${MAX_ENABLED_STYLE_EXAMPLES} 条。`
)
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
const eveningBatchFilledRows = computed(() => eveningBatchRows.value.filter((row) => row.homework_summary.trim()))
const eveningBatchGenerateCount = computed(() =>
  eveningBatchFilledRows.value.length
)
const eveningBatchSaveCount = computed(() =>
  eveningBatchRows.value.filter((row) => row.final_feedback.trim()).length
)
const eveningBatchExportCount = computed(() => eveningBatchSaveCount.value)
const eveningExportCount = computed(() => eveningExportSource.mode === 'archive' ? eveningExportSource.count : eveningBatchExportCount.value)
const selectedEveningArchives = computed(() =>
  eveningFeedbackArchiveResults.value.filter((archive) => selectedEveningArchiveKeys.value.includes(eveningArchiveKey(archive)))
)
const selectedEveningFeedbacks = computed(() =>
  eveningFeedbackSearchResults.value.filter((feedback) => selectedEveningFeedbackIds.value.includes(feedback.id))
)
const eveningExportFilenameSuggestion = computed(() => {
  const suffix = `${eveningExportForm.owner_name.trim()}${eveningExportForm.export_subject.trim()}`.trim()
  const className = eveningExportSource.class_name || currentClass.value?.name || ''
  const base = `${eveningExportForm.term_label.trim()}${eveningExportPeriodLabel()}${className}晚辅反馈${suffix ? `——${suffix}` : ''}`
  return safeDocxFilename(base)
})
const eveningExportFilenamePreview = computed(() => `${safeDocxFilename(eveningExportForm.filename_base)}.docx`)
const eveningBatchDoneCount = computed(() => eveningBatchRows.value.filter((row) => row.feedback_id).length)
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
    student_name: '',
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
    class_id: '',
    student_name: '',
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

function eveningExportPeriodLabel() {
  const type = eveningExportSource.period_type || eveningBatchForm.period_type
  const value = eveningExportSource.period_value || eveningBatchForm.period_value || ''
  if (type === 'day') {
    const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/)
    return match ? `${Number(match[2])}.${Number(match[3])}` : value
  }
  if (type === 'week') {
    const match = value.match(/^(\d{4})-W(\d{2})$/)
    if (!match) return value
    const start = isoWeekStartDate(Number(match[1]), Number(match[2]))
    return `${start.getMonth() + 1}月第${Math.ceil(start.getDate() / 7)}周`
  }
  const match = value.match(/^(\d{4})-(\d{2})$/)
  return match ? `${Number(match[2])}月` : value
}

function isoWeekStartDate(year, week) {
  const date = new Date(year, 0, 1 + (week - 1) * 7)
  const day = date.getDay() || 7
  date.setDate(date.getDate() + (day <= 4 ? 1 - day : 8 - day))
  return date
}

function safeDocxFilename(value) {
  const cleaned = String(value || '').replace(/[\\/:*?"<>|\r\n]+/g, '').trim().replace(/\.docx$/i, '').trim()
  return cleaned || '晚辅反馈'
}

function resetEveningExportFilename() {
  eveningExportForm.filename_base = eveningExportFilenameSuggestion.value
  eveningExportFilenameManuallyEdited.value = false
  editingEveningExportFilename.value = false
}

function syncEveningExportFilename() {
  if (eveningExportFilenameManuallyEdited.value) return
  nextTick(() => {
    if (eveningExportFilenameManuallyEdited.value) return
    eveningExportForm.filename_base = eveningExportFilenameSuggestion.value
  })
}

function markEveningExportFilenameEdited() {
  eveningExportFilenameManuallyEdited.value = true
}

async function startEditingEveningExportFilename() {
  editingEveningExportFilename.value = true
  await nextTick()
  document.querySelector('.filename-preview-box input')?.focus()
}

function exportSubjectDefault() {
  return eveningBatchForm.default_subject || eveningBatchRows.value.find((row) => row.subject)?.subject || ''
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

function styleTypeLabel(type = activeStyleExampleType.value) {
  return type === 'evening_feedback' ? '晚辅' : '一对一'
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
    subject: '',
    homework_summary: '',
    ai_draft: '',
    final_feedback: '',
  }
}

function newEveningBatchForm() {
  return {
    period_type: 'day',
    period_value: currentDateInput(),
    default_subject: '',
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

function lessonNumberFromTitle(title = '') {
  const match = String(title).match(/第\s*(\d+)\s*次/)
  return match ? Number.parseInt(match[1], 10) : null
}

function nextOneOnOneLessonNumber(history = []) {
  const recentNumber = lessonNumberFromTitle(history[0]?.lesson_title)
  if (recentNumber) return recentNumber + 1
  const maxNumber = history.reduce((max, feedback) => {
    const number = lessonNumberFromTitle(feedback.lesson_title)
    return number && number > max ? number : max
  }, 0)
  return maxNumber ? maxNumber + 1 : history.length + 1
}

function defaultStyleExampleTitle() {
  if (activeStyleExampleType.value === 'evening_feedback') return '晚辅反馈样例'
  return '一对一课后反馈样例'
}

function firstLineStyleExampleTitle(content) {
  return String(content || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find(Boolean) || ''
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
  feedbackEntryMode.value = 'raw'
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
    feedback_entry_mode: feedbackEntryMode.value,
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
  feedbackEntryMode.value = draft.feedback_entry_mode || 'raw'
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

async function setFeedbackEntryMode(mode) {
  feedbackEntryMode.value = mode
  saveFeedbackDraft()
  await resizeAllTextareas()
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
  target.subject = source.subject || ''
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

function subjectWorkLabel(subject) {
  return subject?.trim() ? `${subject.trim()}作业` : '作业'
}

function eveningBatchFingerprint(row) {
  return JSON.stringify({
    feedback_id: row.feedback_id || null,
    subject: row.subject || '',
    homework_summary: row.homework_summary || '',
    ai_draft: row.ai_draft || '',
    final_feedback: row.final_feedback || '',
  })
}

function eveningBatchRowDirty(row) {
  return eveningBatchFingerprint(row) !== row.original_fingerprint
}

function eveningBatchDraftKey() {
  if (!teacher.value?.id || !currentClass.value?.id || !eveningBatchForm.period_type || !eveningBatchForm.period_value) return ''
  return [
    EVENING_BATCH_DRAFT_PREFIX,
    teacher.value.id,
    currentClass.value.id,
    eveningBatchForm.period_type,
    eveningBatchForm.period_value,
  ].join(':')
}

function eveningBatchRowHasLocalContent(row) {
  return Boolean(
    row.subject?.trim() ||
      row.homework_summary?.trim() ||
      row.ai_draft?.trim() ||
      row.final_feedback?.trim()
  )
}

function saveEveningBatchDraft() {
  const key = eveningBatchDraftKey()
  if (!key || !eveningBatchRows.value.length) return
  const rows = eveningBatchRows.value
    .filter((row) => (!row.feedback_id && eveningBatchRowHasLocalContent(row)) || eveningBatchRowDirty(row))
    .map((row) => ({
      student_id: row.student_id,
      feedback_id: row.feedback_id,
      subject: row.subject,
      homework_summary: row.homework_summary,
      ai_draft: row.ai_draft,
      final_feedback: row.final_feedback,
      selected_for_generate: row.selected_for_generate,
      generation_model_key: row.generation_model_key,
      last_default_subject: row.last_default_subject,
      status: row.status,
      original_fingerprint: row.original_fingerprint,
    }))
  try {
    if (rows.length) {
      localStorage.setItem(
        key,
        JSON.stringify({
          default_subject: eveningBatchForm.default_subject,
          rows,
          updated_at: new Date().toISOString(),
        })
      )
    } else {
      localStorage.removeItem(key)
    }
  } catch {
    showMessage('晚辅草稿保存失败，请先保存或复制重要内容')
  }
}

function restoreEveningBatchDraft() {
  const key = eveningBatchDraftKey()
  if (!key) return false
  let draft = null
  try {
    draft = JSON.parse(localStorage.getItem(key) || 'null')
  } catch {
    return false
  }
  const draftRows = Array.isArray(draft?.rows) ? draft.rows : []
  if (!draftRows.length) return false
  if (draft?.default_subject !== undefined) eveningBatchForm.default_subject = draft.default_subject || ''
  const draftMap = new Map(draftRows.map((row) => [row.student_id, row]))
  eveningBatchRows.value.forEach((row) => {
    const draftRow = draftMap.get(row.student_id)
    if (!draftRow) return
    if (row.feedback_id && draftRow.feedback_id && row.feedback_id !== draftRow.feedback_id) return
    row.subject = draftRow.subject || ''
    row.homework_summary = draftRow.homework_summary || ''
    row.ai_draft = draftRow.ai_draft || ''
    row.final_feedback = draftRow.final_feedback || ''
    row.selected_for_generate = draftRow.selected_for_generate !== false
    row.generation_model_key = draftRow.generation_model_key || ''
    row.last_default_subject = draftRow.last_default_subject || eveningBatchForm.default_subject
    row.error = ''
    row.original_fingerprint = draftRow.original_fingerprint || eveningBatchFingerprint({
      ...row,
      subject: '',
      homework_summary: '',
      ai_draft: '',
      final_feedback: '',
    })
    row.status = eveningBatchRowDirty(row) ? 'dirty' : (row.feedback_id ? 'saved' : 'idle')
  })
  return true
}

function clearEveningBatchDraftIfClean() {
  const key = eveningBatchDraftKey()
  if (!key) return
  const hasUnsaved = eveningBatchRows.value.some((row) =>
    (!row.feedback_id && eveningBatchRowHasLocalContent(row)) || eveningBatchRowDirty(row)
  )
  if (!hasUnsaved) localStorage.removeItem(key)
}

async function deleteEveningBatchDraft() {
  const key = eveningBatchDraftKey()
  if (!key) return showMessage('请先选择有效的反馈周期')
  if (!window.confirm('确定删除当前周期的未保存草稿吗？表格会重新载入已保存的晚辅反馈，未保存内容将无法恢复。')) return
  localStorage.removeItem(key)
  await loadEveningBatchFeedbacks()
  showMessage('当前周期草稿已删除')
}

function eveningBatchStatusText(row) {
  if (row.status === 'generating') return '生成中'
  if (row.status === 'saving') return '保存中'
  if (row.status === 'error') return row.error || '处理失败'
  if (eveningBatchRowDirty(row)) return row.feedback_id ? '已修改' : '待保存'
  if (row.feedback_id) return '已保存'
  if (row.homework_summary.trim()) return '可生成'
  return '未填写'
}

function makeEveningBatchRow(item) {
  const feedback = item.feedback || {}
  const row = {
    student_id: item.student.id,
    student_name: item.student.name,
    grade: item.student.grade || '',
    school: item.student.school || '',
    feedback_id: feedback.id || null,
    subject: feedback.subject || eveningBatchForm.default_subject || '',
    homework_summary: feedback.homework_summary || '',
    ai_draft: feedback.ai_draft || '',
    final_feedback: feedback.final_feedback || '',
    selected_for_generate: !feedback.final_feedback,
    generation_model_key: '',
    status: feedback.id ? 'saved' : 'idle',
    error: '',
    last_default_subject: feedback.subject ? '' : eveningBatchForm.default_subject,
    original_fingerprint: '',
  }
  row.original_fingerprint = eveningBatchFingerprint(row)
  return row
}

function markEveningBatchRowEdited(row) {
  row.error = ''
  row.status = eveningBatchRowDirty(row) ? 'dirty' : (row.feedback_id ? 'saved' : 'idle')
  if (row.homework_summary.trim() && !row.final_feedback.trim()) row.selected_for_generate = true
  saveEveningBatchDraft()
}

function updateEveningBatchRowModel(row) {
  row.error = ''
  saveEveningBatchDraft()
}

function applyDefaultSubjectToEveningBatch() {
  eveningBatchRows.value.forEach((row) => {
    if (!row.subject.trim() || row.subject === row.last_default_subject) {
      row.subject = eveningBatchForm.default_subject
      row.last_default_subject = eveningBatchForm.default_subject
      markEveningBatchRowEdited(row)
    }
  })
  saveEveningBatchDraft()
}

async function setEveningBatchPeriodType(type) {
  eveningBatchForm.period_type = type
  eveningBatchForm.period_value = defaultPeriodValue(type)
  await loadEveningBatchFeedbacks()
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
  syncGenerationModelSelection()
  syncSettingsModelSelection()
  resetAIConfigForm()
}

function aiModelKey(model) {
  if (!model) return ''
  return model.type === 'personal' ? `personal-${model.id}` : `platform-${model.id || 'default'}`
}

function syncGenerationModelSelection() {
  const options = aiSettings.value?.models || []
  if (generationModelKey.value && options.some((model) => aiModelKey(model) === generationModelKey.value)) return
  generationModelKey.value = aiModelKey(aiSettings.value?.active_model || options[0])
}

function syncSettingsModelSelection() {
  settingsModelKey.value = aiModelKey(aiSettings.value?.active_model || aiSettings.value?.models?.[0])
}

async function ensureAISettingsLoaded() {
  if (aiSettings.value?.models?.length) {
    syncGenerationModelSelection()
    return
  }
  await loadAISettings()
}

function selectedGenerationModelPayload() {
  const model = selectedGenerationModel.value
  if (!model) return {}
  return {
    model_type: model.type,
    platform_model_id: model.type === 'platform' ? model.id : '',
    config_id: model.type === 'personal' ? model.id : null,
  }
}

function modelPayloadFromKey(modelKey = '') {
  const model = aiModelOptions.value.find((item) => aiModelKey(item) === modelKey) || selectedGenerationModel.value
  if (!model) return {}
  return {
    model_type: model.type,
    platform_model_id: model.type === 'platform' ? model.id : '',
    config_id: model.type === 'personal' ? model.id : null,
  }
}

function eveningBatchRowModelKey(row) {
  return row.generation_model_key || generationModelKey.value
}

function generationModelHint() {
  const model = selectedGenerationModel.value
  if (!model) return '请先到设置页选择或添加可用模型'
  if (model.type === 'platform') return `${model.provider} · 平台试用 · 剩余 ${aiTrialRemaining.value} / ${aiTrialTotal.value} 次`
  return `${model.provider} · ${model.model}`
}

function resetAIConfigForm(source = null) {
  aiSettingsForm.id = source?.id || null
  aiSettingsForm.name = source?.name || ''
  aiSettingsForm.provider = source?.provider || 'deepseek'
  aiSettingsForm.base_url = source?.base_url || AI_PRESETS.deepseek.base_url
  aiSettingsForm.model = source?.model || AI_PRESETS.deepseek.model
  aiSettingsForm.api_key = ''
  aiSettingsForm.clear_api_key = false
  aiSettingsForm.make_active = true
}

async function selectSettingsAIModel() {
  const model = aiModelOptions.value.find((item) => aiModelKey(item) === settingsModelKey.value)
  if (!model || model.is_active || !model.has_api_key) return
  await selectAIModel(model)
}

function openNewAIConfigForm() {
  resetAIConfigForm()
  showAIConfigForm.value = true
}

function closeAIConfigForm() {
  resetAIConfigForm()
  showAIConfigForm.value = false
}

async function loadAISettings() {
  const data = await request('/settings/ai')
  assignAISettings(data)
}

async function loadStyleExamples() {
  const data = await request('/settings/style-examples')
  styleExamples.value = data.examples
  clampStyleExamplePages()
}

async function saveAISettings() {
  if (!aiSettingsForm.base_url.trim()) return showMessage('请填写 Base URL')
  if (!aiSettingsForm.model.trim()) return showMessage('请填写模型名')
  if (!aiSettingsForm.id && !aiSettingsForm.api_key.trim()) return showMessage('新增个人模型配置需要填写 API Key')
  loading.value = true
  try {
    const wasEditing = Boolean(aiSettingsForm.id)
    const path = aiSettingsForm.id ? `/settings/ai/configs/${aiSettingsForm.id}` : '/settings/ai/configs'
    const data = await request(path, {
      method: aiSettingsForm.id ? 'PUT' : 'POST',
      body: JSON.stringify({
        name: aiSettingsForm.name,
        provider: aiSettingsForm.provider,
        base_url: aiSettingsForm.base_url,
        model: aiSettingsForm.model,
        api_key: aiSettingsForm.api_key,
        clear_api_key: aiSettingsForm.clear_api_key,
        make_active: aiSettingsForm.make_active,
      }),
    })
    assignAISettings(data)
    showAIConfigForm.value = false
    showMessage(wasEditing ? '模型配置已更新' : '模型配置已保存')
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
        config_id: aiSettingsForm.id,
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
  if (!aiSettingsForm.id) return showMessage('请先选择要编辑的个人模型配置')
  if (!window.confirm('确定清除这条配置的 API Key 吗？清除后这条配置将无法生成 AI 反馈。')) return
  aiSettingsForm.api_key = ''
  aiSettingsForm.clear_api_key = true
  await saveAISettings()
}

function editAIConfig(config) {
  resetAIConfigForm(config)
  showAIConfigForm.value = true
}

async function selectAIModel(model) {
  loading.value = true
  try {
    const data = await request('/settings/ai/select', {
      method: 'POST',
      body: JSON.stringify({
        model_type: model.type,
        platform_model_id: model.type === 'platform' ? model.id : '',
        config_id: model.type === 'personal' ? model.id : null,
      }),
    })
    assignAISettings(data)
    showMessage(`已切换到 ${model.name}`)
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function deleteAIConfig(config) {
  if (!window.confirm(`确定删除模型配置“${config.name}”吗？`)) return
  loading.value = true
  try {
    const data = await request(`/settings/ai/configs/${config.id}`, { method: 'DELETE' })
    assignAISettings(data)
    showMessage('模型配置已删除')
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

function enabledStyleExampleCountFor(type) {
  return styleExamples.value.filter((example) => (example.feedback_type || 'one_on_one') === type && example.enabled).length
}

async function createStyleExampleFromForm(form, successMessage = '风格样例已保存', feedbackType = activeStyleExampleType.value) {
  if (!form.content.trim()) return showMessage('请粘贴一段反馈样例')
  if (form.enabled && enabledStyleExampleCountFor(feedbackType) >= MAX_ENABLED_STYLE_EXAMPLES) {
    return showMessage(`最多启用 5 条${styleTypeLabel(feedbackType)}风格样例参与生成，建议 1-3 条；请先停用一条差异较大的样例`)
  }
  const title = form.title.trim() || firstLineStyleExampleTitle(form.content) || (form === inlineStyleExampleForm ? defaultStyleExampleTitle() : '')
  loading.value = true
  try {
    await request('/settings/style-examples', {
      method: 'POST',
      body: JSON.stringify({
        title,
        content: form.content,
        enabled: form.enabled,
        feedback_type: feedbackType,
      }),
    })
    Object.assign(form, { title: '', content: '', enabled: false })
    await loadStyleExamples()
    showMessage(successMessage)
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function saveStyleExample() {
  await createStyleExampleFromForm(styleExampleForm, `已保存到${styleTypeLabel()}样例库`, activeStyleExampleType.value)
}

async function saveInlineStyleExample() {
  await createStyleExampleFromForm(inlineStyleExampleForm, `已保存到${styleTypeLabel()}样例库，可继续填写反馈`)
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
    enabledStyleExampleCountFor(detailStyleExample.value?.feedback_type || 'one_on_one') >= MAX_ENABLED_STYLE_EXAMPLES
  ) {
    return showMessage(`最多启用 5 条${styleTypeLabel(detailStyleExample.value?.feedback_type)}风格样例参与生成，建议 1-3 条；请先停用一条差异较大的样例`)
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
  if (!example.enabled && enabledStyleExampleCountFor(example.feedback_type || 'one_on_one') >= MAX_ENABLED_STYLE_EXAMPLES) {
    return showMessage(`最多启用 5 条${styleTypeLabel(example.feedback_type)}风格样例参与生成，建议 1-3 条；请先停用一条差异较大的样例`)
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
  if (feedbackSearchForm.student_name?.trim()) params.set('student_name', feedbackSearchForm.student_name.trim())
  const query = params.toString()
  return query ? `/feedbacks?${query}` : '/feedbacks'
}

function eveningFeedbackSearchQuery() {
  const params = new URLSearchParams()
  if (eveningFeedbackSearchForm.start_date) params.set('start_date', eveningFeedbackSearchForm.start_date)
  if (eveningFeedbackSearchForm.end_date) params.set('end_date', eveningFeedbackSearchForm.end_date)
  if (eveningFeedbackSearchForm.period_type) params.set('period_type', eveningFeedbackSearchForm.period_type)
  if (eveningFeedbackSearchForm.class_id) params.set('class_id', eveningFeedbackSearchForm.class_id)
  if (eveningFeedbackSearchForm.student_name?.trim()) params.set('student_name', eveningFeedbackSearchForm.student_name.trim())
  const query = params.toString()
  return query ? `/evening/feedbacks?${query}` : '/evening/feedbacks'
}

function eveningFeedbackArchiveQuery() {
  const params = new URLSearchParams()
  if (eveningFeedbackSearchForm.start_date) params.set('start_date', eveningFeedbackSearchForm.start_date)
  if (eveningFeedbackSearchForm.end_date) params.set('end_date', eveningFeedbackSearchForm.end_date)
  if (eveningFeedbackSearchForm.period_type) params.set('period_type', eveningFeedbackSearchForm.period_type)
  if (eveningFeedbackSearchForm.class_id) params.set('class_id', eveningFeedbackSearchForm.class_id)
  const query = params.toString()
  return query ? `/evening/feedbacks/archive?${query}` : '/evening/feedbacks/archive'
}

async function loadFeedbackSearchResults() {
  loading.value = true
  try {
    const data = await request(feedbackSearchQuery())
    feedbackSearchResults.value = data.feedbacks
    selectedFeedbackSearchIds.value = selectedFeedbackSearchIds.value.filter((id) =>
      feedbackSearchResults.value.some((feedback) => feedback.id === id)
    )
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

function toggleFeedbackSearchSelection(feedback) {
  selectedFeedbackSearchIds.value = selectedFeedbackSearchIds.value.includes(feedback.id)
    ? selectedFeedbackSearchIds.value.filter((id) => id !== feedback.id)
    : [...selectedFeedbackSearchIds.value, feedback.id]
}

function toggleAllFeedbackSearchSelection() {
  if (selectedFeedbackSearchIds.value.length === feedbackSearchResults.value.length) {
    selectedFeedbackSearchIds.value = []
  } else {
    selectedFeedbackSearchIds.value = feedbackSearchResults.value.map((feedback) => feedback.id)
  }
}

function toggleStudentFeedbackSelection(feedback) {
  selectedStudentFeedbackIds.value = selectedStudentFeedbackIds.value.includes(feedback.id)
    ? selectedStudentFeedbackIds.value.filter((id) => id !== feedback.id)
    : [...selectedStudentFeedbackIds.value, feedback.id]
}

function toggleAllStudentFeedbackSelection() {
  const visibleIds = filteredStudentFeedbacks.value.map((feedback) => feedback.id)
  if (selectedStudentFeedbackItems.value.length === filteredStudentFeedbacks.value.length) {
    selectedStudentFeedbackIds.value = selectedStudentFeedbackIds.value.filter((id) => !visibleIds.includes(id))
  } else {
    selectedStudentFeedbackIds.value = [...new Set([...selectedStudentFeedbackIds.value, ...visibleIds])]
  }
}

async function deleteOneOnOneFeedbackItems(ids, label, refresh) {
  if (!ids.length) return showMessage('请选择要删除的一对一反馈')
  if (!window.confirm(`确定删除${label}的 ${ids.length} 条一对一反馈吗？删除后无法恢复。`)) return
  loading.value = true
  try {
    const data = await request('/feedbacks/batch', {
      method: 'DELETE',
      body: JSON.stringify({ ids }),
    })
    await refresh()
    showMessage(`已删除 ${data.deleted_count || 0} 条一对一反馈`)
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function deleteSelectedFeedbackSearchItems() {
  const ids = selectedFeedbackSearchItems.value.map((feedback) => feedback.id)
  await deleteOneOnOneFeedbackItems(ids, '选中', async () => {
    selectedFeedbackSearchIds.value = []
    await loadFeedbackSearchResults()
  })
}

async function deleteSelectedStudentFeedbackItems() {
  const ids = selectedStudentFeedbackItems.value.map((feedback) => feedback.id)
  await deleteOneOnOneFeedbackItems(ids, '选中', async () => {
    selectedStudentFeedbackIds.value = []
    await loadOneStudentContext(true)
  })
}

async function loadEveningFeedbackSearchResults() {
  loading.value = true
  try {
    if (!eveningClasses.value.length) await loadEveningClasses()
    const [feedbackData, archiveData] = await Promise.all([
      request(eveningFeedbackSearchQuery()),
      request(eveningFeedbackArchiveQuery()),
    ])
    eveningFeedbackSearchResults.value = feedbackData.feedbacks
    eveningFeedbackArchiveResults.value = archiveData.archives || []
    selectedEveningArchiveKeys.value = selectedEveningArchiveKeys.value.filter((key) =>
      eveningFeedbackArchiveResults.value.some((archive) => eveningArchiveKey(archive) === key)
    )
    selectedEveningFeedbackIds.value = selectedEveningFeedbackIds.value.filter((id) =>
      eveningFeedbackSearchResults.value.some((feedback) => feedback.id === id)
    )
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

function eveningArchiveKey(archive) {
  return `${archive.class_id}:${archive.period_type}:${archive.period_value}`
}

function toggleEveningArchiveSelection(archive) {
  const key = eveningArchiveKey(archive)
  selectedEveningArchiveKeys.value = selectedEveningArchiveKeys.value.includes(key)
    ? selectedEveningArchiveKeys.value.filter((item) => item !== key)
    : [...selectedEveningArchiveKeys.value, key]
}

function toggleAllEveningArchiveSelection() {
  if (selectedEveningArchiveKeys.value.length === eveningFeedbackArchiveResults.value.length) {
    selectedEveningArchiveKeys.value = []
  } else {
    selectedEveningArchiveKeys.value = eveningFeedbackArchiveResults.value.map(eveningArchiveKey)
  }
}

function toggleEveningFeedbackSelection(feedback) {
  selectedEveningFeedbackIds.value = selectedEveningFeedbackIds.value.includes(feedback.id)
    ? selectedEveningFeedbackIds.value.filter((id) => id !== feedback.id)
    : [...selectedEveningFeedbackIds.value, feedback.id]
}

function toggleAllEveningFeedbackSelection() {
  if (selectedEveningFeedbackIds.value.length === eveningFeedbackSearchResults.value.length) {
    selectedEveningFeedbackIds.value = []
  } else {
    selectedEveningFeedbackIds.value = eveningFeedbackSearchResults.value.map((feedback) => feedback.id)
  }
}

function openEveningArchiveInClass(archive) {
  setEveningBatchPeriodType(archive.period_type)
  eveningBatchForm.period_value = archive.period_value
  openEveningBatchAfterClassLoad.value = true
  go(`#/evening/classes/${archive.class_id}`)
}

async function deleteEveningArchiveItems(archives, scopeText) {
  if (!archives.length) return showMessage('请选择要删除的反馈归档')
  const feedbackCount = archives.reduce((total, archive) => total + Number(archive.feedback_count || 0), 0)
  if (!window.confirm(`确定删除${scopeText}的 ${archives.length} 个归档、共 ${feedbackCount} 条晚辅反馈吗？删除后无法恢复。`)) return
  loading.value = true
  try {
    const data = await request('/evening/feedbacks/archive/batch', {
      method: 'DELETE',
      body: JSON.stringify({
        items: archives.map((archive) => ({
          class_id: archive.class_id,
          period_type: archive.period_type,
          period_value: archive.period_value,
        })),
      }),
    })
    selectedEveningArchiveKeys.value = []
    await loadEveningFeedbackSearchResults()
    showMessage(`已删除 ${data.deleted_count || 0} 条晚辅反馈`)
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
}

async function deleteSelectedEveningArchives() {
  await deleteEveningArchiveItems(selectedEveningArchives.value, '选中')
}

async function deleteCurrentEveningArchiveResults() {
  await deleteEveningArchiveItems(eveningFeedbackArchiveResults.value, '当前查询结果下')
}

async function deleteSelectedEveningFeedbackDetails() {
  if (!selectedEveningFeedbacks.value.length) return showMessage('请选择要删除的反馈明细')
  if (!window.confirm(`确定删除选中的 ${selectedEveningFeedbacks.value.length} 条晚辅反馈明细吗？删除后无法恢复。`)) return
  loading.value = true
  try {
    const data = await request('/evening/feedbacks/batch', {
      method: 'DELETE',
      body: JSON.stringify({ ids: selectedEveningFeedbackIds.value }),
    })
    selectedEveningFeedbackIds.value = []
    await loadEveningFeedbackSearchResults()
    showMessage(`已删除 ${data.deleted_count || 0} 条晚辅反馈`)
  } catch (error) {
    showMessage(error.message)
  } finally {
    loading.value = false
  }
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
    selectedStudentFeedbackIds.value = selectedStudentFeedbackIds.value.filter((feedbackId) =>
      feedbacks.value.some((feedback) => feedback.id === feedbackId)
    )
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
  feedbackForm.lesson_title = `${displayName}第${nextOneOnOneLessonNumber(feedbacks.value)}次${subject}课`
  try {
    await Promise.all([loadStyleExamples(), ensureAISettingsLoaded()])
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

async function openFeedbackStyleModal(type = 'one_on_one') {
  activeStyleExampleType.value = type
  feedbackStyleExamplePage.value = 1
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
        ...selectedGenerationModelPayload(),
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
    await loadAISettings()
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
        ...selectedGenerationModelPayload(),
      }),
    })
    feedbackForm.ai_draft = data.draft
    feedbackForm.final_feedback = data.draft
    feedbackForm.lesson_title = titleForGenerate(feedbackForm.lesson_title, feedbackForm.lesson_time)
    feedbackPanels.final = true
    await resizeAllTextareas()
    await loadAISettings()
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
    selectedFeedbackSearchIds.value = selectedFeedbackSearchIds.value.filter((id) => id !== detailFeedback.value.id)
    selectedStudentFeedbackIds.value = selectedStudentFeedbackIds.value.filter((id) => id !== detailFeedback.value.id)
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

async function addCurrentEveningFeedbackAsStyleExample() {
  if (!eveningDetail.value) return
  const defaultTitle = `晚辅反馈样例 ${eveningDetail.value.period_label || ''}`.trim()
  loading.value = true
  try {
    await request('/settings/style-examples/from-feedback', {
      method: 'POST',
      body: JSON.stringify({
        feedback_type: 'evening_feedback',
        feedback_id: eveningDetail.value.id,
        title: defaultTitle,
      }),
    })
    await loadStyleExamples()
    showMessage('已设为晚辅风格样例')
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
  if (!openEveningBatchAfterClassLoad.value) showEveningBatchWorkbench.value = false
  const id = route.value.split('/')[3]
  const [classData, studentData] = await Promise.all([
    request(`/evening/classes/${id}`),
    request(`/evening/classes/${id}/students`),
  ])
  currentClass.value = classData.class
  eveningStudents.value = studentData.students
  await ensureAISettingsLoaded()
  await loadEveningBatchFeedbacks()
  if (openEveningBatchAfterClassLoad.value) {
    showEveningBatchWorkbench.value = true
    openEveningBatchAfterClassLoad.value = false
  }
}

async function loadEveningBatchFeedbacks() {
  if (!currentClass.value?.id || !eveningBatchForm.period_value) return
  const params = new URLSearchParams({
    period_type: eveningBatchForm.period_type,
    period_value: eveningBatchForm.period_value,
  })
  const data = await request(`/evening/classes/${currentClass.value.id}/feedbacks/batch?${params}`)
  eveningBatchRows.value = data.items.map(makeEveningBatchRow)
  if (restoreEveningBatchDraft()) {
    showEveningBatchWorkbench.value = true
    showMessage('已恢复未保存的晚辅填写草稿')
  }
  await resizeAllTextareas()
}

async function generateEveningBatchDrafts(rows = null) {
  const targetRows = rows || eveningBatchRows.value.filter((row) => row.homework_summary.trim())
  if (!targetRows.length) return showMessage('请先填写需要生成的学生情况')
  generatingEveningBatch.value = true
  targetRows.forEach((row) => {
    row.status = 'generating'
    row.error = ''
  })
  try {
    const rowGroups = new Map()
    targetRows.forEach((row) => {
      const key = eveningBatchRowModelKey(row)
      rowGroups.set(key, [...(rowGroups.get(key) || []), row])
    })
    let successCount = 0
    let failedCount = 0
    for (const [modelKey, groupedRows] of rowGroups.entries()) {
      try {
        const data = await request(`/evening/classes/${currentClass.value.id}/feedbacks/batch/generate`, {
          method: 'POST',
          body: JSON.stringify({
            period_type: eveningBatchForm.period_type,
            period_value: eveningBatchForm.period_value,
            use_style_examples: useStyleExamplesForMonthlyDraft.value,
            ...modelPayloadFromKey(modelKey),
            items: groupedRows.map((row) => ({
              student_id: row.student_id,
              subject: row.subject,
              homework_summary: row.homework_summary,
            })),
          }),
        })
        const resultMap = new Map(data.results.map((result) => [result.student_id, result]))
        groupedRows.forEach((row) => {
          const result = resultMap.get(row.student_id)
          if (result?.ok) {
            row.ai_draft = result.draft
            row.final_feedback = result.draft
            row.status = 'dirty'
            row.error = ''
            successCount += 1
          } else {
            row.status = 'error'
            row.error = result?.error || '生成失败'
            failedCount += 1
          }
        })
      } catch (error) {
        groupedRows.forEach((row) => {
          row.status = 'error'
          row.error = error.message
          failedCount += 1
        })
      }
    }
    await loadAISettings()
    saveEveningBatchDraft()
    showMessage(failedCount ? `已生成 ${successCount} 条，${failedCount} 条失败` : `已生成 ${successCount} 条晚辅初稿`)
  } catch (error) {
    targetRows.forEach((row) => {
      row.status = 'error'
      row.error = error.message
    })
    showMessage(error.message)
  } finally {
    generatingEveningBatch.value = false
    await resizeAllTextareas()
  }
}

async function generateEveningBatchRow(row) {
  if (!row.homework_summary.trim()) return showMessage('请先填写这名学生的情况')
  row.selected_for_generate = true
  await generateEveningBatchDrafts([row])
}

async function saveEveningBatchRows(rows, successMessage = '') {
  const targetRows = rows.filter((row) => row.final_feedback.trim())
  if (!targetRows.length) return showMessage('没有需要保存的晚辅反馈')
  savingEveningBatch.value = true
  targetRows.forEach((row) => {
    row.status = 'saving'
    row.error = ''
  })
  try {
    const data = await request(`/evening/classes/${currentClass.value.id}/feedbacks/batch`, {
      method: 'POST',
      body: JSON.stringify({
        period_type: eveningBatchForm.period_type,
        period_value: eveningBatchForm.period_value,
        items: targetRows.map((row) => ({
          feedback_id: row.feedback_id,
          student_id: row.student_id,
          subject: row.subject,
          homework_summary: row.homework_summary,
          ai_draft: row.ai_draft,
          final_feedback: row.final_feedback,
        })),
      }),
    })
    const resultMap = new Map(data.results.map((result) => [result.student_id, result]))
    targetRows.forEach((row) => {
      const result = resultMap.get(row.student_id)
      if (result?.ok) {
        const feedback = result.feedback || {}
        row.feedback_id = feedback.id || row.feedback_id
        row.subject = feedback.subject || row.subject
        row.homework_summary = feedback.homework_summary || row.homework_summary
        row.ai_draft = feedback.ai_draft || row.ai_draft
        row.final_feedback = feedback.final_feedback || row.final_feedback
        row.selected_for_generate = false
        row.error = ''
        row.status = 'saved'
        row.original_fingerprint = eveningBatchFingerprint(row)
      } else {
        row.status = 'error'
        row.error = result?.error || '保存失败'
      }
    })
    const successCount = data.results.filter((result) => result.ok).length
    saveEveningBatchDraft()
    clearEveningBatchDraftIfClean()
    showMessage(successMessage || `已保存 ${successCount} 条晚辅反馈`)
  } catch (error) {
    targetRows.forEach((row) => {
      row.status = 'error'
      row.error = error.message
    })
    showMessage(error.message)
  } finally {
    savingEveningBatch.value = false
  }
}

async function saveEveningBatchFeedbacks() {
  await saveEveningBatchRows(
    eveningBatchRows.value.filter((row) => row.final_feedback.trim())
  )
}

function openEveningBatchExportModal() {
  if (!eveningBatchExportCount.value) return showMessage('没有可导出的晚辅反馈')
  Object.assign(eveningExportSource, {
    mode: 'batch',
    class_id: currentClass.value?.id || null,
    class_name: currentClass.value?.name || '',
    period_type: eveningBatchForm.period_type,
    period_value: eveningBatchForm.period_value,
    count: eveningBatchExportCount.value,
  })
  eveningExportForm.export_subject = exportSubjectDefault()
  eveningExportForm.document_title = `${eveningExportForm.term_label || ''}${currentClass.value?.name || ''}晚辅`
  resetEveningExportFilename()
  editingEveningExportFilename.value = false
  showEveningExportModal.value = true
}

function openEveningArchiveExportModal(archive) {
  if (!archive?.feedback_count) return showMessage('没有可导出的晚辅反馈')
  Object.assign(eveningExportSource, {
    mode: 'archive',
    class_id: archive.class_id || currentClass.value?.id || null,
    class_name: archive.class_name || currentClass.value?.name || '',
    period_type: archive.period_type,
    period_value: archive.period_value,
    count: archive.feedback_count,
  })
  eveningExportForm.export_subject = archive.subjects?.split(',').filter(Boolean).join('、') || exportSubjectDefault()
  eveningExportForm.document_title = `${eveningExportForm.term_label || ''}${eveningExportSource.class_name || ''}晚辅`
  resetEveningExportFilename()
  editingEveningExportFilename.value = false
  showEveningExportModal.value = true
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename || '晚辅反馈.docx'
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

async function exportEveningBatchWord() {
  const isArchiveExport = eveningExportSource.mode === 'archive'
  const rows = eveningBatchRows.value.filter((row) => row.final_feedback.trim())
  if (!isArchiveExport && !rows.length) return showMessage('没有可导出的晚辅反馈')
  if (!eveningExportSource.period_value) return showMessage('请选择反馈时间')
  exportingEveningWord.value = true
  try {
    const payload = {
      period_type: eveningExportSource.period_type,
      period_value: eveningExportSource.period_value,
      term_label: eveningExportForm.term_label,
      owner_name: eveningExportForm.owner_name,
      export_subject: eveningExportForm.export_subject,
      document_title: eveningExportForm.document_title,
      filename_base: eveningExportForm.filename_base,
    }
    if (!isArchiveExport) {
      payload.items = rows.map((row) => ({
        student_id: row.student_id,
        student_name: row.student_name,
        final_feedback: row.final_feedback,
      }))
    }
    const exportClassId = eveningExportSource.class_id || currentClass.value?.id
    const endpoint = isArchiveExport
      ? `/evening/classes/${exportClassId}/feedbacks/archive/export`
      : `/evening/classes/${exportClassId}/feedbacks/batch/export`
    const { blob, filename } = await downloadRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    downloadBlob(blob, filename)
    showEveningExportModal.value = false
    showMessage('已导出 Word')
  } catch (error) {
    showMessage(error.message)
  } finally {
    exportingEveningWord.value = false
  }
}

async function saveEveningBatchRow(row) {
  if (!row.final_feedback.trim()) return showMessage('请先生成或填写这名学生的最终反馈')
  await saveEveningBatchRows([row], `${row.student_name}的晚辅反馈已保存`)
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
    showEveningBatchWorkbench.value = false
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
  useStyleExamplesForMonthlyDraft.value = true
  ensureAISettingsLoaded().catch((error) => showMessage(error.message))
  const selectedStudent = student || currentEveningStudent.value || eveningStudents.value[0]
  monthlyForm.student_id = selectedStudent?.id || ''
  showMonthlyModal.value = true
  resizeAllTextareas()
}

async function generateMonthlyDraft() {
  if (!monthlyForm.student_id) return showMessage('请选择晚辅学生')
  if (!monthlyForm.period_value) return showMessage('请选择反馈时间')
  if (!monthlyForm.homework_summary.trim()) return showMessage('请填写作业完成情况简述')
  generatingMonthlyDraft.value = true
  loading.value = true
  try {
    const classId = currentClass.value?.id || currentEveningStudent.value?.class_id
    const data = await request(`/evening/classes/${classId}/feedbacks/generate`, {
      method: 'POST',
      body: JSON.stringify({
        student_id: Number(monthlyForm.student_id),
        period_type: monthlyForm.period_type,
        period_value: monthlyForm.period_value,
        subject: monthlyForm.subject,
        homework_summary: monthlyForm.homework_summary,
        use_style_examples: useStyleExamplesForMonthlyDraft.value,
        ...selectedGenerationModelPayload(),
      }),
    })
    monthlyForm.ai_draft = data.draft
    monthlyForm.final_feedback = data.draft
    await resizeAllTextareas()
    await loadAISettings()
    showMessage('AI 初稿已生成')
  } catch (error) {
    showMessage(error.message)
  } finally {
    generatingMonthlyDraft.value = false
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

async function openEveningStudentHistory(row) {
  eveningHistoryStudent.value = {
    id: row.student_id,
    name: row.student_name,
  }
  eveningHistoryFeedbacks.value = []
  loadingEveningHistory.value = true
  try {
    const data = await request(`/evening/students/${row.student_id}/feedbacks`)
    eveningHistoryFeedbacks.value = data.feedbacks.map((feedback) => ({
      ...feedback,
      student_name: row.student_name,
    }))
  } catch (error) {
    showMessage(error.message)
    eveningHistoryStudent.value = null
  } finally {
    loadingEveningHistory.value = false
  }
}

function closeEveningStudentHistory() {
  eveningHistoryStudent.value = null
  eveningHistoryFeedbacks.value = []
  loadingEveningHistory.value = false
}

function openEveningHistoryDetail(feedback) {
  closeEveningStudentHistory()
  openEveningDetail(feedback)
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
    <datalist id="subject-options">
      <option v-for="subject in COMMON_SUBJECTS" :key="subject" :value="subject"></option>
    </datalist>
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
            <label>学生姓名<input v-model="feedbackSearchForm.student_name" placeholder="输入姓名关键字" /></label>
            <label>开始日期<input v-model="feedbackSearchForm.start_date" type="date" /></label>
            <label>结束日期<input v-model="feedbackSearchForm.end_date" type="date" /></label>
            <div class="button-row">
              <button class="primary-btn" :disabled="loading">查询</button>
              <button type="button" class="ghost-btn" :disabled="loading" @click="resetFeedbackSearch">最近 30 天</button>
              <button type="button" class="ghost-btn" :disabled="loading" @click="feedbackSearchForm.start_date = ''; feedbackSearchForm.end_date = ''; feedbackSearchForm.student_name = ''; loadFeedbackSearchResults()">清空</button>
            </div>
          </form>
          <div class="history-header">
            <div><h3>反馈列表</h3><small>选中后可批量删除。</small></div>
            <div class="button-row">
              <button type="button" class="ghost-btn" :disabled="!feedbackSearchResults.length" @click="toggleAllFeedbackSearchSelection">{{ selectedFeedbackSearchIds.length === feedbackSearchResults.length && feedbackSearchResults.length ? '取消全选' : '全选当前' }}</button>
              <button type="button" class="danger-btn" :disabled="loading || !selectedFeedbackSearchItems.length" @click="deleteSelectedFeedbackSearchItems">删除选中</button>
            </div>
          </div>
          <div class="history-list">
            <article v-for="feedback in feedbackSearchResults" :key="feedback.id" class="history-card feedback-card feedback-search-card selectable-feedback-card" :class="{ selected: selectedFeedbackSearchIds.includes(feedback.id) }">
              <label class="archive-select-check" @click.stop>
                <input type="checkbox" :checked="selectedFeedbackSearchIds.includes(feedback.id)" @change="toggleFeedbackSearchSelection(feedback)" />
              </label>
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
              <h3>晚辅反馈归档</h3>
              <small>{{ searchRangeLabel(eveningFeedbackSearchForm.start_date, eveningFeedbackSearchForm.end_date) }} · {{ eveningFeedbackArchiveResults.length }} 个归档 · {{ eveningFeedbackSearchResults.length }} 条明细</small>
            </div>
            <label>晚辅班级<select v-model="eveningFeedbackSearchForm.class_id"><option value="">全部班级</option><option v-for="cls in eveningClasses" :key="cls.id" :value="cls.id">{{ cls.name }}</option></select></label>
            <label>反馈类型<select v-model="eveningFeedbackSearchForm.period_type"><option value="">全部</option><option v-for="type in EVENING_PERIOD_TYPES" :key="type.value" :value="type.value">{{ type.label }}</option></select></label>
            <label>学生姓名（仅筛选明细）<input v-model="eveningFeedbackSearchForm.student_name" placeholder="输入姓名关键字" /></label>
            <label>开始日期<input v-model="eveningFeedbackSearchForm.start_date" type="date" /></label>
            <label>结束日期<input v-model="eveningFeedbackSearchForm.end_date" type="date" /></label>
            <div class="button-row">
              <button class="primary-btn" :disabled="loading">查询</button>
              <button type="button" class="ghost-btn" :disabled="loading" @click="resetEveningFeedbackSearch">最近 90 天</button>
              <button type="button" class="ghost-btn" :disabled="loading" @click="eveningFeedbackSearchForm.start_date = ''; eveningFeedbackSearchForm.end_date = ''; eveningFeedbackSearchForm.period_type = ''; eveningFeedbackSearchForm.class_id = ''; eveningFeedbackSearchForm.student_name = ''; loadEveningFeedbackSearchResults()">清空</button>
            </div>
          </form>
          <section class="paper-card evening-archive-panel">
            <div class="history-header">
              <div>
                <h3>班级归档目录</h3>
                <small>按班级和周期管理，可导出整班 Word，也可批量删除归档。</small>
              </div>
              <div class="button-row">
                <button type="button" class="ghost-btn" :disabled="!eveningFeedbackArchiveResults.length" @click="toggleAllEveningArchiveSelection">{{ selectedEveningArchiveKeys.length === eveningFeedbackArchiveResults.length && eveningFeedbackArchiveResults.length ? '取消全选' : '全选当前' }}</button>
                <button type="button" class="danger-btn" :disabled="loading || !selectedEveningArchiveKeys.length" @click="deleteSelectedEveningArchives">删除选中</button>
                <button type="button" class="danger-btn" :disabled="loading || !eveningFeedbackArchiveResults.length" @click="deleteCurrentEveningArchiveResults">删除当前查询结果</button>
              </div>
            </div>
            <div v-if="eveningFeedbackArchiveResults.length" class="history-list evening-archive-list">
              <article v-for="archive in eveningFeedbackArchiveResults" :key="eveningArchiveKey(archive)" class="history-card evening-archive-card" :class="{ selected: selectedEveningArchiveKeys.includes(eveningArchiveKey(archive)) }">
                <label class="archive-select-check" @click.stop>
                  <input type="checkbox" :checked="selectedEveningArchiveKeys.includes(eveningArchiveKey(archive))" @change="toggleEveningArchiveSelection(archive)" />
                </label>
                <button class="feedback-card-main" type="button" @click="openEveningArchiveInClass(archive)">
                  <strong>{{ archive.class_name }} · {{ archive.period_label }}</strong>
                  <span>{{ periodTypeLabel(archive.period_type) }} · {{ archive.feedback_count }} 条反馈 · {{ archive.subjects ? archive.subjects.split(',').join('、') : '未填学科' }}</span>
                  <small>点击进入班级，可继续按学生处理该班反馈。</small>
                </button>
                <button type="button" class="ghost-btn" :disabled="exportingEveningWord" @click="openEveningArchiveExportModal(archive)">导出 Word</button>
              </article>
            </div>
            <div v-else class="empty-state small"><span>当前条件下没有晚辅反馈归档。</span></div>
          </section>
          <section class="paper-card evening-detail-panel" :class="{ collapsed: !showEveningFeedbackDetails }">
            <div class="history-header">
              <div>
                <h3>反馈明细</h3>
                <small>用于查看、编辑或批量删除单个学生反馈，默认收起。</small>
              </div>
              <div class="button-row">
                <button type="button" class="ghost-btn" @click="showEveningFeedbackDetails = !showEveningFeedbackDetails">{{ showEveningFeedbackDetails ? '收起明细' : `展开明细（${eveningFeedbackSearchResults.length}）` }}</button>
                <button v-if="showEveningFeedbackDetails" type="button" class="ghost-btn" :disabled="!eveningFeedbackSearchResults.length" @click="toggleAllEveningFeedbackSelection">{{ selectedEveningFeedbackIds.length === eveningFeedbackSearchResults.length && eveningFeedbackSearchResults.length ? '取消全选' : '全选当前' }}</button>
                <button v-if="showEveningFeedbackDetails" type="button" class="danger-btn" :disabled="loading || !selectedEveningFeedbackIds.length" @click="deleteSelectedEveningFeedbackDetails">删除选中</button>
              </div>
            </div>
            <div v-if="showEveningFeedbackDetails" class="history-list evening-detail-list">
              <article v-for="feedback in eveningFeedbackSearchResults" :key="feedback.id" class="history-card evening-detail-card" :class="{ selected: selectedEveningFeedbackIds.includes(feedback.id) }">
                <label class="archive-select-check" @click.stop>
                  <input type="checkbox" :checked="selectedEveningFeedbackIds.includes(feedback.id)" @change="toggleEveningFeedbackSelection(feedback)" />
                </label>
                <button class="feedback-card-main" type="button" @click="openEveningDetail(feedback)">
                  <strong>{{ feedback.student_name }} · {{ feedback.period_label }}</strong>
                  <span>{{ periodTypeLabel(feedback.period_type) }} · {{ subjectWorkLabel(feedback.subject) }} · {{ feedback.class_name }} · {{ feedback.grade || '未填年级' }} · {{ feedback.school || '未填学校' }}</span>
                  <small>{{ shortText(feedback.homework_summary, 86) }}</small>
                  <small>{{ shortText(feedback.final_feedback, 130) }}</small>
                </button>
              </article>
              <div v-if="!eveningFeedbackSearchResults.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>这个时间段暂无晚辅反馈。</span></div>
            </div>
          </section>
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
          <div class="history-header">
            <div><h3>历史列表</h3><small>筛选后可全选当前显示的反馈。</small></div>
            <div class="button-row">
              <button type="button" class="ghost-btn" :disabled="!filteredStudentFeedbacks.length" @click="toggleAllStudentFeedbackSelection">{{ selectedStudentFeedbackItems.length === filteredStudentFeedbacks.length && filteredStudentFeedbacks.length ? '取消全选' : '全选当前' }}</button>
              <button type="button" class="danger-btn" :disabled="loading || !selectedStudentFeedbackItems.length" @click="deleteSelectedStudentFeedbackItems">删除选中</button>
            </div>
          </div>
          <div class="history-list">
            <article v-for="feedback in filteredStudentFeedbacks" :key="feedback.id" class="history-card feedback-card selectable-feedback-card" :class="{ selected: selectedStudentFeedbackIds.includes(feedback.id) }">
              <label class="archive-select-check" @click.stop>
                <input type="checkbox" :checked="selectedStudentFeedbackIds.includes(feedback.id)" @change="toggleStudentFeedbackSelection(feedback)" />
              </label>
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
          <section class="paper-card evening-class-actions">
            <div>
              <h3>晚辅反馈填写</h3>
              <small v-if="eveningStudents.length">先确认学生名单，需要写反馈时再展开批量填写区。</small>
              <small v-else>这个班级还没有学生，先录入学生后再填写晚辅反馈。</small>
            </div>
            <div class="button-row">
              <button v-if="eveningStudents.length" type="button" class="primary-btn" @click="showEveningBatchWorkbench = true; resizeAllTextareas()">开始填写反馈</button>
              <button type="button" class="ghost-btn" @click="openMonthlyModal()">单条补录</button>
              <button type="button" class="ghost-btn" @click="showBulkModal = true; resizeAllTextareas()">{{ eveningStudents.length ? '批量录入学生' : '先录入学生' }}</button>
            </div>
          </section>
          <section v-if="showEveningBatchWorkbench && eveningStudents.length" class="paper-card evening-batch-workbench">
            <div class="evening-batch-header">
              <div>
                <p class="eyebrow">Batch Feedback</p>
                <h3>批量生成晚辅反馈</h3>
                <small>当前周期已保存 {{ eveningBatchDoneCount }} / {{ eveningBatchRows.length }} 条</small>
              </div>
              <div class="button-row">
                <button type="button" class="ghost-btn" @click="deleteEveningBatchDraft">删除草稿</button>
                <button type="button" class="ghost-btn" @click="showEveningBatchWorkbench = false">收起填写区</button>
              </div>
            </div>
            <div class="evening-batch-controls">
              <label>反馈类型<select v-model="eveningBatchForm.period_type" @change="setEveningBatchPeriodType(eveningBatchForm.period_type)"><option v-for="type in EVENING_PERIOD_TYPES" :key="type.value" :value="type.value">{{ type.label }}</option></select></label>
              <label>{{ periodFieldLabel(eveningBatchForm.period_type) }}<input v-model="eveningBatchForm.period_value" :type="periodInputType(eveningBatchForm.period_type)" @change="loadEveningBatchFeedbacks" /></label>
              <label>默认学科<select v-model="eveningBatchForm.default_subject" @change="applyDefaultSubjectToEveningBatch"><option value="">不统一学科</option><option v-for="subject in COMMON_SUBJECTS" :key="subject" :value="subject">{{ subject }}</option></select></label>
            </div>
            <div class="evening-batch-generate-options">
              <label class="generation-model-picker">本次使用模型<select v-model="generationModelKey"><option v-for="model in aiModelOptions" :key="aiModelKey(model)" :value="aiModelKey(model)">{{ model.name }} · {{ model.model }}</option></select><small>{{ generationModelHint() }}</small></label>
              <section class="feedback-style-entry evening-batch-style-entry">
                <div>
                  <strong>晚辅个人风格</strong>
                  <small>{{ eveningStyleGenerationStatus }}</small>
                </div>
                <div class="button-row">
                  <button v-if="eveningEnabledStyleExampleCount" type="button" class="ghost-btn" :disabled="generatingEveningBatch || savingEveningBatch" @click="useStyleExamplesForMonthlyDraft = !useStyleExamplesForMonthlyDraft">{{ useStyleExamplesForMonthlyDraft ? '本次不用风格' : '使用风格' }}</button>
                  <button type="button" class="ghost-btn" :disabled="generatingEveningBatch || savingEveningBatch" @click="openFeedbackStyleModal('evening_feedback')">{{ eveningStyleExamples.length ? '管理风格' : '晚辅风格' }}</button>
                </div>
              </section>
            </div>
            <div class="evening-batch-actions">
              <span>{{ eveningBatchFilledRows.length }} 行已填写 · {{ eveningBatchGenerateCount }} 行可生成 · {{ eveningBatchSaveCount }} 行可保存</span>
	              <div class="button-row">
	                <button type="button" class="ghost-btn loading-action-btn" :class="{ loading: generatingEveningBatch }" :disabled="generatingEveningBatch || savingEveningBatch || !eveningBatchGenerateCount" @click="generateEveningBatchDrafts()">{{ generatingEveningBatch ? '生成中...' : '批量生成初稿' }}</button>
	                <button type="button" class="primary-btn loading-action-btn" :class="{ loading: savingEveningBatch }" :disabled="generatingEveningBatch || savingEveningBatch || !eveningBatchSaveCount" @click="saveEveningBatchFeedbacks">{{ savingEveningBatch ? '保存中...' : '批量保存反馈' }}</button>
	                <button type="button" class="ghost-btn loading-action-btn" :class="{ loading: exportingEveningWord }" :disabled="generatingEveningBatch || savingEveningBatch || exportingEveningWord || !eveningBatchExportCount" @click="openEveningBatchExportModal">{{ exportingEveningWord ? '导出中...' : '导出 Word' }}</button>
	              </div>
	            </div>
            <div v-if="eveningBatchRows.length" class="evening-batch-table-wrap">
              <table class="evening-batch-table">
                <thead>
                  <tr>
                    <th>学生</th>
                    <th>学科</th>
                    <th>情况简述</th>
                    <th>最终反馈</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in eveningBatchRows" :key="row.student_id" :class="{ saved: row.feedback_id, dirty: eveningBatchRowDirty(row), error: row.status === 'error' }">
                    <td class="student-cell">
                      <strong>{{ row.student_name }}</strong>
                      <select class="student-model-select" v-model="row.generation_model_key" :disabled="generatingEveningBatch || savingEveningBatch" @change="updateEveningBatchRowModel(row)">
                        <option value="">跟随本次模型</option>
                        <option v-for="model in aiModelOptions" :key="aiModelKey(model)" :value="aiModelKey(model)">{{ model.name }}</option>
                      </select>
                    </td>
                    <td><select v-model="row.subject" @change="markEveningBatchRowEdited(row)"><option value="">未填</option><option v-for="subject in COMMON_SUBJECTS" :key="subject" :value="subject">{{ subject }}</option></select></td>
                    <td><textarea v-model="row.homework_summary" class="auto-textarea batch-summary-text" :placeholder="EVENING_SUMMARY_PLACEHOLDER" @input="autoResize($event); markEveningBatchRowEdited(row)"></textarea></td>
                    <td>
                      <textarea v-model="row.final_feedback" class="auto-textarea batch-final-text" placeholder="生成后可在这里修改最终反馈" @input="autoResize($event); markEveningBatchRowEdited(row)"></textarea>
                      <details v-if="row.ai_draft" class="batch-draft-details"><summary>查看 AI 初稿</summary><textarea v-model="row.ai_draft" class="auto-textarea batch-draft-text" @input="autoResize($event); markEveningBatchRowEdited(row)"></textarea></details>
                    </td>
                    <td><span class="batch-status-pill" :class="row.status">{{ eveningBatchStatusText(row) }}</span></td>
                    <td class="batch-row-actions">
                      <button type="button" class="ghost-btn" :disabled="generatingEveningBatch || savingEveningBatch" @click="generateEveningBatchRow(row)">生成</button>
                      <button type="button" class="primary-btn" :disabled="generatingEveningBatch || savingEveningBatch || !row.final_feedback.trim()" @click="saveEveningBatchRow(row)">保存</button>
                      <button type="button" class="ghost-btn" @click="openEveningStudentHistory(row)">历史</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
          <div class="history-header"><h3>学生名单</h3><small>点击学生可查看单人历史反馈。</small></div>
          <div class="student-list">
            <article v-for="student in eveningStudents" :key="student.id" class="student-card" @click="go(`#/evening/students/${student.id}`)">
              <img class="card-sticker" :src="eveningStickerArt" alt="" aria-hidden="true" />
              <span class="avatar">{{ student.name.slice(0, 1) }}</span><h3>{{ student.name }}</h3>
              <p>{{ student.grade || '未填年级' }} · {{ student.school || '未填学校' }}</p><small>{{ student.feedback_count }} 条晚辅反馈</small>
            </article>
            <div v-if="!eveningStudents.length" class="empty-state"><img :src="emptyStateArt" alt="" aria-hidden="true" /><span>这个班级还没有学生，先点击上方“先录入学生”。</span></div>
          </div>
        </section>

        <section v-if="currentView === 'evening-student' && currentEveningStudent" class="history-page">
          <div class="paper-card profile-card">
            <h3>{{ currentEveningStudent.name }}</h3><p>{{ currentEveningStudent.grade || '未填年级' }} · {{ currentEveningStudent.school || '未填学校' }}</p>
            <div class="button-row"><button class="ghost-btn" @click="openEveningStudentEdit">编辑学生信息</button><button class="primary-btn" @click="openMonthlyModal(currentEveningStudent)">新增晚辅反馈</button></div>
          </div>
          <div class="history-list">
            <button v-for="feedback in eveningFeedbacks" :key="feedback.id" class="history-card" @click="openEveningDetail(feedback)">
              <strong>{{ feedback.period_label }}</strong><span>{{ periodTypeLabel(feedback.period_type) }} · {{ subjectWorkLabel(feedback.subject) }} · {{ shortText(feedback.homework_summary, 72) }}</span><small>{{ shortText(feedback.final_feedback, 120) }}</small>
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
                <span class="settings-pill" :class="{ ok: activeAIModel?.has_api_key }">{{ activeAIModel ? `当前：${activeAIModel.name}` : '未选择模型' }}</span>
                <span class="settings-caret">{{ settingsPanels.feedback_ai ? '收起' : '展开' }}</span>
              </span>
            </button>

            <div v-show="settingsPanels.feedback_ai" class="settings-panel-body">
              <p class="settings-hint">反馈生成模型主要负责把老师填写的课堂事实整理成可以发给家长的课后反馈。可以先使用平台默认模型免费试用，也可以保存多套自己的 API 配置并选择当前使用项。</p>

              <section class="ai-model-list">
                <div class="style-library-header">
                  <strong>可用模型</strong>
                  <small>平台默认剩余 {{ aiTrialRemaining }} / {{ aiTrialTotal }} 次</small>
                </div>
                <label class="settings-model-select">当前使用模型
                  <select v-model="settingsModelKey" @change="selectSettingsAIModel">
                    <option v-for="model in aiModelOptions" :key="aiModelKey(model)" :value="aiModelKey(model)" :disabled="!model.has_api_key">{{ model.name }} · {{ model.model }}</option>
                  </select>
                  <small>{{ activeAIModel ? `${activeAIModel.provider} · ${activeAIModel.model}` : '请选择可用模型' }}</small>
                </label>
                <article v-for="model in aiModelOptions" :key="`${model.type}-${model.id}`" class="ai-model-item" :class="{ active: model.is_active }">
                  <div>
                    <strong>{{ model.name }}</strong>
                    <small>{{ model.provider }} · {{ model.model }} · {{ model.type === 'platform' ? '平台默认模型' : (model.has_api_key ? '已保存 API Key' : '未保存 API Key') }}</small>
                  </div>
                  <div class="button-row">
                    <button type="button" class="ghost-btn" :disabled="loading || model.is_active || !model.has_api_key" @click="selectAIModel(model)">{{ model.is_active ? '使用中' : '使用' }}</button>
                    <button v-if="model.type === 'personal'" type="button" class="ghost-btn" :disabled="loading" @click="editAIConfig(model)">编辑</button>
                    <button v-if="model.type === 'personal'" type="button" class="danger-btn" :disabled="loading" @click="deleteAIConfig(model)">删除</button>
                  </div>
                </article>
                <div class="button-row">
                  <button type="button" class="primary-btn" :disabled="loading" @click="openNewAIConfigForm">新增模型配置</button>
                </div>
              </section>

              <section v-if="showAIConfigForm" class="ai-config-editor">
                <div class="style-library-header">
                  <strong>{{ aiSettingsForm.id ? '编辑模型配置' : '新增模型配置' }}</strong>
                  <button type="button" class="ghost-btn" :disabled="loading" @click="closeAIConfigForm">取消</button>
                </div>
                <label>配置名称
                  <input v-model="aiSettingsForm.name" placeholder="例如：我的 DeepSeek / 备用豆包" />
                  <small>只用于你在模型列表里识别这条配置。</small>
                </label>

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
                  <input v-model="aiSettingsForm.model" placeholder="deepseek-v4-pro" />
                  <small>示例：deepseek-v4-pro、doubao-seed-2-0-pro-260215。自定义接口请填写对应平台控制台显示的模型名。</small>
                </label>

                <label>API Key
                  <input v-model="aiSettingsForm.api_key" type="password" :placeholder="aiSettingsForm.id ? '已配置时留空则保留原 Key' : '粘贴你的 API Key'" autocomplete="off" />
                  <small>{{ aiSettingsForm.id ? '编辑配置时，填写新 Key 会覆盖旧 Key；留空则保留。' : '新增个人模型配置需要填写 API Key。' }}</small>
                </label>

                <label class="check-row">
                  <input v-model="aiSettingsForm.make_active" type="checkbox" />
                  <span>保存后设为当前使用模型</span>
                </label>

                <div class="button-row danger-row">
                  <div class="button-row">
                    <button type="button" class="ghost-btn" :disabled="loading" @click="testAISettings">测试连接</button>
                    <button class="primary-btn" :disabled="loading">{{ aiSettingsForm.id ? '更新模型配置' : '保存新的模型配置' }}</button>
                  </div>
                  <button type="button" class="danger-btn" :disabled="loading || !aiSettingsForm.id" @click="clearAIKey">清除这条 Key</button>
                </div>
              </section>
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
                <span class="settings-pill" :class="{ ok: oneOnOneEnabledStyleExampleCount || eveningEnabledStyleExampleCount }">{{ styleExamples.length ? `一对一参与 ${oneOnOneEnabledStyleExampleCount} 条 · 晚辅参与 ${eveningEnabledStyleExampleCount} 条` : '可选 · 暂无样例' }}</span>
                <span class="settings-caret">{{ settingsPanels.style_examples ? '收起' : '展开' }}</span>
              </span>
            </button>

            <div v-show="settingsPanels.style_examples" class="settings-panel-body">
              <label>反馈样例类型
                <select v-model="activeStyleExampleType" @change="styleExamplePage = 1">
                  <option value="one_on_one">一对一反馈样例（参与生成 {{ oneOnOneEnabledStyleExampleCount }} 条）</option>
                  <option value="evening_feedback">晚辅反馈样例（参与生成 {{ eveningEnabledStyleExampleCount }} 条）</option>
                </select>
                <small>不同反馈类型使用独立样例库。以后增加班课反馈时，也会在这里单独切换管理。</small>
              </label>

              <p class="settings-hint">{{ styleSettingsHint }} {{ styleExampleSelectionHelp }}</p>

              <label>样例标题
                <input v-model="styleExampleForm.title" :placeholder="styleExampleTitlePlaceholder" />
                <small>{{ styleExampleTitleHelp }}</small>
              </label>

              <label>反馈样例
                <textarea v-model="styleExampleForm.content" class="auto-textarea final-text" :placeholder="styleExampleContentPlaceholder" @input="autoResize"></textarea>
                <small>{{ styleExampleContentHelp }}</small>
              </label>

              <label class="check-row">
                <input v-model="styleExampleForm.enabled" type="checkbox" />
                <span>保存后立即参与生成</span>
              </label>

              <div class="button-row">
                <button class="primary-btn" :disabled="loading">保存到{{ styleTypeLabel() }}样例库</button>
              </div>

              <div class="style-example-list">
                <article v-for="example in paginatedStyleExamples" :key="example.id" class="style-example-item" role="button" tabindex="0" @click="openStyleExampleDetail(example)" @keydown.enter.prevent="openStyleExampleDetail(example)">
                  <div>
                    <strong>{{ example.title || '未命名样例' }}</strong>
                    <small>{{ example.enabled ? '参与生成' : '仅保存' }} · {{ shortText(example.content, 88) }}</small>
                  </div>
                  <div class="button-row">
                    <button type="button" class="ghost-btn" :disabled="loading" @click.stop="toggleStyleExample(example)">{{ example.enabled ? '停用' : '启用' }}</button>
                    <button type="button" class="danger-btn" :disabled="loading" @click.stop="deleteStyleExample(example)">删除</button>
                  </div>
                </article>
                <p v-if="!currentStyleExamples.length" class="settings-hint">还没有{{ styleTypeLabel() }}风格样例。</p>
                <div v-if="currentStyleExamples.length > STYLE_EXAMPLE_PAGE_SIZE" class="pagination-row">
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
            <h3>选择可用模型</h3>
          </div>
          <button type="button" class="icon-btn" @click="closeApiOnboarding">×</button>
        </div>
        <p class="settings-hint">可以先使用平台默认模型免费试用，也可以在设置页保存自己的模型 API。个人 API Key 只保存在当前老师账号下，并会加密保存。</p>
        <div class="guide-step-list">
          <article>
            <strong>1. 平台默认模型可先试用</strong>
            <span>课堂记录整理、一对一反馈和晚辅反馈都可以使用；试用次数用完后再配置自己的 API。</span>
          </article>
          <article>
            <strong>2. 个人模型可保存多套</strong>
            <span>你可以保存多个供应商配置，并选择其中一套作为当前使用模型。</span>
          </article>
        </div>
        <div class="button-row danger-row">
          <button type="button" class="primary-btn" @click="goToApiSettingsFromOnboarding">去选择模型</button>
          <button type="button" class="ghost-btn" @click="closeApiOnboarding">知道了，稍后再说</button>
        </div>
      </article>
    </div>

    <div v-if="detailStyleExample" class="modal-mask style-example-detail-mask">
      <article class="paper-card modal-panel feedback-detail-modal style-example-detail-modal">
        <div class="modal-title">
          <div>
            <p class="eyebrow">{{ styleTypeLabel(detailStyleExample.feedback_type) }}个人风格样例</p>
            <h3>{{ detailStyleExample.title || '未命名样例' }}</h3>
          </div>
          <button type="button" class="icon-btn" @click="closeStyleExampleDetail">×</button>
        </div>

        <template v-if="!isEditingStyleExample">
          <div class="style-example-meta-row">
            <span :class="{ active: detailStyleExample.enabled }">{{ detailStyleExample.enabled ? '参与生成' : '仅保存' }}</span>
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
            <small>{{ styleExampleTitleAutoHelp }}</small>
          </label>
          <label>反馈样例
            <textarea v-model="styleExampleEditForm.content" class="auto-textarea final-text" @input="autoResize"></textarea>
            <small>AI 只学习这里粘贴的反馈正文。若希望 AI 学习标题格式，请把标题行和正文一起放在这里。</small>
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
            <button v-if="oneOnOneEnabledStyleExampleCount" type="button" class="ghost-btn" :disabled="loading" @click="useStyleExamplesForDraft = !useStyleExamplesForDraft; saveFeedbackDraft()">{{ useStyleExamplesForDraft ? '本次不用个人风格' : '使用个人风格' }}</button>
            <button type="button" class="ghost-btn" :disabled="loading" @click="openFeedbackStyleModal('one_on_one')">{{ oneOnOneStyleExamples.length ? '管理个人风格' : '个人风格' }}</button>
          </div>
        </section>
        <section class="feedback-panel classroom-content-panel" :class="{ collapsed: !feedbackPanels.content }">
          <div class="feedback-panel-header feedback-panel-header-actions">
            <button class="feedback-panel-toggle" type="button" @click="toggleFeedbackPanel('content')"><strong>课堂记录整理</strong><span>{{ feedbackPanels.content ? '收起' : '展开' }}</span></button>
            <button type="button" class="ghost-btn reference-toggle-btn" @click="toggleWritingReference">{{ showWritingReference ? '收起参考' : '填写参考' }}</button>
          </div>
          <div v-show="feedbackPanels.content" class="feedback-panel-body">
            <div class="qa-mode-panel quick-note-panel">
              <div class="entry-mode-toggle" role="group" aria-label="课堂记录填写方式">
                <button type="button" :class="{ active: feedbackEntryMode === 'raw' }" @click="setFeedbackEntryMode('raw')">原始记录整理</button>
                <button type="button" :class="{ active: feedbackEntryMode === 'direct' }" @click="setFeedbackEntryMode('direct')">直接填四板块</button>
              </div>
              <label v-if="feedbackEntryMode === 'raw'" class="qa-question">
                <span>本节课原始记录</span>
                <small>随便写：讲了什么、学生表现、哪里需要注意、布置了什么作业。建议和作业最好分开写，例如“建议：……；作业：……”。AI 会先整理分类，不会直接生成最终反馈。</small>
                <textarea v-model="rawLessonNote" class="auto-textarea large-text" placeholder="例如：今天讲了一次函数图像和解析式，图像题还可以，应用题找等量关系有点卡。建议：回去复盘今天错题。作业：完成讲义 3-5 题。" @input="handleRawLessonNoteInput"></textarea>
              </label>
              <p v-if="feedbackEntryMode === 'raw' && hasOrganizedLessonNote && rawLessonNoteDirty" class="settings-warning">原始记录已修改，建议重新整理后再生成。</p>
              <div v-if="feedbackEntryMode === 'direct' || hasOrganizedLessonNote" class="organized-field-grid">
                <label v-for="field in FEEDBACK_CORE_FIELDS" :key="field.formField" :class="{ 'field-missing': isFieldMissing(field.formField) }">
                  <span>{{ field.title }}</span>
                  <small v-if="isFieldMissing(field.formField)">{{ fieldSupplementPrompt(field.formField) }}</small>
                  <textarea v-model="feedbackForm[field.formField]" class="auto-textarea" :placeholder="field.placeholder" @input="autoResize($event); clearOrganizedMissingField(field.formField)"></textarea>
                </label>
              </div>
              <p v-if="(feedbackEntryMode === 'direct' || hasOrganizedLessonNote) && blockingMissingFields.length" class="settings-warning">还需补充：{{ missingFieldText }}。四大板块齐全后才能生成反馈。</p>
              <p v-if="(feedbackEntryMode === 'direct' || hasOrganizedLessonNote) && canGenerateFeedback" class="settings-hint">四大板块已整理完整，请确认内容无误后生成反馈。</p>
              <label class="generation-model-picker">本次使用模型
                <select v-model="generationModelKey">
                  <option v-for="model in aiModelOptions" :key="aiModelKey(model)" :value="aiModelKey(model)">{{ model.name }} · {{ model.model }}</option>
                </select>
                <small>{{ generationModelHint() }}</small>
              </label>
              <div class="button-row classroom-generate-row danger-row">
                <button v-if="feedbackEntryMode === 'raw'" type="button" class="ghost-btn" :disabled="loading" @click="organizeLessonNote">{{ hasOrganizedLessonNote ? '重新整理' : '整理课堂记录' }}</button>
                <button v-if="feedbackEntryMode === 'direct' || hasOrganizedLessonNote" type="button" class="primary-btn" :disabled="loading || !canGenerateFeedback" @click="generateDraft">生成反馈</button>
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
              <h3>{{ styleTypeLabel() }}个人风格</h3>
              <small>{{ currentStyleGenerationStatus }}</small>
            </div>
            <button type="button" class="icon-btn" @click="closeFeedbackStyleModal">×</button>
          </div>

          <p class="guide-hint">{{ activeStyleExampleType === 'evening_feedback' ? '晚辅样例只用于晚辅反馈生成。启用后 AI 会学习你的家长沟通语气、段落详略和晚辅写法，但不会复用样例里的学生事实。' : '一对一样例只用于一对一课后反馈生成。未启用样例时，AI 会按标准四段结构输出；启用后会学习你的语气、排版、段落详略和表达习惯。' }}</p>

          <div class="style-status-row">
            <strong>{{ currentStyleGenerationStatus }}</strong>
              <small>{{ styleExampleSelectionHelp }}</small>
          </div>

          <section class="inline-style-form">
            <strong>快捷添加样例</strong>
            <label>样例标题
              <input v-model="inlineStyleExampleForm.title" :placeholder="styleExampleTitlePlaceholder" />
              <small>{{ styleExampleTitleAutoHelp }}</small>
            </label>
            <label>反馈样例
              <textarea v-model="inlineStyleExampleForm.content" class="auto-textarea large-text" :placeholder="styleExampleContentPlaceholder" @input="autoResize"></textarea>
              <small>AI 只学习这里粘贴的反馈正文。若希望 AI 学习标题格式，请把标题行和正文一起放在这里。</small>
            </label>
            <label class="check-row">
              <input v-model="inlineStyleExampleForm.enabled" type="checkbox" />
              <span>保存后立即参与生成</span>
            </label>
            <div class="button-row">
              <button type="button" class="primary-btn" :disabled="loading" @click="saveInlineStyleExample">保存到样例库</button>
            </div>
          </section>

          <section class="style-library-panel">
            <div class="style-library-header">
              <strong>样例库</strong>
              <small>{{ currentStyleExamples.length ? `${currentStyleExamples.length} 条${styleTypeLabel()}样例` : '暂无样例' }}</small>
            </div>
            <div class="style-example-list">
              <article v-for="example in paginatedFeedbackStyleExamples" :key="example.id" class="style-example-item" role="button" tabindex="0" @click="openStyleExampleDetail(example)" @keydown.enter.prevent="openStyleExampleDetail(example)">
                <div>
                  <strong>{{ example.title || '未命名样例' }}</strong>
                  <small>{{ example.enabled ? '参与生成' : '仅保存' }} · {{ shortText(example.content, 88) }}</small>
                </div>
                <div class="button-row">
                  <button type="button" class="ghost-btn" :disabled="loading" @click.stop="toggleStyleExample(example)">{{ example.enabled ? '停用' : '启用' }}</button>
                  <button type="button" class="danger-btn" :disabled="loading" @click.stop="deleteStyleExample(example)">删除</button>
                </div>
              </article>
              <p v-if="!currentStyleExamples.length" class="settings-hint">还没有{{ styleTypeLabel() }}风格样例，可以先在上方粘贴一段自己的反馈。</p>
              <div v-if="currentStyleExamples.length > STYLE_EXAMPLE_PAGE_SIZE" class="pagination-row">
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
          <div class="button-row danger-row"><div class="button-row"><button class="ghost-btn" @click="isEditingDetail = true; assignFeedback(editForm, detailFeedback); resizeAllTextareas()">编辑反馈</button><button class="ghost-btn" @click="addCurrentFeedbackAsStyleExample">设为一对一风格样例</button></div><button class="danger-btn" @click="deleteFeedback">删除反馈</button></div>
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
        <label>学科<select v-model="monthlyForm.subject"><option value="">不填写学科</option><option v-for="subject in COMMON_SUBJECTS" :key="subject" :value="subject">{{ subject }}</option></select></label>
        <label class="generation-model-picker">本次使用模型<select v-model="generationModelKey"><option v-for="model in aiModelOptions" :key="aiModelKey(model)" :value="aiModelKey(model)">{{ model.name }} · {{ model.model }}</option></select><small>{{ generationModelHint() }}</small></label>
        <section class="feedback-style-entry">
          <div>
            <strong>晚辅个人风格</strong>
            <small>{{ eveningStyleGenerationStatus }}</small>
          </div>
          <div class="button-row">
            <button v-if="eveningEnabledStyleExampleCount" type="button" class="ghost-btn" :disabled="loading" @click="useStyleExamplesForMonthlyDraft = !useStyleExamplesForMonthlyDraft">{{ useStyleExamplesForMonthlyDraft ? '本次不用晚辅风格' : '使用晚辅风格' }}</button>
            <button type="button" class="ghost-btn" :disabled="loading" @click="openFeedbackStyleModal('evening_feedback')">{{ eveningStyleExamples.length ? '管理晚辅风格' : '晚辅风格' }}</button>
          </div>
        </section>
        <label>{{ subjectWorkLabel(monthlyForm.subject) }}完成情况简述<textarea v-model="monthlyForm.homework_summary" class="auto-textarea" :placeholder="EVENING_SUMMARY_PLACEHOLDER" @input="autoResize"></textarea></label>
        <div class="button-row"><button type="button" class="ghost-btn loading-action-btn" :class="{ loading: generatingMonthlyDraft }" :disabled="loading" @click="generateMonthlyDraft">{{ generatingMonthlyDraft ? '生成中...' : '生成 AI 初稿' }}</button><button class="primary-btn" :disabled="loading">保存晚辅反馈</button></div>
        <label>AI 初稿<textarea v-model="monthlyForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label><label>最终反馈<textarea v-model="monthlyForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
      </form>
    </div>

    <div v-if="showEveningExportModal" class="modal-mask">
      <form class="paper-card modal-panel feedback-editor" @submit.prevent="exportEveningBatchWord">
        <div class="modal-title"><h3>导出晚辅反馈 Word</h3><button type="button" class="icon-btn" @click="showEveningExportModal = false">×</button></div>
        <label>学期 / 阶段<input v-model="eveningExportForm.term_label" placeholder="例如：26春季" @input="syncEveningExportFilename" /></label>
        <label>负责人 / 老师<input v-model="eveningExportForm.owner_name" placeholder="例如：王小明" @input="syncEveningExportFilename" /></label>
        <label>导出科目<input v-model="eveningExportForm.export_subject" placeholder="例如：数学" @input="syncEveningExportFilename" /></label>
        <label>Word 第一行标题<input v-model="eveningExportForm.document_title" placeholder="例如：启程26春季七年级D班晚辅" /></label>
        <div class="filename-preview-box" aria-live="polite">
          <div class="filename-preview-header">
            <span>下载文件名预览</span>
            <div class="button-row">
              <button v-if="!editingEveningExportFilename" type="button" class="ghost-btn" @click="startEditingEveningExportFilename">编辑</button>
              <button v-if="editingEveningExportFilename" type="button" class="ghost-btn" @click="editingEveningExportFilename = false">完成</button>
              <button type="button" class="ghost-btn" @click="resetEveningExportFilename">初始化文件名</button>
            </div>
          </div>
          <input v-if="editingEveningExportFilename" v-model="eveningExportForm.filename_base" placeholder="例如：26春季5月第5周七年级D班晚辅反馈——王小明数学" @input="markEveningExportFilenameEdited" @keydown.enter.prevent="editingEveningExportFilename = false" />
          <strong v-else>{{ eveningExportFilenamePreview }}</strong>
          <small>系统会自动清理非法字符并补上 .docx。</small>
        </div>
        <p class="settings-hint">{{ eveningExportSource.mode === 'archive' ? '将导出班级历史归档中' : '将导出当前批量表中' }} {{ eveningExportCount }} 条有最终反馈的内容，{{ eveningExportSource.mode === 'archive' ? '按已保存内容生成 Word。' : '未保存的修改也会一起导出。' }}</p>
        <div class="button-row"><button type="button" class="ghost-btn" :disabled="exportingEveningWord" @click="showEveningExportModal = false">取消</button><button class="primary-btn loading-action-btn" :class="{ loading: exportingEveningWord }" :disabled="exportingEveningWord">{{ exportingEveningWord ? '导出中...' : '下载 Word' }}</button></div>
      </form>
    </div>

    <div v-if="showFeedbackStyleModal && activeStyleExampleType === 'evening_feedback'" class="modal-mask">
      <article class="paper-card modal-panel feedback-style-modal">
        <div class="modal-title">
          <div>
            <h3>晚辅个人风格</h3>
            <small>{{ currentStyleGenerationStatus }}</small>
          </div>
          <button type="button" class="icon-btn" @click="closeFeedbackStyleModal">×</button>
        </div>
        <p class="guide-hint">晚辅样例只用于晚辅反馈生成。启用后 AI 会学习你的家长沟通语气、段落详略和晚辅写法，但不会复用样例里的学生事实。</p>
        <div class="style-status-row">
          <strong>{{ currentStyleGenerationStatus }}</strong>
          <small>{{ styleExampleSelectionHelp }}</small>
        </div>
        <section class="inline-style-form">
          <strong>快捷添加样例</strong>
          <label>样例标题
            <input v-model="inlineStyleExampleForm.title" :placeholder="styleExampleTitlePlaceholder" />
            <small>{{ styleExampleTitleAutoHelp }}</small>
          </label>
          <label>反馈样例
            <textarea v-model="inlineStyleExampleForm.content" class="auto-textarea large-text" :placeholder="styleExampleContentPlaceholder" @input="autoResize"></textarea>
            <small>AI 只学习这里粘贴的晚辅反馈正文。若希望 AI 学习标题格式，请把标题行和正文一起放在这里。</small>
          </label>
          <label class="check-row">
            <input v-model="inlineStyleExampleForm.enabled" type="checkbox" />
            <span>保存后立即参与晚辅反馈生成</span>
          </label>
          <div class="button-row">
            <button type="button" class="primary-btn" :disabled="loading" @click="saveInlineStyleExample">保存到晚辅样例库</button>
          </div>
        </section>
        <section class="style-library-panel">
          <div class="style-library-header">
            <strong>晚辅样例库</strong>
            <small>{{ eveningStyleExamples.length ? `${eveningStyleExamples.length} 条样例` : '暂无样例' }}</small>
          </div>
          <div class="style-example-list">
            <article v-for="example in paginatedFeedbackStyleExamples" :key="example.id" class="style-example-item" role="button" tabindex="0" @click="openStyleExampleDetail(example)" @keydown.enter.prevent="openStyleExampleDetail(example)">
              <div>
                <strong>{{ example.title || '未命名样例' }}</strong>
                <small>{{ example.enabled ? '参与生成' : '仅保存' }} · {{ shortText(example.content, 88) }}</small>
              </div>
              <div class="button-row">
                <button type="button" class="ghost-btn" :disabled="loading" @click.stop="toggleStyleExample(example)">{{ example.enabled ? '停用' : '启用' }}</button>
                <button type="button" class="danger-btn" :disabled="loading" @click.stop="deleteStyleExample(example)">删除</button>
              </div>
            </article>
            <p v-if="!eveningStyleExamples.length" class="settings-hint">还没有晚辅风格样例，可以先在上方粘贴一段自己的晚辅反馈。</p>
            <div v-if="eveningStyleExamples.length > STYLE_EXAMPLE_PAGE_SIZE" class="pagination-row">
              <button type="button" class="ghost-btn" :disabled="feedbackStyleExamplePage <= 1" @click="setStyleExamplePage(feedbackStyleExamplePage - 1, 'feedback')">上一页</button>
              <span>第 {{ feedbackStyleExamplePage }} / {{ feedbackStyleExampleTotalPages }} 页</span>
              <button type="button" class="ghost-btn" :disabled="feedbackStyleExamplePage >= feedbackStyleExampleTotalPages" @click="setStyleExamplePage(feedbackStyleExamplePage + 1, 'feedback')">下一页</button>
            </div>
          </div>
        </section>
      </article>
    </div>

    <div v-if="eveningHistoryStudent" class="modal-mask">
      <article class="paper-card modal-panel feedback-detail-modal evening-history-modal">
        <div class="modal-title"><h3>{{ eveningHistoryStudent.name }} 的历史反馈</h3><button type="button" class="icon-btn" @click="closeEveningStudentHistory">×</button></div>
        <div v-if="loadingEveningHistory" class="empty-state small"><span>正在加载历史反馈...</span></div>
        <div v-else class="evening-history-list">
          <button v-for="feedback in eveningHistoryFeedbacks" :key="feedback.id" class="history-card evening-history-item" type="button" @click="openEveningHistoryDetail(feedback)">
            <strong>{{ feedback.period_label || '未填写时间' }}</strong>
            <span>{{ periodTypeLabel(feedback.period_type) }} · {{ subjectWorkLabel(feedback.subject) }} · {{ shortText(feedback.homework_summary, 64) }}</span>
            <small>{{ shortText(feedback.final_feedback, 110) }}</small>
          </button>
          <div v-if="!eveningHistoryFeedbacks.length" class="empty-state small"><span>暂无晚辅反馈。</span></div>
        </div>
      </article>
    </div>

    <div v-if="eveningDetail" class="modal-mask">
      <article class="paper-card modal-panel feedback-detail-modal">
        <div class="modal-title"><h3>晚辅反馈详情</h3><button type="button" class="icon-btn" @click="eveningDetail = null">×</button></div>
        <template v-if="!isEditingEveningDetail">
          <p><strong>学生：</strong>{{ eveningDetail.student_name || currentEveningStudent?.name || '未填写' }}</p><p><strong>反馈类型：</strong>{{ periodTypeLabel(eveningDetail.period_type) }}</p><p><strong>反馈时间：</strong>{{ eveningDetail.period_label }}</p><p><strong>学科：</strong>{{ eveningDetail.subject || '未填学科' }}</p><p><strong>{{ subjectWorkLabel(eveningDetail.subject) }}情况：</strong>{{ eveningDetail.homework_summary }}</p><h4>最终反馈</h4><pre>{{ eveningDetail.final_feedback }}</pre><details><summary>查看 AI 初稿</summary><pre>{{ eveningDetail.ai_draft }}</pre></details>
          <div class="button-row danger-row"><div class="button-row"><button class="ghost-btn" @click="isEditingEveningDetail = true; assignMonthly(monthlyEditForm, eveningDetail); resizeAllTextareas()">编辑反馈</button><button class="ghost-btn" @click="addCurrentEveningFeedbackAsStyleExample">设为晚辅风格样例</button></div><button class="danger-btn" @click="deleteEveningFeedback">删除反馈</button></div>
        </template>
        <form v-else class="feedback-editor" @submit.prevent="saveEveningDetailEdit">
          <label>晚辅学生<select v-model="monthlyEditForm.student_id"><option v-for="student in eveningFeedbackStudentOptions" :key="student.id" :value="student.id">{{ student.name }}</option></select></label><label>反馈类型<select v-model="monthlyEditForm.period_type" @change="setEveningFeedbackPeriodType(monthlyEditForm, monthlyEditForm.period_type)"><option v-for="type in EVENING_PERIOD_TYPES" :key="type.value" :value="type.value">{{ type.label }}</option></select></label><label>{{ periodFieldLabel(monthlyEditForm.period_type) }}<input v-model="monthlyEditForm.period_value" :type="periodInputType(monthlyEditForm.period_type)" /></label><label>学科<select v-model="monthlyEditForm.subject"><option value="">不填写学科</option><option v-for="subject in COMMON_SUBJECTS" :key="subject" :value="subject">{{ subject }}</option></select></label><label>{{ subjectWorkLabel(monthlyEditForm.subject) }}完成情况简述<textarea v-model="monthlyEditForm.homework_summary" class="auto-textarea" @input="autoResize"></textarea></label><label>AI 初稿<textarea v-model="monthlyEditForm.ai_draft" class="auto-textarea large-text" @input="autoResize"></textarea></label><label>最终反馈<textarea v-model="monthlyEditForm.final_feedback" class="auto-textarea final-text" @input="autoResize"></textarea></label>
          <div class="button-row"><button class="primary-btn">保存修改</button><button type="button" class="ghost-btn" @click="isEditingEveningDetail = false">取消</button></div>
        </form>
      </article>
    </div>

    <div v-if="message" class="toast">{{ message }}</div>
  </main>
</template>
