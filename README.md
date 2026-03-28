# wechat-md-server

Local FastAPI service for converting WeChat public articles into Markdown files in an Obsidian vault.

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765`.

## Defaults

- Output directory: `D:\obsidian\00_Inbox`
- R2 config path: `D:\obsidian\.obsidian\plugins\image-upload-toolkit\data.json`
- FNS target directory: `00_Inbox/微信公众号`

You can override these with environment variables:

- `WECHAT_MD_DEFAULT_OUTPUT_DIR`
- `WECHAT_MD_R2_CONFIG_PATH`
- `WECHAT_MD_ACCESS_TOKEN`
- `WECHAT_MD_FNS_BASE_URL`
- `WECHAT_MD_FNS_TOKEN`
- `WECHAT_MD_FNS_VAULT`
- `WECHAT_MD_FNS_TARGET_DIR`

## v2 Output Modes

- Default behavior is `fns` when all `WECHAT_MD_FNS_*` values are configured.
- Otherwise the service falls back to `local`.
- `POST /api/convert` and `POST /api/batch` both accept `output_target` with `fns` or `local`.
- When `WECHAT_MD_ACCESS_TOKEN` is set, API access requires either:
  - `Authorization: Bearer <token>`
  - or a login session created from the built-in `/api/session` page flow

## Development Notes

- Do not commit integration output directories such as `_integration_output/` or `_integration_output_v2/`.
- If a test needs sample content, keep a minimal fixture under `tests/` instead of committing generated output.
