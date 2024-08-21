def test_study_record(app):
    from flaskr.service.study import get_study_record

    with app.app_context():
        user_id = "b2960e2a27d94f6e9e9f68e83cd3f8e4"

        from flaskr.route.common import make_common_response

        res = get_study_record(
            app, user_id, lesson_id="fc7e346cb46b432f8c5ac35e271226a0"
        )
        app.logger.info("res:{}".format(make_common_response(res)))
