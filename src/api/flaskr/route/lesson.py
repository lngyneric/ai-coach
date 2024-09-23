from flask import Flask, request
from flaskr.service.lesson.funs import delete_lesson
from flaskr.service.common.models import raise_param_error
from flaskr.service.lesson.const import LESSON_TYPE_NORMAL
from .common import bypass_token_validation, make_common_response
from ..service.lesson import update_lesson_info, get_lessons


def register_lesson_handler(app: Flask, path_prefix: str) -> Flask:
    @app.route(path_prefix + "/update_lesson", methods=["GET"])
    @bypass_token_validation
    def update_lesson():

        """
        更新课程
        ---
        tags:
        - 课程
        parameters:
            - name: doc_id
              in: query
              description: 文档id
              required: true
              schema:
                type: string
            - name: table_id
              in: query
              description: 课程表格id
              required: true
              schema:
                type: string
            - name: title
              in: query
              description: 课程标题
              required: true
              schema:
                type: string
            - name: index
              in: query
              description: 课程序号
              required: true
              schema:
                type: string
            - name: view_id
              in: query
              description: 视图id
              required: true
              schema:
                type: string
            - name: lesson_type
              in: query
              description: 课程类型
              required: false
              schema:
                type: string
            - name: app_id
              in: query
              description: 飞书应用id
              required: false
              schema:
                type: string
            - name: app_secrect
              in: query
              description: 飞书应用秘钥
              required: false
              schema:
                type: string
        """
        doc_id = request.args.get("doc_id")
        table_id = request.args.get("table_id")
        title = request.args.get("title")
        index = request.args.get("index")
        view_id = request.args.get("view_id")
        lesson_type = request.args.get("lesson_type", LESSON_TYPE_NORMAL)
        app_id = request.args.get("app_id", None)
        app_secrect = request.args.get("app_secrect", None)
        if not doc_id:
            raise_param_error("doc_id is not found")
        if not table_id:
            raise_param_error("table_id is not found")
        if not title:
            raise_param_error("title is not found")
        if not index:
            raise_param_error("index is not found")
        return make_common_response(
            update_lesson_info(
                app,
                doc_id,
                table_id,
                view_id,
                title,
                index,
                lesson_type,
                app_id,
                app_secrect,
            )
        )

    @app.route(path_prefix + "/get_chatper_info", methods=["GET"])
    @bypass_token_validation
    def get_chatper_info():
        course_id = request.args.get("doc_id")
        if not course_id:
            raise_param_error("doc_id is not found")
        return make_common_response(get_lessons(app, course_id))

    @app.route(path_prefix + "/delete_lesson", methods=["GET"])
    @bypass_token_validation
    def delete_lesson_by_table():
        """
        删除课程
        ---
        tags:
        - 课程
        parameters:
            - name: table_id
              in: query
              description: 课程表格id
              required: true
              schema:
                type: string
        """
        lesson_id = request.args.get("table_id")
        if not lesson_id:
            raise_param_error("lesson_id is not found")
        return make_common_response(delete_lesson(app, lesson_id))

    return app
