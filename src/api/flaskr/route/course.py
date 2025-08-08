from flask import Flask, request
from .common import bypass_token_validation, make_common_response
from flaskr.service.lesson.funcs import get_course_info


def register_course_handler(app: Flask, path_prefix: str) -> Flask:
    @app.route(path_prefix + "/get-course-info", methods=["GET"])
    @bypass_token_validation
    def get_course_info_api():
        """

        get course info api
        ---
        tags:
        - course
        parameters:
            -   in: query
                required: true
                schema:
                    properties:
                        course_id:
                            type: string
                            description: 课程id
        responses:
            200:
                description: 获取课程信息成功
                content:
                    application/json:
                        schema:
                            properties:
                                code:
                                    type: integer
                                    description: 返回码
                                message:
                                    type: string
                                    description: 返回信息
                                data:
                                    $ref: '#/components/schemas/AICourseDTO'
        """
        course_id = request.args.get("course_id", None)
        preview_mode = request.args.get("preview_mode", "False").lower() == "true"
        return make_common_response(get_course_info(app, course_id, preview_mode))

    return app
