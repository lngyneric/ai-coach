#!/usr/bin/env python3
"""批量建档：把 person_master 的主数据变成可登录账号（幂等）。

背景
----
`person_master` 已具备 userid（762）与员工号（729），但应用侧没有任何真实账号；
`ensure_user_for_identifier`（flaskr/service/user/repository.py:482）先按
`(provider, identifier)` 查凭据——**命中则复用既有账号，不命中才新建**。
因此预先写好像据，就能让企微 OAuth 登录落到同一账号，而不是每人新建一个。

每人写入
--------
1) `user_users`                —— user_identify=工号, nickname=姓名, state=1102, 部门/岗位/入职日期
2) `user_auth_credentials` ×3  —— employee(工号) / email(合成) / wecom(UserId)
3) `user_role_assignments`     —— 默认 role-learner

幂等键：`user_users.employee_no`、`user_auth_credentials(provider_name, identifier)`。

运行（宿主无 pymysql，需在容器内执行）
--------------------------------------
  docker cp provision_users.py <api容器>:/tmp/
  docker exec <api容器> sh -c 'cd /tmp && \\
    DB_HOST=ai-shifu-mysql-dev DB_PORT=3306 DB_USER=root DB_PASS=ai-shifu DB_NAME=ai-shifu_dev \\
    python3 provision_users.py --employees sch00068,swx00145 --dry-run'

参数
----
  --employees 逗号分隔工号（与 --limit / --department 互斥，优先）
  --department 按部门前缀筛（如 "希森美康/SCH/人力资源行政部"）
  --limit      最多取 N 人（配合 --department 或单独用）
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime

try:
    import pymysql
except ImportError:  # pragma: no cover
    pymysql = None

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "ai-shifu_dev")

USER_STATE_REGISTERED = 1102
CREDENTIAL_STATE_VERIFIED = 1202
SYNTHETIC_EMAIL_DOMAIN = "sysmex.internal"
DEFAULT_LANGUAGE = "zh"


def gen_id() -> str:
    """与 flaskr/util/uuid.generate_id 一致：uuid4 去连字符（32 位）。"""
    return str(uuid.uuid4()).replace("-", "")


def raw_profile(provider: str, metadata: dict | None = None) -> str:
    """与 flaskr/service/user/repository.serialize_raw_profile 一致。"""
    return json.dumps(
        {"provider": provider, "metadata": metadata or {}}, ensure_ascii=False
    )


def pick_people(conn, args) -> list[dict]:
    where = ["employee_no IS NOT NULL", "employee_no <> ''"]
    params: list = []
    if args.employees:
        emps = [e.strip().lower() for e in args.employees.split(",") if e.strip()]
        where.append("employee_no IN (%s)" % ",".join(["%s"] * len(emps)))
        params.extend(emps)
    else:
        if args.department:
            where.append("dept_name LIKE %s")
            params.append(args.department + "%")
        if args.limit:
            pass  # 在 SQL 尾部加 LIMIT
    sql = (
        "SELECT employee_no, wecom_userid, name, position_name, dept_name "
        "FROM person_master WHERE " + " AND ".join(where) + " ORDER BY employee_no"
    )
    if args.limit and not args.employees:
        sql += " LIMIT %d" % int(args.limit)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def existing_employee_nos(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT employee_no FROM user_users WHERE employee_no IS NOT NULL "
            "AND employee_no <> '' AND deleted = 0"
        )
        return {r["employee_no"].lower() for r in cur.fetchall()}


def existing_credential_identifiers(conn) -> set[tuple[str, str]]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT provider_name, identifier FROM user_auth_credentials WHERE deleted = 0"
        )
        return {(r["provider_name"], r["identifier"]) for r in cur.fetchall()}


def provision_one(conn, person: dict, dry_run: bool) -> dict:
    """为一人建 user + 3 条凭据 + learner 角色。返回动作摘要。"""
    emp_no = person["employee_no"].strip().lower()
    userid = (person["wecom_userid"] or "").strip()
    if not userid:
        return {"employee_no": emp_no, "action": "skipped", "reason": "无 wecom_userid"}

    user_bid = gen_id()
    synthetic_email = "%s@%s" % (emp_no, SYNTHETIC_EMAIL_DOMAIN)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if dry_run:
        return {
            "employee_no": emp_no,
            "name": person["name"],
            "action": "would_create",
            "user_bid": user_bid,
            "credentials": ["employee", "email", "wecom"],
        }

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO `user_users` "
            "(`user_bid`,`user_identify`,`nickname`,`avatar`,`language`,`state`,"
            " `is_creator`,`deleted`,`created_at`,`updated_at`,`api_key`,`is_operator`,"
            " `employee_no`,`department`,`position_name`,`is_certifier`) "
            "VALUES (%s,%s,%s,'',%s,%s,0,0,%s,%s,'',0,%s,%s,%s,0)",
            (
                user_bid,
                emp_no,
                person["name"] or emp_no,
                DEFAULT_LANGUAGE,
                USER_STATE_REGISTERED,
                now,
                now,
                emp_no,
                person["dept_name"],
                person["position_name"],
            ),
        )

        creds = [
            # 工号登录（与 EmployeeAuthProvider 完全一致）
            ("employee", emp_no, emp_no, "employee_no", {"source": "provision"}),
            # 合成邮箱（前端 initUser() 靠 mobile||email 判定登录态）
            ("email", synthetic_email, synthetic_email, "email",
             {"source": "employee_aad"}),
            # 企微 OAuth（identifier = UserId，登录时命中即复用本账号）
            ("wecom", userid, userid, "wecom_userid", {"source": "provision"}),
        ]
        for provider, subject_id, identifier, subject_format, meta in creds:
            cur.execute(
                "INSERT INTO `user_auth_credentials` "
                "(`credential_bid`,`user_bid`,`provider_name`,`subject_id`,"
                " `subject_format`,`identifier`,`raw_profile`,`state`,`deleted`,"
                " `created_at`,`updated_at`) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s) "
                "ON DUPLICATE KEY UPDATE "
                "`user_bid`=VALUES(`user_bid`),`subject_id`=VALUES(`subject_id`),"
                "`subject_format`=VALUES(`subject_format`),"
                "`raw_profile`=VALUES(`raw_profile`),`state`=VALUES(`state`),"
                "`deleted`=0,`updated_at`=VALUES(`updated_at`)",
                (
                    gen_id(),
                    user_bid,
                    provider,
                    subject_id,
                    subject_format,
                    identifier,
                    raw_profile(provider, meta),
                    CREDENTIAL_STATE_VERIFIED,
                    now,
                    now,
                ),
            )

        cur.execute(
            "INSERT IGNORE INTO `user_role_assignments` (`user_bid`,`role_bid`) "
            "VALUES (%s,'role-learner')",
            (user_bid,),
        )
    conn.commit()
    return {
        "employee_no": emp_no,
        "name": person["name"],
        "action": "created",
        "user_bid": user_bid,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--employees", default=None, help="逗号分隔工号")
    ap.add_argument("--department", default=None, help="按 dept_name 前缀筛选")
    ap.add_argument("--limit", type=int, default=None, help="最多处理 N 人")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not pymysql:
        print("错误：未安装 pymysql，本脚本需在 api 容器内执行", file=sys.stderr)
        return 3

    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset="utf8mb4", autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        people = pick_people(conn, args)
        if not people:
            print("没有匹配到人员，退出")
            return 2
        have_emp = existing_employee_nos(conn)
        have_cred = existing_credential_identifiers(conn)

        created = skipped = 0
        results = []
        for p in people:
            emp = p["employee_no"].strip().lower()
            if emp in have_emp:
                results.append({"employee_no": emp, "name": p["name"],
                                "action": "skipped", "reason": "已有 user 账号"})
                skipped += 1
                continue
            if ("wecom", (p["wecom_userid"] or "").strip()) in have_cred:
                results.append({"employee_no": emp, "name": p["name"],
                                "action": "skipped", "reason": "wecom 凭据已存在"})
                skipped += 1
                continue
            r = provision_one(conn, p, args.dry_run)
            results.append(r)
            if r["action"] in ("created", "would_create"):
                created += 1
            else:
                skipped += 1

        print("目标 %d 人 → 建档 %d / 跳过 %d%s"
              % (len(people), created, skipped, "（dry-run）" if args.dry_run else ""))
        for r in results:
            if r["action"] == "created":
                print("   ✅ %-12s %-8s user_bid=%s" % (r["employee_no"], r["name"], r["user_bid"]))
            elif r["action"] == "would_create":
                print("   ○ %-12s %-8s 将建档" % (r["employee_no"], r["name"]))
            else:
                print("   – %-12s %-8s 跳过：%s" % (r["employee_no"], r.get("name", "?"), r.get("reason", "")))
        if args.dry_run:
            print("\n[dry-run] 未写入任何数据")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
