# 真超级省钱！把 Jina 注入 OpenCode ，Token 消耗暴跌 196 倍，抓网页成本几乎为 0！

作者: 外星人.瓜瓜

你没有看错，今天要介绍的这个工具，你用和不用，`Token` 消耗差异 **196** 倍。

我有一个 **AI** 写作工作流，每次我给到主题，**AI** 自动调研的时候，丢给它一个 URL，动辄得消耗几万个 Token，肉疼，根本用不起！

我原本以为是技术局限，也没特别注意，直到我最近发现了 **Jina MCP**。

现在，同样的调研抓网页， `Token` 消耗不到原来的 **1%！**

不夸张，实测案例说话。

## 01 | 数据说话：AI Agent 的省钱保姆

我分别用 `Playwright` 和 `jina` 获取同一个网页信息，`Playwright` 的 `token` 消耗 是 `Jina` 的 **196** 倍。

![image](https://lulalula.eu.org/i/2026/03/28/ac9e2accafb2da26360b357c25b22a37.webp)

### 1、关键实测数据：

- Playwright 消耗，约 170,310 tokens
- Jina 消耗，仅约 868 tokens
- Playwright 消耗是 Jina 的 **196** 倍
- 使用 jina 可节省 **99.49%** 的 token 消耗，实际节省 169,442 tokens

实测结论很明确了，使用 Jina MCP 抓取网页内容，几乎只需要消耗原来 1% 的 token。

#### 2、快速探明原因：

① 常规的网页抓取方式，会将大量无用的 `HTML` 标签一并抓取回来。

② Jina 会过滤掉这些无用的 `HTML` 标签，仅保留有效信息，并 `Markdown` 格式输出。

## 02 | 极速配置：让 Agent 光速接入 Jina

这事儿根本不用亲自动手，直接让 AI 自己搞起来。

### 第 1 步，安装Jina MCP

#### 方式 1：让 AI 帮我们安装（推荐）

在对话框输入指令，AI 会自动下载远程 MCP 并完成初始化。安装好后，还让 AI 帮配置上 API Key。

![image](https://lulalula.eu.org/i/2026/03/28/a0f61b09393cf44700cc8ebfcc0ee091.webp)

Jina MCP 安装成功

![image](https://lulalula.eu.org/i/2026/03/28/fd90cd9df606836d71878e4f93f7607e.webp)

##### 方式 2：手动配置（可选）

如果你非要手动配，也不是不可以。

打开 ~/.config/opencode/opencode.json，复制粘贴下面 json 代码：

```text
},
  "mcpServers": {
    "jina-ai": {
      "url": "https://mcp.jina.ai/sse",
      "headers": {
        "Authorization": "Bearer ${JINA_API_KEY}"
      }
    }
```

#### 第 2 步，获取和配置 Jina API Key

访问 jina 官网（https://jina.ai/reader） ，获取一个免费的 API key，直接复制。

![image](https://lulalula.eu.org/i/2026/03/28/27a37b51d49f1686657056e4d8fbf086.webp)

通知 `opencode`，给大哥配上

![image](https://lulalula.eu.org/i/2026/03/28/3fddc490156fbc81ba53c971d7cdef6d.webp)

重启 `opencode` 生效。

#### 第 3 步，校验安装配置成功？

以下两种方式都能校验，你高兴就行，任选。

##### 方式 1：输入 `/mcps` 命令，查看已安装的 MCP 列表

![image](https://lulalula.eu.org/i/2026/03/28/2ec3df59afbefb081037147c16282e67.webp)

##### 方式 2：输入`!`，切换到命令执行模式，直接敲下面的命令

```text
opencode mcp list
```

![image](https://lulalula.eu.org/i/2026/03/28/e07b70e4e70b1ed85e0cfb29df06281a.webp)

补关键的一句：

默认免费的 Jina API Key，提供个1000万的免费token用量。用完了，你再考虑花不花钱的事，先薅一波再说。

## 03 | 实战：从 “乱七八糟” 到 “极度舒适”

以小龙虾官网为例，让我们看看 Agent 视角下的差异。

### 1、人类肉眼看到的

这是浏览器里，我们肉眼看到的信息，整体是很清爽的，阅读起来也没什么障碍。

![image](https://lulalula.eu.org/i/2026/03/28/6c54f4c50bd2037e866d301ff85fae14.webp)

#### 2、Agent 看到的

这是 AI Agent 在执行调研任务，抓取你指定网页时，它看到的信息。

![image](https://lulalula.eu.org/i/2026/03/28/3af5e2815e37a7e5e95ed9a57f52853d.webp)

为了方便演示，我在提示词里，强制约束不使用 Jina，执行网页信息抓取。

![image](https://lulalula.eu.org/i/2026/03/28/467401ccf6f639693ab585dc23c5f0e4.webp)

这是传统的使用 `Playwright` 抓取 `URL` 的内容，返回原始 `HTML`，这些对我们来说都是无效信息，还需额外耗费 token 解析。

![image](https://lulalula.eu.org/i/2026/03/28/d3571e8d6744b9e6a179da9bbf408ac2.webp)

#### 3、Jina 化腐朽为神奇

调用 Jina 后，Agent 看到的信息，是清洗后的 Markdown 文本。干干净净，是真真实实的帮你省下99%的 token 开销。

![image](https://lulalula.eu.org/i/2026/03/28/7c38f18c27d2512550541aade79942ef.webp)

#### Token 消耗对比总结

再来直观的对比下，两者对 token 消耗的影响，一目了然。

![image](https://lulalula.eu.org/i/2026/03/28/a3dfc58847ed5168bdfe0db3146a6e2e.webp)

## 04 | 快速给个结论

使用 Jina MCP 抓取相同 URL 网页内容：

- Token 消耗减少约 196 倍
- 直接返回结构化的 Markdown，无需额外解析
- 更适合 LLM 直接处理和理解

结论很清晰，对于静态文档类网站，Jina MCP 是相当高效。

## 05 | 写在最后

Jina 这类工具跟普通的工具定位不同，出身就不是直接服务于人类的，而是服务于智能体（Agnet）。

在网页抓取这个场景下，帮你自动过滤网页无用 `HTML` 标签，将非结构化网页转化为 LLM 最易读的 Markdown，从源头降低推理成本。

没什么好说的了，抓紧去试试吧！

最后，帮大家罗列下，Jina MCP 的主要功能，方便你继续往下挖更有价值的使用场景。

![image](https://lulalula.eu.org/i/2026/03/28/ce7949f7749ce78b6809fdc563bf6cf5.webp)

---

原文链接: [https://mp.weixin.qq.com/s/eUTi02-J4Xu-a5MBwtHA8g](https://mp.weixin.qq.com/s/eUTi02-J4Xu-a5MBwtHA8g)
