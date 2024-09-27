def test_get_access_token(app):
    from flaskr.api.llm.ernie import get_access_token

    access_token = get_access_token()
    app.logger.info(access_token)
    assert get_access_token() != ""


def test_chat(app):
    from flaskr.api.llm.ernie import get_ernie_response

    resp = get_ernie_response(app, "ERNIE-4.0-8K", "你好,最近有什么新闻")
    for r in resp:
        app.logger.info(r.result)
