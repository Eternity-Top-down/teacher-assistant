import os
import json
import re
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _normalize_platform_model_id(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return normalized or fallback


def _load_platform_ai_models() -> list[dict]:
    def legacy_deepseek_model() -> dict:
        return {
            "id": "deepseek",
            "name": os.getenv("AI_DISPLAY_NAME", "DeepSeek 平台默认"),
            "provider": "deepseek",
            "base_url": os.getenv("AI_BASE_URL", "https://api.deepseek.com").rstrip("/"),
            "model": os.getenv("AI_MODEL", "deepseek-v4-pro"),
            "api_key": os.getenv("AI_API_KEY", ""),
        }

    def item_value(item: dict, key: str, default: str = "") -> str:
        env_name = str(item.get(f"{key}_env") or "").strip()
        if env_name:
            return os.getenv(env_name, str(item.get(key) or default)).strip()
        return str(item.get(key) or default).strip()

    raw_models = os.getenv("AI_PLATFORM_MODELS", "").strip()
    if raw_models:
        try:
            parsed = json.loads(raw_models)
        except json.JSONDecodeError as exc:
            raise RuntimeError("AI_PLATFORM_MODELS 必须是合法的 JSON 数组") from exc
        if not isinstance(parsed, list):
            raise RuntimeError("AI_PLATFORM_MODELS 必须是 JSON 数组")

        models: list[dict] = []
        seen_ids: set[str] = set()
        for index, item in enumerate(parsed, start=1):
            if not isinstance(item, dict):
                continue
            provider = item_value(item, "provider", "platform")
            model = item_value(item, "model")
            base_url = item_value(item, "base_url").rstrip("/")
            if not model or not base_url:
                continue
            model_id = _normalize_platform_model_id(
                str(item.get("id") or provider or model),
                f"platform-{index}",
            )
            if provider.lower() != "deepseek" and "deepseek" not in model_id:
                continue
            if model_id in seen_ids:
                raise RuntimeError(f"AI_PLATFORM_MODELS 中存在重复 id：{model_id}")
            seen_ids.add(model_id)
            api_key = item_value(item, "api_key")
            models.append(
                {
                    "id": model_id,
                    "name": item_value(item, "name", f"{provider} {model}"),
                    "provider": provider,
                    "base_url": base_url,
                    "model": model,
                    "api_key": api_key,
                }
            )
        return models or [legacy_deepseek_model()]

    return [legacy_deepseek_model()]


class Settings:
    app_secret: str = os.getenv("APP_SECRET", "dev-secret-change-me")
    database_path: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "teacher_assistant.db"))

    smtp_host: str = os.getenv("SMTP_HOST", "smtp.qq.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "465"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "")

    ai_api_key: str = os.getenv("AI_API_KEY", "")
    ai_base_url: str = os.getenv("AI_BASE_URL", "https://api.deepseek.com").rstrip("/")
    ai_model: str = os.getenv("AI_MODEL", "deepseek-v4-pro")
    ai_display_name: str = os.getenv("AI_DISPLAY_NAME", "DeepSeek 平台默认")
    ai_provider: str = "deepseek"
    ai_trial_quota: int = int(os.getenv("AI_TRIAL_QUOTA", "30"))
    allow_global_ai_fallback: bool = os.getenv("ALLOW_GLOBAL_AI_FALLBACK", "true").lower() == "true"
    ai_platform_models: list[dict] = _load_platform_ai_models()


settings = Settings()
