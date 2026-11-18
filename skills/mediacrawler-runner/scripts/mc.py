#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""MediaCrawler runner — thin orchestrator around a user-installed MediaCrawler.

Interacts with MediaCrawler ONLY via subprocess CLI + output files.
No upstream code is bundled, imported, or modified here.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PLATFORMS = ["xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"]
DEPS = ["typer", "playwright", "aiofiles", "httpx"]

# Field alias candidates: first key present in the record wins.
POST_ALIASES = {
    "content_id": ["note_id", "aweme_id", "video_id"],
    "title": ["title"],
    "content": ["desc", "content"],
    "author_id": ["creator_hash", "user_id"],
    "author_name": ["nickname"],
    "publish_ts": ["time", "create_time", "publish_time"],
    "url": ["note_url", "aweme_url", "video_url", "content_url"],
    "likes": ["liked_count"],
    "collects": ["collected_count"],
    "comments": ["comment_count"],
    "shares": ["share_count"],
    "tags": ["tag_list"],
    "keyword": ["source_keyword"],
}
COMMENT_ALIASES = {
    "comment_id": ["comment_id", "cid"],
    "content_id": ["note_id", "aweme_id", "video_id"],
    "content": ["content"],
    "author_id": ["user_id"],
    "author_name": ["nickname"],
    "like_count": ["like_count", "liked_count"],
    "publish_ts": ["create_time", "time", "publish_time"],
}
# Keys copied into `extra` verbatim; the rest (bookkeeping) is dropped.
META_KEYS = {"add_ts", "last_modify_ts", "xsec_token"}


# ---------- locate ----------

def find_home(explicit: str = "") -> Path | None:
    cands: list[Path] = []
    if explicit:
        cands.append(Path(explicit))
    marker = Path(__file__).resolve().parent / ".mc_home"
    if marker.exists():
        cands.append(Path(marker.read_text(encoding="utf-8").strip()))
    env = os.environ.get("MEDIACRAWLER_HOME")
    if env:
        cands.append(Path(env))
    cwd = Path.cwd()
    cands += [cwd / "MediaCrawler", cwd.parent / "MediaCrawler", cwd]
    for p in list(cwd.parents)[:4]:
        cands += [p / "MediaCrawler", p]
    for c in cands:
        if (c / "main.py").exists() and (c / "cmd_arg").exists():
            return c.resolve()
    return None


def python_for(home: Path) -> str:
    sub = "Scripts" if os.name == "nt" else "bin"
    name = "python.exe" if os.name == "nt" else "python"
    py = home / ".venv" / sub / name
    return str(py) if py.exists() else sys.executable


def venv_layout(home: Path) -> str:
    if (home / ".venv" / "Scripts").exists():
        return "scripts"
    if (home / ".venv" / "bin").exists():
        return "bin"
    return "none"


def read_version(home: Path) -> str:
    py = home / "pyproject.toml"
    if py.exists():
        m = re.search(r'^version\s*=\s*"([^"]+)"', py.read_text(encoding="utf-8", errors="ignore"), re.M)
        if m:
            return m.group(1)
    return "unknown"


# ---------- check ----------

def cmd_check(args: argparse.Namespace) -> dict:
    home = find_home(args.home)
    out: dict = {"home": str(home) if home else None, "ok": False}
    if not home:
        return out
    py = python_for(home)
    missing = []
    for dep in DEPS:
        r = subprocess.run([py, "-c", f"import {dep}"], capture_output=True)
        if r.returncode != 0:
            missing.append(dep)
    layout = venv_layout(home)
    hint = ""
    if os.name == "nt" and layout == "bin":
        hint = "venv 为 Linux 布局（bin/），Windows 宿主无法直接使用；需在 WSL 内运行或重建 venv"
    out.update({
        "python": py,
        "version": read_version(home),
        "venv_layout": layout,
        "hint": hint,
        "missing_deps": missing,
        "data_dir": str(home / "data"),
        "ok": not missing,
    })
    return out


# ---------- setup ----------

HOST_SKILL_DIRS = ["~/.agents/skills", "~/.claude/skills", "~/.codex/skills"]
MARKER = Path(__file__).resolve().parent / ".mc_home"


def cmd_setup(args: argparse.Namespace) -> dict:
    repo_skills = Path(__file__).resolve().parent.parent.parent  # scripts/ -> mediacrawler-runner/ -> skills/
    if args.target:
        target = Path(args.target).expanduser().resolve()
    else:
        target = next((Path(c).expanduser() for c in HOST_SKILL_DIRS if Path(c).expanduser().is_dir()),
                      Path(HOST_SKILL_DIRS[0]).expanduser())
    installed = []
    for d in sorted(repo_skills.iterdir()):
        if (d / "SKILL.md").exists():
            dst = target / d.name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(d, dst)
            installed.append(d.name)

    home = find_home(args.home)
    action = "found"
    if home is None:
        if args.skip_install:
            action = "not-found (install skipped)"
        else:
            url = load_source_url("")
            dest = Path(args.home).resolve() if args.home else Path.cwd() / "MediaCrawler"
            print(f"[setup] cloning {url} -> {dest}", file=sys.stderr)
            r = subprocess.run(["git", "clone", url, str(dest)])
            if r.returncode == 0:
                py = python_for(dest)
                subprocess.run([py, "-m", "pip", "install", "-r", str(dest / "requirements.txt")], check=False)
                subprocess.run([py, "-m", "playwright", "install", "chromium"], cwd=dest, check=False)
                MARKER.write_text(str(dest), encoding="utf-8")
                home, action = dest, "installed"
            else:
                action = f"clone-failed(exit={r.returncode})"
    else:
        MARKER.write_text(str(home), encoding="utf-8")
    check = cmd_check(argparse.Namespace(home=str(home) if home else ""))
    hint = check.get("hint") or ("依赖缺失，按 SKILL.md 第 1 步补装" if check.get("missing_deps") else "")
    return {"skills": installed, "target": str(target), "mediacrawler": {
        "home": str(home) if home else None, "action": action,
        "ok": check.get("ok", False), "hint": hint}}


# ---------- install ----------

def load_source_url(explicit: str) -> str:
    if explicit:
        return explicit
    cfg = Path(__file__).resolve().parent.parent / "sources.json"
    if cfg.exists():
        return json.loads(cfg.read_text(encoding="utf-8"))["mediacrawler"]["url"]
    return "https://github.com/NanmiCoder/MediaCrawler"


def cmd_install(args: argparse.Namespace) -> int:
    url = load_source_url(args.source)
    dest = Path(args.home).resolve() if args.home else Path.cwd() / "MediaCrawler"
    if (dest / "main.py").exists():
        print(json.dumps({"status": "exists", "home": str(dest)}, ensure_ascii=False))
        return 0
    print(f"[install] cloning {url} -> {dest}", file=sys.stderr)
    r = subprocess.run(["git", "clone", url, str(dest)])
    if r.returncode != 0:
        return r.returncode
    py = python_for(dest)
    if args.with_deps:
        subprocess.run([py, "-m", "pip", "install", "-r", str(dest / "requirements.txt")], check=False)
        subprocess.run([py, "-m", "playwright", "install", "chromium"], cwd=dest, check=False)
    print(json.dumps({"status": "installed", "home": str(dest)}, ensure_ascii=False))
    return 0


# ---------- crawl ----------

def strbool(v: bool) -> str:
    return "true" if v else "false"


def cmd_crawl(args: argparse.Namespace) -> int:
    home = find_home(args.home)
    if not home:
        print("[crawl] MediaCrawler not found; run: python mc.py install", file=sys.stderr)
        return 2
    py = python_for(home)
    login = args.login
    headless = args.headless if args.headless is not None else (login != "qrcode")
    cmd = [
        py, "main.py",
        "--platform", args.platform,
        "--lt", login,
        "--type", args.type,
        "--keywords", args.keywords,
        "--save_data_option", "jsonl",
        "--crawler_max_notes_count", str(args.limit),
        "--get_comment", strbool(args.get_comment),
        "--get_sub_comment", strbool(args.sub_comment),
        "--get_media", "false",
        "--headless", strbool(headless),
    ]
    if args.cookies:
        cmd += ["--cookies", args.cookies]
    if args.specified_id:
        cmd += ["--specified_id", args.specified_id]
    if args.creator_id:
        cmd += ["--creator_id", args.creator_id]
    if args.dry_run:
        print(json.dumps({"dry_run": True, "cwd": str(home), "cmd": cmd}, ensure_ascii=False))
        return 0
    print(f"[crawl] {' '.join(cmd)}", file=sys.stderr)
    try:
        r = subprocess.run(cmd, cwd=home, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(f"[crawl] timeout after {args.timeout}s", file=sys.stderr)
        return 3
    if r.returncode != 0:
        return r.returncode
    if not args.no_normalize:
        return cmd_normalize(args)
    return 0


# ---------- normalize ----------

def parse_count(v) -> float | None:
    """'1.2万' -> 12000.0, '3亿' -> 3e8, '456' -> 456.0, None passes through."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    m = re.fullmatch(r"([\d.]+)\s*([万亿]?)", s)
    if not m:
        return None
    mult = {"": 1, "万": 1e4, "亿": 1e8}[m.group(2)]
    return float(m.group(1)) * mult


def to_iso(v) -> str | None:
    """Numeric epoch (s or ms) -> ISO 8601; strings pass through unchanged."""
    if v is None:
        return None
    if isinstance(v, str) and not v.isdigit():
        return v
    try:
        ts = float(v)
    except (TypeError, ValueError):
        return None
    if ts > 1e12:  # milliseconds
        ts /= 1000.0
    return datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def map_record(rec: dict, aliases: dict) -> tuple[dict | None, dict]:
    mapped, consumed = {}, set()
    for field, keys in aliases.items():
        for k in keys:
            if rec.get(k) not in (None, ""):
                mapped[field] = rec[k]
                consumed.add(k)
                break
    if not mapped.get("content_id"):
        return None, rec
    extra = {k: v for k, v in rec.items() if k not in consumed and k not in META_KEYS}
    return mapped, extra


def read_jsonl_dir(data_dir: Path, platform: str, item_type: str) -> list[dict]:
    recs: list[dict] = []
    for p in sorted((data_dir / platform / "jsonl").glob(f"*_{item_type}_*.jsonl")):
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line:
                try:
                    recs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return recs


def dedupe(recs: list[dict], key: str, prefer: str = "last_modify_ts") -> list[dict]:
    best: dict = {}
    for r in recs:
        k = r.get(key)
        if k is None:
            continue
        old = best.get(k)
        if old is None:
            best[k] = r
        elif (r.get(prefer) or 0) >= (old.get(prefer) or 0):
            best[k] = {**old, **r}  # newer record wins per-key, keeps fields it lacks
    return list(best.values())


def cmd_normalize(args: argparse.Namespace) -> int:
    home = find_home(args.home)
    data_dir = Path(args.data_dir).resolve() if args.data_dir else (home / "data" if home else Path("data"))
    out_dir = Path(args.out).resolve() if args.out else (data_dir / "normalized")
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")

    posts, comments = [], []
    for rec in read_jsonl_dir(data_dir, args.platform, "contents"):
        m, extra = map_record(rec, POST_ALIASES)
        if m is None:
            continue
        m.update({"platform": args.platform, "crawled_at": now, "extra": extra})
        posts.append(m)
    for rec in read_jsonl_dir(data_dir, args.platform, "comments"):
        m, extra = map_record(rec, COMMENT_ALIASES)
        if m is None:
            continue
        m.update({"platform": args.platform, "crawled_at": now, "extra": extra})
        comments.append(m)

    posts = dedupe(posts, "content_id")
    comments = dedupe(comments, "comment_id")
    for r in posts:
        r["likes"], r["collects"], r["comments"], r["shares"] = (
            parse_count(r.get(k)) for k in ("likes", "collects", "comments", "shares")
        )
        r["publish_time"] = to_iso(r.pop("publish_ts", None))
    for r in comments:
        r["like_count"] = parse_count(r.get("like_count"))
        r["publish_time"] = to_iso(r.pop("publish_ts", None))
    posts.sort(key=lambda r: r.get("publish_time") or "", reverse=True)
    comments.sort(key=lambda r: r.get("publish_time") or "", reverse=True)

    posts_path = out_dir / f"{args.platform}_posts.jsonl"
    comments_path = out_dir / f"{args.platform}_comments.jsonl"
    posts_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in posts) + ("\n" if posts else ""),
        encoding="utf-8",
    )
    comments_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in comments) + ("\n" if comments else ""),
        encoding="utf-8",
    )
    manifest = {
        "platform": args.platform,
        "data_dir": str(data_dir),
        "posts": len(posts),
        "comments": len(comments),
        "posts_file": str(posts_path),
        "comments_file": str(comments_path),
        "generated_at": now,
    }
    (out_dir / f"{args.platform}_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


# ---------- cli ----------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mc", description="MediaCrawler runner (black-box orchestrator)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check", help="locate MediaCrawler and check deps")
    p.add_argument("--home", default="", help="MediaCrawler path (else $MEDIACRAWLER_HOME / auto-search)")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("setup", help="one-shot: copy skills to host dir + locate/install MediaCrawler + check")
    p.add_argument("--target", default="", help="host skills dir (default: auto among ~/.agents/skills, ~/.claude/skills, ~/.codex/skills)")
    p.add_argument("--home", default="", help="MediaCrawler path (default ./MediaCrawler when installing)")
    p.add_argument("--skip-install", action="store_true", help="only copy skills and check, never clone")
    p.set_defaults(fn=cmd_setup)

    p = sub.add_parser("install", help="clone MediaCrawler from configured source URL")
    p.add_argument("--source", default="", help="git URL override (default: sources.json or upstream)")
    p.add_argument("--home", default="", help="target directory (default ./MediaCrawler)")
    p.add_argument("--with-deps", action="store_true", help="pip install -r requirements.txt + playwright chromium")
    p.set_defaults(fn=cmd_install)

    p = sub.add_parser("crawl", help="run a crawl then normalize output")
    p.add_argument("--platform", required=True, choices=PLATFORMS)
    p.add_argument("--keywords", default="")
    p.add_argument("--type", default="search", choices=["search", "detail", "creator"])
    p.add_argument("--limit", type=int, default=20, help="max posts (--crawler_max_notes_count)")
    p.add_argument("--get-comment", action="store_true")
    p.add_argument("--sub-comment", action="store_true")
    p.add_argument("--login", default="qrcode", choices=["qrcode", "phone", "cookie"])
    p.add_argument("--cookies", default="", help="cookie string for --login cookie")
    p.add_argument("--headless", type=int, choices=[0, 1], default=None, help="default: 0 for qrcode login, 1 otherwise")
    p.add_argument("--specified_id", default="", help="detail mode: ids/urls comma separated")
    p.add_argument("--creator_id", default="", help="creator mode: ids/urls comma separated")
    p.add_argument("--timeout", type=int, default=3600)
    p.add_argument("--home", default="")
    p.add_argument("--data-dir", default="", help="override data dir for normalize")
    p.add_argument("--out", default="", help="normalize output dir (default <data>/normalized)")
    p.add_argument("--dry-run", action="store_true", help="print command, do not run")
    p.add_argument("--no-normalize", action="store_true")
    p.set_defaults(fn=cmd_crawl)

    p = sub.add_parser("normalize", help="convert MediaCrawler jsonl output to standard schema")
    p.add_argument("--platform", required=True, choices=PLATFORMS)
    p.add_argument("--home", default="")
    p.add_argument("--data-dir", default="")
    p.add_argument("--out", default="")
    p.set_defaults(fn=cmd_normalize)

    args = ap.parse_args(argv)
    result = args.fn(args)
    if args.cmd == "check":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    if args.cmd == "setup":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["mediacrawler"]["ok"] or result["mediacrawler"]["action"] == "not-found (install skipped)" else 1
    return int(result)


if __name__ == "__main__":
    sys.exit(main())
