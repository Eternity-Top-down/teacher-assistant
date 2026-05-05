import sqlite3
from contextlib import contextmanager
from datetime import datetime

from .config import settings


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


@contextmanager
def get_db():
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS verification_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                grade TEXT NOT NULL DEFAULT '',
                subject TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                lesson_title TEXT NOT NULL DEFAULT '',
                lesson_time TEXT NOT NULL,
                lesson_summary TEXT NOT NULL,
                performance_summary TEXT NOT NULL DEFAULT '',
                advice_summary TEXT NOT NULL DEFAULT '',
                homework_plan TEXT NOT NULL DEFAULT '',
                ai_draft TEXT NOT NULL,
                final_feedback TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS evening_classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS evening_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                grade TEXT NOT NULL DEFAULT '',
                school TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES evening_classes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS evening_monthly_feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                feedback_month TEXT NOT NULL,
                homework_summary TEXT NOT NULL,
                ai_draft TEXT NOT NULL,
                final_feedback TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(student_id, feedback_month),
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES evening_students(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS teacher_ai_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL UNIQUE,
                provider TEXT NOT NULL DEFAULT 'deepseek',
                base_url TEXT NOT NULL,
                model TEXT NOT NULL,
                encrypted_api_key TEXT NOT NULL DEFAULT '',
                feedback_format_mode TEXT NOT NULL DEFAULT 'structured',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS teacher_vision_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL UNIQUE,
                provider TEXT NOT NULL DEFAULT 'doubao_v',
                base_url TEXT NOT NULL,
                model TEXT NOT NULL,
                encrypted_api_key TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS teacher_style_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'manual',
                source_feedback_id INTEGER,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
            );
            """
        )
        columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(feedbacks)").fetchall()
        }
        if "homework_plan" not in columns:
            db.execute("ALTER TABLE feedbacks ADD COLUMN homework_plan TEXT NOT NULL DEFAULT ''")
        if "lesson_title" not in columns:
            db.execute("ALTER TABLE feedbacks ADD COLUMN lesson_title TEXT NOT NULL DEFAULT ''")
        if "advice_summary" not in columns:
            db.execute("ALTER TABLE feedbacks ADD COLUMN advice_summary TEXT NOT NULL DEFAULT ''")
        settings_columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(teacher_ai_settings)").fetchall()
        }
        if "feedback_format_mode" not in settings_columns:
            db.execute(
                "ALTER TABLE teacher_ai_settings ADD COLUMN feedback_format_mode TEXT NOT NULL DEFAULT 'structured'"
            )
