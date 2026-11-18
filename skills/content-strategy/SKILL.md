---
name: content-strategy
description: 爆文拆解与内容策略分析。当用户要求拆解爆款内容、分析什么内容火、制定内容策略、给发布时间/标签/标题建议时使用。输入为 mediacrawler-runner 产出的标准化 posts jsonl。
---

# content-strategy

> ⚠️ 仅供学习研究使用，禁止用于商业用途；采集合规见 mediacrawler-runner 的「前置与合规」。

输入：`<platform>_posts.jsonl`（schema 见 mediacrawler-runner 的「输出契约」）。
方法：临时 Python 脚本（json 标准库）计算，用完即删。
互动公式（与其他分析 skill 统一）：`engagement = likes + collects*2 + comments*3`。

## 数据要求

posts ≥ 30 且跨 ≥ 2 个关键词，样本不足则停下要求补采（加大 `--limit` 或加关键词），不硬编结论。

## 步骤

### 1. 定义爆款线

计算 engagement 的 P90 与中位数；engagement ≥ P90 记为爆款，中位数记为普通内容基线。
完成判据：两个数字落定并写进后续每一节引用。

### 2. 拆解爆款共性

爆款组 vs 普通组逐维对比，每维给出两组的具体数字：
1. 标题模式：长度分布、高频开头词/数字型标题占比
2. 标签：`tags` 词频对比，爆款独有标签清单
3. 发布时间：`publish_time` 按小时/星期的互动中位数分布
4. 内容类型：`extra.type`（视频/图文）在两组的占比
5. 互动结构：爆款互动中 comments 占比 vs collects 占比（评论驱动 vs 收藏驱动）

### 3. 出策略建议

输出 `<out>/content_strategy_<platform>.md`，四节：爆款定义与基线 → 爆款共性（5 维数字）→ 机会缺口（普通内容里表现好但未成爆款的模式）→ 建议（≤5 条，每条挂依据数字，含：发什么、什么时间发、带什么标签、用什么形式）。
完成判据：报告落盘，建议全部可追溯到第 2 步数字；无数字支撑的句子删除。
