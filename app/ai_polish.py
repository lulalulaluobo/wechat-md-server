from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")
PROMPT_PLACEHOLDER_PATTERN = re.compile(r'{{\s*"([^"]+)"\s*}}')
ESCAPED_PROMPT_PLACEHOLDER_PATTERN = re.compile(r'{{\s*\\"([^"]+)\\"\s*}}')


def render_template(template: str, variables: dict[str, Any], *, list_format: str = "comma") -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = variables.get(key, "")
        if isinstance(value, list):
            if list_format == "json":
                return json.dumps([str(item) for item in value], ensure_ascii=False)
            return ", ".join(str(item) for item in value)
        return str(value or "")

    return PLACEHOLDER_PATTERN.sub(replace, template or "")


def request_interpreter_variables(
    *,
    ai_base_url: str,
    ai_api_key: str,
    ai_model: str,
    prompt: str,
    http_session=None,
    timeout: int = 60,
) -> dict[str, Any]:
    session = http_session or requests.Session()
    response = session.post(
        f"{ai_base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {ai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": ai_model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": "你是一个结构化笔记解释器，只返回 JSON 对象。"},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    choices = payload.get("choices") if isinstance(payload, dict) else None
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("AI 返回缺少 choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise RuntimeError("AI 返回缺少 message")
    content = message.get("content")
    if isinstance(content, list):
        content_text = "".join(
            str(item.get("text") or "")
            for item in content
            if isinstance(item, dict)
        ).strip()
    else:
        content_text = str(content or "").strip()
    if not content_text:
        raise RuntimeError("AI 返回内容为空")
    return _parse_json_response(content_text)


def build_prompt_from_variable_prompts(
    variable_prompts: dict[str, str],
    metadata: dict[str, Any],
    context: str,
) -> str:
    lines = [
        "你是一个 Obsidian 笔记解释器。请基于提供的元数据和上下文，一次性返回 JSON 对象。",
        "不要输出 Markdown，不要额外解释，只返回 JSON。",
        "",
        "元数据：",
        f"- title: {metadata.get('title') or ''}",
        f"- author: {metadata.get('author') or ''}",
        f"- url: {metadata.get('url') or ''}",
        f"- date: {metadata.get('date') or ''}",
        "",
        "需要输出的 JSON 字段：",
    ]
    for key, prompt in variable_prompts.items():
        lines.append(f'- {key}: {prompt}')
    lines.extend(
        [
            "",
            "上下文：",
            context.strip(),
        ]
    )
    return "\n".join(lines).strip()


def extract_prompt_variables_from_templates(
    *,
    frontmatter_template: str,
    body_template: str,
) -> tuple[str, str, dict[str, str]]:
    variable_prompts: dict[str, str] = {}

    def normalize_prompt_text(raw_prompt: str) -> str:
        return str(raw_prompt or "").strip()

    normalized_frontmatter_lines: list[str] = []
    for line in str(frontmatter_template or "").splitlines():
        if ":" not in line:
            normalized_frontmatter_lines.append(line)
            continue
        key_part, value_part = line.split(":", 1)
        field_name = key_part.strip()
        prompt_text = _extract_prompt_placeholder(value_part.strip())
        if field_name and prompt_text:
            variable_prompts[field_name] = normalize_prompt_text(prompt_text)
            normalized_frontmatter_lines.append(f"{key_part}: {{{{{field_name}}}}}")
        else:
            normalized_frontmatter_lines.append(line)

    block_index = 0

    def replace_body_prompt(match: re.Match[str]) -> str:
        nonlocal block_index
        block_index += 1
        variable_name = f"clipper_block_{block_index}"
        variable_prompts[variable_name] = normalize_prompt_text(match.group(1))
        return f"{{{{{variable_name}}}}}"

    normalized_body = PROMPT_PLACEHOLDER_PATTERN.sub(replace_body_prompt, str(body_template or ""))
    normalized_body = ESCAPED_PROMPT_PLACEHOLDER_PATTERN.sub(replace_body_prompt, normalized_body)

    return "\n".join(normalized_frontmatter_lines), normalized_body, variable_prompts


def apply_ai_polish_to_markdown(
    *,
    markdown_path: Path,
    metadata: dict[str, Any],
    ai_base_url: str,
    ai_api_key: str,
    ai_model: str,
    interpreter_prompt: str,
    frontmatter_template: str,
    body_template: str,
    context_template: str = "{{content}}",
    allow_body_polish: bool,
    enable_content_polish: bool = False,
    content_polish_prompt: str = "",
    http_session=None,
    timeout: int = 60,
) -> dict[str, Any]:
    original_content = markdown_path.read_text(encoding="utf-8")
    normalized_frontmatter_template, normalized_body_template, extracted_variable_prompts = extract_prompt_variables_from_templates(
        frontmatter_template=frontmatter_template,
        body_template=body_template,
    )
    base_variables = {
        "title": str(metadata.get("title") or ""),
        "author": str(metadata.get("author") or ""),
        "url": str(metadata.get("url") or ""),
        "date": str(metadata.get("date") or datetime.now().strftime("%Y-%m-%d")),
        "content": original_content.strip(),
        "summary": "",
        "tags": "",
        "my_understand": "",
        "body_polish": "",
        "content_polished": "",
        "content_polish_prompt_enabled": bool(enable_content_polish),
        "content_polish_prompt": str(content_polish_prompt or "").strip(),
    }
    rendered_context = render_template(context_template, base_variables).strip() or base_variables["content"]
    prompt = _build_interpreter_prompt(
        interpreter_prompt=interpreter_prompt,
        template_variable_prompts=extracted_variable_prompts,
        metadata=base_variables,
        context=rendered_context,
    )
    interpreted = request_interpreter_variables(
        ai_base_url=ai_base_url,
        ai_api_key=ai_api_key,
        ai_model=ai_model,
        prompt=prompt,
        http_session=http_session,
        timeout=timeout,
    )
    normalized = _normalize_interpreted_variables(interpreted, allow_body_polish=allow_body_polish)
    polished_content = str(normalized.get("content_polished") or "").strip()
    final_content = original_content.strip()
    if enable_content_polish and polished_content:
        final_content = polished_content
    variables = {
        **base_variables,
        **normalized,
        "content": final_content,
        "content_raw": original_content.strip(),
        "content_polished": polished_content,
    }
    frontmatter = render_template(
        normalized_frontmatter_template,
        variables,
        list_format="json",
    ).strip()
    body = render_template(normalized_body_template, variables).strip()
    sections = [section for section in (frontmatter, body) if section]
    if "{{content}}" not in (normalized_body_template or "") and "{{content_polished}}" not in (normalized_body_template or ""):
        sections.append(final_content)
    markdown_path.write_text("\n\n".join(sections).strip() + "\n", encoding="utf-8")
    return {
        "enabled": True,
        "status": "success",
        "model": ai_model,
        "template_applied": True,
        "summary": normalized["summary"],
        "tags": normalized["tags"],
        "content_polished": bool(enable_content_polish and polished_content),
        "message": "AI 润色已应用",
    }


def _build_interpreter_prompt(
    *,
    interpreter_prompt: str,
    template_variable_prompts: dict[str, str],
    metadata: dict[str, Any],
    context: str,
) -> str:
    parsed = _try_parse_prompt_mapping(interpreter_prompt)
    merged_prompts = {**template_variable_prompts}
    if parsed:
        merged_prompts.update(parsed)
    if metadata.get("content_polish_prompt_enabled"):
        merged_prompts.setdefault(
            "content_polished",
            str(metadata.get("content_polish_prompt") or "").strip(),
        )
    if not merged_prompts:
        return render_template(
            interpreter_prompt,
            {
                **metadata,
                "content": context,
            },
        )
    return build_prompt_from_variable_prompts(merged_prompts, metadata=metadata, context=context)


def _try_parse_prompt_mapping(interpreter_prompt: str) -> dict[str, str] | None:
    text = (interpreter_prompt or "").strip()
    if not text.startswith("{"):
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    normalized: dict[str, str] = {}
    for key, value in parsed.items():
        normalized_key = str(key).strip()
        if not normalized_key:
            continue
        normalized[normalized_key] = str(value or "").strip()
    return normalized or None


def _extract_prompt_placeholder(value: str) -> str | None:
    for pattern in (PROMPT_PLACEHOLDER_PATTERN, ESCAPED_PROMPT_PLACEHOLDER_PATTERN):
        match = pattern.fullmatch(str(value or "").strip())
        if match:
            return str(match.group(1) or "").strip()
    return None


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError("AI 返回不是有效 JSON")
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as error:
            raise RuntimeError("AI 返回不是有效 JSON") from error
    if not isinstance(parsed, dict):
        raise RuntimeError("AI 返回 JSON 必须是对象")
    return parsed


def _normalize_interpreted_variables(payload: dict[str, Any], *, allow_body_polish: bool) -> dict[str, Any]:
    tags_value = payload.get("tags")
    tags: list[str]
    if isinstance(tags_value, list):
        tags = [str(item).strip() for item in tags_value if str(item).strip()]
    elif isinstance(tags_value, str):
        tags = [part.strip() for part in re.split(r"[,\n]", tags_value) if part.strip()]
    else:
        tags = []
    deduped_tags: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        if tag in seen:
            continue
        seen.add(tag)
        deduped_tags.append(tag)
    normalized = {
        "summary": str(payload.get("summary") or "").strip(),
        "tags": deduped_tags,
        "my_understand": str(payload.get("my_understand") or "").strip(),
        "body_polish": str(payload.get("body_polish") or "").strip() if allow_body_polish else "",
        "content_polished": str(payload.get("content_polished") or "").strip(),
    }
    for key, value in payload.items():
        if key in normalized:
            continue
        normalized[str(key)] = value
    return normalized
