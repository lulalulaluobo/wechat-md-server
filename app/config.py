from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.auth import (
    build_initial_admin_credentials,
    decrypt_secret,
    emit_generated_admin_password,
    encrypt_secret,
    generate_session_secret,
    hash_password,
    session_cookie_secure_enabled,
)


DEFAULT_FNS_TARGET_DIR = "00_Inbox/微信公众号"
DEFAULT_IMAGE_MODE = "wechat_hotlink"
IMAGE_MODE_VALUES = {"wechat_hotlink", "s3_hotlink"}
DEFAULT_TELEGRAM_NOTIFY_ON_COMPLETE = True
DEFAULT_AI_MODEL = "gpt-5.4-mini"
DEFAULT_AI_PROMPT_TEMPLATE = """你是一个 Obsidian 笔记解释器。请基于提供的标题、作者、原文链接和清洗后的 Markdown 正文，提炼结构化笔记变量。

请只返回 JSON 对象，不要输出 Markdown，不要额外解释。JSON 字段固定为：
- summary: 一句话总结，说明这篇文章解决什么问题或传达什么核心观点
- tags: 3 到 5 个中文或英文 tag，使用数组返回，每个 tag 不要包含空格
- my_understand: 2 到 4 句话，说明阅读后的理解、适用场景或个人启发
- body_polish: 可选的补充块内容。如果没有额外补充，返回空字符串

上下文：
- 标题：{{title}}
- 作者：{{author}}
- 原文链接：{{url}}
- 日期：{{date}}

正文：
{{content}}
"""
DEFAULT_AI_FRONTMATTER_TEMPLATE = """---
title: {{title}}
author: {{author}}
source: {{url}}
created_day: {{date}}
summary: {{summary}}
tags: {{tags}}
---
"""
DEFAULT_AI_BODY_TEMPLATE = """> [!summary] 一句话总结
> {{summary}}

---

> [!tip] 我的理解
> {{my_understand}}

{{body_polish}}
"""
DEFAULT_AI_CONTEXT_TEMPLATE = "{{content}}"
DEFAULT_AI_CONTENT_POLISH_PROMPT = """请把正文整理为更适合 Obsidian 阅读的 Markdown。

要求：
1. 不改变原文事实、观点和结论
2. 保留所有图片、链接、代码块、表格和列表
3. 代码块必须使用三个反引号 fenced code block
4. 表格必须输出为标准 Markdown 表格
5. 适度优化标题层级、空行、列表结构和段落组织，提升阅读体验
6. 不要输出解释，只返回润色后的正文 Markdown
"""
AI_TEMPLATE_SOURCE_VALUES = {"manual", "clipper_import"}


@dataclass(frozen=True)
class Settings:
    default_output_dir: Path
    runtime_config_path: Path
    username: str
    password_hash: str
    session_secret: str
    session_cookie_secure: bool
    default_timeout: int = 30
    fns_base_url: str | None = None
    fns_token: str | None = None
    fns_vault: str | None = None
    fns_target_dir: str = DEFAULT_FNS_TARGET_DIR
    cleanup_temp_on_success: bool = True
    image_mode: str = DEFAULT_IMAGE_MODE
    image_storage_provider: str | None = None
    image_storage_endpoint: str | None = None
    image_storage_region: str | None = None
    image_storage_bucket: str | None = None
    image_storage_access_key_id: str | None = None
    image_storage_secret_access_key: str | None = None
    image_storage_path_template: str | None = None
    image_storage_public_base_url: str | None = None
    telegram_enabled: bool = False
    telegram_bot_token: str | None = None
    telegram_webhook_public_base_url: str | None = None
    telegram_webhook_secret: str | None = None
    telegram_allowed_chat_ids: tuple[str, ...] = ()
    telegram_notify_on_complete: bool = DEFAULT_TELEGRAM_NOTIFY_ON_COMPLETE
    telegram_webhook_status: str = "inactive"
    telegram_webhook_message: str = ""
    ai_enabled: bool = False
    ai_base_url: str | None = None
    ai_api_key: str | None = None
    ai_model: str = DEFAULT_AI_MODEL
    ai_prompt_template: str = DEFAULT_AI_PROMPT_TEMPLATE
    ai_frontmatter_template: str = DEFAULT_AI_FRONTMATTER_TEMPLATE
    ai_body_template: str = DEFAULT_AI_BODY_TEMPLATE
    ai_context_template: str = DEFAULT_AI_CONTEXT_TEMPLATE
    ai_allow_body_polish: bool = False
    ai_enable_content_polish: bool = False
    ai_content_polish_prompt: str = DEFAULT_AI_CONTENT_POLISH_PROMPT
    ai_template_source: str = "manual"

    @property
    def fns_enabled(self) -> bool:
        return bool(self.fns_base_url and self.fns_token and self.fns_vault)

    @property
    def image_storage_enabled(self) -> bool:
        return self.image_mode == "s3_hotlink" and all(
            [
                self.image_storage_provider == "s3",
                self.image_storage_endpoint,
                self.image_storage_region,
                self.image_storage_bucket,
                self.image_storage_access_key_id,
                self.image_storage_secret_access_key,
                self.image_storage_path_template,
                self.image_storage_public_base_url,
            ]
        )

    @property
    def telegram_enabled_and_configured(self) -> bool:
        return bool(
            self.telegram_enabled
            and self.telegram_bot_token
            and self.telegram_webhook_public_base_url
            and self.telegram_webhook_secret
            and self.telegram_allowed_chat_ids
        )

    @property
    def telegram_webhook_url(self) -> str | None:
        if not self.telegram_webhook_public_base_url:
            return None
        return f"{self.telegram_webhook_public_base_url.rstrip('/')}/api/integrations/telegram/webhook"

    @property
    def ai_configured(self) -> bool:
        return bool(
            self.ai_base_url
            and self.ai_api_key
            and self.ai_model
            and self.ai_prompt_template.strip()
            and self.ai_frontmatter_template.strip()
            and self.ai_body_template.strip()
            and self.ai_context_template.strip()
        )


FNS_FIELDS = {
    "fns_base_url",
    "fns_token",
    "fns_vault",
    "fns_target_dir",
    "cleanup_temp_on_success",
}
IMAGE_STORAGE_TEXT_FIELDS = {
    "image_storage_provider",
    "image_storage_endpoint",
    "image_storage_region",
    "image_storage_bucket",
    "image_storage_access_key_id",
    "image_storage_secret_access_key",
    "image_storage_path_template",
    "image_storage_public_base_url",
}
SECRET_FIELDS = {"fns_token", "image_storage_secret_access_key"}
TELEGRAM_BOOL_FIELDS = {"telegram_enabled", "telegram_notify_on_complete"}
TELEGRAM_TEXT_FIELDS = {
    "telegram_webhook_public_base_url",
    "telegram_webhook_status",
    "telegram_webhook_message",
}
TELEGRAM_SECRET_FIELDS = {"telegram_bot_token", "telegram_webhook_secret"}
SECRET_FIELDS = SECRET_FIELDS | TELEGRAM_SECRET_FIELDS
TELEGRAM_TEXT_FIELD_MAP = {
    "telegram_webhook_public_base_url": "webhook_public_base_url",
    "telegram_webhook_status": "webhook_status",
    "telegram_webhook_message": "webhook_message",
}
AI_BOOL_FIELDS = {"ai_enabled", "ai_allow_body_polish", "ai_enable_content_polish"}
AI_TEXT_FIELDS = {
    "ai_base_url",
    "ai_model",
    "ai_prompt_template",
    "ai_frontmatter_template",
    "ai_body_template",
    "ai_context_template",
    "ai_content_polish_prompt",
    "ai_template_source",
}
AI_SECRET_FIELDS = {"ai_api_key"}
SECRET_FIELDS = SECRET_FIELDS | AI_SECRET_FIELDS


def get_runtime_config_path() -> Path:
    configured = os.environ.get("WECHAT_MD_RUNTIME_CONFIG_PATH")
    if configured:
        return Path(configured).resolve()
    return (Path(__file__).resolve().parents[1] / "data" / "runtime-config.json").resolve()


def load_runtime_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or get_runtime_config_path()
    if config_path.exists():
        try:
            raw_data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise RuntimeError(f"运行时配置文件不是有效 JSON: {config_path}") from error
        if not isinstance(raw_data, dict):
            raise RuntimeError(f"运行时配置文件结构无效: {config_path}")
    else:
        raw_data = {}

    normalized = _normalize_runtime_config(raw_data)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    _write_runtime_config(config_path, normalized)
    return normalized


def save_runtime_config(payload: dict[str, Any], clear_fields: list[str] | None = None) -> dict[str, Any]:
    config_path = get_runtime_config_path()
    current = load_runtime_config(config_path)
    updated = _normalize_runtime_config(current)
    user_settings = dict(updated["user_settings"])
    image_storage = dict(user_settings["image_storage"])
    telegram_settings = dict(user_settings["telegram"])
    clear_set = {field for field in (clear_fields or []) if field in SECRET_FIELDS}

    for field in clear_set:
        if field == "fns_token":
            user_settings["fns_token"] = ""
        elif field == "image_storage_secret_access_key":
            image_storage["secret_access_key"] = ""
        elif field == "telegram_bot_token":
            telegram_settings["bot_token"] = ""
        elif field == "telegram_webhook_secret":
            telegram_settings["webhook_secret"] = ""
        elif field == "ai_api_key":
            user_settings["ai_api_key"] = ""

    for field in FNS_FIELDS:
        if field not in payload:
            continue
        raw_value = payload.get(field)
        if field == "cleanup_temp_on_success":
            user_settings[field] = _as_bool(raw_value, default=True)
            continue
        if raw_value is None:
            continue
        user_settings[field] = str(raw_value).strip()

    if "image_mode" in payload and payload.get("image_mode") is not None:
        user_settings["image_mode"] = str(payload.get("image_mode") or "").strip() or DEFAULT_IMAGE_MODE

    for field in IMAGE_STORAGE_TEXT_FIELDS:
        if field not in payload:
            continue
        raw_value = payload.get(field)
        if raw_value is None:
            continue
        image_storage[field.removeprefix("image_storage_")] = str(raw_value).strip()

    for field in TELEGRAM_BOOL_FIELDS:
        if field not in payload:
            continue
        telegram_settings[field.removeprefix("telegram_")] = _as_bool(payload.get(field), default=field == "telegram_notify_on_complete")

    for field in TELEGRAM_TEXT_FIELDS:
        if field not in payload:
            continue
        raw_value = payload.get(field)
        if raw_value is None:
            continue
        telegram_settings[TELEGRAM_TEXT_FIELD_MAP[field]] = str(raw_value).strip()

    for field in TELEGRAM_SECRET_FIELDS:
        if field not in payload:
            continue
        raw_value = payload.get(field)
        if raw_value is None:
            continue
        telegram_settings[field.removeprefix("telegram_")] = str(raw_value).strip()

    if "telegram_allowed_chat_ids" in payload:
        telegram_settings["allowed_chat_ids"] = _normalize_chat_ids(payload.get("telegram_allowed_chat_ids"))

    for field in AI_BOOL_FIELDS:
        if field not in payload:
            continue
        user_settings[field] = _as_bool(payload.get(field), default=field == "ai_allow_body_polish")

    for field in AI_TEXT_FIELDS | AI_SECRET_FIELDS:
        if field not in payload:
            continue
        raw_value = payload.get(field)
        if raw_value is None:
            continue
        user_settings[field] = str(raw_value)

    user_settings["image_storage"] = image_storage
    user_settings["telegram"] = telegram_settings
    updated["user_settings"] = _normalize_user_settings(user_settings)
    _validate_runtime_config(updated)
    _write_runtime_config(config_path, updated)
    return updated


def update_password(current_password: str, new_password: str) -> dict[str, Any]:
    from app.auth import verify_password

    config_path = get_runtime_config_path()
    current = load_runtime_config(config_path)
    auth_user = current["auth"]["user"]
    if not verify_password(current_password, str(auth_user.get("password_hash") or "")):
        raise ValueError("当前密码不正确")

    normalized_password = (new_password or "").strip()
    if not normalized_password:
        raise ValueError("新密码不能为空")

    auth_user["password_hash"] = hash_password(normalized_password)
    current["auth"]["user"] = auth_user
    _write_runtime_config(config_path, current)
    return current


def reset_admin_credentials(new_password: str, username: str | None = None) -> dict[str, Any]:
    normalized_password = (new_password or "").strip()
    if not normalized_password:
        raise ValueError("新密码不能为空")

    config_path = get_runtime_config_path()
    current = load_runtime_config(config_path)
    auth_user = current["auth"]["user"]
    if username is not None:
        normalized_username = username.strip()
        if not normalized_username:
            raise ValueError("用户名不能为空")
        auth_user["username"] = normalized_username
    auth_user["password_hash"] = hash_password(normalized_password)
    current["auth"]["user"] = auth_user
    current["auth"]["session_secret"] = generate_session_secret()
    _write_runtime_config(config_path, current)
    return current


def update_telegram_webhook_state(status: str, message: str, webhook_url: str | None = None) -> dict[str, Any]:
    config_path = get_runtime_config_path()
    current = load_runtime_config(config_path)
    telegram = dict(current["user_settings"]["telegram"])
    telegram["webhook_status"] = (status or "inactive").strip() or "inactive"
    telegram["webhook_message"] = (message or "").strip()
    if webhook_url is not None:
        telegram["webhook_public_base_url"] = webhook_url.rsplit("/api/integrations/telegram/webhook", 1)[0] if webhook_url else ""
    current["user_settings"]["telegram"] = telegram
    _write_runtime_config(config_path, current)
    return current


def build_admin_settings_payload() -> dict[str, Any]:
    settings = get_settings()
    runtime_values = load_runtime_config(settings.runtime_config_path)
    user_settings = runtime_values["user_settings"]
    image_storage = user_settings["image_storage"]
    telegram = user_settings["telegram"]
    runtime_overrides = [
        "auth.user.username",
        "auth.user.password_hash",
        "auth.session_secret_encrypted",
        *[
            f"user_settings.{key}"
            for key in sorted(user_settings.keys())
            if key != "image_storage"
        ],
        *[f"user_settings.image_storage.{key}" for key in sorted(image_storage.keys())],
        *[f"user_settings.telegram.{key}" for key in sorted(telegram.keys())],
    ]
    return {
        "runtime_config_path": str(settings.runtime_config_path),
        "auth_enabled": True,
        "session_cookie_secure": settings.session_cookie_secure,
        "default_output_target": "fns" if settings.fns_enabled else "local",
        "current_user": {"username": settings.username},
        "fns_base_url": settings.fns_base_url or "",
        "fns_vault": settings.fns_vault or "",
        "fns_target_dir": settings.fns_target_dir or DEFAULT_FNS_TARGET_DIR,
        "fns_token_configured": bool(settings.fns_token),
        "fns_token_masked": _mask_secret(settings.fns_token),
        "cleanup_temp_on_success": settings.cleanup_temp_on_success,
        "image_mode": settings.image_mode,
        "image_storage_enabled": settings.image_storage_enabled,
        "image_storage_provider": settings.image_storage_provider or "s3",
        "image_storage_endpoint": settings.image_storage_endpoint or "",
        "image_storage_region": settings.image_storage_region or "",
        "image_storage_bucket": settings.image_storage_bucket or "",
        "image_storage_access_key_id": settings.image_storage_access_key_id or "",
        "image_storage_path_template": settings.image_storage_path_template or "",
        "image_storage_public_base_url": settings.image_storage_public_base_url or "",
        "image_storage_secret_access_key_configured": bool(settings.image_storage_secret_access_key),
        "image_storage_secret_access_key_masked": _mask_secret(settings.image_storage_secret_access_key),
        "telegram_enabled": settings.telegram_enabled,
        "telegram_bot_token_configured": bool(settings.telegram_bot_token),
        "telegram_bot_token_masked": _mask_secret(settings.telegram_bot_token),
        "telegram_webhook_public_base_url": settings.telegram_webhook_public_base_url or "",
        "telegram_webhook_url": settings.telegram_webhook_url or "",
        "telegram_webhook_secret_configured": bool(settings.telegram_webhook_secret),
        "telegram_webhook_secret_masked": _mask_secret(settings.telegram_webhook_secret),
        "telegram_allowed_chat_ids_text": "\n".join(settings.telegram_allowed_chat_ids),
        "telegram_notify_on_complete": settings.telegram_notify_on_complete,
        "telegram_webhook_status": settings.telegram_webhook_status,
        "telegram_webhook_message": settings.telegram_webhook_message,
        "ai_enabled": settings.ai_enabled,
        "ai_configured": settings.ai_configured,
        "ai_base_url": settings.ai_base_url or "",
        "ai_api_key_configured": bool(settings.ai_api_key),
        "ai_api_key_masked": _mask_secret(settings.ai_api_key),
        "ai_model": settings.ai_model,
        "ai_prompt_template": settings.ai_prompt_template,
        "ai_frontmatter_template": settings.ai_frontmatter_template,
        "ai_body_template": settings.ai_body_template,
        "ai_context_template": settings.ai_context_template,
        "ai_allow_body_polish": settings.ai_allow_body_polish,
        "ai_enable_content_polish": settings.ai_enable_content_polish,
        "ai_content_polish_prompt": settings.ai_content_polish_prompt,
        "ai_template_source": settings.ai_template_source,
        "runtime_overrides": runtime_overrides,
    }


def get_settings() -> Settings:
    runtime_config_path = get_runtime_config_path()
    runtime_values = load_runtime_config(runtime_config_path)
    auth_block = runtime_values["auth"]
    user_block = auth_block["user"]
    runtime_user_settings = runtime_values["user_settings"]
    image_storage = runtime_user_settings["image_storage"]
    telegram = runtime_user_settings["telegram"]

    output_dir = Path(os.environ.get("WECHAT_MD_DEFAULT_OUTPUT_DIR", r"D:\obsidian\00_Inbox")).resolve()
    fns_base_url = str(
        runtime_user_settings.get("fns_base_url") or os.environ.get("WECHAT_MD_FNS_BASE_URL") or ""
    ).strip() or None
    fns_token = str(
        runtime_user_settings.get("fns_token") or os.environ.get("WECHAT_MD_FNS_TOKEN") or ""
    ).strip() or None
    fns_vault = str(
        runtime_user_settings.get("fns_vault") or os.environ.get("WECHAT_MD_FNS_VAULT") or ""
    ).strip() or None
    fns_target_dir = (
        str(
            runtime_user_settings.get("fns_target_dir")
            or os.environ.get("WECHAT_MD_FNS_TARGET_DIR")
            or DEFAULT_FNS_TARGET_DIR
        ).strip()
        or DEFAULT_FNS_TARGET_DIR
    )
    cleanup_temp_on_success = _as_bool(runtime_user_settings.get("cleanup_temp_on_success"), default=True)
    image_mode = _normalize_image_mode(runtime_user_settings.get("image_mode") or os.environ.get("WECHAT_MD_IMAGE_MODE"))

    provider = str(image_storage.get("provider") or os.environ.get("WECHAT_MD_IMAGE_STORAGE_PROVIDER") or "s3").strip() or "s3"
    endpoint = str(image_storage.get("endpoint") or os.environ.get("WECHAT_MD_IMAGE_STORAGE_ENDPOINT") or "").strip() or None
    region = str(image_storage.get("region") or os.environ.get("WECHAT_MD_IMAGE_STORAGE_REGION") or "").strip() or None
    bucket = str(image_storage.get("bucket") or os.environ.get("WECHAT_MD_IMAGE_STORAGE_BUCKET") or "").strip() or None
    access_key_id = str(
        image_storage.get("access_key_id") or os.environ.get("WECHAT_MD_IMAGE_STORAGE_ACCESS_KEY_ID") or ""
    ).strip() or None
    secret_access_key = str(
        image_storage.get("secret_access_key") or os.environ.get("WECHAT_MD_IMAGE_STORAGE_SECRET_ACCESS_KEY") or ""
    ).strip() or None
    path_template = str(
        image_storage.get("path_template") or os.environ.get("WECHAT_MD_IMAGE_STORAGE_PATH_TEMPLATE") or ""
    ).strip() or None
    public_base_url = str(
        image_storage.get("public_base_url") or os.environ.get("WECHAT_MD_IMAGE_STORAGE_PUBLIC_BASE_URL") or ""
    ).strip() or None
    telegram_enabled = _as_bool(telegram.get("enabled"), default=False)
    telegram_bot_token = str(telegram.get("bot_token") or os.environ.get("WECHAT_MD_TELEGRAM_BOT_TOKEN") or "").strip() or None
    telegram_webhook_public_base_url = str(
        telegram.get("webhook_public_base_url") or os.environ.get("WECHAT_MD_TELEGRAM_WEBHOOK_PUBLIC_BASE_URL") or ""
    ).strip() or None
    telegram_webhook_secret = str(
        telegram.get("webhook_secret") or os.environ.get("WECHAT_MD_TELEGRAM_WEBHOOK_SECRET") or ""
    ).strip() or None
    telegram_allowed_chat_ids = tuple(_normalize_chat_ids(telegram.get("allowed_chat_ids") or os.environ.get("WECHAT_MD_TELEGRAM_ALLOWED_CHAT_IDS")))
    telegram_notify_on_complete = _as_bool(
        telegram.get("notify_on_complete"),
        default=DEFAULT_TELEGRAM_NOTIFY_ON_COMPLETE,
    )
    telegram_webhook_status = str(telegram.get("webhook_status") or "inactive").strip() or "inactive"
    telegram_webhook_message = str(telegram.get("webhook_message") or "").strip()
    ai_enabled = _as_bool(runtime_user_settings.get("ai_enabled"), default=False)
    ai_base_url = str(runtime_user_settings.get("ai_base_url") or os.environ.get("WECHAT_MD_AI_BASE_URL") or "").strip() or None
    ai_api_key = str(runtime_user_settings.get("ai_api_key") or os.environ.get("WECHAT_MD_AI_API_KEY") or "").strip() or None
    ai_model = str(runtime_user_settings.get("ai_model") or os.environ.get("WECHAT_MD_AI_MODEL") or DEFAULT_AI_MODEL).strip() or DEFAULT_AI_MODEL
    ai_prompt_template = str(runtime_user_settings.get("ai_prompt_template") or os.environ.get("WECHAT_MD_AI_PROMPT_TEMPLATE") or DEFAULT_AI_PROMPT_TEMPLATE)
    ai_frontmatter_template = str(runtime_user_settings.get("ai_frontmatter_template") or os.environ.get("WECHAT_MD_AI_FRONTMATTER_TEMPLATE") or DEFAULT_AI_FRONTMATTER_TEMPLATE)
    ai_body_template = str(runtime_user_settings.get("ai_body_template") or os.environ.get("WECHAT_MD_AI_BODY_TEMPLATE") or DEFAULT_AI_BODY_TEMPLATE)
    ai_context_template = str(runtime_user_settings.get("ai_context_template") or os.environ.get("WECHAT_MD_AI_CONTEXT_TEMPLATE") or DEFAULT_AI_CONTEXT_TEMPLATE)
    ai_allow_body_polish = _as_bool(runtime_user_settings.get("ai_allow_body_polish"), default=False)
    ai_enable_content_polish = _as_bool(runtime_user_settings.get("ai_enable_content_polish"), default=False)
    ai_content_polish_prompt = str(
        runtime_user_settings.get("ai_content_polish_prompt")
        or os.environ.get("WECHAT_MD_AI_CONTENT_POLISH_PROMPT")
        or DEFAULT_AI_CONTENT_POLISH_PROMPT
    )
    ai_template_source = _normalize_ai_template_source(runtime_user_settings.get("ai_template_source"))

    return Settings(
        default_output_dir=output_dir,
        runtime_config_path=runtime_config_path,
        username=str(user_block.get("username") or "admin"),
        password_hash=str(user_block.get("password_hash") or hash_password("admin")),
        session_secret=str(auth_block.get("session_secret") or generate_session_secret()),
        session_cookie_secure=session_cookie_secure_enabled(),
        fns_base_url=fns_base_url.rstrip("/") if fns_base_url else None,
        fns_token=fns_token,
        fns_vault=fns_vault,
        fns_target_dir=fns_target_dir.strip("/\\"),
        cleanup_temp_on_success=cleanup_temp_on_success,
        image_mode=image_mode,
        image_storage_provider=provider,
        image_storage_endpoint=endpoint.rstrip("/") if endpoint else None,
        image_storage_region=region,
        image_storage_bucket=bucket,
        image_storage_access_key_id=access_key_id,
        image_storage_secret_access_key=secret_access_key,
        image_storage_path_template=path_template,
        image_storage_public_base_url=public_base_url.rstrip("/") if public_base_url else None,
        telegram_enabled=telegram_enabled,
        telegram_bot_token=telegram_bot_token,
        telegram_webhook_public_base_url=telegram_webhook_public_base_url.rstrip("/") if telegram_webhook_public_base_url else None,
        telegram_webhook_secret=telegram_webhook_secret,
        telegram_allowed_chat_ids=telegram_allowed_chat_ids,
        telegram_notify_on_complete=telegram_notify_on_complete,
        telegram_webhook_status=telegram_webhook_status,
        telegram_webhook_message=telegram_webhook_message,
        ai_enabled=ai_enabled,
        ai_base_url=ai_base_url.rstrip("/") if ai_base_url else None,
        ai_api_key=ai_api_key,
        ai_model=ai_model,
        ai_prompt_template=ai_prompt_template,
        ai_frontmatter_template=ai_frontmatter_template,
        ai_body_template=ai_body_template,
        ai_context_template=ai_context_template,
        ai_allow_body_polish=ai_allow_body_polish,
        ai_enable_content_polish=ai_enable_content_polish,
        ai_content_polish_prompt=ai_content_polish_prompt,
        ai_template_source=ai_template_source,
    )


def _normalize_runtime_config(raw_data: dict[str, Any]) -> dict[str, Any]:
    auth_raw = raw_data.get("auth") if isinstance(raw_data.get("auth"), dict) else {}
    auth_user_raw = auth_raw.get("user") if isinstance(auth_raw.get("user"), dict) else {}
    username = str(auth_user_raw.get("username") or "").strip()
    password_hash = str(auth_user_raw.get("password_hash") or "").strip()
    if not username or not password_hash:
        generated_username, generated_password, was_generated = build_initial_admin_credentials()
        username = generated_username
        password_hash = hash_password(generated_password)
        if was_generated:
            emit_generated_admin_password(username, generated_password)

    session_secret = _load_secret_value(
        encrypted_value=auth_raw.get("session_secret_encrypted"),
        plaintext_value=auth_raw.get("session_secret"),
        field_name="session_secret",
        default_factory=generate_session_secret,
    )

    if "auth" not in raw_data and "user_settings" not in raw_data:
        flat_user_settings = {key: raw_data.get(key) for key in FNS_FIELDS if key in raw_data}
        user_settings = _normalize_user_settings(flat_user_settings)
    else:
        user_settings = _normalize_user_settings(raw_data.get("user_settings"))

    return {
        "auth": {
            "user": {
                "username": username,
                "password_hash": password_hash,
            },
            "session_secret": session_secret,
        },
        "user_settings": user_settings,
    }


def _normalize_user_settings(raw_settings: Any) -> dict[str, Any]:
    source = raw_settings if isinstance(raw_settings, dict) else {}
    image_storage_source = source.get("image_storage") if isinstance(source.get("image_storage"), dict) else {}
    telegram_source = source.get("telegram") if isinstance(source.get("telegram"), dict) else {}
    return {
        "fns_base_url": str(source.get("fns_base_url") or "").strip(),
        "fns_token": _load_secret_value(
            encrypted_value=source.get("fns_token_encrypted"),
            plaintext_value=source.get("fns_token"),
            field_name="fns_token",
        ),
        "fns_vault": str(source.get("fns_vault") or "").strip(),
        "fns_target_dir": str(source.get("fns_target_dir") or DEFAULT_FNS_TARGET_DIR).strip() or DEFAULT_FNS_TARGET_DIR,
        "cleanup_temp_on_success": _as_bool(source.get("cleanup_temp_on_success"), default=True),
        "ai_enabled": _as_bool(source.get("ai_enabled"), default=False),
        "ai_base_url": str(source.get("ai_base_url") or "").strip(),
        "ai_api_key": _load_secret_value(
            encrypted_value=source.get("ai_api_key_encrypted"),
            plaintext_value=source.get("ai_api_key"),
            field_name="ai_api_key",
        ),
        "ai_model": str(source.get("ai_model") or DEFAULT_AI_MODEL).strip() or DEFAULT_AI_MODEL,
        "ai_prompt_template": str(source.get("ai_prompt_template") or DEFAULT_AI_PROMPT_TEMPLATE),
        "ai_frontmatter_template": str(source.get("ai_frontmatter_template") or DEFAULT_AI_FRONTMATTER_TEMPLATE),
        "ai_body_template": str(source.get("ai_body_template") or DEFAULT_AI_BODY_TEMPLATE),
        "ai_context_template": str(source.get("ai_context_template") or DEFAULT_AI_CONTEXT_TEMPLATE),
        "ai_allow_body_polish": _as_bool(source.get("ai_allow_body_polish"), default=False),
        "ai_enable_content_polish": _as_bool(source.get("ai_enable_content_polish"), default=False),
        "ai_content_polish_prompt": str(source.get("ai_content_polish_prompt") or DEFAULT_AI_CONTENT_POLISH_PROMPT),
        "ai_template_source": _normalize_ai_template_source(source.get("ai_template_source")),
        "image_mode": _normalize_image_mode(source.get("image_mode")),
        "image_storage": {
            "provider": str(image_storage_source.get("provider") or "s3").strip() or "s3",
            "endpoint": str(image_storage_source.get("endpoint") or "").strip(),
            "region": str(image_storage_source.get("region") or "").strip(),
            "bucket": str(image_storage_source.get("bucket") or "").strip(),
            "access_key_id": str(image_storage_source.get("access_key_id") or "").strip(),
            "secret_access_key": _load_secret_value(
                encrypted_value=image_storage_source.get("secret_access_key_encrypted"),
                plaintext_value=image_storage_source.get("secret_access_key"),
                field_name="image_storage.secret_access_key",
            ),
            "path_template": str(image_storage_source.get("path_template") or "").strip(),
            "public_base_url": str(image_storage_source.get("public_base_url") or "").strip(),
        },
        "telegram": {
            "enabled": _as_bool(telegram_source.get("enabled"), default=False),
            "bot_token": _load_secret_value(
                encrypted_value=telegram_source.get("bot_token_encrypted"),
                plaintext_value=telegram_source.get("bot_token"),
                field_name="telegram.bot_token",
            ),
            "webhook_public_base_url": str(telegram_source.get("webhook_public_base_url") or "").strip(),
            "webhook_secret": _load_secret_value(
                encrypted_value=telegram_source.get("webhook_secret_encrypted"),
                plaintext_value=telegram_source.get("webhook_secret"),
                field_name="telegram.webhook_secret",
            ),
            "allowed_chat_ids": _normalize_chat_ids(telegram_source.get("allowed_chat_ids")),
            "notify_on_complete": _as_bool(telegram_source.get("notify_on_complete"), default=DEFAULT_TELEGRAM_NOTIFY_ON_COMPLETE),
            "webhook_status": str(telegram_source.get("webhook_status") or "inactive").strip() or "inactive",
            "webhook_message": str(telegram_source.get("webhook_message") or "").strip(),
        },
    }


def _write_runtime_config(config_path: Path, data: dict[str, Any]) -> None:
    serialized = _serialize_runtime_config(data)
    config_path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")


def _serialize_runtime_config(data: dict[str, Any]) -> dict[str, Any]:
    auth_block = data["auth"]
    user_settings = data["user_settings"]
    image_storage = user_settings["image_storage"]
    telegram = user_settings["telegram"]
    return {
        "auth": {
            "user": {
                "username": str(auth_block["user"]["username"]),
                "password_hash": str(auth_block["user"]["password_hash"]),
            },
            "session_secret_encrypted": encrypt_secret(str(auth_block.get("session_secret") or generate_session_secret())),
        },
        "user_settings": {
            "fns_base_url": str(user_settings.get("fns_base_url") or "").strip(),
            "fns_token_encrypted": encrypt_secret(str(user_settings.get("fns_token") or "")),
            "fns_vault": str(user_settings.get("fns_vault") or "").strip(),
            "fns_target_dir": str(user_settings.get("fns_target_dir") or DEFAULT_FNS_TARGET_DIR).strip() or DEFAULT_FNS_TARGET_DIR,
            "cleanup_temp_on_success": _as_bool(user_settings.get("cleanup_temp_on_success"), default=True),
            "ai_enabled": _as_bool(user_settings.get("ai_enabled"), default=False),
            "ai_base_url": str(user_settings.get("ai_base_url") or "").strip(),
            "ai_api_key_encrypted": encrypt_secret(str(user_settings.get("ai_api_key") or "")),
            "ai_model": str(user_settings.get("ai_model") or DEFAULT_AI_MODEL).strip() or DEFAULT_AI_MODEL,
            "ai_prompt_template": str(user_settings.get("ai_prompt_template") or DEFAULT_AI_PROMPT_TEMPLATE),
            "ai_frontmatter_template": str(user_settings.get("ai_frontmatter_template") or DEFAULT_AI_FRONTMATTER_TEMPLATE),
            "ai_body_template": str(user_settings.get("ai_body_template") or DEFAULT_AI_BODY_TEMPLATE),
            "ai_context_template": str(user_settings.get("ai_context_template") or DEFAULT_AI_CONTEXT_TEMPLATE),
            "ai_allow_body_polish": _as_bool(user_settings.get("ai_allow_body_polish"), default=False),
            "ai_enable_content_polish": _as_bool(user_settings.get("ai_enable_content_polish"), default=False),
            "ai_content_polish_prompt": str(user_settings.get("ai_content_polish_prompt") or DEFAULT_AI_CONTENT_POLISH_PROMPT),
            "ai_template_source": _normalize_ai_template_source(user_settings.get("ai_template_source")),
            "image_mode": _normalize_image_mode(user_settings.get("image_mode")),
            "image_storage": {
                "provider": str(image_storage.get("provider") or "s3").strip() or "s3",
                "endpoint": str(image_storage.get("endpoint") or "").strip(),
                "region": str(image_storage.get("region") or "").strip(),
                "bucket": str(image_storage.get("bucket") or "").strip(),
                "access_key_id": str(image_storage.get("access_key_id") or "").strip(),
                "secret_access_key_encrypted": encrypt_secret(str(image_storage.get("secret_access_key") or "")),
                "path_template": str(image_storage.get("path_template") or "").strip(),
                "public_base_url": str(image_storage.get("public_base_url") or "").strip(),
            },
            "telegram": {
                "enabled": _as_bool(telegram.get("enabled"), default=False),
                "bot_token_encrypted": encrypt_secret(str(telegram.get("bot_token") or "")),
                "webhook_public_base_url": str(telegram.get("webhook_public_base_url") or "").strip(),
                "webhook_secret_encrypted": encrypt_secret(str(telegram.get("webhook_secret") or "")),
                "allowed_chat_ids": _normalize_chat_ids(telegram.get("allowed_chat_ids")),
                "notify_on_complete": _as_bool(telegram.get("notify_on_complete"), default=DEFAULT_TELEGRAM_NOTIFY_ON_COMPLETE),
                "webhook_status": str(telegram.get("webhook_status") or "inactive").strip() or "inactive",
                "webhook_message": str(telegram.get("webhook_message") or "").strip(),
            },
        },
    }


def _load_secret_value(
    encrypted_value: Any,
    plaintext_value: Any,
    field_name: str,
    default_factory=None,
) -> str:
    encrypted = str(encrypted_value or "").strip()
    plaintext = str(plaintext_value or "").strip()
    if encrypted:
        try:
            return decrypt_secret(encrypted)
        except RuntimeError as error:
            raise RuntimeError(f"无法读取敏感字段 {field_name}: {error}") from error
    if plaintext:
        return plaintext
    if default_factory is not None:
        return str(default_factory())
    return ""


def _normalize_image_mode(value: Any) -> str:
    normalized = str(value or DEFAULT_IMAGE_MODE).strip()
    return normalized if normalized in IMAGE_MODE_VALUES else DEFAULT_IMAGE_MODE


def _normalize_ai_template_source(value: Any) -> str:
    normalized = str(value or "manual").strip()
    return normalized if normalized in AI_TEMPLATE_SOURCE_VALUES else "manual"


def _mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _validate_runtime_config(data: dict[str, Any]) -> None:
    user_settings = data["user_settings"]
    base_url = str(user_settings.get("fns_base_url") or "").strip()
    if base_url and not base_url.startswith(("http://", "https://")):
        raise ValueError("FNS 基础地址必须以 http:// 或 https:// 开头")

    ai_enabled = _as_bool(user_settings.get("ai_enabled"), default=False)
    ai_base_url = str(user_settings.get("ai_base_url") or "").strip()
    if ai_base_url and not ai_base_url.startswith(("http://", "https://")):
        raise ValueError("AI Base URL 必须以 http:// 或 https:// 开头")
    if ai_enabled:
        missing_ai = []
        if not ai_base_url:
            missing_ai.append("ai_base_url")
        if not str(user_settings.get("ai_api_key") or "").strip():
            missing_ai.append("ai_api_key")
        if not str(user_settings.get("ai_model") or "").strip():
            missing_ai.append("ai_model")
        if not str(user_settings.get("ai_prompt_template") or "").strip():
            missing_ai.append("ai_prompt_template")
        if not str(user_settings.get("ai_frontmatter_template") or "").strip():
            missing_ai.append("ai_frontmatter_template")
        if not str(user_settings.get("ai_body_template") or "").strip():
            missing_ai.append("ai_body_template")
        if not str(user_settings.get("ai_context_template") or "").strip():
            missing_ai.append("ai_context_template")
        if _as_bool(user_settings.get("ai_enable_content_polish"), default=False) and not str(user_settings.get("ai_content_polish_prompt") or "").strip():
            missing_ai.append("ai_content_polish_prompt")
        if missing_ai:
            raise ValueError("AI 润色配置不完整，缺少字段: " + ", ".join(missing_ai))

    telegram = user_settings["telegram"]
    telegram_webhook_public_base_url = str(telegram.get("webhook_public_base_url") or "").strip()
    if telegram_webhook_public_base_url and not telegram_webhook_public_base_url.startswith(("http://", "https://")):
        raise ValueError("Telegram Webhook 对外基础地址必须以 http:// 或 https:// 开头")
    if _as_bool(telegram.get("enabled"), default=False):
        missing_telegram = []
        if not str(telegram.get("bot_token") or "").strip():
            missing_telegram.append("bot_token")
        if not telegram_webhook_public_base_url:
            missing_telegram.append("webhook_public_base_url")
        if not str(telegram.get("webhook_secret") or "").strip():
            missing_telegram.append("webhook_secret")
        if not _normalize_chat_ids(telegram.get("allowed_chat_ids")):
            missing_telegram.append("allowed_chat_ids")
        if missing_telegram:
            raise ValueError("Telegram Bot 配置不完整，缺少字段: " + ", ".join(missing_telegram))

    image_mode = user_settings.get("image_mode")
    if image_mode not in IMAGE_MODE_VALUES:
        raise ValueError("图片模式仅支持 wechat_hotlink 或 s3_hotlink")
    if image_mode != "s3_hotlink":
        return

    image_storage = user_settings["image_storage"]
    required_fields = {
        "endpoint": image_storage.get("endpoint"),
        "region": image_storage.get("region"),
        "bucket": image_storage.get("bucket"),
        "access_key_id": image_storage.get("access_key_id"),
        "secret_access_key": image_storage.get("secret_access_key"),
        "path_template": image_storage.get("path_template"),
        "public_base_url": image_storage.get("public_base_url"),
    }
    missing = [name for name, value in required_fields.items() if not str(value or "").strip()]
    if missing:
        raise ValueError("S3 图床配置不完整，缺少字段: " + ", ".join(missing))
    for field_name in ("endpoint", "public_base_url"):
        if not str(required_fields[field_name]).startswith(("http://", "https://")):
            raise ValueError(f"S3 图床字段 {field_name} 必须以 http:// 或 https:// 开头")


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_chat_ids(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        raw_parts = [str(item).strip() for item in value]
    else:
        text = str(value).replace(",", "\n")
        raw_parts = [part.strip() for part in text.splitlines()]
    deduped: list[str] = []
    seen: set[str] = set()
    for part in raw_parts:
        if not part or part in seen:
            continue
        seen.add(part)
        deduped.append(part)
    return deduped
