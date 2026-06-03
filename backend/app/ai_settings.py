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


def first_available_config_id(db, teacher_id: int) -> int | None:
    row = db.execute(
        """
        SELECT id
        FROM teacher_ai_configs
        WHERE teacher_id = ? AND encrypted_api_key != ''
        ORDER BY is_active DESC, id DESC
        LIMIT 1
        """,
        (teacher_id,),
    ).fetchone()
    return row["id"] if row else None


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
            selected_config_id = first_available_config_id(db, teacher_id)
            db.execute(
                """
                INSERT INTO teacher_ai_usage (
                    teacher_id, selected_model_type, selected_platform_model_id, selected_config_id,
                    trial_quota_total, trial_quota_used, created_at, updated_at
                )
                VALUES (?, ?, '', ?, 0, 0, ?, ?)
                """,
                (
                    teacher_id,
                    "personal" if selected_config_id else "",
                    selected_config_id,
                    timestamp,
                    timestamp,
                ),
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
        selected_config_id = usage["selected_config_id"]
        selected_row = next((row for row in rows if row["id"] == selected_config_id), None)
        if not selected_row or not selected_row["encrypted_api_key"]:
            selected_config_id = first_available_config_id(db, teacher_id)
            db.execute(
                """
                UPDATE teacher_ai_usage
                SET selected_model_type = ?, selected_config_id = ?, selected_platform_model_id = '', updated_at = ?
                WHERE teacher_id = ?
                """,
                ("personal" if selected_config_id else "", selected_config_id, now_iso(), teacher_id),
            )
            usage = db.execute(
                "SELECT * FROM teacher_ai_usage WHERE teacher_id = ?",
                (teacher_id,),
            ).fetchone()
        elif usage["selected_model_type"] != "personal":
            db.execute(
                """
                UPDATE teacher_ai_usage
                SET selected_model_type = 'personal', selected_platform_model_id = '', updated_at = ?
                WHERE teacher_id = ?
                """,
                (now_iso(), teacher_id),
            )
            usage = db.execute(
                "SELECT * FROM teacher_ai_usage WHERE teacher_id = ?",
                (teacher_id,),
            ).fetchone()
    configs = [ai_config_summary(dict(row)) for row in rows]
    selected_config_id = usage["selected_config_id"] if usage else None
    active = next((config for config in configs if config["id"] == selected_config_id), None)
    return {
        "configs": configs,
        "models": configs,
        "selected_config_id": selected_config_id,
        "active_model": active,
        "settings": {
            "provider": active["provider"] if active else "",
            "base_url": active["base_url"] if active else "",
            "model": active["model"] if active else "",
            "has_api_key": active["has_api_key"] if active else False,
            "feedback_format_mode": "structured",
            "updated_at": active.get("updated_at", usage["updated_at"]) if active else usage["updated_at"],
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
        if make_active and encrypted_api_key:
            set_active_ai_model(teacher_id, "personal", config_id=saved_id, db=db)
        elif existing and existing["is_active"] and not encrypted_api_key:
            replacement_id = first_available_config_id(db, teacher_id)
            if replacement_id:
                db.execute(
                    "UPDATE teacher_ai_configs SET is_active = CASE WHEN id = ? THEN 1 ELSE 0 END WHERE teacher_id = ?",
                    (replacement_id, teacher_id),
                )
            else:
                db.execute(
                    "UPDATE teacher_ai_configs SET is_active = 0 WHERE teacher_id = ?",
                    (teacher_id,),
                )
            db.execute(
                """
                UPDATE teacher_ai_usage
                SET selected_model_type = ?, selected_platform_model_id = '', selected_config_id = ?, updated_at = ?
                WHERE teacher_id = ?
                """,
                ("personal" if replacement_id else "", replacement_id, timestamp, teacher_id),
            )
        row = db.execute(
            "SELECT * FROM teacher_ai_configs WHERE id = ? AND teacher_id = ?",
            (saved_id, teacher_id),
        ).fetchone()
    return dict(row)


def set_active_ai_model(
    teacher_id: int,
    model_type: str,
    config_id: int | None = None,
    db=None,
) -> None:
    close_db = db is None
    if close_db:
        context = get_db()
        db = context.__enter__()
    try:
        ensure_teacher_ai_usage(teacher_id, db)
        timestamp = now_iso()
        if model_type == "personal" and config_id:
            row = db.execute(
                "SELECT id, encrypted_api_key FROM teacher_ai_configs WHERE id = ? AND teacher_id = ?",
                (config_id, teacher_id),
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="模型配置不存在")
            if not row["encrypted_api_key"]:
                raise HTTPException(status_code=400, detail="这条模型配置还没有可用的 API Key")
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
                SET selected_model_type = 'personal', selected_platform_model_id = '', selected_config_id = ?, updated_at = ?
                WHERE teacher_id = ?
                """,
                (config_id, timestamp, teacher_id),
            )
        else:
            raise HTTPException(status_code=400, detail="请选择有效的个人模型配置")
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
            replacement_id = first_available_config_id(db, teacher_id)
            if replacement_id:
                db.execute(
                    "UPDATE teacher_ai_configs SET is_active = CASE WHEN id = ? THEN 1 ELSE 0 END WHERE teacher_id = ?",
                    (replacement_id, teacher_id),
                )
            else:
                db.execute(
                    "UPDATE teacher_ai_configs SET is_active = 0 WHERE teacher_id = ?",
                    (teacher_id,),
                )
            db.execute(
                """
                UPDATE teacher_ai_usage
                SET selected_model_type = ?, selected_platform_model_id = '', selected_config_id = ?, updated_at = ?
                WHERE teacher_id = ?
                """,
                ("personal" if replacement_id else "", replacement_id, now_iso(), teacher_id),
            )


def get_teacher_ai_config(
    teacher_id: int,
    model_type: str = "",
    config_id: int | None = None,
) -> AIConfig | None:
    with get_db() as db:
        usage = ensure_teacher_ai_usage(teacher_id, db)
        if model_type == "platform":
            raise HTTPException(status_code=400, detail="请在设置页添加自己的 AI 模型配置和 API Key")
        selected_config_id = config_id or usage["selected_config_id"] or first_available_config_id(db, teacher_id)
        if selected_config_id:
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
            if config_id or model_type == "personal":
                raise HTTPException(status_code=400, detail="本次选择的个人模型不可用，请检查 API Key 或重新选择模型。")

    return None


def require_teacher_ai_config(
    teacher_id: int,
    model_type: str = "",
    config_id: int | None = None,
) -> AIConfig:
    config = get_teacher_ai_config(
        teacher_id,
        model_type=model_type,
        config_id=config_id,
    )
    if not config:
        raise HTTPException(status_code=400, detail="请先到设置页添加自己的 AI 模型配置和 API Key")
    return config


def get_teacher_ai_settings(teacher_id: int) -> dict | None:
    payload = ai_settings_payload(teacher_id)
    return payload["settings"]


def ai_settings_summary(row: dict | None) -> dict:
    if not row:
        return {
            "provider": "",
            "base_url": "",
            "model": "",
            "has_api_key": False,
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
            return "API Key 不正确。请确认你填的是当前模型服务商生成的 API Key，并检查复制时没有多余空格或换行。"
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
