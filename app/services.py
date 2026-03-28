from __future__ import annotations

import os
import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.core.pipeline import run_pipeline


URL_PATTERN = re.compile(r"https?://mp\.weixin\.qq\.com/s/[^\s)>]+", re.IGNORECASE)


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
            "results": [],
            "errors": [],
        }
        with self._lock:
            self._jobs[job_id] = payload
        self._executor.submit(self._run_batch_job, job_id, urls, output_dir, save_html, timeout)
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
    ) -> None:
        ensure_runtime_environment()
        self._update(job_id, status="running")
        for url in urls:
            try:
                result = run_pipeline(url=url, output_base_dir=output_dir, save_html=save_html, timeout=timeout)
                self._append_result(job_id, {"url": url, "status": "success", "result": result})
            except Exception as error:  # pragma: no cover - exercised in integration flow
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


def ensure_runtime_environment() -> None:
    settings = get_settings()
    os.environ["WECHAT_MD_R2_CONFIG_PATH"] = str(settings.default_r2_config_path)


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
    r2_config_exists = settings.default_r2_config_path.exists()
    return {
        "default_output_dir": str(settings.default_output_dir),
        "default_r2_config_path": str(settings.default_r2_config_path),
        "r2_config_exists": r2_config_exists,
        "service_mode": "local_only",
    }


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
