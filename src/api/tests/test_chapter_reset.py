def test_chapter_reset(app):
    from flaskr.service.study.funcs import reset_user_study_info_by_lesson

    app.logger.info("test_chapter_reset")

    user_id = "ab769989275a4eddbdf589558b9df089"
    lesson_id = "84aa585dd0b54ffa9437ddc47494e901"
    reset_user_study_info_by_lesson(app, user_id, lesson_id)
