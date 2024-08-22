def test_feishu(app):
    from flaskr.service.order.funs import send_order_feishu

    with app.app_context():
        send_order_feishu(app, "b0a9ea91561f44bfbf6e6b8cd2c9a549")
