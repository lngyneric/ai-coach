#!/usr/bin/env python3
"""
知识图谱同步审计脚本
对比数据库课程与两个知识图谱的覆盖情况，输出差异报告。
"""

import json
import re
import subprocess
import sys
from datetime import datetime


def get_db_courses():
    """从数据库获取所有已发布课程"""
    result = subprocess.run(
        [
            "docker", "exec", "ai-shifu-mysql", "mysql",
            "-uroot", "-pai-shifu",
            "--default-character-set=utf8mb4", "-N", "-e",
            "SELECT shifu_bid, title, COALESCE(description,''), COALESCE(keywords,''), "
            "created_at FROM `ai-shifu`.shifu_published_shifus WHERE deleted=0 ORDER BY id"
        ],
        capture_output=True, text=True
    )
    courses = {}
    for line in result.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.strip().split('\t')
        if len(parts) >= 2:
            courses[parts[0]] = {
                "title": parts[1],
                "description": parts[2] if len(parts) > 2 else "",
                "keywords": parts[3] if len(parts) > 3 else "",
                "created_at": parts[4] if len(parts) > 4 else "",
            }
    return courses


def get_outline_count(shifu_bid):
    """获取课程的课节数"""
    result = subprocess.run(
        [
            "docker", "exec", "ai-shifu-mysql", "mysql",
            "-uroot", "-pai-shifu", "-N", "-e",
            f"SELECT COUNT(*) FROM `ai-shifu`.shifu_published_outline_items "
            f"WHERE shifu_bid='{shifu_bid}' AND deleted=0"
        ],
        capture_output=True, text=True
    )
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0


def get_lesson_titles(shifu_bid):
    """获取课程的课节标题"""
    result = subprocess.run(
        [
            "docker", "exec", "ai-shifu-mysql", "mysql",
            "-uroot", "-pai-shifu", "-N", "-e",
            f"SELECT title FROM `ai-shifu`.shifu_published_outline_items "
            f"WHERE shifu_bid='{shifu_bid}' AND deleted=0 "
            f"AND outline_item_bid != '{shifu_bid}' ORDER BY position"
        ],
        capture_output=True, text=True
    )
    return [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]


def analyze_kg(filepath, label):
    """解析单个知识图谱，返回节点信息"""
    try:
        with open(filepath, "r") as f:
            html = f.read()
    except FileNotFoundError:
        print(f"❌ 文件不存在: {filepath}")
        return {"nodes": 0, "courses": set(), "course_count": 0, "domains": {}}

    tree_m = re.search(r'const TREE = ({.*?});', html, re.DOTALL)
    if not tree_m:
        print(f"❌ 无法解析 TREE 数据: {filepath}")
        return {"nodes": 0, "courses": set(), "course_count": 0, "domains": {}}

    tree = json.loads(tree_m.group(1))
    courses = set()
    domain_info = {}

    for domain in tree.get("domains", []):
        did = domain["id"]
        domain_courses = 0
        for node in domain.get("nodes", []):
            for c in node.get("courses", []):
                courses.add(c["shifu_bid"])
                domain_courses += 1
        domain_info[did] = {
            "name": domain["name"],
            "nodes": len(domain.get("nodes", [])),
            "courses": domain_courses,
        }

    return {
        "nodes": sum(d["nodes"] for d in domain_info.values()),
        "courses": courses,
        "course_count": len(courses),
        "domains": domain_info,
        "tree": tree,
    }


def print_report(kg_result, label):
    """打印单个图谱信息"""
    print(f"\n{'='*60}")
    print(f"📊 {label}")
    print(f"{'='*60}")
    print(f"  节点总数: {kg_result['nodes']}")
    print(f"  已关联课程: {kg_result['course_count']} 门")
    print()
    for did, info in kg_result["domains"].items():
        status = "✅" if info["courses"] > 0 else "⬜"
        print(f"  {status} [{did}] {info['name']}: {info['nodes']}节点, {info['courses']}课程")
    return kg_result["courses"]


def main():
    print(f"\n🔍 知识图谱审计报告: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    # 1. Analyze both knowledge graphs
    kg_files = [
        ("IVD 知识图谱", "src/cook-web/public/ivd-knowledge-tree.html"),
        ("个人能力提升图谱", "src/cook-web/public/personal-growth-tree.html"),
    ]

    all_kg_courses = set()
    for label, filepath in kg_files:
        result = analyze_kg(filepath, label)
        kg_courses = print_report(result, label)
        all_kg_courses.update(kg_courses)

    # 2. Get DB courses
    db_courses = get_db_courses()

    print(f"\n{'='*60}")
    print(f"📋 汇总")
    print(f"{'='*60}")
    print(f"  数据库课程总数: {len(db_courses)} 门")
    print(f"  图谱已覆盖: {len(all_kg_courses)} 门")

    # 3. Find gaps
    ignored_bids = {"a27a833a6d50412f928a5bcfb8e88750"}  # Test Course
    missing = [bid for bid in db_courses if bid not in all_kg_courses and bid not in ignored_bids]
    skipped = [bid for bid in db_courses if bid in ignored_bids]

    print(f"\n{'='*60}")
    print(f"❌ 未关联到图谱的课程")
    print(f"{'='*60}")
    if missing:
        for bid in sorted(missing):
            info = db_courses[bid]
            print(f"  ⚠️  {bid}")
            print(f"     标题: {info['title'][:60]}")
            print(f"     描述: {info['description'][:80]}")
            print(f"     关键词: {info['keywords'][:60]}")
            lesson_count = get_outline_count(bid)
            if lesson_count > 0:
                print(f"     课节数: {lesson_count}")
                titles = get_lesson_titles(bid)
                if titles:
                    print(f"     课节: {', '.join(titles[:5])}{'...' if len(titles) > 5 else ''}")
            print()
    else:
        print("  ✅ 全部已覆盖，无需操作")

    if skipped:
        print(f"\n⏭️  已跳过的课程（测试/无效课程）:")
        for bid in skipped:
            print(f"  - {bid}: {db_courses[bid]['title'][:50]}")

    # 4. Show last 5 DB courses for quick reference
    print(f"\n{'='*60}")
    print(f"🆕 最近发布的课程")
    print(f"{'='*60}")
    sorted_courses = sorted(db_courses.items(),
                            key=lambda x: x[1].get("created_at", ""), reverse=True)
    for bid, info in sorted_courses[:5]:
        status = "✅" if bid in all_kg_courses else "❌"
        print(f"  {status} {info['created_at'][:10]} {info['title'][:50]}")

    # Summary
    print(f"\n{'='*60}")
    total_kg_nodes = sum(
        analyze_kg(fp, "")["nodes"] for _, fp in kg_files
    )
    print(f"📈 总覆盖: {len(all_kg_courses)}/{len(db_courses)} 课程 | {total_kg_nodes} 节点")

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
