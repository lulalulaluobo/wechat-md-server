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

You can override these with environment variables:

- `WECHAT_MD_DEFAULT_OUTPUT_DIR`
- `WECHAT_MD_R2_CONFIG_PATH`
