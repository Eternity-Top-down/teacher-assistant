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
