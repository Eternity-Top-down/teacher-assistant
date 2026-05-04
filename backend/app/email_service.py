import random
import smtplib
from email.message import EmailMessage

from .config import settings


def make_code() -> str:
    return f"{random.randint(100000, 999999)}"


def send_verification_email(email: str, code: str) -> bool:
    if not settings.smtp_username or not settings.smtp_password:
        print(f"[DEV 验证码] {email}: {code}")
        return False

    message = EmailMessage()
    message["Subject"] = "教师助手注册验证码"
    message["From"] = settings.smtp_from or settings.smtp_username
    message["To"] = email
    message.set_content(f"你好，欢迎使用教师助手。\n\n你的注册验证码是：{code}\n验证码 10 分钟内有效。\n")

    with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
    return True
