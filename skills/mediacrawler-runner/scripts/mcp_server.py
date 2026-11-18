#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""MCP stdio adapter for mediacrawler-runner. Thin wrapper: every tool shells out to mc.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

MC = [sys.executable, str(Path(__file__).resolve().with_name("mc.py"))]
mcp = FastMCP("mediacrawler-runner", instructions="MediaCrawler 采集编排：check/install/crawl/normalize。仅限学习研究用途。")


def _run(args: list[str]) -> str:
    r = subprocess.run(MC + args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3900)
    out = r.stdout.strip() or r.stderr.strip()
    return f"exit={r.returncode}\n{out}"


@mcp.tool()
def mc_check(home: str = "") -> str:
    """定位 MediaCrawler 安装并检查依赖。返回 JSON：home/python/version/missing_deps/ok。"""
    return _run(["check", "--home", home])


@mcp.tool()
def mc_install(source: str = "", home: str = "", with_deps: bool = True) -> str:
    """从 sources.json 或指定 git URL 克隆 MediaCrawler，可选安装依赖与 chromium。"""
    args = ["install", "--source", source, "--home", home]
    if with_deps:
        args.append("--with-deps")
    return _run(args)


@mcp.tool()
def mc_crawl(
    platform: str,
    keywords: str = "",
    type: str = "search",
    limit: int = 20,
    get_comment: bool = False,
    sub_comment: bool = False,
    login: str = "qrcode",
    cookies: str = "",
    specified_id: str = "",
    creator_id: str = "",
    timeout: int = 3600,
    home: str = "",
    out: str = "",
) -> str:
    """执行一次采集并自动归一化。首次登录需用户在浏览器窗口扫码。platform: xhs|dy|ks|bili|wb|tieba|zhihu。"""
    args = ["crawl", "--platform", platform, "--keywords", keywords, "--type", type,
            "--limit", str(limit), "--login", login, "--timeout", str(timeout),
            "--home", home, "--out", out]
    if get_comment:
        args.append("--get-comment")
    if sub_comment:
        args.append("--sub-comment")
    if cookies:
        args += ["--cookies", cookies]
    if specified_id:
        args += ["--specified_id", specified_id]
    if creator_id:
        args += ["--creator_id", creator_id]
    return _run(args)


@mcp.tool()
def mc_normalize(platform: str, data_dir: str = "", out: str = "", home: str = "") -> str:
    """把 MediaCrawler jsonl 输出转成标准 schema（posts/comments/manifest）。"""
    return _run(["normalize", "--platform", platform, "--data-dir", data_dir, "--out", out, "--home", home])


if __name__ == "__main__":
    mcp.run()
