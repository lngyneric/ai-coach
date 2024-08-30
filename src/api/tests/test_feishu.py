def test_feishu(app):
    from flaskr.service.order.funs import send_order_feishu

    with app.app_context():
        send_order_feishu(app, "4cb9823c1bfe46e0a6abd6a3c306756c")
