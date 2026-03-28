# 我删了 Cursor！转 Gemini CLI 这一周，手搓 11 个应用，从 3D 到全栈商业项目，太强了！

作者: 轻踩油门

就在上周，我做了一个挺疯狂的决定：我把电脑里的`Cursor`删了。

`Cursor`虽好，但`Gemini CLI`每天 **1000** 次免费 + **Gemini 3 Pro** 的速度，才是真正的 '**生产力自由**'。

说实话，作为 **AI** 编程独立开发者，我对工具挺挑剔的。刚入门那会儿我也对`Cursor`爱不释手，`VScode`布局、模型多、提示词也聪明。但用久了总觉得差点意思，要么额度卡脖子，要么任务执行慢得像老头遛弯。

直到我换上了谷歌开源的`Gemini CLI`。

![image](https://lulalula.eu.org/i/2026/03/28/829d53015ccca788fe71da6615e3af78.webp)

这玩意儿接入了最新的 **Gemini 3 Pro**，不仅界面简洁、速度飞快，更像是一个自带 **1000** 次免费额度的全栈外挂。这一周，我用它一口气手搓了十几个应用，从 3D 建模到商用系统全覆盖，完成度高到离谱。

# 一、实战开发案例集

废话不多说，我把近期用它手搓的几个小应用分享出来，大家看看这个完成度，是不是很魔幻。

## 01 | 审美觉醒 - 3D 建模类

以前搞 3D 景观，你得学建模、学渲染，没个一年半载根本做不出来。现在？我一句话丢给 Gemini CLI，它直接给你吐出一堆让你惊艳的 3D 微缩景观。

### 埃菲尔铁塔（写实）

一个超写实的埃菲尔铁塔 3D 等轴测缩微景观，写实风的悬浮地层感，逻辑非常严密。

![image](https://lulalula.eu.org/i/2026/03/28/08c2c035853647e3d92fdacf0ca5f6c1.webp)

![image](https://mmbiz.qpic.cn/mmbiz_gif/fuwVhPovjMLNVzlIPkGDohYTxlffsnjoGnibnDo6WKgD4u549ibMLkXgl2EJRGHrKNbm1vVvLibqxVoBOkibmac6eA/640?wx_fmt=gif&from=appmsg)

### 麦当劳店（Q版）

超萌的Q版麦当劳，还有上下两层，细节拉满。

![image](https://lulalula.eu.org/i/2026/03/28/5e8fbab6874d5a400ea052ce36760d9d.webp)

![image](https://mmbiz.qpic.cn/mmbiz_gif/fuwVhPovjMLNVzlIPkGDohYTxlffsnjonvS0Cq3zp8hbTozXs2mdaEcsXdGFpfG0U7icWibkb5wxQzVekndC5bOQ/640?wx_fmt=gif&from=appmsg)

### 北京天坛（泥版）

泥土风格的北京天坛，也是 Gemini CLI 用代码捏出来的。

![image](https://lulalula.eu.org/i/2026/03/28/48aeda946d63736bb74278fbd1dd0c2c.webp)

![image](https://mmbiz.qpic.cn/mmbiz_gif/fuwVhPovjMLNVzlIPkGDohYTxlffsnjokJGGjJxdCJGE6e5zDeFnwibbLLK8DDsmls5YFugtKVibnIgS9ZEicP4Pw/640?wx_fmt=gif&from=appmsg)

看着这效果，我心疼以前那些熬夜画模型的兄弟们 **3** 秒。

## 02 | 效率飙升 - 小工具/网站类

很多人问我：AI 编程能落地吗？能解决实际问题吗？看看我做的几个练手小项目。

### 书法练习网

给书法爱好者做的，电脑上就能练。

![image](https://lulalula.eu.org/i/2026/03/28/c17a0338e4ef156033ce161ca45f08b8.webp)

### 小学生口算神器

四位数乘法自动生成，专治各种不服。

![image](https://lulalula.eu.org/i/2026/03/28/43b7addb6dbf27e6ac1811b06aa42742.webp)

### 个人笔记站

我让它设计了 '**浅色**' 和 '**深色**' 两个版本。那个深色版的质感，真的绝了，已经达到专业设计师水准。

浅色版

![image](https://lulalula.eu.org/i/2026/03/28/d324cc3800582f7e2e757ffe29c43836.webp)

深色版

![image](https://lulalula.eu.org/i/2026/03/28/53cf11bac6cccfa3808f1ba2cf98d098.webp)

## 03 | 商业级实战 - 全栈系统

如果说上面的还只是一些玩具，那接下来的就是 '**商业级项目**' 了。 我尝试让它用 `Python` + `Flask` 做全栈一体化开发，整出了几套企业内直接能跑的系统。

### 会议预约系统

支持注册登录和 '**用户/管理员**' 权限分离。建会议室、选时间、存数据，一气呵成。

登录页 - 支持用户和管理员登录

![image](https://lulalula.eu.org/i/2026/03/28/a90d5d3c01dcb50368b9f1dfeb962edd.webp)

用户预订页面 - 用户可选择会议室、会议时间进行预约

![image](https://lulalula.eu.org/i/2026/03/28/d86733d407090660fd74a9751f1dc3a1.webp)

管理员后台页面 - 支持会议室管理、会议管理

![image](https://lulalula.eu.org/i/2026/03/28/1ec975ee5955e5e8e6dd5573ecc8df46.webp)

### 小米风格管理系统

我跟 `Gemini CLI` 说 '**要小米那种极简风**'，它反手就给我接通了 API 数据看板。

这审美和逻辑，真不像是个编程工具，更像是个小米资深产品经理的作品。

登录页 - 用户登录页

![image](https://lulalula.eu.org/i/2026/03/28/fdd0ec11003f3d382812108d8bc940e7.webp)

服务页 - 用户自主服务

![image](https://lulalula.eu.org/i/2026/03/28/d8312a81db6d6522a73b077cc1d85026.webp)

管理页 - 数据看板和设备管理页面

![image](https://lulalula.eu.org/i/2026/03/28/dbf84b552b99b7ef9b531583a19f9769.webp)

## 04 | 商业级实战 - 复杂工作流

最让我震撼的是，它还能处理那种 '**前后端分离**' 的复杂活儿。

### wechat2feishu（公众号转飞书）

这是一个实打实的工具，能把 '**公众号文章**' 一键转存 '**飞书文档**'，不仅能永久存储，还自带版本迭代记录（Changelog）。

![image](https://lulalula.eu.org/i/2026/03/28/6c14f7fc1a46ec715afb58e1df95bc65.webp)

热门转存列表

![image](https://lulalula.eu.org/i/2026/03/28/424bef7ebc0c12cc52b8624d41ddbdf7.webp)

迭代记录

![image](https://lulalula.eu.org/i/2026/03/28/0221a6c91d46bf297fc91326306e0089.webp)

### AI 写作工作流

更离谱的是这个 'AI写作工作流'，只要给个主题，它自己去调研、还会跟我讨论选题、然后自己生成、自己校对。我就站边上，看它表演就行。

AI写作首页

![image](https://lulalula.eu.org/i/2026/03/28/1995c2e6468f2421edb05cc09b17072f.webp)

新建写作

![image](https://lulalula.eu.org/i/2026/03/28/4b98dcdcfbfef3de32b839e0ffcee58e.webp)

调研与撰写

![image](https://lulalula.eu.org/i/2026/03/28/9795ad0f8d849412d8bd95bbf27fd025.webp)

略过校验和手动编辑，成品输出

![image](https://lulalula.eu.org/i/2026/03/28/431cce4f5bbbc0c6162a7620704a7f71.webp)

### 小红书图卡生成器

这个工具，简直是运营人的 '**救命稻草**'。

以前做一张小红书图卡，你要先在本地写文案，再上网找模版，最后手动复制粘贴、调整对齐，半小时能出一张图就不错了。

我让 Gemini CLI 搓出来的这个生成器，把这个流程缩短到了 **10** 秒：

文稿一键导入。直接丢进去原始文档，AI自动识别标题、金句、正文和图片。

![image](https://lulalula.eu.org/i/2026/03/28/3386feea3110feacdd87e1cc4442b851.webp)

实时预览。点击 '**预览内容**'，图卡瞬间生成。左边改文字、右边变效果。

![image](https://lulalula.eu.org/i/2026/03/28/d11174975cfb4211d75d674f38dac4a4.webp)

多风格切换。提供多种主题风格，不满意？点一下风格卡，背景、配色、字体一秒切换。

![image](https://lulalula.eu.org/i/2026/03/28/dc86f5563e240b76eef31a92bddd02fb.webp)

确认没问题后，点击 '**批量下载**'整套图卡直接下载到本地，秒发小红书、朋友圈。

我最喜欢它的一点在于：如果对生成的图卡不满意，随时可以回退编辑。这种后悔药机制，比用AI生图爽太多了。

## 05 | 写在最后

写到这，我其实挺感慨的。以前我们学编程，像是自己在搬砖，一砖一瓦都得自己扛。而现在Gemini CLI，更像给你配了一个7x24小时的资深开发工程师，它负责把逻辑填满，你负责把脑洞开大。

我们再也不用去请美工、求开发，只要你有想法，这个命令行工具就能帮你把想法变成现实。

AI 时代，不要再去卷体力了，去卷 '**想象力**' 吧。

---

原文链接: [https://mp.weixin.qq.com/s/5y3FlGXMssN1Jx49QzWW7Q](https://mp.weixin.qq.com/s/5y3FlGXMssN1Jx49QzWW7Q)
