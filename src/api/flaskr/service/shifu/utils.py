"""
Shifu utils

This module contains utility functions for shifu.

Author: yfge
Date: 2025-08-07
"""

from flaskr.service.lesson.models import AILesson, AILessonScript
from flaskr.service.lesson.const import (
    STATUS_PUBLISH,
    STATUS_DRAFT,
    SCRIPT_TYPE_SYSTEM,
    STATUS_TO_DELETE,
)
from flaskr.service.resource.models import Resource
from flask import Flask
from flaskr.dao import db


class OutlineTreeNode:
    """
    Outline tree node
    """

    outline: AILesson
    children: list["OutlineTreeNode"]
    outline_id: str
    lesson_no: str
    parent_node: "OutlineTreeNode"

    def __init__(self, outline: AILesson):
        """
        Init outline tree node
        """
        self.outline = outline
        self.children = []
        if outline:
            self.outline_id = outline.lesson_id
            self.lesson_no = outline.lesson_no
        else:
            self.outline_id = ""
            self.lesson_no = ""
        self.parent_node = None

    def add_child(self, child: "OutlineTreeNode"):
        """
        Add a child to the outline tree node
        """
        self.children.append(child)
        child.parent_node = self

    def remove_child(self, child: "OutlineTreeNode"):
        """
        Remove a child from the outline tree node
        """
        child.parent_node = None
        self.children.remove(child)

    def get_new_lesson_no(self):
        if not self.parent_node:
            return self.lesson_no
        else:
            return (
                self.parent_node.get_new_lesson_no()
                + f"{self.parent_node.children.index(self) + 1:02d}"
            )


def get_existing_outlines(app: Flask, shifu_id: str, parent_id: str = None):
    """
    Get the existing outlines for a shifu.
    deprecated:  only for migration
    Args:
        app: Flask application instance
        shifu_id: The ID of the shifu
        parent_id: The ID of the parent outline
    """
    subquery = (
        db.session.query(db.func.max(AILesson.id))
        .filter(
            AILesson.course_id == shifu_id,
        )
        .group_by(AILesson.lesson_id)
    )
    if parent_id:
        outlines = AILesson.query.filter(
            AILesson.id.in_(subquery),
            AILesson.status.in_([STATUS_PUBLISH, STATUS_DRAFT]),
            AILesson.parent_id == parent_id,
        ).all()
    else:
        outlines = AILesson.query.filter(
            AILesson.id.in_(subquery),
            AILesson.status.in_([STATUS_PUBLISH, STATUS_DRAFT]),
        ).all()
    return sorted(outlines, key=lambda x: (len(x.lesson_no), x.lesson_no))


def get_existing_outlines_for_publish(app: Flask, shifu_id: str):
    """
    Get the existing outlines for a shifu for publish.
    deprecated:  only for migration
    Args:
        app: Flask application instance
        shifu_id: The ID of the shifu
    Returns:
        list[AILesson]: The existing outlines for a shifu for publish
    """
    subquery = (
        db.session.query(db.func.max(AILesson.id))
        .filter(
            AILesson.course_id == shifu_id,
        )
        .group_by(AILesson.lesson_id)
    )
    outlines = AILesson.query.filter(
        AILesson.id.in_(subquery),
        AILesson.status.in_([STATUS_PUBLISH, STATUS_DRAFT, STATUS_TO_DELETE]),
    ).all()
    app.logger.info(f"get_existing_outlines_for_publish: {len(outlines)}")
    for outline in outlines:
        app.logger.info(
            f"outline: {outline.lesson_no} {outline.lesson_name} {outline.status}"
        )
    return outlines


def get_existing_blocks(app: Flask, outline_ids: list[str]) -> list[AILessonScript]:
    """
    Get the existing blocks (publish and draft)
    deprecated:  only for migration

    Args:
        app: Flask application instance
        outline_ids: The IDs of the outlines

    Returns:
        list[AILessonScript]: The existing blocks (publish and draft)
    """
    subquery = (
        db.session.query(db.func.max(AILessonScript.id))
        .filter(
            AILessonScript.lesson_id.in_(outline_ids),
            AILessonScript.script_type != SCRIPT_TYPE_SYSTEM,
        )
        .group_by(AILessonScript.script_id)
    )

    query = AILessonScript.query.filter(
        AILessonScript.id.in_(subquery),
        AILessonScript.status.in_([STATUS_PUBLISH, STATUS_DRAFT]),
    ).order_by(AILessonScript.script_index.asc())

    blocks = query.all()
    return blocks


def get_existing_blocks_for_publish(
    app: Flask, outline_ids: list[str]
) -> list[AILessonScript]:
    """
    Get the existing blocks (publish and draft) for publish
    deprecated:  only for migration

    Args:
        app: Flask application instance
        outline_ids: The IDs of the outlines

    Returns:
        list[AILessonScript]: The existing blocks (publish and draft) for publish
    """
    subquery = (
        db.session.query(db.func.max(AILessonScript.id))
        .filter(
            AILessonScript.lesson_id.in_(outline_ids),
        )
        .group_by(AILessonScript.script_id)
    )
    blocks = (
        AILessonScript.query.filter(
            AILessonScript.id.in_(subquery),
            AILessonScript.status.in_([STATUS_PUBLISH, STATUS_DRAFT, STATUS_TO_DELETE]),
        )
        .order_by(AILessonScript.script_index.asc())
        .all()
    )
    return blocks


def get_original_outline_tree(app: Flask, shifu_id: str) -> list["OutlineTreeNode"]:
    """
    Get the original outline tree for a shifu.
    deprecated:  only for migration

    Args:
        app: Flask application instance
        shifu_id: The ID of the shifu

    Returns:
        list[OutlineTreeNode]: The original outline tree for a shifu
    """
    outlines = get_existing_outlines(app, shifu_id)
    sorted_outlines = sorted(outlines, key=lambda x: (len(x.lesson_no), x.lesson_no))
    outline_tree = []

    nodes_map = {}
    for outline in sorted_outlines:
        node = OutlineTreeNode(outline)
        nodes_map[outline.lesson_no] = node

    # 构建树结构
    for lesson_no, node in nodes_map.items():
        if len(lesson_no) == 2:
            # 这是根节点
            outline_tree.append(node)
        else:
            # 找到父节点的lesson_no
            parent_no = lesson_no[:-2]
            if parent_no in nodes_map:
                parent_node = nodes_map[parent_no]
                # 添加到父节点的children列表中
                if node not in parent_node.children:  # 避免重复添加
                    parent_node.add_child(node)
            else:
                app.logger.error(f"Parent node not found for lesson_no: {lesson_no}")

    return outline_tree


def get_shifu_res_url(res_bid: str):
    """
    Get the URL of a resource.

    Args:
        res_bid: The ID of the resource

    Returns:
        str: The URL of the resource
    """
    res = Resource.query.filter_by(resource_id=res_bid).first()
    if res:
        return res.url
    return ""


def get_shifu_res_url_dict(res_bids: list[str]) -> dict[str, str]:
    """
    Get the URL of a resource.

    Args:
        res_bids: The IDs of the resources

    Returns:
        dict[str, str]: The URL of the resource
    """
    res_url_map = {}
    res = Resource.query.filter(Resource.resource_id.in_(res_bids)).all()
    for r in res:
        res_url_map[r.resource_id] = r.url
    return res_url_map


def parse_shifu_res_bid(res_url: str):
    """
    Parse the resource ID from a URL.

    Args:
        res_url: The URL of the resource

    Returns:
        str: The resource ID
    """
    if res_url:
        return res_url.split("/")[-1]
    return ""
