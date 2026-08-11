#!/usr/bin/env python3
"""Subagent 运行状态采集器 → subagent-status.json

数据源（只读）：
  1. ~/.reasonix/projects/*/sessions/*/goal-state.json  — 每个会话的 status + todos
  2. ps 抓取运行中的 reasonix subagent run 进程
  3. worktrees/coach-lab/docs 等 P0-/TRAINING-LOOP-/ARCHITECTURE-DECISION-/REPORT/FIX 产物 mtime
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
    """最近会话：以 .meta 文件为会话标识（实时 updated_at + preview），
    todos/status 从 goal-state.json 补充（该文件是会话封存产物，非实时，存在才显示）。"""
    sessions = []
    if not PROJECTS.exists():
        return sessions
    for proj in PROJECTS.iterdir():
        sess_dir = proj / "sessions"
        if not sess_dir.is_dir():
            continue
        for meta_f in sess_dir.glob("*.meta"):
            try:
                meta = json.loads(meta_f.read_text())
            except Exception:
                continue
            sid = meta.get("id") or meta_f.name[: -len(".jsonl.meta")]
            gs = sess_dir / f"{sid}.goal-state.json"
            todos, status = [], ""
            try:
                g = json.loads(gs.read_text())
                todos = g.get("todos", [])
                status = g.get("status", "")
            except Exception:
                pass
            updated = meta.get("updated_at", "")
            updated = updated[:16].replace("T", " ") if updated else ""
            sessions.append({
                "dir": sid,
                "preview": meta.get("preview", ""),
                "status": status,
                "todos": todos,
                "model": meta.get("model", ""),
                "turns": meta.get("turns", ""),
                "updated": updated,
                "mtime": meta_f.stat().st_mtime,
            })
    sessions.sort(key=lambda s: s["mtime"], reverse=True)
    return sessions[:6]

# 采集的产物 glob 模式（显式白名单，避免 *DESIGN* 等过宽匹配拉全量文档）
ARTIFACT_PATTERNS = (
    "P0-*.md",
    "TRAINING-LOOP-*.md",
    "ARCHITECTURE-DECISION-*.md",
    "*-REPORT*.md",
    "*-FIX*.md",
)
ARTIFACT_LIMIT = 8

def collect_artifacts() -> list:
    arts = []
    seen = set()
    for d in DOCS_DIRS:
        if not d.exists():
            continue
        for pat in ARTIFACT_PATTERNS:
            for f in d.glob(pat):
                if f in seen:  # 同一文件可能命中多个模式（如 BATCH234-FIX-REPORT.md）
                    continue
                seen.add(f)
                st = f.stat()
                arts.append({
                    "name": f.name,
                    "path": str(f),
                    "size": st.st_size,
                    "_ts": st.st_mtime,
                })
    arts.sort(key=lambda a: a["_ts"], reverse=True)
    return [{
        "name": a["name"],
        "path": a["path"],
        "size": a["size"],
        "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(a["_ts"])),
    } for a in arts[:ARTIFACT_LIMIT]]


def file_title(content: str) -> str:
    """从任务文件内容提取标题：取第一个 Markdown 标题行，去掉 # 与可选「任务」前缀。"""
    for ln in content.splitlines():
        ln = ln.strip()
        if ln.startswith("#"):
            t = re.sub(r"^#+\s*", "", ln).strip()
            t = re.sub(r"^任务[:：]?\s*", "", t)
            return t[:60]
    return ""


def extract_task(cmd: str, task_files: dict = None) -> str:
    """从 Pi 的 run 命令提取任务标题。

    优先级：
      1. `$(cat /tmp/xxx.md)` → 会话 heredoc 缓存 → 文件系统 → 回退文件名
      2. 内联双引号参数（如 "审查 docs/... 写入 docs/...md"）→ 取第一个句子，超长截断
    task_files: {/tmp/xxx.md: 文件内容}，从会话 heredoc 命令恢复（/tmp 可能已被清理）。
    """
    TMP_TASK = re.compile(r"\$\(cat (/tmp/[a-z0-9-]+\.md)\)")
    m = TMP_TASK.search(cmd)
    if m:
        fn = m.group(1)
        content = (task_files or {}).get(fn)
        if content:
            title = file_title(content)
            if title:
                return title
        p = Path(fn)
        if p.exists():
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                title = file_title(text)
                if title:
                    return title
            except Exception:
                pass
        return f"cat {fn}"
    q = re.search(r'"([^"]{10,})"', cmd)
    if q:
        t = q.group(1).strip()
        head = re.split(r"[，。；\n]", t)[0].strip()
        if not head:
            head = t
        return head[:60] + ("…" if len(head) > 60 else "")
    return ""


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
            # 先扫描本会话的 heredoc 命令，恢复任务文件内容（/tmp 可能已被清理）
            task_files = {}
            heredoc_re = re.compile(r"cat > (/tmp/[a-z0-9-]+\.md) << 'EOF'\n(.*?)\nEOF", re.S)
            for line in open(f, encoding="utf-8", errors="ignore"):
                try:
                    d0 = json.loads(line)
                except Exception:
                    continue
                for c0 in d0.get("message", {}).get("content", []):
                    if c0.get("type") == "toolCall" and c0.get("name") == "bash":
                        cmd0 = c0.get("arguments", {}).get("command", "")
                        for hm in heredoc_re.finditer(cmd0):
                            task_files[hm.group(1)] = hm.group(2)
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
                                "task": extract_task(cmd, task_files),
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
