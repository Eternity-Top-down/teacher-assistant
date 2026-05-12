import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass

import httpx
from fastapi import HTTPException

from .config import settings
from .database import get_db, now_iso


@dataclass
class AIConfig:
    api_key: str
    base_url: str
    model: str
    provider: str = "custom"


def _secret_key() -> bytes:
    return hashlib.sha256(settings.app_secret.encode("utf-8")).digest()


def _keystream(nonce: bytes, length: int) -> bytes:
    chunks = []
    counter = 0
    key = _secret_key()
    while sum(len(chunk) for chunk in chunks) < length:
        counter += 1
        chunks.append(hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest())
    return b"".join(chunks)[:length]


def encrypt_api_key(api_key: str) -> str:
    nonce = secrets.token_bytes(16)
    plain = api_key.encode("utf-8")
    cipher = bytes(a ^ b for a, b in zip(plain, _keystream(nonce, len(plain))))
    tag = hmac.new(_secret_key(), nonce + cipher, hashlib.sha256).digest()[:16]
    return "v1:" + base64.urlsafe_b64encode(nonce + tag + cipher).decode("ascii")


def decrypt_api_key(encrypted: str) -> str:
    if not encrypted:
        return ""
    try:
        version, encoded = encrypted.split(":", 1)
        if version != "v1":
            return ""
        raw = base64.urlsafe_b64decode(encoded.encode("ascii"))
        nonce, tag, cipher = raw[:16], raw[16:32], raw[32:]
        expected = hmac.new(_secret_key(), nonce + cipher, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(tag, expected):
            return ""
        plain = bytes(a ^ b for a, b in zip(cipher, _keystream(nonce, len(cipher))))
        return plain.decode("utf-8")
    except Exception:
        return ""


def ai_settings_summary(row: dict | None) -> dict:
    if not row:
        return {
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-v4-flash",
            "has_api_key": False,
            "feedback_format_mode": "structured",
            "updated_at": "",
        }
    return {
        "provider": row["provider"],
        "base_url": row["base_url"],
        "model": row["model"],
        "has_api_key": bool(row["encrypted_api_key"]),
        "feedback_format_mode": row["feedback_format_mode"] if "feedback_format_mode" in row.keys() else "structured",
        "updated_at": row["updated_at"],
    }


def vision_settings_summary(row: dict | None) -> dict:
    if not row:
        return {
            "provider": "doubao_v",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "doubao-1.5-vision-pro-32k",
            "has_api_key": False,
            "updated_at": "",
        }
    return {
        "provider": row["provider"],
        "base_url": row["base_url"],
        "model": row["model"],
        "has_api_key": bool(row["encrypted_api_key"]),
        "updated_at": row["updated_at"],
    }


def get_teacher_ai_settings(teacher_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM teacher_ai_settings WHERE teacher_id = ?",
            (teacher_id,),
        ).fetchone()
    return dict(row) if row else None


def get_teacher_vision_settings(teacher_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM teacher_vision_settings WHERE teacher_id = ?",
            (teacher_id,),
        ).fetchone()
    return dict(row) if row else None


def save_teacher_ai_settings(
    teacher_id: int,
    provider: str,
    base_url: str,
    model: str,
    api_key: str = "",
    clear_api_key: bool = False,
    feedback_format_mode: str = "structured",
) -> dict:
    existing = get_teacher_ai_settings(teacher_id)
    encrypted_api_key = existing["encrypted_api_key"] if existing else ""
    if clear_api_key:
        encrypted_api_key = ""
    elif api_key.strip():
        encrypted_api_key = encrypt_api_key(api_key.strip())

    timestamp = now_iso()
    with get_db() as db:
        if existing:
            db.execute(
                """
                UPDATE teacher_ai_settings
                SET provider = ?, base_url = ?, model = ?, encrypted_api_key = ?, feedback_format_mode = ?, updated_at = ?
                WHERE teacher_id = ?
                """,
                (
                    provider,
                    base_url.rstrip("/"),
                    model,
                    encrypted_api_key,
                    feedback_format_mode,
                    timestamp,
                    teacher_id,
                ),
            )
        else:
            db.execute(
                """
                INSERT INTO teacher_ai_settings (
                    teacher_id, provider, base_url, model, encrypted_api_key, feedback_format_mode, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    teacher_id,
                    provider,
                    base_url.rstrip("/"),
                    model,
                    encrypted_api_key,
                    feedback_format_mode,
                    timestamp,
                    timestamp,
                ),
            )
        row = db.execute(
            "SELECT * FROM teacher_ai_settings WHERE teacher_id = ?",
            (teacher_id,),
        ).fetchone()
    return dict(row)


def save_teacher_vision_settings(
    teacher_id: int,
    provider: str,
    base_url: str,
    model: str,
    api_key: str = "",
    clear_api_key: bool = False,
) -> dict:
    existing = get_teacher_vision_settings(teacher_id)
    encrypted_api_key = existing["encrypted_api_key"] if existing else ""
    if clear_api_key:
        encrypted_api_key = ""
    elif api_key.strip():
        encrypted_api_key = encrypt_api_key(api_key.strip())

    timestamp = now_iso()
    with get_db() as db:
        if existing:
            db.execute(
                """
                UPDATE teacher_vision_settings
                SET provider = ?, base_url = ?, model = ?, encrypted_api_key = ?, updated_at = ?
                WHERE teacher_id = ?
                """,
                (
                    provider,
                    base_url.rstrip("/"),
                    model,
                    encrypted_api_key,
                    timestamp,
                    teacher_id,
                ),
            )
        else:
            db.execute(
                """
                INSERT INTO teacher_vision_settings (
                    teacher_id, provider, base_url, model, encrypted_api_key, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    teacher_id,
                    provider,
                    base_url.rstrip("/"),
                    model,
                    encrypted_api_key,
                    timestamp,
                    timestamp,
                ),
            )
        row = db.execute(
            "SELECT * FROM teacher_vision_settings WHERE teacher_id = ?",
            (teacher_id,),
        ).fetchone()
    return dict(row)


def get_teacher_ai_config(teacher_id: int) -> AIConfig | None:
    row = get_teacher_ai_settings(teacher_id)
    if row and row["encrypted_api_key"]:
        api_key = decrypt_api_key(row["encrypted_api_key"])
        if api_key:
            return AIConfig(
                api_key=api_key,
                base_url=row["base_url"].rstrip("/"),
                model=row["model"],
                provider=row["provider"],
            )

    if settings.allow_global_ai_fallback and settings.ai_api_key:
        return AIConfig(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model,
            provider="env",
        )

    return None


def get_teacher_vision_config(teacher_id: int) -> AIConfig | None:
    row = get_teacher_vision_settings(teacher_id)
    if row and row["encrypted_api_key"]:
        api_key = decrypt_api_key(row["encrypted_api_key"])
        if api_key:
            return AIConfig(
                api_key=api_key,
                base_url=row["base_url"].rstrip("/"),
                model=row["model"],
                provider=row["provider"],
            )
    return None


def require_teacher_ai_config(teacher_id: int) -> AIConfig:
    config = get_teacher_ai_config(teacher_id)
    if not config:
        raise HTTPException(status_code=400, detail="请先到设置页配置 AI 模型和 API Key")
    return config


def require_teacher_vision_config(teacher_id: int) -> AIConfig:
    config = get_teacher_vision_config(teacher_id)
    if not config:
        raise HTTPException(status_code=400, detail="请先在设置页配置“图片识别模型”。普通文本模型不能识别课堂图片。")
    return config


def _model_service_error_text(response: httpx.Response) -> str:
    try:
        payload = response.json()
        error = payload.get("error", payload)
        message = error.get("message", "") if isinstance(error, dict) else ""
        code = error.get("code", "") if isinstance(error, dict) else ""
        if code == "invalid_api_key" or "Incorrect API key" in message:
            return "API Key 不正确。请确认你填的是当前模型平台生成的 API Key，并检查复制时没有多余空格或换行。"
        if message:
            return f"服务商提示：{message[:220]}"
    except (json.JSONDecodeError, ValueError, AttributeError):
        pass
    compact = " ".join(response.text.split())
    return f"服务商返回：{compact[:220]}" if compact else ""


async def test_ai_connection(config: AIConfig) -> str:
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": "你只返回一句简短中文。"},
            {"role": "user", "content": "请回复：连接成功"},
        ],
        "temperature": 0,
        "max_tokens": 20,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{config.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {config.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as exc:
        detail = _model_service_error_text(exc.response)
        raise HTTPException(status_code=400, detail=f"AI 连接失败：请检查 API Key、模型名或额度。{detail}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=400, detail=f"AI 连接失败：请检查 Base URL 是否正确。{exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="AI 连接失败：接口返回格式不符合 OpenAI-compatible 格式") from exc


async def test_vision_connection(config: AIConfig) -> str:
    sample_png = (
        "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAi0lEQVR42u3bMQ4AEAwFUPc/qLgBW92AwdR6EmMl3vRT1caMOO1Y"
        "/biz1zcAAAAAAADgY4DqF7zVAwAAAAAAAD8DSIIALgdkXwAAAAAA4KEfkH09J0EAAAAAAACgMIAkCAAAAAAAAOgHSIIAAAAAAMB8gPkAz"
        "+MAAAAAAACA/wKSIAAAAAAAAFAeYAPWonEDSdErYQAAAABJRU5ErkJggg=="
    )
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": "你只返回一句简短中文。"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "这是一张内置测试图片。请回复：图片识别连接成功"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{sample_png}"},
                    },
                ],
            },
        ],
        "temperature": 0,
        "max_tokens": 30,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{config.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {config.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as exc:
        detail = _model_service_error_text(exc.response)
        raise HTTPException(
            status_code=400,
            detail=f"图片识别模型连接失败：请检查 API Key、模型名、额度，或确认该模型支持图片输入。{detail}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=400, detail=f"图片识别模型连接失败：请检查 Base URL 是否正确。{exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="图片识别模型连接失败：接口返回格式不符合 OpenAI-compatible 格式") from exc
