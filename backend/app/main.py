import base64
import binascii
from datetime import datetime, timedelta

import sqlite3

import httpx
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from .ai_client import analyze_lesson_materials, generate_evening_monthly_feedback, generate_feedback
from .ai_settings import (
    AIConfig,
    ai_settings_summary,
    get_teacher_ai_settings,
    get_teacher_vision_settings,
    require_teacher_ai_config,
    require_teacher_vision_config,
    save_teacher_ai_settings,
    save_teacher_vision_settings,
    test_ai_connection,
    test_vision_connection,
    vision_settings_summary,
)
from .database import get_db, init_db, now_iso
from .email_service import make_code, send_verification_email
from .schemas import (
    AISettingsTest,
    AISettingsUpdate,
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
    GroupClassCreate,
    GroupClassUpdate,
    LoginRequest,
    MaterialsAnalyzeRequest,
    MaterialsAnalyzeResponse,
    RegisterRequest,
    StudentCreate,
    StudentUpdate,
    StyleExampleCreate,
    StyleExampleFromFeedback,
    StyleExampleUpdate,
    VisionSettingsTest,
    VisionSettingsUpdate,
)
from .security import CurrentTeacher, create_token, hash_password, verify_password


app = FastAPI(title="教师一对一反馈助手 API")

MAX_ENABLED_STYLE_EXAMPLES = 5

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


def require_group_class(class_id: int, teacher_id: int) -> dict:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM group_classes WHERE id = ? AND teacher_id = ?",
            (class_id, teacher_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="班课班级不存在")
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


def list_enabled_style_examples(teacher_id: int, limit: int = 5) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            """
            SELECT id, title, content, source_type, source_feedback_id, enabled, created_at, updated_at
            FROM teacher_style_examples
            WHERE teacher_id = ? AND enabled = 1
            ORDER BY id DESC
            LIMIT ?
            """,
            (teacher_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def count_enabled_style_examples(teacher_id: int, exclude_example_id: int | None = None) -> int:
    query = "SELECT COUNT(*) AS count FROM teacher_style_examples WHERE teacher_id = ? AND enabled = 1"
    params: list[int] = [teacher_id]
    if exclude_example_id is not None:
        query += " AND id != ?"
        params.append(exclude_example_id)
    with get_db() as db:
        return db.execute(query, params).fetchone()["count"]


def ensure_style_example_enable_slot(teacher_id: int, exclude_example_id: int | None = None) -> None:
    if count_enabled_style_examples(teacher_id, exclude_example_id) >= MAX_ENABLED_STYLE_EXAMPLES:
        raise HTTPException(status_code=400, detail="最多启用 5 条风格样例参与生成，请先停用一条样例")


def require_style_example(example_id: int, teacher_id: int) -> dict:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM teacher_style_examples WHERE id = ? AND teacher_id = ?",
            (example_id, teacher_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="风格样例不存在")
    return dict(row)


def _service_error_excerpt(text: str) -> str:
    compact = " ".join((text or "").split())
    return compact[:300]


def ai_error_detail(exc: Exception, action: str) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        excerpt = _service_error_excerpt(exc.response.text)
        suffix = f" 服务商返回：{excerpt}" if excerpt else ""
        if status_code in (401, 403):
            return f"{action}失败：API Key 无效、权限不足或账号无权访问该模型，请检查设置页里的 API Key 和模型权限。{suffix}"
        if status_code == 404:
            return f"{action}失败：接口地址或模型路径不存在，请检查 Base URL 是否包含正确的 /v1 兼容地址，以及模型名是否正确。{suffix}"
        if status_code == 429:
            return f"{action}失败：模型服务限流或额度不足，请稍后重试，或检查账号余额/调用额度。{suffix}"
        if status_code == 400:
            return f"{action}失败：请求参数、模型名或模型能力不匹配，请检查模型名和当前模型是否支持本功能。{suffix}"
        if status_code >= 500:
            return f"{action}失败：模型服务商暂时异常，请稍后重试。{suffix}"
        return f"{action}失败：模型服务返回 HTTP {status_code}。{suffix}"

    if isinstance(exc, httpx.TimeoutException):
        return f"{action}失败：连接模型服务超时，请稍后重试，或检查 Base URL 和服务商状态。"
    if isinstance(exc, httpx.RequestError):
        return f"{action}失败：无法连接模型服务，请检查 Base URL、网络连接或服务商状态。错误：{exc}"
    if isinstance(exc, (KeyError, IndexError, TypeError, ValueError)):
        return f"{action}失败：AI 返回内容格式异常，不符合 OpenAI-compatible Chat Completions 格式，请检查 Base URL 和模型接口。"
    return f"{action}失败：发生未知错误，请检查模型配置后重试。"


def raise_ai_exception(exc: Exception, action: str) -> None:
    raise HTTPException(status_code=502, detail=ai_error_detail(exc, action)) from exc


ALLOWED_MATERIAL_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_MATERIAL_IMAGES = 9
MAX_MATERIAL_IMAGE_BYTES = 8 * 1024 * 1024


def validate_material_images(payload: MaterialsAnalyzeRequest) -> list[dict]:
    if len(payload.images) > MAX_MATERIAL_IMAGES:
        raise HTTPException(status_code=400, detail=f"一次最多上传 {MAX_MATERIAL_IMAGES} 张课堂资料图片")

    images = []
    for index, image in enumerate(payload.images, start=1):
        mime_type = image.mime_type.lower().strip()
        if mime_type not in ALLOWED_MATERIAL_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail=f"第 {index} 个资料页面格式不支持，请上传 JPG、PNG、WEBP 或 PDF")
        try:
            raw = base64.b64decode(image.data_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"第 {index} 个资料页面数据无效，请重新选择") from exc
        if not raw:
            raise HTTPException(status_code=400, detail=f"第 {index} 个资料页面为空，请重新选择")
        if len(raw) > MAX_MATERIAL_IMAGE_BYTES:
            raise HTTPException(status_code=400, detail=f"第 {index} 个资料页面超过 8MB，请压缩后再上传")
        images.append(
            {
                "name": image.name.strip() or f"课堂资料{index}",
                "mime_type": mime_type,
                "data_base64": image.data_base64,
            }
        )
    return images


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


@app.get("/api/settings/ai")
def get_ai_settings(teacher: dict = CurrentTeacher):
    row = get_teacher_ai_settings(teacher["id"])
    return {"settings": ai_settings_summary(row)}


@app.put("/api/settings/ai")
def update_ai_settings(payload: AISettingsUpdate, teacher: dict = CurrentTeacher):
    row = save_teacher_ai_settings(
        teacher_id=teacher["id"],
        provider=payload.provider,
        base_url=payload.base_url,
        model=payload.model,
        api_key=payload.api_key,
        clear_api_key=payload.clear_api_key,
        feedback_format_mode=payload.feedback_format_mode,
    )
    return {"settings": ai_settings_summary(row)}


@app.post("/api/settings/ai/test")
async def test_ai_settings(payload: AISettingsTest, teacher: dict = CurrentTeacher):
    api_key = payload.api_key.strip()
    if not api_key:
        saved = get_teacher_ai_settings(teacher["id"])
        if saved and saved["encrypted_api_key"]:
            config = require_teacher_ai_config(teacher["id"])
            config.provider = payload.provider
            config.base_url = payload.base_url.rstrip("/")
            config.model = payload.model
        else:
            raise HTTPException(status_code=400, detail="请先填写 API Key，或先保存一份可用配置")
    else:
        config = AIConfig(
            api_key=api_key,
            base_url=payload.base_url.rstrip("/"),
            model=payload.model,
            provider=payload.provider,
        )
    reply = await test_ai_connection(config)
    return {"ok": True, "message": "连接成功，可以生成反馈", "reply": reply}


@app.get("/api/settings/vision")
def get_vision_settings(teacher: dict = CurrentTeacher):
    row = get_teacher_vision_settings(teacher["id"])
    return {"settings": vision_settings_summary(row)}


@app.put("/api/settings/vision")
def update_vision_settings(payload: VisionSettingsUpdate, teacher: dict = CurrentTeacher):
    row = save_teacher_vision_settings(
        teacher_id=teacher["id"],
        provider=payload.provider,
        base_url=payload.base_url,
        model=payload.model,
        api_key=payload.api_key,
        clear_api_key=payload.clear_api_key,
    )
    return {"settings": vision_settings_summary(row)}


@app.post("/api/settings/vision/test")
async def test_vision_settings(payload: VisionSettingsTest, teacher: dict = CurrentTeacher):
    api_key = payload.api_key.strip()
    if not api_key:
        saved = get_teacher_vision_settings(teacher["id"])
        if saved and saved["encrypted_api_key"]:
            config = require_teacher_vision_config(teacher["id"])
            config.provider = payload.provider
            config.base_url = payload.base_url.rstrip("/")
            config.model = payload.model
        else:
            raise HTTPException(status_code=400, detail="请先填写图片识别模型的 API Key，或先保存一份可用配置")
    else:
        config = AIConfig(
            api_key=api_key,
            base_url=payload.base_url.rstrip("/"),
            model=payload.model,
            provider=payload.provider,
        )
    reply = await test_vision_connection(config)
    return {"ok": True, "message": "图片识别模型连接成功", "reply": reply}


@app.get("/api/settings/style-examples")
def list_style_examples(teacher: dict = CurrentTeacher):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT id, title, content, source_type, source_feedback_id, enabled, created_at, updated_at
            FROM teacher_style_examples
            WHERE teacher_id = ?
            ORDER BY id DESC
            """,
            (teacher["id"],),
        ).fetchall()
    return {"examples": [dict(row) for row in rows]}


@app.post("/api/settings/style-examples")
def create_style_example(payload: StyleExampleCreate, teacher: dict = CurrentTeacher):
    if payload.enabled:
        ensure_style_example_enable_slot(teacher["id"])
    timestamp = now_iso()
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO teacher_style_examples (
                teacher_id, title, content, source_type, source_feedback_id, enabled, created_at, updated_at
            )
            VALUES (?, ?, ?, 'manual', NULL, ?, ?, ?)
            """,
            (teacher["id"], payload.title.strip(), payload.content.strip(), int(payload.enabled), timestamp, timestamp),
        )
        row = db.execute("SELECT * FROM teacher_style_examples WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return {"example": dict(row)}


@app.put("/api/settings/style-examples/{example_id}")
def update_style_example(example_id: int, payload: StyleExampleUpdate, teacher: dict = CurrentTeacher):
    existing = require_style_example(example_id, teacher["id"])
    if payload.enabled and not existing["enabled"]:
        ensure_style_example_enable_slot(teacher["id"], example_id)
    with get_db() as db:
        db.execute(
            """
            UPDATE teacher_style_examples
            SET title = ?, content = ?, enabled = ?, updated_at = ?
            WHERE id = ? AND teacher_id = ?
            """,
            (
                payload.title.strip(),
                payload.content.strip(),
                int(payload.enabled),
                now_iso(),
                example_id,
                teacher["id"],
            ),
        )
        row = db.execute(
            "SELECT * FROM teacher_style_examples WHERE id = ? AND teacher_id = ?",
            (example_id, teacher["id"]),
        ).fetchone()
    return {"example": dict(row)}


@app.delete("/api/settings/style-examples/{example_id}")
def delete_style_example(example_id: int, teacher: dict = CurrentTeacher):
    require_style_example(example_id, teacher["id"])
    with get_db() as db:
        db.execute(
            "DELETE FROM teacher_style_examples WHERE id = ? AND teacher_id = ?",
            (example_id, teacher["id"]),
        )
    return {"ok": True}


@app.post("/api/settings/style-examples/from-feedback")
def create_style_example_from_feedback(payload: StyleExampleFromFeedback, teacher: dict = CurrentTeacher):
    if payload.feedback_type == "one_on_one":
        feedback = require_feedback(payload.feedback_id, teacher["id"])
        content = feedback["final_feedback"]
        title = payload.title.strip() or feedback["lesson_title"] or f"一对一反馈样例 {feedback['lesson_time']}"
    else:
        feedback = require_evening_monthly_feedback(payload.feedback_id, teacher["id"])
        content = feedback["final_feedback"]
        title = payload.title.strip() or f"晚辅月度反馈样例 {feedback['feedback_month']}"

    ensure_style_example_enable_slot(teacher["id"])
    timestamp = now_iso()
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO teacher_style_examples (
                teacher_id, title, content, source_type, source_feedback_id, enabled, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (teacher["id"], title, content, payload.feedback_type, payload.feedback_id, timestamp, timestamp),
        )
        row = db.execute("SELECT * FROM teacher_style_examples WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return {"example": dict(row)}


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
    ai_config = require_teacher_ai_config(teacher["id"])
    try:
        draft = await generate_feedback(
            student_name=student["name"],
            subject=student["subject"] or "数学",
            lesson_number=feedback_count + 1,
            lesson_title=payload.lesson_title,
            lesson_date=lesson_date_label(payload.lesson_time),
            lesson_summary=payload.lesson_summary,
            performance_summary=payload.performance_summary,
            advice_summary=payload.advice_summary,
            homework_plan=payload.homework_plan,
            supplement_summary=payload.supplement_summary,
            style_examples=list_enabled_style_examples(teacher["id"]) if payload.use_style_examples else [],
            ai_config=ai_config,
        )
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise_ai_exception(exc, "AI 初稿生成")
    except Exception as exc:
        raise_ai_exception(exc, "AI 初稿生成")
    return {"draft": draft}


@app.post("/api/students/{student_id}/feedbacks/materials/analyze", response_model=MaterialsAnalyzeResponse)
async def analyze_feedback_materials(student_id: int, payload: MaterialsAnalyzeRequest, teacher: dict = CurrentTeacher):
    student = require_student(student_id, teacher["id"])
    images = validate_material_images(payload)
    vision_config = require_teacher_vision_config(teacher["id"])
    try:
        return await analyze_lesson_materials(
            student_name=student["name"],
            subject=payload.subject or student["subject"] or "数学",
            lesson_title=payload.lesson_title,
            images=images,
            ai_config=vision_config,
        )
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
        raise_ai_exception(exc, "课堂资料识别")
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"课堂资料识别结果格式异常，请重试或换一个图片识别模型。{exc}") from exc
    except Exception as exc:
        raise_ai_exception(exc, "课堂资料识别")


@app.post("/api/students/{student_id}/feedbacks")
def create_feedback(student_id: int, payload: FeedbackCreate, teacher: dict = CurrentTeacher):
    require_student(student_id, teacher["id"])
    timestamp = now_iso()
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO feedbacks (
                teacher_id, student_id, lesson_title, lesson_time, lesson_summary, performance_summary,
                advice_summary, homework_plan, ai_draft, final_feedback, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                teacher["id"],
                student_id,
                payload.lesson_title,
                payload.lesson_time,
                payload.lesson_summary,
                payload.performance_summary,
                payload.advice_summary,
                payload.homework_plan,
                payload.ai_draft,
                payload.final_feedback,
                timestamp,
                timestamp,
            ),
        )
        feedback = db.execute("SELECT * FROM feedbacks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return {"feedback": dict(feedback)}


@app.get("/api/feedbacks")
def search_feedbacks(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    teacher: dict = CurrentTeacher,
):
    conditions = ["f.teacher_id = ?"]
    params: list[str | int] = [teacher["id"]]

    if start_date:
        conditions.append("f.lesson_time >= ?")
        params.append(f"{start_date}T00:00")
    if end_date:
        conditions.append("f.lesson_time <= ?")
        params.append(f"{end_date}T23:59:59")

    with get_db() as db:
        rows = db.execute(
            f"""
            SELECT
                f.id, f.student_id, s.name AS student_name, s.grade, s.subject,
                f.lesson_title, f.lesson_time, f.lesson_summary, f.final_feedback,
                f.created_at, f.updated_at
            FROM feedbacks f
            JOIN students s ON s.id = f.student_id AND s.teacher_id = f.teacher_id
            WHERE {' AND '.join(conditions)}
            ORDER BY f.lesson_time DESC, f.id DESC
            """,
            params,
        ).fetchall()
    return {"feedbacks": [dict(row) for row in rows]}


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
            SET lesson_title = ?, lesson_time = ?, lesson_summary = ?, performance_summary = ?,
                advice_summary = ?, homework_plan = ?, ai_draft = ?, final_feedback = ?, updated_at = ?
            WHERE id = ? AND teacher_id = ?
            """,
            (
                payload.lesson_title,
                payload.lesson_time,
                payload.lesson_summary,
                payload.performance_summary,
                payload.advice_summary,
                payload.homework_plan,
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
            INSERT INTO evening_classes (teacher_id, name, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (teacher["id"], payload.name, timestamp, timestamp),
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
            "UPDATE evening_classes SET name = ?, updated_at = ? WHERE id = ? AND teacher_id = ?",
            (payload.name, now_iso(), class_id, teacher["id"]),
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


@app.get("/api/group-classes")
def list_group_classes(teacher: dict = CurrentTeacher):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT *
            FROM group_classes
            WHERE teacher_id = ?
            ORDER BY id DESC
            """,
            (teacher["id"],),
        ).fetchall()
    return {"classes": [dict(row) for row in rows]}


@app.post("/api/group-classes")
def create_group_class(payload: GroupClassCreate, teacher: dict = CurrentTeacher):
    timestamp = now_iso()
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO group_classes (teacher_id, name, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (teacher["id"], payload.name, timestamp, timestamp),
        )
        row = db.execute("SELECT * FROM group_classes WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return {"class": dict(row)}


@app.get("/api/group-classes/{class_id}")
def get_group_class(class_id: int, teacher: dict = CurrentTeacher):
    return {"class": require_group_class(class_id, teacher["id"])}


@app.put("/api/group-classes/{class_id}")
def update_group_class(class_id: int, payload: GroupClassUpdate, teacher: dict = CurrentTeacher):
    require_group_class(class_id, teacher["id"])
    with get_db() as db:
        db.execute(
            "UPDATE group_classes SET name = ?, updated_at = ? WHERE id = ? AND teacher_id = ?",
            (payload.name, now_iso(), class_id, teacher["id"]),
        )
        row = db.execute(
            "SELECT * FROM group_classes WHERE id = ? AND teacher_id = ?",
            (class_id, teacher["id"]),
        ).fetchone()
    return {"class": dict(row)}


@app.delete("/api/group-classes/{class_id}")
def delete_group_class(class_id: int, teacher: dict = CurrentTeacher):
    require_group_class(class_id, teacher["id"])
    with get_db() as db:
        db.execute("DELETE FROM group_classes WHERE id = ? AND teacher_id = ?", (class_id, teacher["id"]))
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
                    teacher_id, class_id, name, grade, school, created_at, updated_at
                )
                VALUES (?, ?, ?, '', '', ?, ?)
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
            SET name = ?, grade = ?, school = ?, updated_at = ?
            WHERE id = ? AND teacher_id = ?
            """,
            (payload.name, payload.grade, payload.school, now_iso(), student_id, teacher["id"]),
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


@app.get("/api/evening/monthly-feedbacks")
def search_evening_monthly_feedbacks(
    start_date: str = Query(default=""),
    end_date: str = Query(default=""),
    teacher: dict = CurrentTeacher,
):
    query = """
        SELECT f.*, s.name AS student_name, s.grade, s.school, c.name AS class_name
        FROM evening_monthly_feedbacks f
        JOIN evening_students s ON s.id = f.student_id
        JOIN evening_classes c ON c.id = s.class_id
        WHERE f.teacher_id = ?
    """
    params: list[str | int] = [teacher["id"]]
    if start_date:
        query += " AND f.feedback_month >= ?"
        params.append(start_date[:7])
    if end_date:
        query += " AND f.feedback_month <= ?"
        params.append(end_date[:7])
    query += " ORDER BY f.feedback_month DESC, f.id DESC"
    with get_db() as db:
        rows = db.execute(query, params).fetchall()
    return {"feedbacks": [dict(row) for row in rows]}


@app.post("/api/evening/students/{student_id}/monthly-feedbacks/generate")
async def generate_evening_monthly_draft(
    student_id: int,
    payload: EveningMonthlyGenerateRequest,
    teacher: dict = CurrentTeacher,
):
    student = require_evening_student(student_id, teacher["id"])
    ai_config = require_teacher_ai_config(teacher["id"])
    try:
        draft = await generate_evening_monthly_feedback(
            student_name=student["name"],
            grade=student["grade"],
            school=student["school"],
            feedback_month=payload.feedback_month,
            homework_summary=payload.homework_summary,
            ai_config=ai_config,
        )
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise_ai_exception(exc, "AI 晚辅反馈生成")
    except Exception as exc:
        raise_ai_exception(exc, "AI 晚辅反馈生成")
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
