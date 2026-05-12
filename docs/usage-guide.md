# WeChat MD Server 使用教程

本文档面向新用户，帮助你从零部署并配置 wechat-md-server，最终实现"微信公众号文章 → Markdown → Obsidian"的完整工作流。

---

## 第一部分：部署与登录

### 1. Docker Compose 部署（推荐）

**前提条件**：已安装 Docker 和 Docker Compose。

1. 下载 `docker-compose.yml` 到本地：

```bash
mkdir wechat-md-server && cd wechat-md-server
curl -O https://raw.githubusercontent.com/lulalulaluobo/wechat-md-server/main/docker-compose.yml
```

1. 修改环境变量（至少修改 `WECHAT_MD_APP_MASTER_KEY` 和 `WECHAT_MD_ADMIN_PASSWORD`）：

```yaml
environment:
  WECHAT_MD_APP_MASTER_KEY: "替换为一个随机长字符串"
  WECHAT_MD_ADMIN_USERNAME: "admin"
  WECHAT_MD_ADMIN_PASSWORD: "替换为你的密码"
```

> [!important] 关于 WECHAT_MD_APP_MASTER_KEY
> 这个密钥用于加密存储所有敏感配置（FNS Token、Bot Token、S3 密钥等）。一旦设定后不要修改，否则已加密的配置将无法解密。可以用 `openssl rand -hex 32` 生成一个随机值。

1. 启动服务：

```bash
docker compose up -d
```

1. 打开浏览器访问 `http://127.0.0.1:8765/login`，使用上面配置的账号密码登录。

### 2. 一键脚本部署（适合服务器）

> [!note] 仅支持 Debian / Ubuntu，需要 root 权限。

```bash
curl -fsSL https://raw.githubusercontent.com/lulalulaluobo/wechat-md-server/main/deploy/install.sh | sudo bash -s -- install
```

脚本会自动安装 Docker、生成随机密钥并启动服务。默认账号 `admin`，默认密码 `admin123`。

常用管理命令：

```bash
sudo ./install.sh status     # 查看服务状态
sudo ./install.sh logs       # 实时查看日志
sudo ./install.sh update     # 更新镜像（保留数据）
sudo ./install.sh restart    # 重启服务
sudo ./install.sh uninstall  # 卸载
```

启动后访问 `http://服务器IP:8765/login`。

> [!warning] 安全提示
> 一键部署的默认密码是 `admin123`，登录后请立即在"设置 → 账户安全"中修改。

### 3. 本地开发启动

```bash
cp .env.example .env
# 编辑 .env，至少设置 WECHAT_MD_APP_MASTER_KEY 和管理员账号密码
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8765
```

Windows PowerShell：

```powershell
copy .env.example .env
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8765
```

启动后访问 `http://127.0.0.1:8765/login`。

> [!tip] 忘记密码？
> 通过命令行重置：`python -m app.cli.reset_admin_password --random`

---

## 第二部分：功能配置教程

登录后进入"设置"页面，按以下顺序完成配置。

### 4. 配置 FNS 同步（必须）

> [!important] 这是核心配置
> FNS（Fast Note Sync）负责把生成的 Markdown 同步到你的 Obsidian 仓库。不配置这一步，文章可以转换但无法同步到 Obsidian。

**路径**：设置 → FNS 同步

#### 方式一：快捷导入（推荐）

1. 在 Obsidian 中安装 [Fast Note Sync](https://github.com/haierkeys/obsidian-fast-note-sync) 插件并配置好
2. 从 FNS 插件中复制配置 JSON（包含 `api`、`apiToken`、`vault` 字段）
3. 粘贴到 **FNS JSON Import** 文本框，点击 **解析并填充**

#### 方式二：手动填写

| 配置项 | 说明 | 填写示例 |
| --- | --- | --- |
| **FNS 服务地址** | FNS 服务器的地址 | `https://obsync.example.com` |
| **Vault 名称** | 你的 Obsidian 仓库名称 | `MyVault` |
| **目标目录** | 文件同步到仓库内的子目录 | `00_Inbox/微信公众号` |
| **FNS Token** | FNS 服务的 API 认证令牌 | 从 FNS 插件配置中复制 |

填写完成后点击 **检查 FNS 连接**，验证是否配置成功。

> [!tip] Token 掩码是正常的
> 页面刷新后 Token 会显示为 `****`，这是安全行为，不需要重新填写。系统已经保存了你的实际 Token。

---

### 5. 配置图片模式

**路径**：设置 → 图片模式

系统提供两种图片处理方式：

| 模式 | 说明 | 适合场景 |
| --- | --- | --- |
| **微信热链**（默认） | 直接使用微信原始图片 URL | 先跑通流程、不关心图片长期可用性 |
| **S3 热链** | 上传图片到你的 S3 兼容存储 | 追求图片长期可控和可迁移 |

如果选择 **微信热链**，不需要额外配置。

如果选择 **S3 热链**，需要填写以下参数：

| 参数 | 说明 | 如何获取 |
| --- | --- | --- |
| **S3 Endpoint** | S3 兼容存储的 API 地址 | 你的对象存储服务商提供（如 Cloudflare R2: `https://<account>.r2.cloudflarestorage.com`） |
| **Region** | 存储区域 | 服务商提供，通常填 `auto` 即可 |
| **Bucket** | 存储桶名称 | 在对象存储控制台创建 |
| **Access Key ID** | 访问密钥 ID | 在对象存储控制台的"API 密钥"页面生成 |
| **Secret Access Key** | 访问密钥 | 同上，生成时一并获取 |
| **路径模板** | 图片上传的路径格式 | 默认 `wechat/{year}/{filename}`，支持 `{year}`、`{filename}` 占位符 |
| **公开访问 URL** | 图片的公开访问前缀 | 如果绑定了自定义域名填域名；否则填 Bucket 的公开访问地址 |

> [!note] GIF 和 SVG
> 选择 S3 模式时，GIF 和 SVG 图片仍保留微信原始链接，只有静态图片（jpg/png）会上传到 S3。

---

### 6. 配置 Telegram Bot

**路径**：设置 → Telegram Bot

配置后，你可以在 Telegram 中直接发送文章链接给 Bot，Bot 自动转换并同步到 Obsidian。

#### 6.1 获取 Bot Token

1. 在 Telegram 中搜索 [@BotFather](https://t.me/BotFather) 并发送 `/newbot`
2. 按提示输入 Bot 名称和用户名
3. 创建完成后 BotFather 会返回 Bot Token（格式如 `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

#### 6.2 获取你的 Chat ID

1. 在 Telegram 中搜索 @userinfobot
2. 向它发送任意消息
3. 它会回复你的 Chat ID（纯数字，如 `123456789`）

#### 6.3 选择连接模式

| 模式 | 原理 | 适合场景 |
| --- | --- | --- |
| **Webhook** | Telegram 主动推送消息到你的公网地址 | 有公网 HTTPS 地址、VPS 部署 |
| **Polling** | 服务每秒轮询 Telegram 获取新消息 | 本地运行、NAS 部署、无公网地址 |

> [!tip] 本地 / NAS 用户选 Polling
> 如果你的服务运行在本地或 NAS 上，没有公网 IP 或域名，选择 Polling 模式。不需要填写 Webhook 地址和 Secret。

#### 6.4 填写配置

| 配置项 | 说明 |
| --- | --- |
| **启用 Telegram Bot** | 勾选 |
| **转换完成后发送通知** | 勾选后 Bot 会回复转换结果（推荐开启） |
| **连接模式** | Webhook 或 Polling |
| **Bot Token** | 第 6.1 步获取的 Token |
| **Webhook Secret** | 自定义一个密钥（Polling 模式不需要） |
| **Webhook 公开地址** | 你的外网 HTTPS 地址（Polling 模式不需要） |
| **白名单 Chat ID** | 第 6.2 步获取的 Chat ID |

保存配置后，向你的 Bot 发送一个微信公众号文章链接测试。

---

### 7. 配置飞书 Bot

**路径**：设置 → 飞书 Bot

配置后，你可以在飞书中直接发送文章链接给 Bot。

#### 7.1 创建飞书自建应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)，登录后点击"创建应用"
2. 选择"企业自建应用"，填写应用名称
3. 进入应用详情页，开启"机器人"能力

#### 7.2 获取配置参数

| 参数 | 如何获取 |
| --- | --- |
| **App ID** | 应用详情页 → "凭证与基础信息" → App ID（格式如 `cli_xxx`） |
| **App Secret** | 同上页面，点击"显示"获取 |
| **Verification Token** | 应用详情页 → "事件订阅" → Verification Token |
| **Encrypt Key** | 应用详情页 → "事件订阅" → Encrypt Key |

#### 7.3 配置应用权限

在飞书开放平台的应用详情页 → "权限管理"中，搜索并开通以下权限：

- `im:message`（获取与发送单聊、群组消息）
- `im:message.p2p_msg:readonly`（读取私聊消息）

#### 7.4 选择连接模式

| 模式 | 原理 | 适合场景 |
| --- | --- | --- |
| **Webhook** | 飞书主动推送事件到你的公网地址 | 有公网 HTTPS 地址、VPS 部署 |
| **长连接** | 服务主动与飞书建立 WebSocket 连接 | 本地运行、NAS 部署、无公网地址 |

> [!tip] 本地 / NAS 用户选长连接
> 长连接模式不需要公网地址和 HTTPS，系统会自动在后台维持与飞书的连接。

#### 7.5 配置事件订阅

- **Webhook 模式**：在飞书开放平台 → "事件订阅"中，设置回调地址为 `https://你的域名/api/integrations/feishu/webhook`
- **长连接模式**：在飞书开放平台 → "事件订阅"中，选择"使用长连接接收事件"

#### 7.6 填写配置并测试

| 配置项 | 说明 |
| --- | --- |
| **启用飞书 Bot** | 勾选 |
| **转换完成后发送通知** | 勾选（推荐） |
| **连接模式** | Webhook 或长连接 |
| **App ID / App Secret** | 第 7.2 步获取 |
| **Verification Token / Encrypt Key** | 第 7.2 步获取（Webhook 模式需要） |
| **Webhook 公开地址** | 你的外网地址（长连接模式不需要） |
| **白名单 open_id** | 初次调试时留空即可 |

> [!tip] open_id 白名单的获取
> 白名单留空时任何人都可以使用 Bot。私聊 Bot 发送一条消息后，查看服务日志中的 `open_id=xxx`，将其填入白名单即可限制为仅自己使用。也可以在设置页点击"自动检测"获取。

保存后，在飞书中向你的 Bot 发送一条文章链接测试。

---

### 8. 配置 AI 润色

**路径**：设置 → AI 润色

AI 润色是可选功能，默认关闭。开启后可以为转换后的文章自动生成摘要、标签、Frontmatter 元数据和正文润色。

#### 8.1 理解三层 AI 能力

设置页有三个开关，它们不是三个同类功能，而是三层递进的处理：

| 层级 | 开关 | 效果 | 相关提示词 |
| --- | --- | --- | --- |
| **第一层** | 启用 AI 摘要与 Frontmatter | 生成 `summary`、`tags`、`my_understand`，写入 Frontmatter 和笔记顶部 | 解释器提示词 |
| **第二层** | 启用正文补充块生成 | 在第一层基础上额外生成 `body_polish`（一段 AI 补充说明），插入笔记中 | 解释器提示词（`body_polish` 部分） |
| **第三层** | 启用全文正文润色 | 额外发起一次 AI 调用，对整篇正文重新排版和润色 | 正文润色提示词 |

常见组合：

- **只想要摘要和标签**：只开启第一层
- **想要 AI 点评或理解**：开启第一层 + 第二层，确认正文模板中有 `{{body_polish}}`
- **想让正文也经过 AI 整理**：三层全部开启

> [!important] 第一层是总开关
> 如果关闭"启用 AI 摘要与 Frontmatter"，第二层和第三层都不会生效。

#### 8.2 配置 AI 提供商

系统内置了 6 个提供商预设，选择你已有 API Key 的服务商：

| 提供商 | 类型 | 需要 Base URL 吗 |
| --- | --- | --- |
| OpenAI Compatible | `openai_compatible` | 需要，填你的 API 地址 |
| Anthropic | `anthropic` | 不需要，已内置 |
| Gemini | `gemini` | 不需要，已内置 |
| Ollama | `ollama` | 不需要（默认 `http://127.0.0.1:11434`） |
| OpenRouter | `openrouter` | 不需要，已内置 |
| DeepSeek | `openai_compatible` | 需要，填 `https://api.deepseek.com` |

对于每个提供商，你需要填写：

- **显示名称**：随意起名，如 "我的 OpenAI"
- **Base URL**：API 地址（部分提供商已内置，不需要填）
- **API Key**：在你的 AI 服务商控制台生成

> [!tip] 如何获取 API Key
> 登录你的 AI 服务商控制台（如 [OpenAI](https://platform.openai.com/api-keys)、[Anthropic](https://console.anthropic.com/)），在 "API Keys" 页面创建新密钥。

#### 8.3 配置模型

在"模型池"中添加一个模型：

| 配置项 | 说明 | 示例 |
| --- | --- | --- |
| **显示名称** | 界面中显示的标签 | `GPT-4o` |
| **模型 ID** | 发送给 API 的实际模型标识 | `gpt-4o`、`claude-sonnet-4-20250514`、`deepseek-chat` |
| **绑定提供商** | 关联到上面配置的提供商 | 选择你刚创建的提供商 |

添加完成后，在"当前模型"下拉框中选中它。

#### 8.4 测试 AI 连通性

点击 **测试 AI 连通性** 按钮。系统会向当前配置的 AI 服务发送一个测试请求，如果配置正确会显示延迟和响应预览。

#### 8.5 自定义提示词（可选）

如果你需要自定义 AI 的输出格式，可以修改以下模板：

| 模板 | 作用 | 什么时候需要改 |
| --- | --- | --- |
| **解释器提示词** | 控制 AI 如何生成摘要、标签等 | 想改变 AI 的输出风格或增加字段 |
| **正文润色提示词** | 控制全文润色的规则 | 开启第三层后想定制润色风格 |
| **Frontmatter 模板** | 控制 YAML Frontmatter 格式 | 想增加或调整 Frontmatter 字段 |
| **正文模板** | 控制笔记正文的组织方式 | 想改变 AI 内容在笔记中的展示格式 |

模板中使用 `{{变量名}}` 占位符，如 `{{title}}`、`{{summary}}`、`{{tags}}`、`{{body_polish}}`、`{{content}}`。

#### 8.6 导入 Obsidian Web Clipper 模板（可选）

如果你已有 Obsidian Web Clipper 的 JSON 模板文件，可以粘贴到导入框，点击"解析并填充"一键映射为各项提示词模板。

---

### 9. 其他设置

#### 行为设置

**路径**：设置 → 行为设置

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| 成功后自动清理临时目录 | 转换成功后删除临时文件，失败的任务文件始终保留 | 启用 |
| 单次转换进程隔离 | 每篇文章在独立子进程中运行，防止单个任务卡死影响整体 | 启用 |
| 单次转换硬超时 | 单篇转换的最大运行时间 | 180 秒 |

> [!tip] 建议
> 保持默认值即可。如果文章内容特别复杂或网络较慢，可适当增大超时时间。

#### 设置导入导出

**路径**：设置 → 设置导入导出

- **导出**：将当前配置导出为 JSON 文件（敏感字段脱敏）
- **导入**：从 JSON 文件恢复配置（会覆盖当前设置）

适合迁移部署或备份配置时使用。

> [!warning] 导入会覆盖
> 导入前建议先导出备份。敏感字段（Token、Key 等）导入后需要重新填写。

#### 账户安全

**路径**：设置 → 账户安全

修改登录密码：输入当前密码 → 输入新密码 → 点击修改。

---

## 第三部分：日常使用

### 10. 手动转 Markdown

**路径**：转换中心（首页）

**单篇转换**：

1. 在输入框粘贴微信公众号文章链接
2. 可展开"高级选项"设置超时时间、是否保存 HTML 调试文件、是否启用 AI 润色
3. 点击"开始转换"

**批量转换**：

1. 切换到"批量转换"标签
2. 粘贴多个链接（每行一个），或上传包含链接的文件（支持 txt/md/csv）
3. 点击"开始批量转换"

页面顶部状态栏会显示 FNS 连接状态、Vault 名称、图片模式和 AI 功能状态。

### 11. 公众号自动同步

**路径**：同步来源

#### 扫码登录公众号后台

1. 点击"扫码登录"，用微信扫描弹出的二维码
2. 系统自动获取 Token 和 Cookie

> [!warning] 凭证有时效性
> 微信公众号后台凭证会过期，过期后需要重新扫码登录。

#### 搜索并添加公众号

输入公众号名称关键词 → 搜索 → 点击"添加同步源"。

#### 同步文章

- **首次/范围同步**：指定日期范围，批量拉取文章索引
- **增量同步**：仅拉取上次同步后的新文章

> [!note] 同步 ≠ 转换
> 同步只抓取文章元数据（标题、链接），不执行转换。转换需要在文章库中操作。

#### 全局同步计划

可配置每天或每周自动同步所有公众号来源（仅索引，不转换）。

### 12. 文章库管理

**路径**：文章库

文章库集中管理所有从公众号同步过来的文章索引。

- **筛选**：按公众号、处理状态（待处理/成功/失败）、入库状态、日期范围等筛选
- **批量操作**：全选后批量加入处理队列或删除
- **执行计划**：配置每天或每周自动处理未执行的文章（每次最多 20 篇）
- **执行记录**：点击"查看执行记录"查看单篇文章的所有转换历史

### 13. 主题搜索

**路径**：主题搜索

通过搜狗微信搜索按关键词查找公众号文章。搜索结果不会自动入库，需要你手动勾选后点击"批量入库"。

### 14. 任务历史

**路径**：任务历史

查看所有转换任务的状态、来源和触发方式。支持按状态（成功/失败/处理理中）和来源（手动/Bot/批量/计划）筛选。

失败的任务可以点击"重跑"重新执行。

> [!tip] 重跑前先检查
> 重跑失败任务前，建议先检查 FNS 连接和 AI 配置是否正常，避免因配置问题再次失败。

---

## 典型工作流

从零开始到日常使用的推荐流程：

```text
第一步：部署
  └─ Docker Compose 或一键脚本部署
  └─ 访问 http://IP:8765/login 登录
  └─ 修改默认密码

第二步：核心配置
  └─ 设置 → FNS 同步 → 填写 FNS 连接信息并验证
  └─ 设置 → 图片模式 → 选择图片处理方式

第三步：按需启用扩展
  └─ 设置 → AI 润色 → 配置 AI 服务商和模型
  └─ 设置 → Telegram Bot 或 飞书 Bot → 选择连接模式并配置
     （本地运行推荐 Polling / 长连接模式，无需公网地址）

第四步：开始使用
  └─ 转换中心 → 粘贴链接，开始转换
  └─ 同步来源 → 扫码登录，添加公众号，执行首次同步
  └─ 文章库 → 批量处理已同步的文章

第五步：日常使用
  └─ 通过 Telegram / 飞书 Bot 发送链接即时转换
  └─ 任务历史 → 查看状态，重跑失败任务
  └─ 文件自动同步到 Obsidian 指定目录
```
