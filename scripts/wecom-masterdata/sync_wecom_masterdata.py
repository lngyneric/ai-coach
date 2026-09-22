#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_wecom_masterdata.py —— 企微通讯录主数据 → 主系统（person_master + 组织树）全量同步

流程：
  1. 调用 wecom-cli contact users search --json '{"search_mode":"list"}' 拉全量人员
  2. upsert person_master（wecom_userid 主键，ON DUPLICATE KEY UPDATE）
  3. 从全量 departments[] 路径反推组织节点（root→leaf 去重）→ departments 表
  4. 重建 user_departments 关联（is_primary = departments[0]）
  5. 写 wecom_sync_log（sync_type=person_master，summary 含 synced/updated 数）

依赖（授权环境）：
  - python3 + PyMySQL
  - wecom-cli 已授权（contact users search）
  - MySQL 连接信息经环境变量注入（避免明文落库）

用法示例：
  DB_HOST=127.0.0.1 DB_PORT=3306 DB_USER=root DB_PASS=xxx \
  DB_NAME=ai-shifu python3 sync_wecom_masterdata.py [--users-json /path/users.json]

  --users-json <file>  可选：跳过调 wecom-cli，直接从本地 JSON 读全量人员（便于离线/调试）
  --dry-run            只解析与打印统计，不写库

幂等性：
  - person_master：INSERT ... ON DUPLICATE KEY UPDATE（按 wecom_userid）
  - user_departments：先删该用户全部关联再插（成对重建）
  - departments：按 full_path 去重 upsert
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

try:
    import pymysql
except ImportError:
    pymysql = None

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "ai-shifu")
DB_NAME = os.environ.get("DB_NAME", "ai-shifu")

WECOM_CLI = os.environ.get("WECOM_CLI", "wecom-cli")


def _cli_search(keywords, search_mode="list"):
    """调一次 wecom-cli 搜索，返回 users 列表。

    注意：企微该接口 **keywords 为必填**（缺了会报 40058），且是"按人名/别名/邮箱
    搜索"语义（带数量截断），不支持按部门、也不支持无关键词拉全量。因此全量同步
    只能退化为「关键词枚举 + 去重合并」。
    """
    payload = {"keywords": list(keywords), "search_mode": search_mode}
    cmd = [WECOM_CLI, "contact", "users", "search", "--json", json.dumps(payload, ensure_ascii=False)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("wecom-cli 调用失败: rc=%s\nstdout=%s\nstderr=%s"
                           % (proc.returncode, proc.stdout, proc.stderr))
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError("wecom-cli 输出非 JSON: %s\n%s" % (e, proc.stdout))
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError("wecom-cli 返回错误: %s" % data["error"])
    if isinstance(data, dict):
        inner = data.get("data", data)
        users = (inner.get("users") if isinstance(inner, dict) else None) \
                or data.get("users") or data.get("list") or []
    else:
        users = data
    return users


# keywords 为空时的兜底枚举：常见姓氏。覆盖率依赖接口截断，不保证全量。
DEFAULT_KEYWORDS = [c for c in "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳鲍史唐费廉岑薛雷贺倪汤"]


def fetch_all_users(users_json_path=None, keywords=None, search_mode="list"):
    """返回 users 列表。每个元素含 userid/name/alias/email/position/departments[]。"""
    if users_json_path:
        with open(users_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            inner = data.get("data", data)
            users = (inner.get("users") if isinstance(inner, dict) else None) \
                    or data.get("users") or data.get("list") or []
        else:
            users = data
        return users

    kws = [k.strip() for k in (keywords or []) if k.strip()] or DEFAULT_KEYWORDS
    merged, seen = [], set()
    for kw in kws:
        try:
            batch = _cli_search([kw], search_mode=search_mode)
        except RuntimeError as e:
            print("  ⚠ 关键词 %r 拉取失败：%s" % (kw, e))
            continue
        got = 0
        for u in batch or []:
            uid = (u or {}).get("userid")
            if not uid or uid in seen:
                continue
            seen.add(uid)
            merged.append(u)
            got += 1
        print("  关键词 %r → 新增 %d 人（累计 %d）" % (kw, got, len(merged)))
    return merged


def ensure_person_cols(conn, dry_run=False):
    """确保 person_master 补齐同步所需列（幂等；由 DB 侧 schema.sql 已含，此处双保险）。"""
    with conn.cursor() as cur:
        cur.execute("SHOW COLUMNS FROM `person_master`")
        rows = cur.fetchall()
    # DictCursor 时为 dict（key 'Field'），普通游标时为 tuple（index 0）
    cols = {r["Field"] if isinstance(r, dict) else r[0] for r in rows}
    needed = {"email", "position_name", "dept_path", "dept_name", "sync_time", "roster_source"}
    missing = needed - cols
    if missing:
        col_sql = {
            "email": "VARCHAR(255) NULL",
            "position_name": "VARCHAR(100) NULL",
            "dept_path": "JSON NULL",
            "dept_name": "VARCHAR(200) NULL",
            "sync_time": "TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
            "roster_source": "VARCHAR(32) NULL COMMENT '数据来源：smartsheet-5dept=权威表, keyword-enum=CLI关键词枚举'",
        }
        if dry_run:
            print("[dry-run] person_master 缺列，将添加: %s" % (", ".join(sorted(missing))))
            return
        for c in sorted(missing):
            conn.cursor().execute("ALTER TABLE `person_master` ADD COLUMN `%s` %s" % (c, col_sql[c]))
        conn.commit()
        print("person_master 已补列: %s" % (", ".join(sorted(missing))))


def path_to_nodes(departments):
    """把 departments[]（root→leaf 路径）fold 成逐级节点全路径列表。
    departments 可能为 ["希森美康","SCH","人力资源行政部","人事课"]
    → [("希森美康", "" , 1, "希森美康"),
       ("SCH", "希森美康", 2, "希森美康/SCH"),
       ("人力资源行政部", "希森美康/SCH", 3, "希森美康/SCH/人力资源行政部"),
       ("人事课", "希森美康/SCH/人力资源行政部", 4, "希森美康/SCH/人力资源行政部/人事课")]
    全文用 "/" 连接，成员路径即 full_path。
    """
    nodes = []
    acc = []
    for i, seg in enumerate(departments):
        seg = str(seg).strip()
        if not seg:
            continue
        acc.append(seg)
        parent_path = "/".join(acc[:-1]) if len(acc) > 1 else ""
        full_path = "/".join(acc)
        nodes.append({
            "dept_name": seg,
            "parent_path": parent_path,
            "level": len(acc),
            "full_path": full_path,
        })
    return nodes


def upsert_departments(conn, nodes, dry_run=False):
    """按 full_path upsert 组织节点，返回节点数。"""
    seen = {}
    for n in nodes:
        seen[n["full_path"]] = n  # 去重（保留同路径任一）
    sql = (
        "INSERT INTO `departments` (`dept_name`,`parent_path`,`level`,`full_path`) "
        "VALUES (%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE `dept_name`=VALUES(`dept_name`), "
        "`parent_path`=VALUES(`parent_path`), `level`=VALUES(`level`), `sync_time`=NOW()"
    )
    n = 0
    if dry_run:
        return len(seen)
    with conn.cursor() as cur:
        for path, nd in sorted(seen.items()):
            cur.execute(sql, (nd["dept_name"], nd["parent_path"], nd["level"], nd["full_path"]))
            n += 1
    conn.commit()
    return n


def upsert_person(conn, user, dry_run=False, roster_source=None):
    """upsert 单个人到 person_master；返回 'inserted'/'updated'。

    roster_source 为 None 时不写该列（保留既有值）。
    """
    userid = user.get("userid")
    if not userid:
        return None
    departments = user.get("departments") or []
    primary_dept = departments[0] if departments else ""
    dept_path_json = json.dumps(departments, ensure_ascii=False)
    rows = {
        "name": (user.get("name") or ""),
        # 接口字段是 position（职务），非 title
        "position_name": (user.get("position") or ""),
        "email": (user.get("email") or ""),
        "dept_path": dept_path_json,
        "dept_name": primary_dept,
    }
    src_sql = ",`roster_source`" if roster_source is not None else ""
    src_ph = ",%s" if roster_source is not None else ""
    src_up = ",`roster_source`=VALUES(`roster_source`)" if roster_source is not None else ""
    sql = (
        "INSERT INTO `person_master` (`wecom_userid`,`name`,`position_name`,`email`,`dept_path`,`dept_name`%s) "
        "VALUES (%%s,%%s,%%s,%%s,%%s,%%s%s) "
        "ON DUPLICATE KEY UPDATE "
        "`name`=VALUES(`name`),`position_name`=VALUES(`position_name`),"
        "`email`=VALUES(`email`),`dept_path`=VALUES(`dept_path`),"
        "`dept_name`=VALUES(`dept_name`)%s,`sync_time`=NOW()"
    ) % (src_sql, src_ph, src_up)
    args = (userid, rows["name"], rows["position_name"],
            rows["email"], rows["dept_path"], rows["dept_name"])
    if roster_source is not None:
        args = args + (roster_source,)
    if dry_run:
        return "dry"
    with conn.cursor() as cur:
        cur.execute(sql, args)
        if cur.rowcount == 1:
            return "inserted"
        return "updated"


def rebuild_user_departments(conn, user, dry_run=False):
    """重建成对该用户部门关联（先删后插）。
    departments[] 是单条路径的逐段（root→leaf），此处将其 fold 成完整路径
    写入 user_departments.dept_path（与 departments.full_path 对齐），is_primary 取首段。
    """
    userid = user.get("userid")
    if not userid:
        return 0
    departments = [str(d).strip() for d in (user.get("departments") or []) if str(d).strip()]
    full_path = "/".join(departments)
    if dry_run:
        return 1 if full_path else 0
    with conn.cursor() as cur:
        cur.execute("DELETE FROM `user_departments` WHERE `wecom_userid`=%s", (userid,))
        if full_path:
            cur.execute(
                "INSERT INTO `user_departments` (`wecom_userid`,`dept_path`,`is_primary`) "
                "VALUES (%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE `is_primary`=VALUES(`is_primary`),`sync_time`=NOW()",
                (userid, full_path, 1))
    conn.commit()
    return 1 if full_path else 0


def build_org_list(users):
    """从全量人员提取所有组织节点列表（root→leaf 全路径）。"""
    nodes = []
    for u in users:
        if not u.get("userid"):
            continue
        for n in path_to_nodes(u.get("departments") or []):
            nodes.append(n)
    return nodes


def write_sync_log(conn, sync_type, status, summary, error_msg=None, log_id=None, dry_run=False):
    if dry_run:
        print("[dry-run] wecom_sync_log: %s %s %s" % (sync_type, status, summary))
        return
    with conn.cursor() as cur:
        if log_id:
            cur.execute(
                "UPDATE `wecom_sync_log` SET `status`=%s,`finished_at`=NOW(),`summary`=%s,`error_msg`=%s WHERE `id`=%s",
                (status, json.dumps(summary, ensure_ascii=False), error_msg, log_id))
        else:
            cur.execute(
                "INSERT INTO `wecom_sync_log` (`sync_type`,`status`,`summary`,`error_msg`) "
                "VALUES (%s,%s,%s,%s)",
                (sync_type, status, json.dumps(summary, ensure_ascii=False), error_msg))
    conn.commit()
    if log_id:
        return log_id
    with conn.cursor() as cur:
        cur.execute("SELECT LAST_INSERT_ID() AS i")
        row = cur.fetchone()
        return row["i"] if isinstance(row, dict) else row[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--users-json", default=None, help="从本地 JSON 读全量人员（跳过 wecom-cli）")
    ap.add_argument("--keywords", default=None,
                    help="逗号分隔的搜索关键词（姓名/别名/邮箱）。接口要求必填，缺省时用常见姓氏枚举")
    ap.add_argument("--dry-run", action="store_true", help="只解析不写库")
    ap.add_argument("--roster-source", default=None,
                    help="写入 person_master.roster_source 的来源标记；缺省时 "
                         "CLI 枚举路径记为 keyword-enum，--users-json 路径不写（保留既有值）")
    args = ap.parse_args()

    roster_source = args.roster_source or (None if args.users_json else "keyword-enum")

    started = datetime.now()
    print("[%s] 开始同步 person_master" % started.strftime("%Y-%m-%d %H:%M:%S"))

    # 0) 拉全量人员
    kws = [k.strip() for k in (args.keywords or "").split(",") if k.strip()]
    users = fetch_all_users(args.users_json, keywords=kws)
    if not users:
        print("未获取到人员数据，退出")
        return 2
    print("拉取到人员数: %d" % len(users))

    # 建日志（running）
    conn = None
    if not args.dry_run and pymysql:
        conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                               password=DB_PASS, database=DB_NAME, charset="utf8mb4",
                               autocommit=False, cursorclass=pymysql.cursors.DictCursor)
        ensure_person_cols(conn)
        log_id = write_sync_log(conn, "person_master", "running",
                                {"phase": "start", "total": len(users)})
    elif not args.dry_run:
        print("错误: 未安装 pymysql，无法写库。")
        return 3

    try:
        inserted = updated = dept_nodes = 0
        dept_map = {}  # full_path -> {dept_name,parent_path,level}

        # ① + ② 组织节点收集 + ③④ 逐人处理
        for u in users:
            r = upsert_person(conn, u, dry_run=args.dry_run, roster_source=roster_source)
            if r == "inserted":
                inserted += 1
            elif r == "updated":
                updated += 1
            rebuild_user_departments(conn, u, dry_run=args.dry_run)
            for n in path_to_nodes(u.get("departments") or []):
                dept_map[n["full_path"]] = n

        # ③ 组织树 upsert
        dept_nodes = upsert_departments(conn, list(dept_map.values()), dry_run=args.dry_run)

        summary = {
            "total": len(users),
            "inserted": inserted,
            "updated": updated,
            "dept_nodes": dept_nodes,
        }
        print("同步完成: 总数=%s 新增=%s 更新=%s 组织节点=%s" %
              (len(users), inserted, updated, dept_nodes))

        if not args.dry_run:
            write_sync_log(conn, "person_master", "success", summary, log_id=log_id)
            conn.close()
        return 0
    except Exception as e:
        print("同步失败: %s" % e)
        if not args.dry_run and conn:
            write_sync_log(conn, "person_master", "failed", {"phase": "error"},
                           error_msg=str(e)[:2000], log_id=log_id)
            conn.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
