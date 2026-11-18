---
name: product-selection
description: 电商选品与品类趋势分析。当用户要求选品、看品类趋势、分析产品热度、评估带货内容表现时使用。输入为 mediacrawler-runner 产出的标准化 posts jsonl（小红书/抖音场景最优）。
---

# product-selection

> ⚠️ 仅供学习研究使用，禁止用于商业用途；采集合规见 mediacrawler-runner 的「前置与合规」。

输入：`<platform>_posts.jsonl` + 可选 `<platform>_comments.jsonl`（schema 见 mediacrawler-runner 的「输出契约」）。
方法：临时 Python 脚本（json 标准库）计算，用完即删。
互动公式（与其他分析 skill 统一）：`engagement = likes + collects*2 + comments*3`。选品场景 collects（收藏=种草意向）权重已内置。

## 数据要求

目标品类关键词 ≥ 3 个且 posts 合计 ≥ 50。品类词清单先与用户确认（如「防晒」拆成：防晒霜/防晒喷雾/硬防晒）。不足则停下要求补采。

## 已知边界

数据来自内容互动，不是成交数据。`ponytail:` 用「种草热度」近似需求信号，成交验证需接入电商数据源后升级——报告中明确写这个局限。

## 步骤

### 1. 品类热度盘点

按 `keyword` 分组：内容量、互动中位数、爆款率（engagement ≥ P90 的占比）、近 30/90 天内容量趋势（按 `publish_time`）。
完成判据：每个关键词 5 个数字齐全。

### 2. 信号挖掘

1. 需求信号：`tags` 词频 Top 20 + `content` 高频名词（规格/场景/痛点词），标出增速最快的新词
2. 意向强度：collects/comments 比值高的关键词 = 收藏型需求（比价/囤货倾向）；comments 高 = 讨论型需求（科普/对比需求）
3. 价格带线索：`content` 中出现的价格数字分布（有则报，无则写「无价格信号」）
4. 痛点与差评（有 comments 时）：命中负面词的评论摘录 Top 10——竞品差评即机会点

### 3. 出选品报告

输出 `<out>/selection_<category>.md`：品类热度表 → 需求信号 → 候选清单（≤5 个，每个挂：热度数字、意向类型、竞品差评机会）→ 风险（数据局限声明 + 季节性提示）。
完成判据：报告落盘，候选全部可追溯到第 1/2 步数字；「种草热度 ≠ 成交」的局限声明必须出现在报告里。
