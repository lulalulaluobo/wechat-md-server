from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    default_output_dir: Path
    default_r2_config_path: Path
    default_timeout: int = 30


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
    return Settings(
        default_output_dir=output_dir,
        default_r2_config_path=r2_config_path,
    )
