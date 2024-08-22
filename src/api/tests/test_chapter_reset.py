def test_chapter_reset(app):
    from flaskr.service.study.funcs import reset_user_study_info_by_lesson

    app.logger.info("test_chapter_reset")

    user_id = "ab769989275a4eddbdf589558b9df089"
    lesson_id = "42f1b809bb1247a4aebf0a756fb46640"
    reset_user_study_info_by_lesson(app, user_id, lesson_id)
