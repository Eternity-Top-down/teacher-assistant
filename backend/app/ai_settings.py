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
    source: str = "personal"
    config_id: int | None = None
    display_name: str = ""


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


def platform_model_summary() -> dict:
    return {
        "id": "platform",
        "type": "platform",
        "name": settings.ai_display_name,
        "provider": settings.ai_provider,
        "base_url": settings.ai_base_url,
        "model": settings.ai_model,
        "has_api_key": bool(settings.ai_api_key),
        "is_active": False,
    }


def ai_config_summary(row: dict) -> dict:
    return {
        "id": row["id"],
        "type": "personal",
        "name": row["name"] or f"{row['provider']} {row['model']}",
        "provider": row["provider"],
        "base_url": row["base_url"],
        "model": row["model"],
        "has_api_key": bool(row["encrypted_api_key"]),
        "is_active": bool(row["is_active"]),
        "updated_at": row["updated_at"],
    }


def ensure_teacher_ai_usage(teacher_id: int, db=None) -> dict:
    close_db = db is None
    if close_db:
        context = get_db()
        db = context.__enter__()
    try:
        row = db.execute(
            "SELECT * FROM teacher_ai_usage WHERE teacher_id = ?",
            (teacher_id,),
        ).fetchone()
        if not row:
            timestamp = now_iso()
            db.execute(
                """
                INSERT INTO teacher_ai_usage (
                    teacher_id, selected_model_type, selected_config_id,
                    trial_quota_total, trial_quota_used, created_at, updated_at
                )
                VALUES (?, 'platform', NULL, ?, 0, ?, ?)
                """,
                (teacher_id, settings.ai_trial_quota, timestamp, timestamp),
            )
            row = db.execute(
                "SELECT * FROM teacher_ai_usage WHERE teacher_id = ?",
                (teacher_id,),
            ).fetchone()
        return dict(row)
    finally:
        if close_db:
            context.__exit__(None, None, None)


def get_teacher_ai_configs(teacher_id: int) -> list[dict]:
    with get_db() as db:
        ensure_teacher_ai_usage(teacher_id, db)
        rows = db.execute(
            """
            SELECT *
            FROM teacher_ai_configs
            WHERE teacher_id = ?
            ORDER BY is_active DESC, id DESC
            """,
            (teacher_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_teacher_ai_config_row(teacher_id: int, config_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM teacher_ai_configs WHERE id = ? AND teacher_id = ?",
            (config_id, teacher_id),
        ).fetchone()
    return dict(row) if row else None


def ai_settings_payload(teacher_id: int) -> dict:
    with get_db() as db:
        usage = ensure_teacher_ai_usage(teacher_id, db)
        rows = db.execute(
            """
            SELECT *
            FROM teacher_ai_configs
            WHERE teacher_id = ?
            ORDER BY is_active DESC, id DESC
            """,
            (teacher_id,),
        ).fetchall()
    configs = [ai_config_summary(dict(row)) for row in rows]
    selected_model_type = usage["selected_model_type"]
    selected_config_id = usage["selected_config_id"]
    if selected_model_type == "personal" and not any(config["id"] == selected_config_id for config in configs):
        selected_model_type = "platform"
        selected_config_id = None
    platform = platform_model_summary()
    platform["is_active"] = selected_model_type == "platform"
    quota_remaining = max(0, usage["trial_quota_total"] - usage["trial_quota_used"])
    active_personal = next((config for config in configs if config["id"] == selected_config_id), None)
    active = active_personal if selected_model_type == "personal" else platform
    return {
        "platform": platform,
        "configs": configs,
        "models": [platform, *configs],
        "selected_model_type": selected_model_type,
        "selected_config_id": selected_config_id,
        "active_model": active,
        "trial_quota_total": usage["trial_quota_total"],
        "trial_quota_used": usage["trial_quota_used"],
        "trial_quota_remaining": quota_remaining,
        "settings": {
            "provider": active["provider"],
            "base_url": active["base_url"],
            "model": active["model"],
            "has_api_key": active["has_api_key"],
            "feedback_format_mode": "structured",
            "updated_at": active.get("updated_at", usage["updated_at"]),
        },
    }


def save_teacher_ai_config(
    teacher_id: int,
    name: str,
    provider: str,
    base_url: str,
    model: str,
    api_key: str = "",
    config_id: int | None = None,
    clear_api_key: bool = False,
    make_active: bool = True,
) -> dict:
    timestamp = now_iso()
    with get_db() as db:
        ensure_teacher_ai_usage(teacher_id, db)
        existing = None
        if config_id:
            existing = db.execute(
                "SELECT * FROM teacher_ai_configs WHERE id = ? AND teacher_id = ?",
                (config_id, teacher_id),
            ).fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="模型配置不存在")
        encrypted_api_key = existing["encrypted_api_key"] if existing else ""
        if clear_api_key:
            encrypted_api_key = ""
        elif api_key.strip():
            encrypted_api_key = encrypt_api_key(api_key.strip())
        display_name = name.strip() or f"{provider} {model}".strip()
        if existing:
            db.execute(
                """
                UPDATE teacher_ai_configs
                SET name = ?, provider = ?, base_url = ?, model = ?, encrypted_api_key = ?, updated_at = ?
                WHERE id = ? AND teacher_id = ?
                """,
                (
                    display_name,
                    provider,
                    base_url.rstrip("/"),
                    model,
                    encrypted_api_key,
                    timestamp,
                    config_id,
                    teacher_id,
                ),
            )
            saved_id = config_id
        else:
            cursor = db.execute(
                """
                INSERT INTO teacher_ai_configs (
                    teacher_id, name, provider, base_url, model, encrypted_api_key, is_active, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    teacher_id,
                    display_name,
                    provider,
                    base_url.rstrip("/"),
                    model,
                    encrypted_api_key,
                    timestamp,
                    timestamp,
                ),
            )
            saved_id = cursor.lastrowid
        if make_active:
            set_active_ai_model(teacher_id, "personal", saved_id, db)
        row = db.execute(
            "SELECT * FROM teacher_ai_configs WHERE id = ? AND teacher_id = ?",
            (saved_id, teacher_id),
        ).fetchone()
    return dict(row)


def set_active_ai_model(teacher_id: int, model_type: str, config_id: int | None = None, db=None) -> None:
    close_db = db is None
    if close_db:
        context = get_db()
        db = context.__enter__()
    try:
        ensure_teacher_ai_usage(teacher_id, db)
        timestamp = now_iso()
        if model_type == "platform":
            db.execute(
                "UPDATE teacher_ai_configs SET is_active = 0 WHERE teacher_id = ?",
                (teacher_id,),
            )
            db.execute(
                """
                UPDATE teacher_ai_usage
                SET selected_model_type = 'platform', selected_config_id = NULL, updated_at = ?
                WHERE teacher_id = ?
                """,
                (timestamp, teacher_id),
            )
        elif model_type == "personal" and config_id:
            row = db.execute(
                "SELECT id FROM teacher_ai_configs WHERE id = ? AND teacher_id = ?",
                (config_id, teacher_id),
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="模型配置不存在")
            db.execute(
                "UPDATE teacher_ai_configs SET is_active = 0 WHERE teacher_id = ?",
                (teacher_id,),
            )
            db.execute(
                "UPDATE teacher_ai_configs SET is_active = 1, updated_at = ? WHERE id = ? AND teacher_id = ?",
                (timestamp, config_id, teacher_id),
            )
            db.execute(
                """
                UPDATE teacher_ai_usage
                SET selected_model_type = 'personal', selected_config_id = ?, updated_at = ?
                WHERE teacher_id = ?
                """,
                (config_id, timestamp, teacher_id),
            )
        else:
            raise HTTPException(status_code=400, detail="请选择有效的模型")
    finally:
        if close_db:
            context.__exit__(None, None, None)


def delete_teacher_ai_config(teacher_id: int, config_id: int) -> None:
    with get_db() as db:
        usage = ensure_teacher_ai_usage(teacher_id, db)
        row = db.execute(
            "SELECT is_active FROM teacher_ai_configs WHERE id = ? AND teacher_id = ?",
            (config_id, teacher_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        db.execute(
            "DELETE FROM teacher_ai_configs WHERE id = ? AND teacher_id = ?",
            (config_id, teacher_id),
        )
        if row["is_active"] or usage["selected_config_id"] == config_id:
            db.execute(
                """
                UPDATE teacher_ai_usage
                SET selected_model_type = 'platform', selected_config_id = NULL, updated_at = ?
                WHERE teacher_id = ?
                """,
                (now_iso(), teacher_id),
            )


def get_teacher_ai_config(
    teacher_id: int,
    consume_trial: bool = False,
    model_type: str = "",
    config_id: int | None = None,
) -> AIConfig | None:
    with get_db() as db:
        usage = ensure_teacher_ai_usage(teacher_id, db)
        selected_model_type = model_type or usage["selected_model_type"]
        selected_config_id = config_id if model_type == "personal" else usage["selected_config_id"]
        if selected_model_type == "personal" and selected_config_id:
            row = db.execute(
                "SELECT * FROM teacher_ai_configs WHERE id = ? AND teacher_id = ?",
                (selected_config_id, teacher_id),
            ).fetchone()
            if row and row["encrypted_api_key"]:
                api_key = decrypt_api_key(row["encrypted_api_key"])
                if api_key:
                    return AIConfig(
                        api_key=api_key,
                        base_url=row["base_url"].rstrip("/"),
                        model=row["model"],
                        provider=row["provider"],
                        source="personal",
                        config_id=row["id"],
                        display_name=row["name"],
                    )
            if model_type == "personal":
                raise HTTPException(status_code=400, detail="本次选择的个人模型不可用，请检查 API Key 或重新选择模型。")

        if selected_model_type == "platform" and settings.ai_api_key:
            if consume_trial:
                remaining = usage["trial_quota_total"] - usage["trial_quota_used"]
                if remaining <= 0:
                    raise HTTPException(status_code=400, detail="平台默认模型免费试用次数已用完，请到设置页配置自己的 API。")
                db.execute(
                    """
                    UPDATE teacher_ai_usage
                    SET trial_quota_used = trial_quota_used + 1, updated_at = ?
                    WHERE teacher_id = ?
                    """,
                    (now_iso(), teacher_id),
                )
            return AIConfig(
                api_key=settings.ai_api_key,
                base_url=settings.ai_base_url,
                model=settings.ai_model,
                provider=settings.ai_provider,
                source="platform",
                display_name=settings.ai_display_name,
            )

    return None


def require_teacher_ai_config(
    teacher_id: int,
    consume_trial: bool = True,
    model_type: str = "",
    config_id: int | None = None,
) -> AIConfig:
    config = get_teacher_ai_config(
        teacher_id,
        consume_trial=consume_trial,
        model_type=model_type,
        config_id=config_id,
    )
    if not config:
        raise HTTPException(status_code=400, detail="请先到设置页选择平台默认模型，或配置自己的 AI 模型和 API Key")
    return config


def get_teacher_ai_settings(teacher_id: int) -> dict | None:
    payload = ai_settings_payload(teacher_id)
    return payload["settings"]


def ai_settings_summary(row: dict | None) -> dict:
    if not row:
        return {
            "provider": settings.ai_provider,
            "base_url": settings.ai_base_url,
            "model": settings.ai_model,
            "has_api_key": bool(settings.ai_api_key),
            "feedback_format_mode": "structured",
            "updated_at": "",
        }
    if "encrypted_api_key" in row:
        return {
            "provider": row["provider"],
            "base_url": row["base_url"],
            "model": row["model"],
            "has_api_key": bool(row["encrypted_api_key"]),
            "feedback_format_mode": "structured",
            "updated_at": row["updated_at"],
        }
    return row


def save_teacher_ai_settings(
    teacher_id: int,
    provider: str,
    base_url: str,
    model: str,
    api_key: str = "",
    clear_api_key: bool = False,
    feedback_format_mode: str = "structured",
) -> dict:
    return save_teacher_ai_config(
        teacher_id=teacher_id,
        name=f"{provider} {model}".strip(),
        provider=provider,
        base_url=base_url,
        model=model,
        api_key=api_key,
        clear_api_key=clear_api_key,
        make_active=True,
    )


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
