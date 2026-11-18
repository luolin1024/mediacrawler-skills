---
name: mediacrawler-runner
description: 采集社交平台公开内容数据（小红书/抖音/快手/B站/微博/贴吧/知乎），输出标准化 jsonl 供分析。当用户要求抓取/采集/拉取社媒数据、跑爬虫、更新数据集时使用。仅限学习研究用途，遵守目标平台条款。
---

# mediacrawler-runner

> ⚠️ 仅供学习研究使用，禁止用于商业用途；使用者自行遵守目标平台条款与法律法规。

薄封装：通过 subprocess 调用用户自行安装的 MediaCrawler，再把输出归一化。
本 skill 不包含、不导入、不修改 MediaCrawler 代码。

## 前置与合规（每次执行前自查）

1. 小规模、公开内容、学习研究用途；控制条数（默认 ≤20），不加大多账号/高频采集。
2. 登录态（扫码/cookie）由用户本人提供并自担账号责任；AI 不索要、不存储密码。
3. 未安装 MediaCrawler 时，第 1 步会给出安装路径；仅从 `sources.json` 配置的 URL 下载。

## 步骤

> 用户要求"安装整个技能包"时：运行 `python scripts/mc.py setup`（自动拷贝全部技能到宿主目录 + 定位/克隆 MediaCrawler + 装依赖），把 JSON 结果解读给用户。

### 1. 环境检查

```bash
python scripts/mc.py check --home <MediaCrawler路径>
```

完成判据：JSON 输出 `"ok": true`。
- `"home": null` → 执行 `python scripts/mc.py install [--source <URL>] --with-deps`，或让用户指定已有安装路径。
- `missing_deps` 非空 → 在该环境补装依赖：`<home>/.venv/Scripts/python -m pip install -r <home>/requirements.txt && <home>/.venv/Scripts/python -m playwright install chromium`（Windows；Linux/macOS 用 `bin/python`）。
- 都通过 → 进入第 2 步。

### 2. 采集

```bash
python scripts/mc.py crawl --platform xhs --keywords "关键词1,关键词2" --limit 20 --get-comment
```

- `--platform`：xhs | dy | ks | bili | wb | tieba | zhihu
- `--type search` 关键词搜索（默认）；`--type detail --specified_id <id,url,...>` 指定内容；`--type creator --creator_id <...>` 指定作者
- 首次登录：默认 `--lt qrcode`；安装源默认 CDP 模式（连接用户已有 Chrome），首次使用需用户在 Chrome 地址栏打开 `chrome://inspect/#remote-debugging` 勾选 **Allow remote debugging**；报错含 CDP/9222 时提示此操作，或建议在 `config/base_config.py` 设 `ENABLE_CDP_MODE = False` 改走 Playwright 扫码。已有 cookie 可 `--login cookie --cookies "..."`（cookie 由用户在终端提供，不写入任何文件）
- 完成判据：进程退出码 0，且 stdout 有 manifest（posts/comments 计数 > 0）
- 退出码 2 = 未找到安装；3 = 超时（调大 `--timeout` 或减小 `--limit`）

### 3. 归一化（crawl 已自动执行，可单独重跑）

```bash
python scripts/mc.py normalize --platform xhs [--data-dir <dir>] [--out <dir>]
```

完成判据：manifest 中 `posts_file` / `comments_file` 存在且行数与计数一致。

## 输出契约（skill B 依赖，勿随意改动）

`<out>/<platform>_posts.jsonl` 每行一条：

```json
{"platform": "xhs", "content_id": "...", "title": "...", "content": "...",
 "author_id": "...", "author_name": "...", "publish_time": "2025-01-01T12:00:00",
 "url": "...", "likes": 123, "collects": 4, "comments": 5, "shares": 6,
 "tags": "话题1,话题2", "keyword": "搜索词", "crawled_at": "...", "extra": {}}
```

`<platform>_comments.jsonl`：`comment_id, content_id, content, author_id, author_name, like_count, publish_time, crawled_at, extra`。
上游未映射字段全部保留在 `extra`；`<platform>_manifest.json` 记录来源与计数。

## MCP 模式

宿主支持 MCP 时，用 `scripts/mcp_server.py`（stdio）替代直接调脚本，工具名：`mc_check` / `mc_install` / `mc_crawl` / `mc_normalize`，参数同上。
