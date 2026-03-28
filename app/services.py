from __future__ import annotations

import os
import re
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import requests

from app.config import get_settings, update_telegram_webhook_state
from app.core.pipeline import run_pipeline, sanitize_filename


URL_PATTERN = re.compile(r"https?://mp\.weixin\.qq\.com/s(?:[/?][^\s)>]+)?", re.IGNORECASE)
TELEGRAM_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


def get_internal_workdir_root() -> Path:
    settings = get_settings()
    root = (settings.runtime_config_path.parent / "workdir").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_internal_workdir(prefix: str) -> Path:
    workdir = get_internal_workdir_root() / f"{prefix}-{uuid.uuid4().hex[:12]}"
    workdir.mkdir(parents=True, exist_ok=False)
    return workdir


def cleanup_internal_workdir(path: Path | None) -> None:
    if path is None:
        return
    shutil.rmtree(path, ignore_errors=True)


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2)

    def create_batch_job(
        self,
        urls: list[str],
        output_dir: Path,
        save_html: bool,
        timeout: int,
        output_target: str,
    ) -> dict[str, Any]:
        job_id = uuid.uuid4().hex
        payload = {
            "job_id": job_id,
            "status": "queued",
            "total": len(urls),
            "completed": 0,
            "success_count": 0,
            "failure_count": 0,
            "output_dir": str(output_dir),
            "save_html": save_html,
            "timeout": timeout,
            "output_target": output_target,
            "results": [],
            "errors": [],
        }
        with self._lock:
            self._jobs[job_id] = payload
        self._executor.submit(self._run_batch_job, job_id, urls, output_dir, save_html, timeout, output_target)
        return payload.copy()

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return None if job is None else _copy_job(job)

    def _run_batch_job(
        self,
        job_id: str,
        urls: list[str],
        output_dir: Path,
        save_html: bool,
        timeout: int,
        output_target: str,
    ) -> None:
        ensure_runtime_environment()
        settings = get_settings()
        self._update(job_id, status="running")
        for url in urls:
            workspace: Path | None = None
            try:
                active_output_dir = output_dir
                if output_target == "fns":
                    workspace = create_internal_workdir(f"batch-{job_id[:8]}")
                    active_output_dir = workspace

                result = run_pipeline(url=url, output_base_dir=active_output_dir, save_html=save_html, timeout=timeout)
                sync = sync_result_to_output(result, output_target=output_target)
                local_artifacts = {"retained": False, "workdir": None}
                if workspace is not None:
                    if settings.cleanup_temp_on_success:
                        cleanup_internal_workdir(workspace)
                    else:
                        local_artifacts = {"retained": True, "workdir": str(workspace)}
                self._append_result(
                    job_id,
                    {
                        "url": url,
                        "status": "success",
                        "result": result,
                        "sync": sync,
                        "output_target": output_target,
                        "local_artifacts": local_artifacts,
                    },
                )
            except Exception as error:  # pragma: no cover - exercised in integration flow
                cleanup_internal_workdir(workspace)
                self._append_result(job_id, {"url": url, "status": "error", "error": str(error)})
        self._finalize(job_id)

    def _append_result(self, job_id: str, entry: dict[str, Any]) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job["results"].append(entry)
            job["completed"] += 1
            if entry["status"] == "success":
                job["success_count"] += 1
            else:
                job["failure_count"] += 1
                job["errors"].append({"url": entry["url"], "error": entry["error"]})

    def _finalize(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job["status"] = "completed"

    def _update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            self._jobs[job_id].update(fields)


def normalize_output_dir(output_dir: str | None) -> Path:
    settings = get_settings()
    return Path(output_dir).resolve() if output_dir else settings.default_output_dir


def execute_single_conversion(
    url: str,
    timeout: int | None = None,
    save_html: bool = False,
    output_target: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    normalized_target = build_output_target(output_target, settings)
    normalized_timeout = int(timeout or settings.default_timeout)
    ensure_runtime_environment()

    workspace: Path | None = None
    output_dir = normalize_output_dir(None)
    if normalized_target == "fns":
        workspace = create_internal_workdir("single")
        output_dir = workspace

    try:
        result = run_pipeline(
            url=url,
            output_base_dir=output_dir,
            save_html=save_html,
            timeout=normalized_timeout,
        )
        sync = sync_result_to_output(result, output_target=normalized_target)
        local_artifacts = {"retained": False, "workdir": None}
        if workspace is not None:
            if settings.cleanup_temp_on_success:
                cleanup_internal_workdir(workspace)
            else:
                local_artifacts = {"retained": True, "workdir": str(workspace)}
    except Exception:
        cleanup_internal_workdir(workspace)
        raise

    return {
        "status": "success",
        "output_target": normalized_target,
        "result": result,
        "sync": sync,
        "local_artifacts": local_artifacts,
    }


def ensure_runtime_environment() -> None:
    settings = get_settings()
    os.environ["WECHAT_MD_IMAGE_MODE"] = settings.image_mode
    os.environ["WECHAT_MD_IMAGE_STORAGE_PROVIDER"] = settings.image_storage_provider or "s3"
    os.environ["WECHAT_MD_IMAGE_STORAGE_ENDPOINT"] = settings.image_storage_endpoint or ""
    os.environ["WECHAT_MD_IMAGE_STORAGE_REGION"] = settings.image_storage_region or ""
    os.environ["WECHAT_MD_IMAGE_STORAGE_BUCKET"] = settings.image_storage_bucket or ""
    os.environ["WECHAT_MD_IMAGE_STORAGE_ACCESS_KEY_ID"] = settings.image_storage_access_key_id or ""
    os.environ["WECHAT_MD_IMAGE_STORAGE_SECRET_ACCESS_KEY"] = settings.image_storage_secret_access_key or ""
    os.environ["WECHAT_MD_IMAGE_STORAGE_PATH_TEMPLATE"] = settings.image_storage_path_template or ""
    os.environ["WECHAT_MD_IMAGE_STORAGE_PUBLIC_BASE_URL"] = settings.image_storage_public_base_url or ""


def parse_links(urls: list[str] | None = None, urls_text: str | None = None, file_text: str | None = None) -> list[str]:
    raw_values: list[str] = []
    for source in urls or []:
        if source:
            raw_values.append(source.strip())
    for blob in (urls_text or "", file_text or ""):
        raw_values.extend(URL_PATTERN.findall(blob))
        raw_values.extend(
            line.strip()
            for line in blob.splitlines()
            if line.strip().startswith(("http://", "https://"))
        )

    deduped: list[str] = []
    seen: set[str] = set()
    for item in raw_values:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def read_uploaded_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def build_config_payload() -> dict[str, Any]:
    settings = get_settings()
    default_output_target = build_output_target(None, settings)
    return {
        "default_output_dir": str(settings.default_output_dir),
        "service_mode": "hybrid" if settings.fns_enabled else "local_only",
        "default_output_target": default_output_target,
        "auth_enabled": True,
        "session_cookie_secure": settings.session_cookie_secure,
        "fns_enabled": settings.fns_enabled,
        "fns_base_url": settings.fns_base_url,
        "fns_vault": settings.fns_vault,
        "fns_target_dir": settings.fns_target_dir,
        "current_user": {"username": settings.username},
        "cleanup_temp_on_success": settings.cleanup_temp_on_success,
        "image_mode": settings.image_mode,
        "image_storage_enabled": settings.image_storage_enabled,
        "image_public_base_url": settings.image_storage_public_base_url,
        "image_storage_bucket": settings.image_storage_bucket,
        "image_storage_path_template": settings.image_storage_path_template,
    }


def check_fns_status(http_session=None) -> dict[str, Any]:
    settings = get_settings()
    payload: dict[str, Any] = {
        "configured": settings.fns_enabled,
        "connected": False,
        "vault_exists": False,
        "vault_name": settings.fns_vault,
        "vault_count": 0,
        "user": None,
        "base_url": settings.fns_base_url,
        "message": "",
    }
    if not settings.fns_enabled:
        payload["message"] = "FNS 尚未配置完整"
        return payload

    session = http_session or requests.Session()
    headers = {"token": str(settings.fns_token)}
    try:
        user_response = session.get(
            f"{settings.fns_base_url}/api/user/info",
            headers=headers,
            timeout=max(settings.default_timeout, 15),
        )
        user_response.raise_for_status()
        vault_response = session.get(
            f"{settings.fns_base_url}/api/vault",
            headers=headers,
            timeout=max(settings.default_timeout, 15),
        )
        vault_response.raise_for_status()
        user_data = user_response.json()
        vault_data = vault_response.json()
    except requests.RequestException as error:
        payload["message"] = f"连接失败: {error}"
        return payload
    except ValueError:
        payload["message"] = "FNS 返回了无法解析的 JSON"
        return payload

    user_block = user_data.get("data") if isinstance(user_data, dict) else None
    vault_list = vault_data.get("data") if isinstance(vault_data, dict) else []
    if not isinstance(vault_list, list):
        vault_list = []
    payload["connected"] = True
    payload["user"] = user_block if isinstance(user_block, dict) else None
    payload["vault_count"] = len(vault_list)
    payload["vault_exists"] = any(
        isinstance(item, dict) and str(item.get("vault") or "") == str(settings.fns_vault or "")
        for item in vault_list
    )
    payload["message"] = "连接正常" if payload["vault_exists"] else "连接正常，但目标 vault 不存在"
    return payload


def build_output_target(output_target: str | None, settings=None) -> str:
    settings = settings or get_settings()
    normalized = (output_target or "").strip().lower()
    if normalized:
        if normalized not in {"local", "fns"}:
            raise ValueError("output_target 仅支持 local 或 fns")
        if normalized == "fns" and not settings.fns_enabled:
            raise ValueError("Fast Note Sync 未完成配置，无法输出到 fns")
        return normalized
    return "fns" if settings.fns_enabled else "local"


def sync_result_to_output(result: dict[str, Any], output_target: str) -> dict[str, Any]:
    if output_target == "local":
        return {
            "status": "success",
            "target": "local",
            "markdown_file": result["markdown_file"],
        }
    return sync_markdown_to_fns(
        markdown_path=Path(str(result["markdown_file"])),
        note_title=str(result["title"]),
        folder_name=str(result.get("folder_name") or ""),
    )


def sync_markdown_to_fns(
    markdown_path: Path,
    note_title: str,
    folder_name: str,
    http_session=None,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.fns_enabled:
        raise RuntimeError("Fast Note Sync 未完成配置")

    file_name = f"{sanitize_filename(note_title)}.md"
    target_dir = settings.fns_target_dir.strip("/\\")
    note_path = "/".join(part for part in (target_dir, file_name) if part)
    content = markdown_path.read_text(encoding="utf-8")
    stat = markdown_path.stat()
    payload = {
        "vault": settings.fns_vault,
        "path": note_path,
        "content": content,
        "createOnly": False,
        "ctime": int(stat.st_ctime),
        "mtime": int(stat.st_mtime),
    }
    session = http_session or requests.Session()
    try:
        response = session.post(
            f"{settings.fns_base_url}/api/note",
            headers={
                "token": str(settings.fns_token),
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=max(get_settings().default_timeout, 30),
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(f"Fast Note Sync 请求失败: {error}") from error

    try:
        data = response.json()
    except ValueError as error:
        raise RuntimeError("Fast Note Sync 返回了无法解析的 JSON") from error

    if isinstance(data, dict):
        success_flag = data.get("status")
        code = data.get("code")
        if success_flag is False or code not in (None, 0, 1):
            raise RuntimeError(
                f"Fast Note Sync 写入失败: {data.get('msg') or data.get('message') or data.get('code')}"
            )

    return {
        "status": "success",
        "target": "fns",
        "vault": settings.fns_vault,
        "path": note_path,
        "folder_name": folder_name,
        "response": data,
    }


def configure_telegram_webhook(http_session=None) -> dict[str, Any]:
    settings = get_settings()
    if not settings.telegram_bot_token:
        state = {"status": "inactive", "message": "Telegram Bot Token 未配置", "webhook_url": ""}
        update_telegram_webhook_state(state["status"], state["message"])
        return state

    session = http_session or requests.Session()
    if not settings.telegram_enabled:
        response = session.post(
            _telegram_api_url(settings.telegram_bot_token, "deleteWebhook"),
            json={"drop_pending_updates": False},
            timeout=max(settings.default_timeout, 15),
        )
        response.raise_for_status()
        state = {"status": "inactive", "message": "Telegram Webhook 已删除", "webhook_url": ""}
        update_telegram_webhook_state(state["status"], state["message"])
        return state

    if not settings.telegram_enabled_and_configured or not settings.telegram_webhook_url:
        state = {"status": "error", "message": "Telegram Bot 配置不完整", "webhook_url": settings.telegram_webhook_url or ""}
        update_telegram_webhook_state(state["status"], state["message"])
        return state

    response = session.post(
        _telegram_api_url(settings.telegram_bot_token, "setWebhook"),
        json={
            "url": settings.telegram_webhook_url,
            "secret_token": settings.telegram_webhook_secret,
            "allowed_updates": ["message"],
        },
        timeout=max(settings.default_timeout, 15),
    )
    response.raise_for_status()
    payload = response.json()
    ok = bool(payload.get("ok", False))
    description = str(payload.get("description") or ("Telegram Webhook 已注册" if ok else "Telegram Webhook 注册失败"))
    state = {
        "status": "success" if ok else "error",
        "message": description,
        "webhook_url": settings.telegram_webhook_url,
    }
    update_telegram_webhook_state(state["status"], state["message"])
    return state


def send_telegram_message(chat_id: str, text: str, http_session=None) -> dict[str, Any]:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("Telegram Bot Token 未配置")
    session = http_session or requests.Session()
    response = session.post(
        _telegram_api_url(settings.telegram_bot_token, "sendMessage"),
        json={"chat_id": chat_id, "text": text},
        timeout=max(settings.default_timeout, 15),
    )
    response.raise_for_status()
    return response.json()


def submit_telegram_convert_task(url: str, chat_id: str) -> None:
    _telegram_executor.submit(process_telegram_convert_task, url, chat_id)


def process_telegram_convert_task(url: str, chat_id: str) -> None:
    settings = get_settings()
    try:
        payload = execute_single_conversion(
            url=url,
            timeout=settings.default_timeout,
            save_html=False,
            output_target="fns",
        )
    except Exception as error:
        send_telegram_message(chat_id, f"转换失败：{error}")
        return

    if not settings.telegram_notify_on_complete:
        return

    title = str(payload["result"].get("title") or "转换完成")
    sync_path = str(payload["sync"].get("path") or payload["sync"].get("markdown_file") or "-")
    image_mode = "S3 图床外链" if str(payload["result"].get("image_mode") or "") == "s3_hotlink" else "微信原链"
    send_telegram_message(
        chat_id,
        "\n".join(
            [
                f"转换完成：{title}",
                f"同步路径：{sync_path}",
                f"图片模式：{image_mode}",
            ]
        ),
    )


def extract_single_wechat_url(text: str) -> tuple[str | None, int]:
    links = URL_PATTERN.findall(text or "")
    if not links:
        return None, 0
    unique_links: list[str] = []
    seen: set[str] = set()
    for item in links:
        if item in seen:
            continue
        seen.add(item)
        unique_links.append(item)
    return unique_links[0], len(unique_links)


def _telegram_api_url(token: str, method: str) -> str:
    return f"https://api.telegram.org/bot{token}/{method}"


def _copy_job(job: dict[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for key, value in job.items():
        if isinstance(value, list):
            copied[key] = list(value)
        elif isinstance(value, dict):
            copied[key] = dict(value)
        else:
            copied[key] = value
    return copied


job_store = JobStore()
_telegram_executor = ThreadPoolExecutor(max_workers=2)
