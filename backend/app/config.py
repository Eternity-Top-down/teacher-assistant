import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    app_secret: str = os.getenv("APP_SECRET", "dev-secret-change-me")
    database_path: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "teacher_assistant.db"))

    smtp_host: str = os.getenv("SMTP_HOST", "smtp.qq.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "465"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "")


settings = Settings()
