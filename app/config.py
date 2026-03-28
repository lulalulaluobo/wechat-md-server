from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    default_output_dir: Path
    default_r2_config_path: Path
    default_timeout: int = 30
    access_token: str | None = None
    fns_base_url: str | None = None
    fns_token: str | None = None
    fns_vault: str | None = None
    fns_target_dir: str = "00_Inbox/微信公众号"

    @property
    def fns_enabled(self) -> bool:
        return bool(self.fns_base_url and self.fns_token and self.fns_vault)


def get_settings() -> Settings:
    output_dir = Path(
        os.environ.get("WECHAT_MD_DEFAULT_OUTPUT_DIR", r"D:\obsidian\00_Inbox")
    ).resolve()
    r2_config_path = Path(
        os.environ.get(
            "WECHAT_MD_R2_CONFIG_PATH",
            r"D:\obsidian\.obsidian\plugins\image-upload-toolkit\data.json",
        )
    ).resolve()
    access_token = os.environ.get("WECHAT_MD_ACCESS_TOKEN") or None
    fns_base_url = (os.environ.get("WECHAT_MD_FNS_BASE_URL") or "").strip() or None
    fns_token = (os.environ.get("WECHAT_MD_FNS_TOKEN") or "").strip() or None
    fns_vault = (os.environ.get("WECHAT_MD_FNS_VAULT") or "").strip() or None
    fns_target_dir = (
        os.environ.get("WECHAT_MD_FNS_TARGET_DIR", "00_Inbox/微信公众号").strip() or "00_Inbox/微信公众号"
    )
    return Settings(
        default_output_dir=output_dir,
        default_r2_config_path=r2_config_path,
        access_token=access_token,
        fns_base_url=fns_base_url.rstrip("/") if fns_base_url else None,
        fns_token=fns_token,
        fns_vault=fns_vault,
        fns_target_dir=fns_target_dir.strip("/\\"),
    )
