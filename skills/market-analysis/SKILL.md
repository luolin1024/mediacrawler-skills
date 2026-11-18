---
name: market-analysis
description: 分析 mediacrawler-runner 产出的标准化社媒数据（posts/comments jsonl），产出市场分析报告：热门内容、关键词话题、互动基准、竞品对比。当用户要求分析采集到的社媒数据、出市场/竞品/内容分析报告时使用。
---

# market-analysis

> ⚠️ 仅供学习研究使用，禁止用于商业用途；采集合规见 mediacrawler-runner 的「前置与合规」。

输入：`mediacrawler-runner` 产出的 `<platform>_posts.jsonl` / `<platform>_comments.jsonl` / `_manifest.json`。
方法：用临时 Python 脚本（json 标准库即可，量大于 10 万行再考虑 pandas）读数据、算指标；脚本用完即删，不进仓库。

## 步骤

### 1. 读数据并画像

读 manifest + 两个 jsonl，先报告：条数、时间跨度、关键词分布、缺失字段比例。
完成判据：确认数据量足以分析（posts ≥ 10）；不足则停下，告知用户补采（回到 mediacrawler-runner skill 加大 `--limit` 或加关键词），不硬编报告。

### 2. 计算核心指标

逐项计算，每项给出具体数字：
1. 热门内容：按 `likes+collects*2+comments*3` 加权互动 Top 10（列出 title/url/互动拆解）
2. 互动基准：likes/comments/shares 的中位数与 P90 —— 中位数代表"正常水平"，P90 代表"爆款门槛"
3. 关键词与话题：`tags` 词频 Top 20；`keyword` 分组对比各组互动中位数
4. 发布节奏：`publish_time` 按小时/星期分布，找互动峰值时段
5. 竞品模式（多关键词采集时）：各关键词在内容量、互动、标签上的差异

### 3. 写报告

输出 `<out>/<platform>_market_report.md`，固定六节：
概览 → 热门内容 → 关键词与话题 → 互动基准 → 内容机会（未被满足的话题/时段/形式）→ 建议动作（最多 5 条，每条带依据数字）。
完成判据：报告落盘，六节齐全，每个结论都能追溯到第 2 步的具体数字；无数字支撑的判断删掉。

## 规则

- 只陈述数据支持的结论；样本不足的维度明确写"样本不足"，不脑补。
- 竞品对比基于公开内容互动数据，不下"对方造假/买量"类断言。
- 数据含脱敏作者信息（author_id 为匿名哈希），报告中不尝试还原个人身份。
