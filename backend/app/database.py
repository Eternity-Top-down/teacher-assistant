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
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS group_classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                name TEXT NOT NULL,
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
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES evening_classes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS evening_feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                period_type TEXT NOT NULL,
                period_value TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                period_label TEXT NOT NULL,
                homework_summary TEXT NOT NULL,
                ai_draft TEXT NOT NULL,
                final_feedback TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(student_id, period_type, period_value),
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

            CREATE TABLE IF NOT EXISTS teacher_style_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL,
                feedback_type TEXT NOT NULL DEFAULT 'one_on_one',
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
        style_example_columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(teacher_style_examples)").fetchall()
        }
        if "feedback_type" not in style_example_columns:
            db.execute(
                "ALTER TABLE teacher_style_examples ADD COLUMN feedback_type TEXT NOT NULL DEFAULT 'one_on_one'"
            )
            db.execute(
                """
                UPDATE teacher_style_examples
                SET feedback_type = 'evening_feedback'
                WHERE source_type IN ('evening_feedback', 'evening_monthly')
                """
            )
            db.execute(
                """
                UPDATE teacher_style_examples
                SET source_type = 'feedback'
                WHERE source_type IN ('one_on_one', 'evening_feedback', 'evening_monthly')
                """
            )
        evening_class_columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(evening_classes)").fetchall()
        }
        if "note" in evening_class_columns:
            db.execute("PRAGMA foreign_keys = OFF")
            db.executescript(
                """
                CREATE TABLE evening_classes_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
                );
                INSERT INTO evening_classes_new (id, teacher_id, name, created_at, updated_at)
                SELECT id, teacher_id, name, created_at, updated_at FROM evening_classes;
                DROP TABLE evening_classes;
                ALTER TABLE evening_classes_new RENAME TO evening_classes;
                """
            )
            violations = db.execute("PRAGMA foreign_key_check").fetchall()
            db.execute("PRAGMA foreign_keys = ON")
            if violations:
                raise RuntimeError("evening_classes migration failed foreign key check")
        evening_student_columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(evening_students)").fetchall()
        }
        if "note" in evening_student_columns:
            db.execute("PRAGMA foreign_keys = OFF")
            db.executescript(
                """
                CREATE TABLE evening_students_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    class_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    grade TEXT NOT NULL DEFAULT '',
                    school TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                    FOREIGN KEY (class_id) REFERENCES evening_classes(id) ON DELETE CASCADE
                );
                INSERT INTO evening_students_new (id, teacher_id, class_id, name, grade, school, created_at, updated_at)
                SELECT id, teacher_id, class_id, name, grade, school, created_at, updated_at FROM evening_students;
                DROP TABLE evening_students;
                ALTER TABLE evening_students_new RENAME TO evening_students;
                """
            )
            violations = db.execute("PRAGMA foreign_key_check").fetchall()
            db.execute("PRAGMA foreign_keys = ON")
            if violations:
                raise RuntimeError("evening_students migration failed foreign key check")
        legacy_evening_feedback_table = db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'evening_monthly_feedbacks'"
        ).fetchone()
        if legacy_evening_feedback_table:
            db.execute(
                """
                INSERT OR IGNORE INTO evening_feedbacks (
                    id, teacher_id, student_id, period_type, period_value,
                    period_start, period_end, period_label, homework_summary,
                    ai_draft, final_feedback, created_at, updated_at
                )
                SELECT
                    id,
                    teacher_id,
                    student_id,
                    'month',
                    feedback_month,
                    feedback_month || '-01',
                    date(feedback_month || '-01', 'start of month', '+1 month', '-1 day'),
                    substr(feedback_month, 1, 4) || '年' || substr(feedback_month, 6, 2) || '月',
                    homework_summary,
                    ai_draft,
                    final_feedback,
                    created_at,
                    updated_at
                FROM evening_monthly_feedbacks
                """
            )
