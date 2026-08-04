#!/usr/bin/env python3
"""Subagent 运行状态采集器 → subagent-status.json

数据源（只读）：
  1. ~/.reasonix/projects/*/sessions/*/goal-state.json  — 每个会话的 status + todos
  2. ps 抓取运行中的 reasonix subagent run 进程
  3. worktrees/coach-lab/docs/P0-*.md 等产物 mtime
输出：/home/sysmex/worktrees/ai-shifu-dev/docker/subagent-status.json
"""
import json, os, re, subprocess, time
from pathlib import Path

HOME = Path.home()
STATUS_OUT = Path("/home/sysmex/worktrees/ai-shifu-dev/docker/subagent-status.json")
PROJECTS = HOME / ".reasonix" / "projects"
DOCS_DIRS = [
    Path("/home/sysmex/worktrees/coach-lab/docs"),
    Path("/home/sysmex/worktrees/ai-shifu-dev/docs/design-docs"),
]

def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")

def get_running_subagents() -> list:
    """ps 抓 reasonix subagent run 进程"""
    out = subprocess.run(
        ["ps", "aux"], capture_output=True, text=True, timeout=5
    ).stdout
    running = []
    for line in out.splitlines():
        if "reasonix subagent run" in line or "reasonix subagent" in line and "grep" not in line:
            parts = line.split()
            if len(parts) >= 11:
                running.append({
                    "pid": parts[1],
                    "cpu": parts[2],
                    "mem": parts[3],
                    "start": parts[8],
                    "cmd": " ".join(parts[10:14]),
                })
    return running

def collect_sessions() -> list:
    sessions = []
    if not PROJECTS.exists():
        return sessions
    for proj in PROJECTS.iterdir():
        sess_dir = proj / "sessions"
        if not sess_dir.is_dir():
            continue
        for gs in sorted(sess_dir.glob("*.goal-state.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:6]:
            d = gs.parent
            try:
                data = json.loads(gs.read_text())
            except Exception:
                continue
            # 会话身份：meta 文件名
            meta = None
            for f in d.glob("*.meta"):
                try:
                    meta = json.loads(f.read_text())
                except Exception:
                    pass
                break
            sessions.append({
                "dir": d.name,
                "status": data.get("status", "unknown"),
                "todos": data.get("todos", []),
                "model": (meta or {}).get("model", ""),
                "updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(gs.stat().st_mtime)),
            })
    return sessions

def collect_artifacts() -> list:
    arts = []
    for d in DOCS_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("P0-*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:6]:
            arts.append({
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size,
                "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime)),
            })
    return arts

def main():
    status = {
        "generated_at": now(),
        "running_subagents": get_running_subagents(),
        "sessions": collect_sessions(),
        "artifacts": collect_artifacts(),
    }
    STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2))
    print(f"✅ {STATUS_OUT} ({len(status['running_subagents'])} running, {len(status['sessions'])} sessions, {len(status['artifacts'])} artifacts)")

if __name__ == "__main__":
    main()

if __name__ == "__main__" and os.environ.get("SUBAGENT_CRON") == "1":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
