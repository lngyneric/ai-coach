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
PI_SESSIONS = HOME / ".pi" / "agent" / "sessions"
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


def collect_pi_subagent_calls(running_map: dict) -> list:
    """解析 Pi 会话 jsonl 中 nohup reasonix subagent run 的启动记录。

    Pi 用 `nohup reasonix subagent run <name> ... &` 启动 subagent（无 PID 回显），
    这里用「启动时间戳 HH:MM」与 ps 进程启动时间做匹配，推断该次拉起的
    subagent 是否仍在运行（running）还是已完成/休眠（done）。
    running_map: {pid: "HH:MM"}
    """
    calls = []
    if not PI_SESSIONS.exists():
        return calls
    latest = sorted(PI_SESSIONS.glob("*/*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:1]
    for f in latest:
        try:
            for line in open(f, encoding="utf-8", errors="ignore"):
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                ts = d.get("timestamp", "")
                msg = d.get("message", {})
                for c in msg.get("content", []):
                    if c.get("type") == "toolCall" and c.get("name") == "bash":
                        cmd = c.get("arguments", {}).get("command", "")
                        if "reasonix subagent run" in cmd and "nohup" in cmd:
                            m = re.search(r"reasonix subagent run ([a-z0-9-]+)", cmd)
                            name = m.group(1) if m else "?"
                            hhmm = ts[11:16] if len(ts) >= 16 else ""
                            # 匹配运行中的进程（同 HH:MM 且命令含 name）
                            matched = None
                            for pid, (pstart, pcmd) in running_map.items():
                                if pstart == hhmm and name in pcmd:
                                    matched = pid
                                    break
                            calls.append({
                                "ts": ts[:16],
                                "subagent": name,
                                "status": "running" if matched else "done",
                                "pid": matched or "",
                                "cmd": " ".join(cmd.split())[:150],
                            })
        except Exception:
            continue
    return calls


def main():
    running_map = {}
    for r in get_running_subagents():
        running_map[r["pid"]] = (r["start"], r["cmd"])
    status = {
        "generated_at": now(),
        "running_subagents": list(running_map.values() and [{
            "pid": pid, "start": start, "cmd": cmd,
        } for pid, (start, cmd) in running_map.items()]),
        "sessions": collect_sessions(),
        "artifacts": collect_artifacts(),
        "pi_subagent_calls": collect_pi_subagent_calls(running_map),
    }
    STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2))
    print(f"✅ {STATUS_OUT} ({len(status['running_subagents'])} running, {len(status['sessions'])} sessions, {len(status['artifacts'])} arts, {len(status['pi_subagent_calls'])} pi calls)")

if __name__ == "__main__":
    main()
