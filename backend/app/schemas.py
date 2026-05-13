from pydantic import BaseModel, EmailStr, Field


class EmailCodeRequest(BaseModel):
    email: EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    code: str = Field(min_length=4, max_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    grade: str = Field(default="", max_length=50)
    subject: str = Field(default="", max_length=50)
    note: str = Field(default="", max_length=500)


class StudentUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    grade: str = Field(default="", max_length=50)
    subject: str = Field(default="", max_length=50)
    note: str = Field(default="", max_length=500)


class FeedbackGenerateRequest(BaseModel):
    lesson_title: str = Field(min_length=1, max_length=120)
    lesson_time: str = Field(min_length=1)
    lesson_summary: str = Field(min_length=5, max_length=2000)
    performance_summary: str = Field(default="", max_length=1000)
    advice_summary: str = Field(default="", max_length=1000)
    homework_plan: str = Field(default="", max_length=1000)
    supplement_summary: str = Field(default="", max_length=1000)
    use_style_examples: bool = True


class FeedbackCreate(BaseModel):
    lesson_title: str = Field(default="", max_length=120)
    lesson_time: str = Field(min_length=1)
    lesson_summary: str = Field(min_length=5, max_length=2000)
    performance_summary: str = Field(default="", max_length=1000)
    advice_summary: str = Field(default="", max_length=1000)
    homework_plan: str = Field(default="", max_length=1000)
    ai_draft: str = Field(min_length=1)
    final_feedback: str = Field(min_length=1)


class FeedbackUpdate(BaseModel):
    lesson_title: str = Field(default="", max_length=120)
    lesson_time: str = Field(min_length=1)
    lesson_summary: str = Field(min_length=5, max_length=2000)
    performance_summary: str = Field(default="", max_length=1000)
    advice_summary: str = Field(default="", max_length=1000)
    homework_plan: str = Field(default="", max_length=1000)
    ai_draft: str = Field(min_length=1)
    final_feedback: str = Field(min_length=1)


class EveningClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class EveningClassUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class GroupClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class GroupClassUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class EveningStudentBulkCreate(BaseModel):
    names_text: str = Field(min_length=1, max_length=5000)


class EveningStudentUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    grade: str = Field(default="", max_length=50)
    school: str = Field(default="", max_length=100)


class EveningMonthlyGenerateRequest(BaseModel):
    feedback_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    homework_summary: str = Field(min_length=5, max_length=2000)


class EveningMonthlyFeedbackCreate(BaseModel):
    feedback_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    homework_summary: str = Field(min_length=5, max_length=2000)
    ai_draft: str = Field(min_length=1)
    final_feedback: str = Field(min_length=1)


class EveningMonthlyFeedbackUpdate(BaseModel):
    feedback_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    homework_summary: str = Field(min_length=5, max_length=2000)
    ai_draft: str = Field(min_length=1)
    final_feedback: str = Field(min_length=1)


class AISettingsUpdate(BaseModel):
    provider: str = Field(default="deepseek", max_length=50)
    base_url: str = Field(min_length=1, max_length=300)
    model: str = Field(min_length=1, max_length=120)
    api_key: str = Field(default="", max_length=500)
    clear_api_key: bool = False
    feedback_format_mode: str = Field(default="structured", pattern=r"^(structured|free_style)$")


class AISettingsTest(BaseModel):
    provider: str = Field(default="deepseek", max_length=50)
    base_url: str = Field(min_length=1, max_length=300)
    model: str = Field(min_length=1, max_length=120)
    api_key: str = Field(default="", max_length=500)


class VisionSettingsUpdate(BaseModel):
    provider: str = Field(default="doubao_v", max_length=50)
    base_url: str = Field(min_length=1, max_length=300)
    model: str = Field(min_length=1, max_length=120)
    api_key: str = Field(default="", max_length=500)
    clear_api_key: bool = False


class VisionSettingsTest(BaseModel):
    provider: str = Field(default="doubao_v", max_length=50)
    base_url: str = Field(min_length=1, max_length=300)
    model: str = Field(min_length=1, max_length=120)
    api_key: str = Field(default="", max_length=500)


class MaterialImageInput(BaseModel):
    name: str = Field(default="", max_length=200)
    mime_type: str = Field(min_length=1, max_length=80)
    data_base64: str = Field(min_length=1)


class MaterialsAnalyzeRequest(BaseModel):
    lesson_title: str = Field(default="", max_length=120)
    subject: str = Field(default="", max_length=50)
    images: list[MaterialImageInput] = Field(min_length=1, max_length=9)


class MaterialsAnalyzeResponse(BaseModel):
    knowledge_points: list[str]
    question_types: list[str]
    practice_summary: str
    weak_points: list[str]
    lesson_summary_suggestion: str


class StyleExampleCreate(BaseModel):
    title: str = Field(default="", max_length=80)
    content: str = Field(min_length=20, max_length=5000)
    enabled: bool = True


class StyleExampleUpdate(BaseModel):
    title: str = Field(default="", max_length=80)
    content: str = Field(min_length=20, max_length=5000)
    enabled: bool = True


class StyleExampleFromFeedback(BaseModel):
    feedback_type: str = Field(default="one_on_one", pattern=r"^(one_on_one|evening_monthly)$")
    feedback_id: int
    title: str = Field(default="", max_length=80)
