#!/usr/bin/env python3
"""
知识图谱课程关联工具
半自动化地将一门课程添加到指定知识图谱的指定节点。

使用方式:
  python3 scripts/kg_add_course.py \\
    --kg ivd|personal \\
    --shifu-bid <课程ID> \\
    --node-id <节点ID> \\
    [--dry-run]

示例:
  # 预览
  python3 scripts/kg_add_course.py --kg personal --shifu-bid abc123 --node-id agent-tools --dry-run

  # 执行
  python3 scripts/kg_add_course.py --kg personal --shifu-bid abc123 --node-id agent-tools
"""

import json
import re
import subprocess
import sys
import argparse
from copy import deepcopy


KG_FILES = {
    "ivd": "src/cook-web/public/ivd-knowledge-tree.html",
    "personal": "src/cook-web/public/personal-growth-tree.html",
}

KG_NAMES = {
    "ivd": "IVD 知识图谱",
    "personal": "个人能力提升图谱",
}


def get_db_course_info(shifu_bid):
    """从数据库获取课程信息"""
    result = subprocess.run(
        [
            "docker", "exec", "ai-shifu-mysql", "mysql",
            "-uroot", "-pai-shifu",
            "--default-character-set=utf8mb4", "-N", "-e",
            f"SELECT title, COALESCE(description,''), COALESCE(keywords,'') "
            f"FROM `ai-shifu`.shifu_published_shifus "
            f"WHERE shifu_bid='{shifu_bid}' AND deleted=0"
        ],
        capture_output=True, text=True
    )
    line = result.stdout.strip()
    if not line:
        print(f"❌ 数据库中未找到课程: {shifu_bid}")
        return None
    parts = line.split('\t')
    return {
        "title": parts[0],
        "description": parts[1] if len(parts) > 1 else "",
        "keywords": parts[2] if len(parts) > 2 else "",
    }


def get_lesson_info(shifu_bid):
    """获取课节信息"""
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
    titles = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
    return titles


def load_html(filepath):
    with open(filepath, "r") as f:
        return f.read()


def save_html(filepath, content):
    with open(filepath, "w") as f:
        f.write(content)


def find_node_in_tree(html, node_id):
    """在 TREE 中定位节点"""
    pattern = f'"id":"{node_id}"'
    idx = html.find(pattern)
    if idx == -1:
        return None
    # Find the courses array
    courses_idx = html.find('"courses":', idx)
    if courses_idx == -1:
        return None
    # Find the end of courses array (next "metadata" or end of node)
    # Find matching closing bracket
    arr_start = html.index('[', courses_idx)
    depth = 0
    arr_end = arr_start
    for i in range(arr_start, len(html)):
        if html[i] == '[':
            depth += 1
        elif html[i] == ']':
            depth -= 1
            if depth == 0:
                arr_end = i
                break
    return {
        "start": courses_idx,
        "arr_start": arr_start,
        "arr_end": arr_end + 1,
    }


def find_node_in_nodes(html, node_id):
    """在 NODES 数组中定位节点"""
    pattern = f'"id":"{node_id}"'
    nodes_start = html.find('const NODES = [')
    idx = html.find(pattern, nodes_start)
    if idx == -1:
        return None
    # Find the courses array
    courses_idx = html.find('"courses":', idx)
    if courses_idx == -1:
        return None
    arr_start = html.index('[', courses_idx)
    depth = 0
    arr_end = arr_start
    for i in range(arr_start, len(html)):
        if html[i] == '[':
            depth += 1
        elif html[i] == ']':
            depth -= 1
            if depth == 0:
                arr_end = i
                break
    return {
        "start": courses_idx,
        "arr_start": arr_start,
        "arr_end": arr_end + 1,
    }


def build_course_json(shifu_bid, course_info, lessons):
    """构造课程 JSON 代码段"""
    lessons_json = json.dumps(lessons, ensure_ascii=False)
    return (
        f'{{"shifu_bid":"{shifu_bid}",'
        f'"title":"{course_info["title"]}",'
        f'"description":"{course_info["description"]}",'
        f'"keywords":"{course_info["keywords"]}",'
        f'"lesson_count":{len(lessons)},'
        f'"lesson_titles":[],'
        f'"lessons":{lessons_json}}}'
    )


def main():
    parser = argparse.ArgumentParser(description="将课程关联到知识图谱节点")
    parser.add_argument("--kg", required=True, choices=["ivd", "personal"],
                        help="目标知识图谱")
    parser.add_argument("--shifu-bid", required=True,
                        help="课程 ID (shifu_bid)")
    parser.add_argument("--node-id", required=True,
                        help="目标节点 ID")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅预览，不修改文件")
    args = parser.parse_args()

    kg_file = KG_FILES[args.kg]
    kg_name = KG_NAMES[args.kg]

    print(f"\n{'='*60}")
    print(f"📌 {kg_name} — 课程关联")
    print(f"{'='*60}")

    # 1. Get course data from DB
    course_info = get_db_course_info(args.shifu_bid)
    if not course_info:
        return 1

    lessons = get_lesson_info(args.shifu_bid)
    print(f"\n📖 课程: {course_info['title']}")
    print(f"   课节数: {len(lessons)}")

    # 2. Load HTML
    html = load_html(kg_file)

    # 3. Check if already exists
    if args.shifu_bid in html:
        print(f"⚠️  课程 {args.shifu_bid} 已存在于 {kg_name} 中")
        print(f"   已跳过，如需更新请手动修改")
        return 0

    # 4. Locate node in TREE
    tree_loc = find_node_in_tree(html, args.node_id)
    if not tree_loc:
        print(f"❌ 未在 TREE 中找到节点: {args.node_id}")
        print(f"   可用节点:")
        tree_m = re.search(r'const TREE = ({.*?});', html, re.DOTALL)
        if tree_m:
            tree = json.loads(tree_m.group(1))
            for d in tree["domains"]:
                print(f"  [{d['id']}]")
                for n in d["nodes"]:
                    has = "✅" if n.get("courses") else "⬜"
                    print(f"    {has} {n['id']}: {n['name']}")
        return 1

    # Check if empty
    current_content = html[tree_loc["arr_start"]:tree_loc["arr_end"]]
    is_empty = current_content.strip() == "[]"

    print(f"\n📍 节点: {args.node_id}")
    print(f"   当前课程数: {'空节点' if is_empty else '已有课程'}")

    # 5. Build new course JSON
    course_json = build_course_json(args.shifu_bid, course_info, lessons)

    if args.dry_run:
        print(f"\n🔍 DRY RUN — 以下为将要执行的修改")
        print(f"\nTREE 修改:")
        print(f"  替换位置: 字符 {tree_loc['arr_start']}-{tree_loc['arr_end']}")
        if is_empty:
            print(f"  替换: [] → [{course_json}]")
        else:
            print(f"  插入课程到现有 courses 数组")
        print(f"\nNODES 修改:")
        print(f"  同步更新 has_course/course_count/courses")
        print(f"\n✅ 预览完成，使用 --dry-run 去掉后执行")
        return 0

    # 6. Apply changes to TREE
    if is_empty:
        new_courses = f'[{course_json}]'
        html = html[:tree_loc["arr_start"]] + new_courses + html[tree_loc["arr_end"]:]
        print(f"✅ TREE: courses 已更新")
    else:
        # Insert before the closing bracket
        html = html[:tree_loc["arr_end"] - 1] + f',{course_json}' + html[tree_loc["arr_end"] - 1:]
        print(f"✅ TREE: 课程已追加到现有数组")

    # 7. Update NODES
    nodes_loc = find_node_in_nodes(html, args.node_id)
    if nodes_loc:
        nodes_content = html[nodes_loc["arr_start"]:nodes_loc["arr_end"]]
        nodes_empty = nodes_content.strip() == "[]"

        # Also update has_course/course_count
        # Find has_course
        has_course_idx = html.find('"has_course":false', nodes_loc["start"] - 50)
        if has_course_idx != -1 and has_course_idx < nodes_loc["arr_end"]:
            html = html[:has_course_idx] + '"has_course":true' + html[has_course_idx + 16:]
            print(f"✅ NODES: has_course 已更新")

        course_count_idx = html.find('"course_count":', nodes_loc["start"] - 50)
        if course_count_idx != -1 and course_count_idx < nodes_loc["arr_end"]:
            # Find the current count value
            val_start = html.index(':', course_count_idx) + 1
            val_end = html.index(',', val_start)
            # Count existing courses in nodes array
            arr_start_in_nodes = html.index('[', val_start)
            depth = 0
            arr_end_in_nodes = arr_start_in_nodes
            for i in range(arr_start_in_nodes, len(html)):
                if html[i] == '[':
                    depth += 1
                elif html[i] == ']':
                    depth -= 1
                    if depth == 0:
                        arr_end_in_nodes = i
                        break
            existing = html[arr_start_in_nodes:arr_end_in_nodes + 1]
            # Count objects
            count = existing.count('"shifu_bid"')
            html = html[:val_start] + str(count) + html[val_end:]
            print(f"✅ NODES: course_count 已更新为 {count}")

        if nodes_empty:
            new_courses = f'[{course_json}]'
            html = html[:nodes_loc["arr_start"]] + new_courses + html[nodes_loc["arr_end"]:]
            print(f"✅ NODES: courses 已更新")
        else:
            html = html[:nodes_loc["arr_end"] - 1] + f',{course_json}' + html[nodes_loc["arr_end"] - 1:]
            print(f"✅ NODES: 课程已追加到现有数组")
    else:
        print(f"⚠️  未找到 NODES 中对应节点，请手动更新")

    # 8. Save
    save_html(kg_file, html)
    print(f"\n✅ 文件已保存: {kg_file}")

    # 9. Reminder to deploy
    deploy_path = kg_file.replace("src/cook-web/public/", "")
    print(f"\n{'='*60}")
    print(f"📋 后续步骤")
    print(f"{'='*60}")
    print(f"1. 部署到 nginx:")
    print(f"   docker cp {kg_file} ai-shifu-nginx:/usr/share/nginx/html/{deploy_path}")
    print(f"2. 提交 git:")
    print(f"   git add {kg_file}")
    print(f"   git commit -m \"feat: 知识图谱关联课程 {course_info['title'][:30]}\"")
    print(f"   git push github main")
    print(f"3. 验证:")
    print(f"   curl -s https://eu.sysmex.com.cn/{deploy_path} | grep '{course_info['title'][:10]}'")

    return 0


if __name__ == "__main__":
    sys.exit(main())
