# wechat-md-server

[English](README.md)

一个本地运行的 FastAPI 服务，用于把微信公众号文章转换为 Markdown，并同步到面向 Obsidian 的 Fast Note Sync。

## 运行方式

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8765
```

打开 `http://127.0.0.1:8765` 或 `http://<your-lan-ip>:8765`。

- 主页面：`http://127.0.0.1:8765/` 或 `http://<your-lan-ip>:8765/`
- 登录页：内置单账号登录
- 设置页：`http://127.0.0.1:8765/settings` 或 `http://<your-lan-ip>:8765/settings`

## Docker

推荐的容器基础镜像：

- `python:3.14-slim-bookworm`
- `amd64 / x86_64`
- 以 `docker-compose.yml` 作为主要部署入口

使用 Docker Compose 启动：

```bash
docker compose build
docker compose up -d
docker compose logs -f
```

面向生产的 Compose：

```bash
cp .env.prod.example .env.prod
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f
```

访问地址：

- `http://127.0.0.1:8765/login`
- `http://<your-lan-ip>:8765/login`

容器行为：

- 应用监听在 `0.0.0.0:8765`
- 运行时数据通过 `./data:/app/data` 持久化
- 运行时配置路径为 `/app/data/runtime-config.json`
- 临时工作输出目录为 `/app/data/workdir-output`

部署相关文件：

- `Dockerfile`
- `.dockerignore`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `.env.prod.example`

镜像体积预估：

- 推荐构建目标约为 `180MB - 280MB`
- 偏保守的第一版构建可能落在 `250MB - 340MB`

为什么不选 Alpine：

- `Pillow` 和 `cryptography` 在 Debian slim 上更容易保持稳定
- 这个项目更受益于可预测的 wheels 和更容易排障的环境，而不是节省几十 MB

## 必需环境变量

运行时敏感配置依赖主密钥，没有它服务无法加载加密后的运行时配置。

- `WECHAT_MD_APP_MASTER_KEY`
- `WECHAT_MD_ADMIN_USERNAME`
- `WECHAT_MD_ADMIN_PASSWORD`

如果首次启动时省略 `WECHAT_MD_ADMIN_PASSWORD`，服务会自动生成一个随机初始密码，并在 stdout 中打印一次。

把 [.env.example](/path/to/wechat-md-server/.env.example) 复制到你的部署环境里，并替换所有占位值。

## 默认值

- FNS 目标目录：`00_Inbox/微信公众号`
- 图片模式：`wechat_hotlink`
- 运行时配置路径：`data/runtime-config.json`
- 内部工作目录根路径：`data/workdir/`

可选环境变量：

- `WECHAT_MD_RUNTIME_CONFIG_PATH`
- `WECHAT_MD_DEFAULT_OUTPUT_DIR`
- `WECHAT_MD_SESSION_COOKIE_SECURE`
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

## 当前行为

- Web UI 受登录保护。
- Session Cookie 可以通过 `WECHAT_MD_SESSION_COOKIE_SECURE=true` 开启 `Secure` 模式。
- 连续登录失败会触发限流。
- 敏感运行时值在写入 `runtime-config.json` 前会先加密：
  - FNS token
  - S3 secret access key
  - session secret
- 转换后的笔记会写入当前配置的 Fast Note Sync 目标。
- FNS 模式会使用内部临时工作目录，不会直接写入 Obsidian Inbox 路径。
- 图片处理由 `/settings` 全局控制：
  - `wechat_hotlink`：Markdown 中保留原始微信图片链接
  - `s3_hotlink`：把静态图片上传到兼容 S3 的对象存储，并使用 `public_base_url/object_key`
- 在 `s3_hotlink` 模式下，GIF 和 SVG 继续保留原始微信图片链接。

## 设置页

- `/settings` 提供服务端持久化的管理员设置页。
- 设置页包含概览卡片、FNS 连通性检测、图片模式选择和表单内联校验提示。
- FNS 配置支持从剪贴板导入，或粘贴如下 JSON 结构：
  - `api`
  - `apiToken`
  - `vault`
- 剪贴板导入只会填充表单，只有点击保存后才会真正持久化。
- 敏感字段在重新加载后会以掩码显示，不会以明文从设置 API 返回。
- S3 图片配置需要在设置页手工填写，不依赖 Obsidian 插件或 R2 配置文件。

## 重置管理员密码

如果 `.env` 已经改过，但现有 `runtime-config.json` 中已经保存了管理员密码哈希，就不要指望 `.env` 自动覆盖，而应使用离线重置命令。

Python CLI：

```powershell
python -m app.cli.reset_admin_password --password "new-secret"
python -m app.cli.reset_admin_password --random
python -m app.cli.reset_admin_password --username admin --password "new-secret"
```

PowerShell 包装脚本：

```powershell
.\scripts\reset-admin-password.ps1 -Password "new-secret"
.\scripts\reset-admin-password.ps1 -Random
```

说明：

- 命令需要正确的 `WECHAT_MD_APP_MASTER_KEY`
- 重置密码时也会轮换 `session_secret`，因此已有登录会话会失效
- 这个命令只更新管理员凭据，不会修改 FNS 或 S3 配置

## VPS 部署

推荐目录结构：

```text
/opt/wechat-md-server/
├── .env
├── data/
│   ├── runtime-config.json
│   ├── workdir/
│   └── workdir-output/
├── docker-compose.yml
└── deploy/systemd/wechat-md-server.service.example
```

推荐部署步骤：

1. 把 `.env.example` 复制为 `.env`，并设置强随机的 `WECHAT_MD_APP_MASTER_KEY`
2. 设置 `WECHAT_MD_SESSION_COOKIE_SECURE=true`
3. 如有需要，先创建宿主机 `data/` 目录
4. 把 `.env.prod.example` 复制为 `.env.prod`
5. 运行 `docker compose -f docker-compose.prod.yml build` 和 `docker compose -f docker-compose.prod.yml up -d`
6. 生产版 compose 目前仍直接暴露 `8765`，因此可以直接通过 `http://<server-ip>:8765` 访问
7. 如果后面想改成只走反代，把端口绑定改回 loopback，并在前面加 Nginx 或 Caddy
8. 如果你不想容器化，仍可以使用 [wechat-md-server.service.example](/path/to/wechat-md-server/deploy/systemd/wechat-md-server.service.example) 里的 systemd 样例

推荐的反向代理边界：

- 只暴露 Web 服务入口
- 应用可以监听在 `0.0.0.0`，但应在主机防火墙或反代层限制暴露范围
- 让反向代理处理 HTTPS 终止
- 建议在代理层增加 HSTS 和 Host 限制

## 备份与恢复

需要备份：

- `data/runtime-config.json`
- 如果你选择保留成功任务的临时产物，也要备份 `data/workdir/`
- `.env` 文件，或者至少保存 `WECHAT_MD_APP_MASTER_KEY`

恢复流程：

1. 恢复项目文件并安装依赖
2. 恢复 `runtime-config.json`
3. 恢复完全相同的 `WECHAT_MD_APP_MASTER_KEY`
4. 启动服务

如果主密钥变了，之前加密的运行时敏感字段将无法解密。

## 开发说明

- 不要提交 `_integration_output/`、`_integration_output_v2/` 这类集成输出目录
- 不要提交 `.env` 或 `data/runtime-config.json`
- 如果你想在 Windows 本地使用固定启动入口，可以直接用 [start-server.ps1](/path/to/wechat-md-server/scripts/start-server.ps1)
