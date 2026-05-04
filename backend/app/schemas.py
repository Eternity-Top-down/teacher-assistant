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
    lesson_time: str = Field(min_length=1)
    lesson_summary: str = Field(min_length=5, max_length=2000)
    performance_summary: str = Field(default="", max_length=1000)


class FeedbackCreate(BaseModel):
    lesson_time: str = Field(min_length=1)
    lesson_summary: str = Field(min_length=5, max_length=2000)
    performance_summary: str = Field(default="", max_length=1000)
    ai_draft: str = Field(min_length=1)
    final_feedback: str = Field(min_length=1)


class FeedbackUpdate(BaseModel):
    lesson_time: str = Field(min_length=1)
    lesson_summary: str = Field(min_length=5, max_length=2000)
    performance_summary: str = Field(default="", max_length=1000)
    ai_draft: str = Field(min_length=1)
    final_feedback: str = Field(min_length=1)


class EveningClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    note: str = Field(default="", max_length=500)


class EveningClassUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    note: str = Field(default="", max_length=500)


class EveningStudentBulkCreate(BaseModel):
    names_text: str = Field(min_length=1, max_length=5000)


class EveningStudentUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    grade: str = Field(default="", max_length=50)
    school: str = Field(default="", max_length=100)
    note: str = Field(default="", max_length=500)


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
