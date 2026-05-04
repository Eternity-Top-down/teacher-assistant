from datetime import datetime, timedelta

import sqlite3

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .ai_client import generate_evening_monthly_feedback, generate_feedback
from .database import get_db, init_db, now_iso
from .email_service import make_code, send_verification_email
from .schemas import (
    EmailCodeRequest,
    EveningClassCreate,
    EveningClassUpdate,
    EveningMonthlyFeedbackCreate,
    EveningMonthlyFeedbackUpdate,
    EveningMonthlyGenerateRequest,
    EveningStudentBulkCreate,
    EveningStudentUpdate,
    FeedbackCreate,
    FeedbackGenerateRequest,
    FeedbackUpdate,
    LoginRequest,
    RegisterRequest,
    StudentCreate,
    StudentUpdate,
)
from .security import CurrentTeacher, create_token, hash_password, verify_password


app = FastAPI(title="教师一对一反馈助手 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def require_student(student_id: int, teacher_id: int) -> dict:
    with get_db() as db:
        student = db.execute(
            "SELECT * FROM students WHERE id = ? AND teacher_id = ?",
            (student_id, teacher_id),
        ).fetchone()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return dict(student)


def require_feedback(feedback_id: int, teacher_id: int) -> dict:
    with get_db() as db:
        feedback = db.execute(
            "SELECT * FROM feedbacks WHERE id = ? AND teacher_id = ?",
            (feedback_id, teacher_id),
        ).fetchone()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    return dict(feedback)


def require_evening_class(class_id: int, teacher_id: int) -> dict:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM evening_classes WHERE id = ? AND teacher_id = ?",
            (class_id, teacher_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="晚辅班级不存在")
    return dict(row)


def require_evening_student(student_id: int, teacher_id: int) -> dict:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM evening_students WHERE id = ? AND teacher_id = ?",
            (student_id, teacher_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="晚辅学生不存在")
    return dict(row)


def require_evening_monthly_feedback(feedback_id: int, teacher_id: int) -> dict:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM evening_monthly_feedbacks WHERE id = ? AND teacher_id = ?",
            (feedback_id, teacher_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="晚辅反馈不存在")
    return dict(row)


def lesson_date_label(lesson_time: str) -> str:
    try:
        normalized = lesson_time.replace("Z", "").replace("T", " ")
        value = datetime.fromisoformat(normalized)
        return f"{value.month}.{value.day}"
    except ValueError:
        return lesson_time[:10] or "本次"


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/auth/send-code")
def send_code(payload: EmailCodeRequest):
    code = make_code()
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat(timespec="seconds") + "Z"
    with get_db() as db:
        db.execute(
            "INSERT INTO verification_codes (email, code, expires_at, used, created_at) VALUES (?, ?, ?, 0, ?)",
            (payload.email, code, expires_at, now_iso()),
        )
    sent = send_verification_email(payload.email, code)
    return {"message": "验证码已发送" if sent else "开发模式：验证码已打印在后端终端"}


@app.post("/api/auth/register")
def register(payload: RegisterRequest):
    with get_db() as db:
        exists = db.execute("SELECT id FROM teachers WHERE email = ?", (payload.email,)).fetchone()
        if exists:
            raise HTTPException(status_code=400, detail="该邮箱已注册")

        code = db.execute(
            """
            SELECT id, expires_at FROM verification_codes
            WHERE email = ? AND code = ? AND used = 0
            ORDER BY id DESC LIMIT 1
            """,
            (payload.email, payload.code),
        ).fetchone()
        if not code:
            raise HTTPException(status_code=400, detail="验证码不正确")
        if datetime.fromisoformat(code["expires_at"].removesuffix("Z")) < datetime.utcnow():
            raise HTTPException(status_code=400, detail="验证码已过期")

        cursor = db.execute(
            "INSERT INTO teachers (email, password_hash, created_at) VALUES (?, ?, ?)",
            (payload.email, hash_password(payload.password), now_iso()),
        )
        db.execute("UPDATE verification_codes SET used = 1 WHERE id = ?", (code["id"],))
        teacher_id = cursor.lastrowid

    return {"token": create_token(teacher_id), "teacher": {"id": teacher_id, "email": payload.email}}


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    with get_db() as db:
        teacher = db.execute(
            "SELECT id, email, password_hash FROM teachers WHERE email = ?",
            (payload.email,),
        ).fetchone()
    if not teacher or not verify_password(payload.password, teacher["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    return {"token": create_token(teacher["id"]), "teacher": {"id": teacher["id"], "email": teacher["email"]}}


@app.get("/api/auth/me")
def me(teacher: dict = CurrentTeacher):
    return {"teacher": teacher}


@app.get("/api/students")
def list_students(teacher: dict = CurrentTeacher):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT s.*, COUNT(f.id) AS feedback_count
            FROM students s
            LEFT JOIN feedbacks f ON f.student_id = s.id
            WHERE s.teacher_id = ?
            GROUP BY s.id
            ORDER BY s.id DESC
            """,
            (teacher["id"],),
        ).fetchall()
    return {"students": [dict(row) for row in rows]}


@app.post("/api/students")
def create_student(payload: StudentCreate, teacher: dict = CurrentTeacher):
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO students (teacher_id, name, grade, subject, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (teacher["id"], payload.name, payload.grade, payload.subject, payload.note, now_iso()),
        )
        student = db.execute("SELECT * FROM students WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return {"student": dict(student)}


@app.get("/api/students/{student_id}")
def get_student(student_id: int, teacher: dict = CurrentTeacher):
    return {"student": require_student(student_id, teacher["id"])}


@app.put("/api/students/{student_id}")
def update_student(student_id: int, payload: StudentUpdate, teacher: dict = CurrentTeacher):
    require_student(student_id, teacher["id"])
    with get_db() as db:
        db.execute(
            """
            UPDATE students
            SET name = ?, grade = ?, subject = ?, note = ?
            WHERE id = ? AND teacher_id = ?
            """,
            (payload.name, payload.grade, payload.subject, payload.note, student_id, teacher["id"]),
        )
        student = db.execute(
            "SELECT * FROM students WHERE id = ? AND teacher_id = ?",
            (student_id, teacher["id"]),
        ).fetchone()
    return {"student": dict(student)}


@app.delete("/api/students/{student_id}")
def delete_student(student_id: int, teacher: dict = CurrentTeacher):
    require_student(student_id, teacher["id"])
    with get_db() as db:
        db.execute("DELETE FROM students WHERE id = ? AND teacher_id = ?", (student_id, teacher["id"]))
    return {"ok": True}


@app.get("/api/students/{student_id}/feedbacks")
def list_feedbacks(student_id: int, teacher: dict = CurrentTeacher):
    require_student(student_id, teacher["id"])
    with get_db() as db:
        rows = db.execute(
            """
            SELECT * FROM feedbacks
            WHERE student_id = ? AND teacher_id = ?
            ORDER BY lesson_time DESC, id DESC
            """,
            (student_id, teacher["id"]),
        ).fetchall()
    return {"feedbacks": [dict(row) for row in rows]}


@app.post("/api/students/{student_id}/feedbacks/generate")
async def create_ai_draft(student_id: int, payload: FeedbackGenerateRequest, teacher: dict = CurrentTeacher):
    student = require_student(student_id, teacher["id"])
    with get_db() as db:
        feedback_count = db.execute(
            "SELECT COUNT(*) AS count FROM feedbacks WHERE student_id = ? AND teacher_id = ?",
            (student_id, teacher["id"]),
        ).fetchone()["count"]
    try:
        draft = await generate_feedback(
            student_name=student["name"],
            subject=student["subject"] or "数学",
            lesson_number=feedback_count + 1,
            lesson_date=lesson_date_label(payload.lesson_time),
            lesson_summary=payload.lesson_summary,
            performance_summary=payload.performance_summary,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"AI 服务暂时不可用：{exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI 反馈生成失败，请稍后重试") from exc
    return {"draft": draft}


@app.post("/api/students/{student_id}/feedbacks")
def create_feedback(student_id: int, payload: FeedbackCreate, teacher: dict = CurrentTeacher):
    require_student(student_id, teacher["id"])
    timestamp = now_iso()
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO feedbacks (
                teacher_id, student_id, lesson_time, lesson_summary, performance_summary,
                ai_draft, final_feedback, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                teacher["id"],
                student_id,
                payload.lesson_time,
                payload.lesson_summary,
                payload.performance_summary,
                payload.ai_draft,
                payload.final_feedback,
                timestamp,
                timestamp,
            ),
        )
        feedback = db.execute("SELECT * FROM feedbacks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return {"feedback": dict(feedback)}


@app.get("/api/feedbacks/{feedback_id}")
def get_feedback(feedback_id: int, teacher: dict = CurrentTeacher):
    return {"feedback": require_feedback(feedback_id, teacher["id"])}


@app.put("/api/feedbacks/{feedback_id}")
def update_feedback(feedback_id: int, payload: FeedbackUpdate, teacher: dict = CurrentTeacher):
    require_feedback(feedback_id, teacher["id"])
    timestamp = now_iso()
    with get_db() as db:
        db.execute(
            """
            UPDATE feedbacks
            SET lesson_time = ?, lesson_summary = ?, performance_summary = ?,
                ai_draft = ?, final_feedback = ?, updated_at = ?
            WHERE id = ? AND teacher_id = ?
            """,
            (
                payload.lesson_time,
                payload.lesson_summary,
                payload.performance_summary,
                payload.ai_draft,
                payload.final_feedback,
                timestamp,
                feedback_id,
                teacher["id"],
            ),
        )
        feedback = db.execute(
            "SELECT * FROM feedbacks WHERE id = ? AND teacher_id = ?",
            (feedback_id, teacher["id"]),
        ).fetchone()
    return {"feedback": dict(feedback)}


@app.delete("/api/feedbacks/{feedback_id}")
def delete_feedback(feedback_id: int, teacher: dict = CurrentTeacher):
    require_feedback(feedback_id, teacher["id"])
    with get_db() as db:
        db.execute("DELETE FROM feedbacks WHERE id = ? AND teacher_id = ?", (feedback_id, teacher["id"]))
    return {"ok": True}


@app.get("/api/evening/classes")
def list_evening_classes(teacher: dict = CurrentTeacher):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT c.*, COUNT(s.id) AS student_count
            FROM evening_classes c
            LEFT JOIN evening_students s ON s.class_id = c.id
            WHERE c.teacher_id = ?
            GROUP BY c.id
            ORDER BY c.id DESC
            """,
            (teacher["id"],),
        ).fetchall()
    return {"classes": [dict(row) for row in rows]}


@app.post("/api/evening/classes")
def create_evening_class(payload: EveningClassCreate, teacher: dict = CurrentTeacher):
    timestamp = now_iso()
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO evening_classes (teacher_id, name, note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (teacher["id"], payload.name, payload.note, timestamp, timestamp),
        )
        row = db.execute("SELECT * FROM evening_classes WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return {"class": dict(row)}


@app.get("/api/evening/classes/{class_id}")
def get_evening_class(class_id: int, teacher: dict = CurrentTeacher):
    return {"class": require_evening_class(class_id, teacher["id"])}


@app.put("/api/evening/classes/{class_id}")
def update_evening_class(class_id: int, payload: EveningClassUpdate, teacher: dict = CurrentTeacher):
    require_evening_class(class_id, teacher["id"])
    with get_db() as db:
        db.execute(
            "UPDATE evening_classes SET name = ?, note = ?, updated_at = ? WHERE id = ? AND teacher_id = ?",
            (payload.name, payload.note, now_iso(), class_id, teacher["id"]),
        )
        row = db.execute(
            "SELECT * FROM evening_classes WHERE id = ? AND teacher_id = ?",
            (class_id, teacher["id"]),
        ).fetchone()
    return {"class": dict(row)}


@app.delete("/api/evening/classes/{class_id}")
def delete_evening_class(class_id: int, teacher: dict = CurrentTeacher):
    require_evening_class(class_id, teacher["id"])
    with get_db() as db:
        db.execute("DELETE FROM evening_classes WHERE id = ? AND teacher_id = ?", (class_id, teacher["id"]))
    return {"ok": True}


@app.get("/api/evening/classes/{class_id}/students")
def list_evening_students(class_id: int, teacher: dict = CurrentTeacher):
    require_evening_class(class_id, teacher["id"])
    with get_db() as db:
        rows = db.execute(
            """
            SELECT s.*, COUNT(f.id) AS feedback_count
            FROM evening_students s
            LEFT JOIN evening_monthly_feedbacks f ON f.student_id = s.id
            WHERE s.class_id = ? AND s.teacher_id = ?
            GROUP BY s.id
            ORDER BY s.id DESC
            """,
            (class_id, teacher["id"]),
        ).fetchall()
    return {"students": [dict(row) for row in rows]}


@app.post("/api/evening/classes/{class_id}/students/bulk")
def bulk_create_evening_students(class_id: int, payload: EveningStudentBulkCreate, teacher: dict = CurrentTeacher):
    require_evening_class(class_id, teacher["id"])
    names = []
    for line in payload.names_text.splitlines():
        name = line.strip()
        if name and name not in names:
            names.append(name)
    if not names:
        raise HTTPException(status_code=400, detail="请至少输入一名学生")

    timestamp = now_iso()
    with get_db() as db:
        for name in names:
            db.execute(
                """
                INSERT INTO evening_students (
                    teacher_id, class_id, name, grade, school, note, created_at, updated_at
                )
                VALUES (?, ?, ?, '', '', '', ?, ?)
                """,
                (teacher["id"], class_id, name, timestamp, timestamp),
            )
        rows = db.execute(
            "SELECT * FROM evening_students WHERE class_id = ? AND teacher_id = ? ORDER BY id DESC",
            (class_id, teacher["id"]),
        ).fetchall()
    return {"students": [dict(row) for row in rows], "created_count": len(names)}


@app.get("/api/evening/students/{student_id}")
def get_evening_student(student_id: int, teacher: dict = CurrentTeacher):
    return {"student": require_evening_student(student_id, teacher["id"])}


@app.put("/api/evening/students/{student_id}")
def update_evening_student(student_id: int, payload: EveningStudentUpdate, teacher: dict = CurrentTeacher):
    require_evening_student(student_id, teacher["id"])
    with get_db() as db:
        db.execute(
            """
            UPDATE evening_students
            SET name = ?, grade = ?, school = ?, note = ?, updated_at = ?
            WHERE id = ? AND teacher_id = ?
            """,
            (payload.name, payload.grade, payload.school, payload.note, now_iso(), student_id, teacher["id"]),
        )
        row = db.execute(
            "SELECT * FROM evening_students WHERE id = ? AND teacher_id = ?",
            (student_id, teacher["id"]),
        ).fetchone()
    return {"student": dict(row)}


@app.delete("/api/evening/students/{student_id}")
def delete_evening_student(student_id: int, teacher: dict = CurrentTeacher):
    require_evening_student(student_id, teacher["id"])
    with get_db() as db:
        db.execute("DELETE FROM evening_students WHERE id = ? AND teacher_id = ?", (student_id, teacher["id"]))
    return {"ok": True}


@app.get("/api/evening/students/{student_id}/monthly-feedbacks")
def list_evening_monthly_feedbacks(student_id: int, teacher: dict = CurrentTeacher):
    require_evening_student(student_id, teacher["id"])
    with get_db() as db:
        rows = db.execute(
            """
            SELECT * FROM evening_monthly_feedbacks
            WHERE student_id = ? AND teacher_id = ?
            ORDER BY feedback_month DESC, id DESC
            """,
            (student_id, teacher["id"]),
        ).fetchall()
    return {"feedbacks": [dict(row) for row in rows]}


@app.post("/api/evening/students/{student_id}/monthly-feedbacks/generate")
async def generate_evening_monthly_draft(
    student_id: int,
    payload: EveningMonthlyGenerateRequest,
    teacher: dict = CurrentTeacher,
):
    student = require_evening_student(student_id, teacher["id"])
    try:
        draft = await generate_evening_monthly_feedback(
            student_name=student["name"],
            grade=student["grade"],
            school=student["school"],
            feedback_month=payload.feedback_month,
            homework_summary=payload.homework_summary,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"AI 服务暂时不可用：{exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI 晚辅反馈生成失败，请稍后重试") from exc
    return {"draft": draft}


@app.post("/api/evening/students/{student_id}/monthly-feedbacks")
def create_evening_monthly_feedback(
    student_id: int,
    payload: EveningMonthlyFeedbackCreate,
    teacher: dict = CurrentTeacher,
):
    require_evening_student(student_id, teacher["id"])
    timestamp = now_iso()
    try:
        with get_db() as db:
            cursor = db.execute(
                """
                INSERT INTO evening_monthly_feedbacks (
                    teacher_id, student_id, feedback_month, homework_summary,
                    ai_draft, final_feedback, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    teacher["id"],
                    student_id,
                    payload.feedback_month,
                    payload.homework_summary,
                    payload.ai_draft,
                    payload.final_feedback,
                    timestamp,
                    timestamp,
                ),
            )
            row = db.execute(
                "SELECT * FROM evening_monthly_feedbacks WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="该学生这个月份已经有反馈，请编辑已有反馈") from exc
    return {"feedback": dict(row)}


@app.put("/api/evening/monthly-feedbacks/{feedback_id}")
def update_evening_monthly_feedback(
    feedback_id: int,
    payload: EveningMonthlyFeedbackUpdate,
    teacher: dict = CurrentTeacher,
):
    require_evening_monthly_feedback(feedback_id, teacher["id"])
    try:
        with get_db() as db:
            db.execute(
                """
                UPDATE evening_monthly_feedbacks
                SET feedback_month = ?, homework_summary = ?, ai_draft = ?,
                    final_feedback = ?, updated_at = ?
                WHERE id = ? AND teacher_id = ?
                """,
                (
                    payload.feedback_month,
                    payload.homework_summary,
                    payload.ai_draft,
                    payload.final_feedback,
                    now_iso(),
                    feedback_id,
                    teacher["id"],
                ),
            )
            row = db.execute(
                "SELECT * FROM evening_monthly_feedbacks WHERE id = ? AND teacher_id = ?",
                (feedback_id, teacher["id"]),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="该学生这个月份已经有反馈，请编辑已有反馈") from exc
    return {"feedback": dict(row)}


@app.delete("/api/evening/monthly-feedbacks/{feedback_id}")
def delete_evening_monthly_feedback(feedback_id: int, teacher: dict = CurrentTeacher):
    require_evening_monthly_feedback(feedback_id, teacher["id"])
    with get_db() as db:
        db.execute(
            "DELETE FROM evening_monthly_feedbacks WHERE id = ? AND teacher_id = ?",
            (feedback_id, teacher["id"]),
        )
    return {"ok": True}
