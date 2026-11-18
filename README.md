<div align="center">

# 🕷️ mediacrawler-skills

**让 AI Agent 一句话完成「社媒数据采集 → 场景化分析报告」的开源技能集**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-%E5%B0%8F%E7%BA%A2%E4%B9%A6%20%7C%20%E6%8A%96%E9%9F%B3%20%7C%20%E5%BF%AB%E6%89%8B%20%7C%20B%E7%AB%99%20%7C%20%E5%BE%AE%E5%8D%9A%20%7C%20%E8%B4%B4%E5%90%A7%20%7C%20%E7%9F%A5%E4%B9%8E-ff69b4.svg)](#-功能特性)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#-贡献)
[![MCP](https://img.shields.io/badge/MCP-%E6%94%AF%E6%8C%81-9cf.svg)](#-两种接入方式)

*English | [中文](#readme)*

</div>

---

> **⚠️ 免责声明（请务必阅读）**
>
> 大家请以**学习为目的**使用本仓库 ⚠️⚠️⚠️⚠️（[爬虫违法违规的案件](https://github.com/HiddenStrawberry/Crawler_Illegal_Cases_In_China)）。
>
> 本仓库的所有内容仅供学习和研究之用，**禁止用于商业用途**。任何人或组织不得将本仓库的内容用于非法用途或侵犯他人合法权益。本仓库所涉及的数据采集技术仅用于小规模、公开内容的学习研究，不得用于大规模爬虫、干扰平台运营或其他非法行为。使用者应自行遵守目标平台的使用条款、《数据安全法》《个人信息保护法》等法律法规，因使用本仓库内容而引起的任何法律责任由使用者自行承担，本仓库不承担任何责任。**使用本仓库的内容即表示您同意本免责声明的所有条款和条件。**

---

## 📖 目录

- [项目简介](#-项目简介)
- [功能特性](#-功能特性)
- [架构设计](#-架构设计)
- [快速开始](#-快速开始)
- [两种接入方式](#-两种接入方式)
- [数据契约](#-数据契约)
- [常见问题](#-常见问题)
- [赞赏支持](#-赞赏支持)
- [贡献](#-贡献)
- [License](#-license)
- [致谢](#-致谢)

## 📖 项目简介

`mediacrawler-skills` 是一套面向 AI Agent（Claude Code / Cursor / Trae / 任何支持 skills 或 MCP 的宿主）的开源技能集：

- **mediacrawler-runner**：把 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 封装成 AI 可直接驱动的采集编排技能（检测环境 → 安装 → 采集 → 数据归一化）
- **5 个场景分析技能**：市场分析、爆文拆解、达人筛选、品牌监测、电商选品——输入标准化数据，输出带数字依据的分析报告

**核心设计**：本仓库与 MediaCrawler 严格保持黑盒边界——只通过命令行调用和输出文件交互，**不包含、不导入、不修改 MediaCrawler 代码**。MediaCrawler 由用户自行安装（默认从 [luolin1024/MediaCrawler](https://github.com/luolin1024/MediaCrawler) 获取）。

```text
用户一句话需求
   │
   ▼
┌─────────────────────┐     subprocess CLI     ┌──────────────┐
│ mediacrawler-runner  │ ─────────────────────▶ │  MediaCrawler │  (用户自装)
│  check→install→crawl │ ◀───────────────────── │  jsonl 输出   │
└─────────┬───────────┘      读取输出文件       └──────────────┘
          │ normalize → 标准 schema (posts/comments jsonl)
          ▼
┌─────────────────────────────────────────────────┐
│ market-analysis / content-strategy /            │
│ kol-screening / brand-monitoring /              │
│ product-selection                               │
│        → 带数字依据的分析报告 (.md)               │
└─────────────────────────────────────────────────┘
```

## ✨ 功能特性

| Skill | 用途 | 输出 |
|---|---|---|
| 🕷️ `mediacrawler-runner` | 环境检测 / 自动安装 / 采集编排 / 数据归一化 | 标准 jsonl + manifest |
| 📈 `market-analysis` | 市场/竞品分析：热门内容、互动基准、机会点 | 六节分析报告 |
| 🔥 `content-strategy` | 爆文拆解：爆款线、共性五维、内容策略建议 | 策略报告 |
| 🧑‍🎤 `kol-screening` | 达人筛选：篇均互动分层、风险标记、投放名单 | 分层名单 |
| 📢 `brand-monitoring` | 品牌声量、负面监测、竞品对比、趋势环比 | 舆情报告 |
| 🛒 `product-selection` | 电商选品：品类热度、需求信号、候选清单 | 选品报告 |

**runner 特性**：

- ✅ 7 平台支持：小红书 / 抖音 / 快手 / B站 / 微博 / 贴吧 / 知乎
- ✅ 数据归一化：跨平台字段别名映射（`note_id`/`aweme_id`/`video_id` → `content_id`）、中文计数解析（`"1.2万"` → `25000`）、毫秒时间戳 → ISO 8601
- ✅ 增量去重：同 ID 多次采集按键合并，新值覆盖旧值、不丢字段
- ✅ 隐私脱敏：依赖脱敏版 MediaCrawler（作者 ID 匿名化、昵称打码），分析层不还原个人身份
- ✅ 双接入：CLI 直调（零依赖）/ MCP stdio server
- ✅ 幂等安装：`sources.json` 可配置下载源，`--with-deps` 一键装依赖 + chromium

## 🏗️ 架构设计

三条边界规则，保证本仓库可以干净地以 Apache-2.0 开源：

1. **进程边界**：只允许 `subprocess` 调用 MediaCrawler 的 `main.py`，永不 import 其模块（调用 ≠ 衍生，import = 衍生）
2. **文件边界**：不打包、不复制、不修改任何上游文件；配置由脚本生成，输出按官方文件规律解析
3. **责任边界**：登录态、账号、平台条款合规由用户自担；本仓库文档持续引导合规使用

分析层与采集层通过一份 **schema 契约**解耦（见下文），上游输出格式变化只需改 `normalize` 一处。

## 🚀 快速开始

### 🗣️ 一句话安装（推荐，WorkBuddy / Codex / Claude Code 通用）

把本仓库下载到本地，然后**对你的 AI 助手说一句话**：

> 帮我安装 mediacrawler-skills：进入仓库目录运行 `python skills/mediacrawler-runner/scripts/mc.py setup`，装完把检查结果告诉我。

AI 会自动完成全部四步：拷贝 6 个技能到宿主技能目录 → 定位/克隆 MediaCrawler → 安装 Python 依赖和浏览器内核 → 输出 JSON 检查报告（含遗留问题提示）。

<details>
<summary><b>手动安装（不用 AI）</b></summary>

```bash
python skills/mediacrawler-runner/scripts/mc.py setup   # 拷技能 + 克隆 MediaCrawler + 装依赖，可重复执行
# 只拷技能不装 MediaCrawler：加 --skip-install；指定宿主目录：--target <dir>
```
</details>

### 🗣️ 一句话使用

装好后直接说人话，AI 按 SKILL.md 自动走完整个流程：

| 你说 | AI 自动做 |
|---|---|
| 「帮我采集小红书"咖啡"和"露营"各 20 篇笔记，带评论」 | check → 采集（首次会让你扫码）→ 归一化 |
| 「用刚采的数据做爆文拆解」 | content-strategy → 爆款共性 + 策略报告 |
| 「这批数据里筛一下值得投的达人」 | kol-screening → 分层名单 |
| 「监测我们品牌和竞品 A 的声量与负面」 | brand-monitoring → 舆情报告 |
| 「"防晒"品类出一份选品分析」 | product-selection → 选品报告 |
| 「出一份咖啡市场的竞品分析」 | market-analysis → 六节报告 |

> 💡 **WorkBuddy / Codex 用户**：如果宿主没有 skills 机制，直接说「**阅读 `skills/mediacrawler-runner/SKILL.md` 并严格按其执行**」即可——每个 SKILL.md 本身就是写给 AI 看的执行手册，不依赖任何宿主的技能加载功能。

## 🤖 两种接入方式

**1. 直接调用（默认）**：Agent 按 `SKILL.md` 运行 `mc.py` 子命令，零额外依赖。

**2. MCP Server**：宿主支持 MCP 时运行：

```bash
python skills/mediacrawler-runner/scripts/mcp_server.py   # stdio
# 工具：mc_check / mc_install / mc_crawl / mc_normalize
```

示例 prompt（装好 skills 后对 AI 说）：

> 用 mediacrawler-runner 采集小红书上「防晒」相关笔记 30 条含评论，然后用 product-selection 出一份选品分析报告。

## 📊 数据契约

`<platform>_posts.jsonl` 每行一条（完整字段见 [runner SKILL.md](skills/mediacrawler-runner/SKILL.md)）：

```json
{"platform": "xhs", "content_id": "...", "title": "...", "content": "...",
 "author_id": "匿名哈希", "publish_time": "2025-01-01T12:00:00",
 "url": "...", "likes": 123, "collects": 45, "comments": 6, "shares": 7,
 "tags": "话题1,话题2", "keyword": "搜索词", "crawled_at": "...", "extra": {}}
```

所有分析 skill 统一互动公式：`engagement = likes + collects*2 + comments*3`。

## ❓ 常见问题

<details>
<summary><b>可以商用吗？</b></summary>
不可以。本仓库免责声明与上游 MediaCrawler 许可证（非商业学习使用许可证）均禁止商用。请以学习研究为目的小规模使用。
</details>

<details>
<summary><b>数据合规吗？</b></summary>
只做公开内容、小规模采集，登录态由用户本人提供。请自行评估并遵守目标平台条款与当地法律法规。
</details>

<details>
<summary><b>为什么不让 AI 直接 import MediaCrawler？</b></summary>
import 即构成衍生作品，会让本仓库无法以 Apache-2.0 干净开源。进程边界 + 文件边界是刻意的架构决策。
</details>

<details>
<summary><b>采集失败提示 CDP / 9222 端口？</b></summary>
默认 CDP 模式需在 Chrome 地址栏打开 <code>chrome://inspect/#remote-debugging</code> 勾选 Allow remote debugging；或在 MediaCrawler 的 <code>config/base_config.py</code> 设 <code>ENABLE_CDP_MODE = False</code> 改用 Playwright 扫码。
</details>

## 💰 赞赏支持

开源维护不易，如果这个项目对你有帮助，欢迎请作者喝杯咖啡 ☕

<div align="center">

| 支付宝 | 微信 |
|:---:|:---:|
| <img src="docs/reward_alipay.jpg" width="260"/> | <img src="docs/reward_wechat.jpg" width="260"/> |

</div>

## 🤝 贡献

欢迎 PR！提 bug 请附 `mc.py check` 与 `--dry-run` 的完整输出。新分析 skill 请复用现有 schema 契约与互动公式，数据门槛不满足时必须停在采集侧而不是硬编报告。

## 📄 License

- 本仓库代码：[Apache-2.0](LICENSE)
- 上游 MediaCrawler：非商业学习使用许可证 1.1（仅限学习研究，商用需其作者书面授权），由用户自行安装并承担遵守责任

## ⭐ 致谢

- [NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) —— 核心采集能力来源，感谢原作者的开源贡献
- [luolin1024/MediaCrawler](https://github.com/luolin1024/MediaCrawler) —— 默认安装源（含脱敏改造与 WebUI）
