---
name: brand-monitoring
description: 品牌声量与舆情监测。当用户要求监测品牌声量、看负面评价、对比竞品声量、出舆情报告时使用。输入为 mediacrawler-runner 产出的标准化 posts/comments jsonl；趋势需要多次采集的日期目录。
---

# brand-monitoring

> ⚠️ 仅供学习研究使用，禁止用于商业用途；采集合规见 mediacrawler-runner 的「前置与合规」。

输入：`<platform>_posts.jsonl` + `<platform>_comments.jsonl`（schema 见 mediacrawler-runner 的「输出契约」）。
方法：临时 Python 脚本（json 标准库）计算，用完即删。

## 数据要求

1. 单次基线：每个监测词 posts ≥ 20。监测词用 mediacrawler-runner 分批采集（`--keywords` 一次一组）。
2. 趋势：≥ 2 个日期目录。归一化时按日期分目录保存：`mc.py normalize --out <data>/normalized/<YYYY-MM-DD>`，本 skill 对比相邻目录。

## 步骤

### 1. 定监测词与负面对象

和用户确认：品牌词、竞品词、产品词清单；负面判定词表（默认起步：质量差、退货、投诉、假货、骗、翻车、避雷，用户可增删）。
完成判据：词表经用户确认后落定，后续步骤引用。

### 2. 单次声量画像

按 `keyword` 分组计算：声量（posts 数）、声量份额占比、互动中位数（engagement = likes + collects*2 + comments*3）、负面内容数与占比（title+content 命中负面词表）。评论区单独算：`comments.content` 命中负面词表的条数与高赞负面（like_count Top 10，列原文摘录）。
完成判据：每个监测词 5 个数字齐全；负面判定只报命中数与摘录，不猜测动机。

### 3. 趋势（有 ≥2 个日期目录才做）

对比相邻目录：声量环比、负面占比环比、新增高互动负面清单。无第二目录则此节写「待下次采集对比」。

### 4. 出报告

输出 `<out>/brand_monitor_<platform>_<date>.md`：监测范围 → 声量份额表 → 负面清单（原文摘录 + url）→ 趋势 → 建议（≤3 条：需回应的负面、需关注的竞品动作）。
完成判据：报告落盘，全部结论可追溯到第 2/3 步数字；数据不足的维度明确写「样本不足」。
