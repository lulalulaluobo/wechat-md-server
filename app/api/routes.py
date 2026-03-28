from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.config import get_settings
from app.core.pipeline import run_pipeline
from app.services import (
    build_config_payload,
    ensure_runtime_environment,
    job_store,
    normalize_output_dir,
    parse_links,
    read_uploaded_text,
)


router = APIRouter()


@router.get("/api/config")
async def get_config() -> dict[str, Any]:
    return build_config_payload()


@router.post("/api/convert")
async def convert_article(request: Request) -> dict[str, Any]:
    payload = await _read_convert_payload(request)
    url = payload.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="缺少微信文章链接 url")

    output_dir = normalize_output_dir(payload.get("output_dir"))
    timeout = int(payload.get("timeout") or get_settings().default_timeout)
    save_html = _parse_bool(payload.get("save_html"))
    ensure_runtime_environment()

    try:
        result = run_pipeline(url=url, output_base_dir=output_dir, save_html=save_html, timeout=timeout)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"status": "success", "result": result}


@router.post("/api/batch")
async def convert_batch(
    request: Request,
    file: UploadFile | None = File(default=None),
) -> dict[str, Any]:
    payload = await _read_batch_payload(request, file=file)
    urls = parse_links(
        urls=payload.get("urls"),
        urls_text=payload.get("urls_text"),
        file_text=payload.get("file_text"),
    )
    if not urls:
        raise HTTPException(status_code=400, detail="未解析到可用的微信文章链接")

    output_dir = normalize_output_dir(payload.get("output_dir"))
    timeout = int(payload.get("timeout") or get_settings().default_timeout)
    save_html = _parse_bool(payload.get("save_html"))

    job = job_store.create_batch_job(
        urls=urls,
        output_dir=output_dir,
        save_html=save_html,
        timeout=timeout,
    )
    return {
        "status": "queued",
        "job_id": job["job_id"],
        "total": job["total"],
        "deduped_count": len(urls),
        "output_dir": job["output_dir"],
    }


@router.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> dict[str, Any]:
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return job


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


async def _read_convert_payload(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return dict(await request.json())
    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        return {key: value for key, value in form.items()}
    return {}


async def _read_batch_payload(request: Request, file: UploadFile | None) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = dict(await request.json())
        payload["file_text"] = ""
        return payload

    form = await request.form()
    payload = {key: value for key, value in form.items() if key != "file"}
    payload["urls"] = []
    if file is not None:
        payload["file_text"] = read_uploaded_text(await file.read())
    else:
        payload["file_text"] = ""
    return payload
