---
name: kol-screening
description: KOL/达人筛选分析。当用户要求筛选博主、找达人、评估创作者、做投放名单时使用。输入为 mediacrawler-runner 产出的标准化 posts jsonl（建议含 --type creator 或同一批作者多篇内容）。
---

# kol-screening

> ⚠️ 仅供学习研究使用，禁止用于商业用途；采集合规见 mediacrawler-runner 的「前置与合规」。

输入：`<platform>_posts.jsonl`（schema 见 mediacrawler-runner 的「输出契约」）。
方法：临时 Python 脚本（json 标准库）计算，用完即删。
互动公式（与其他分析 skill 统一）：`engagement = likes + collects*2 + comments*3`。

## 数据要求

候选作者 ≥ 10 人且每人 ≥ 3 篇内容。数据不够时：先回到 mediacrawler-runner，用 `--type creator --creator_id <作者主页URL,...>` 补采，或加大关键词搜索的 `--limit`。不足则停下，不出名单。

## 已知边界

schema 无粉丝数与阅读量字段（平台不下发），无法计算传统互动率（ER）。`ponytail:` 用「篇均互动 + 发文稳定性」替代排名；接入粉丝数 API 后升级。

## 步骤

### 1. 建作者画像

按 `author_id` 分组：篇均 engagement、engagement 中位数、发文量、代表作（url+数字）。过滤发文量 < 3 的作者进观察池，不进主名单。
完成判据：主名单作者每人 4 个数字齐全。

### 2. 排名与分层

1. 主名单按篇均 engagement 降序，分三档：头部（Top 10%）、腰部（次 30%）、潜力（其余，看 engagement 中位数高但波动小的作者）
2. 每档给出：典型 `tags`/`keyword` 聚类（该作者发什么）、更新频率（`publish_time` 间隔中位数）
3. 风险标记：互动全靠单篇（单篇 > 篇均 5 倍）、`author_name` 无法脱敏核对、内容与目标品类不符

### 3. 出名单

输出 `<out>/kol_list_<platform>.md`：筛选条件回顾 → 分层名单表（作者/篇均互动/发文量/标签/代表作 url）→ 风险标记 → 建议（按预算档位给 Top N 组合）。
完成判据：名单落盘，每位作者的数字可追溯到第 1 步画像；报告中不尝试通过 author_id 反查真实身份。
