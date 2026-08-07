#!/usr/bin/env python3
"""segmentation-eval.py — 医学垂类分解 L3 反馈闭环：课节 × 指标 × 质量分

对 learn_progress_records 按 (shifu_bid, outline_item_bid) 聚合，输出
segmentation-eval.tsv：完成率 / 卡课率 / 质量分，用于强化学习 reward signal，
卡课率高的课节标记「分解不佳」→ 建议重新分段（衔接 L1 垂类分段规则）。

用法（直连 MySQL，需 pymysql）：
    python3 scripts/segmentation-eval.py --dsn "mysql://root:ai-shifu@ai-shifu-mysql-dev:3306/ai-shifu_dev?charset=utf8mb4" \
        --out segmentation-eval.tsv [--min-users 2] [--stick-penalty 1.0]

也可以只传 --dsn 用环境变量默认；质量分公式可配置：
    quality_score = round(100 * completion_rate - 100 * stick_rate * STICK_PENALTY)
    grade: >= GOOD_THRESHOLD → good（分解良好）；>= FAIR_THRESHOLD → fair；else poor（分解不佳）

输出列：
    shifu_bid / shifu_title / outline_item_bid / outline_title / item_type(chapter|lesson)
    parent_title / position / total_users / completed / in_progress / not_started / reset
    completion_rate / stick_rate / quality_score / grade / remark
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# ── 质量分公式参数（可配置）──────────────────────────────
STICK_PENALTY = 1.0        # 卡课率的惩罚权重（越大越强调卡课）
GOOD_THRESHOLD = 60.0      # >= 该分 → good（分解良好）
FAIR_THRESHOLD = 0.0       # >= 该分 → fair；< 该分 → poor（分解不佳）
MAX_GRADE_USERS = 0        # 保留：> 0 时用户数低于该值的课节 grade 标记 low_sample（默认 0=不启用）

# ── 状态码（与 flaskr/service/order/consts.py 一致）──────
STATUS_NOT_STARTED = 601
STATUS_IN_PROGRESS = 602
STATUS_COMPLETED = 603
STATUS_RESET = 608

# outline item type
TYPE_CHAPTER = "chapter"   # parent_bid == ""
TYPE_LESSON = "lesson"     # parent_bid != ""

UNTITLED_TITLES = {"", "Untitled Chapter", "Untitled Lesson", "未命名章节", "未命名课节"}


def _connect(pymysql, dsn: str):
    import urllib.parse

    # dsn: mysql://user:pass@host:port/db?charset=utf8mb4
    rest = dsn[len("mysql://"):]
    cred_host, _, dbpart = rest.rpartition("/")
    query = ""
    if "?" in dbpart:
        dbpart, query = dbpart.split("?", 1)
    params = dict(urllib.parse.parse_qsl(query))
    charset = params.get("charset", "utf8mb4")
    if "@" in cred_host:
        cred, host = cred_host.rsplit("@", 1)
        user, _, password = cred.partition(":")
    else:
        host, user, password = cred_host, os.environ.get("SEG_EVAL_DB_USER", "root"), ""
    if ":" in host:
        host, _, port = host.rpartition(":")
    else:
        port = 3306
    return pymysql.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=dbpart,
        charset=charset,
        autocommit=True,
    )


def _load_outline(cur) -> Dict[Tuple[str, str], dict]:
    """(shifu_bid, outline_item_bid) → 元信息（title 优先非 Untitled，parent_title / position / is_lesson）"""
    cur.execute(
        """
        SELECT shifu_bid, outline_item_bid, title, parent_bid, position
        FROM shifu_published_outline_items
        WHERE deleted = 0
        """
    )
    item_map: Dict[Tuple[str, str], dict] = {}
    parent_title_map: Dict[Tuple[str, str], str] = {}
    for shifu_bid, item_bid, title, parent_bid, position in cur.fetchall():
        key = (shifu_bid, item_bid)
        entry = item_map.setdefault(
            key,
            {
                "title": "",
                "parent_bid": parent_bid,
                "position": position,
                "is_lesson": bool(parent_bid),
            },
        )
        # 优先保留非 Untitled 标题
        if title and title not in UNTITLED_TITLES and not entry["title"]:
            entry["title"] = title
        # 收集父项（章节）自身的标题
        if not parent_bid and title and title not in UNTITLED_TITLES:
            parent_title_map[key] = title

    # 回填父标题（用父项自身的标题）
    for key, entry in item_map.items():
        if entry["parent_bid"]:
            entry["parent_title"] = parent_title_map.get(
                (key[0], entry["parent_bid"]), ""
            )
        else:
            entry["parent_title"] = ""
    return item_map


def _load_course_titles(cur) -> Dict[str, str]:
    cur.execute(
        """
        SELECT shifu_bid, title FROM shifu_published_shifus WHERE deleted = 0
        """
    )
    return {row[0]: row[1] for row in cur.fetchall()}


def _load_progress(cur) -> Dict[Tuple[str, str, str], List[int]]:
    """(shifu_bid, outline_item_bid, user_bid) → 状态历史（按 updated_at/id 升序）"""
    cur.execute(
        """
        SELECT shifu_bid, outline_item_bid, user_bid, status, updated_at
        FROM learn_progress_records
        WHERE deleted = 0
        ORDER BY shifu_bid, outline_item_bid, user_bid, updated_at ASC, id ASC
        """
    )
    rows: Dict[Tuple[str, str, str], List[int]] = defaultdict(list)
    for shifu_bid, item_bid, user_bid, status, _updated_at in cur.fetchall():
        rows[(shifu_bid, item_bid, user_bid)].append(int(status))
    return rows


def _grade(score: float, total_users: int) -> str:
    if MAX_GRADE_USERS and total_users < MAX_GRADE_USERS:
        return "low_sample"
    if score >= GOOD_THRESHOLD:
        return "good"
    if score >= FAIR_THRESHOLD:
        return "fair"
    return "poor"


def _remark(grade: str, stick_rate: float, is_lesson: bool) -> str:
    parts = []
    if grade == "poor":
        parts.append("分解不佳，建议重新分段（衔接 L1 垂类分段规则）")
    elif grade == "fair" and stick_rate >= 0.5:
        parts.append("卡课偏高，建议检查课节粒度/顺序")
    if not is_lesson:
        parts.append("章节聚合（非叶子课节）")
    return "；".join(parts)


def build_rows(dsn: str) -> List[dict]:
    import pymysql

    conn = _connect(pymysql, dsn)
    try:
        with conn.cursor() as cur:
            item_map = _load_outline(cur)
            course_titles = _load_course_titles(cur)
            progress = _load_progress(cur)
    finally:
        conn.close()

    # 按 (shifu, item) 聚合：取每个用户的最新状态
    agg: Dict[Tuple[str, str], Dict[str, int]] = defaultdict(
        lambda: {"completed": 0, "in_progress": 0, "not_started": 0, "reset": 0, "total": 0}
    )
    for (shifu_bid, item_bid, _user_bid), statuses in progress.items():
        latest = statuses[-1]
        stat = agg[(shifu_bid, item_bid)]
        stat["total"] += 1
        if latest == STATUS_COMPLETED:
            stat["completed"] += 1
        elif latest == STATUS_IN_PROGRESS:
            stat["in_progress"] += 1
        elif latest == STATUS_NOT_STARTED:
            stat["not_started"] += 1
        elif latest == STATUS_RESET:
            stat["reset"] += 1

    rows: List[dict] = []
    for (shifu_bid, item_bid), stat in sorted(
        agg.items(), key=lambda kv: (-kv[1]["total"], kv[0])
    ):
        total = stat["total"]
        completion_rate = stat["completed"] / total if total else 0.0
        stick_rate = stat["in_progress"] / total if total else 0.0
        score = round(
            100.0 * completion_rate - 100.0 * stick_rate * STICK_PENALTY, 1
        )
        meta = item_map.get((shifu_bid, item_bid), {})
        rows.append(
            {
                "shifu_bid": shifu_bid,
                "shifu_title": course_titles.get(shifu_bid, ""),
                "outline_item_bid": item_bid,
                "outline_title": meta.get("title", ""),
                "item_type": TYPE_LESSON if meta.get("is_lesson") else TYPE_CHAPTER,
                "parent_title": meta.get("parent_title", ""),
                "position": meta.get("position", ""),
                "total_users": total,
                "completed": stat["completed"],
                "in_progress": stat["in_progress"],
                "not_started": stat["not_started"],
                "reset": stat["reset"],
                "completion_rate": f"{completion_rate:.2f}",
                "stick_rate": f"{stick_rate:.2f}",
                "quality_score": score,
                "grade": _grade(score, total),
                "remark": _remark(
                    _grade(score, total),
                    stick_rate,
                    bool(meta.get("is_lesson")),
                ),
            }
        )
    return rows


HEADER = (
    "shifu_bid\tshifu_title\toutline_item_bid\toutline_title\titem_type\t"
    "parent_title\tposition\ttotal_users\tcompleted\tin_progress\tnot_started\t"
    "reset\tcompletion_rate\tstick_rate\tquality_score\tgrade\tremark"
)


def main(argv: Optional[List[str]] = None) -> int:
    global STICK_PENALTY
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dsn",
        default=os.environ.get(
            "SEG_EVAL_DB_DSN",
            "mysql://root:ai-shifu@ai-shifu-mysql-dev:3306/ai-shifu_dev?charset=utf8mb4",
        ),
        help="MySQL DSN（默认 env SEG_EVAL_DB_DSN）",
    )
    parser.add_argument("--out", default="segmentation-eval.tsv", help="输出 TSV 路径")
    parser.add_argument("--min-users", type=int, default=1, help="过滤 total_users < 该值的课节")
    parser.add_argument(
        "--stick-penalty",
        type=float,
        default=STICK_PENALTY,
        help="卡课率惩罚权重（默认 1.0）",
    )
    args = parser.parse_args(argv)

    STICK_PENALTY = args.stick_penalty

    rows = build_rows(args.dsn)
    rows = [r for r in rows if r["total_users"] >= args.min_users]

    out_path = args.out
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(HEADER + "\n")
        for r in rows:
            f.write(
                "\t".join(
                    [
                        str(r[k])
                        for k in [
                            "shifu_bid", "shifu_title", "outline_item_bid",
                            "outline_title", "item_type", "parent_title",
                            "position", "total_users", "completed",
                            "in_progress", "not_started", "reset",
                            "completion_rate", "stick_rate", "quality_score",
                            "grade", "remark",
                        ]
                    ]
                )
                + "\n"
            )
    print(
        f"written {len(rows)} rows -> {out_path} "
        f"(good={sum(1 for r in rows if r['grade']=='good')}, "
        f"fair={sum(1 for r in rows if r['grade']=='fair')}, "
        f"poor={sum(1 for r in rows if r['grade']=='poor')})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
