# wechat-md-server

Local FastAPI service for converting WeChat public articles into Markdown and syncing them to Fast Note Sync for Obsidian.

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765`.

- Main page: `http://127.0.0.1:8765/`
- Login: use the built-in single account `admin / admin`
- Settings page: `http://127.0.0.1:8765/settings`

## Defaults

- FNS target directory: `00_Inbox/微信公众号`
- Image mode: `wechat_hotlink`

You can override these with environment variables:

- `WECHAT_MD_DEFAULT_OUTPUT_DIR`
- `WECHAT_MD_RUNTIME_CONFIG_PATH`
- `WECHAT_MD_FNS_BASE_URL`
- `WECHAT_MD_FNS_TOKEN`
- `WECHAT_MD_FNS_VAULT`
- `WECHAT_MD_FNS_TARGET_DIR`
- `WECHAT_MD_IMAGE_MODE`
- `WECHAT_MD_IMAGE_STORAGE_PROVIDER`
- `WECHAT_MD_IMAGE_STORAGE_ENDPOINT`
- `WECHAT_MD_IMAGE_STORAGE_REGION`
- `WECHAT_MD_IMAGE_STORAGE_BUCKET`
- `WECHAT_MD_IMAGE_STORAGE_ACCESS_KEY_ID`
- `WECHAT_MD_IMAGE_STORAGE_SECRET_ACCESS_KEY`
- `WECHAT_MD_IMAGE_STORAGE_PATH_TEMPLATE`
- `WECHAT_MD_IMAGE_STORAGE_PUBLIC_BASE_URL`

Runtime settings edited from the web UI are stored in `data/runtime-config.json` by default.

## Current Behavior

- The web UI is login-protected. The built-in account is `admin / admin`.
- Converted notes are written to the currently configured Fast Note Sync target.
- Temporary local work directories are internal implementation detail, not a user-facing output target.
- Image handling is controlled globally from `/settings`:
  - `wechat_hotlink`: keep original WeChat image URLs in Markdown
  - `s3_hotlink`: upload static images to a generic S3-compatible object store and use `public_base_url/object_key`
- In `s3_hotlink`, GIF and SVG keep the original WeChat image URLs.

## Settings UI

- `/settings` provides a server-backed admin settings page.
- The settings page includes overview cards, FNS connection detection, image mode selection, and inline form validation hints.
- FNS config can be imported from clipboard or pasted JSON in this format:
  - `api`
  - `apiToken`
  - `vault`
- Clipboard import only fills the form. Settings are not persisted until you click save.
- Secret fields are masked on reload and never returned in plaintext from the settings API.
- S3 image settings are entered manually in the settings page. There is no Obsidian plugin or R2 config file dependency.

## Development Notes

- Do not commit integration output directories such as `_integration_output/` or `_integration_output_v2/`.
- If a test needs sample content, keep a minimal fixture under `tests/` instead of committing generated output.
