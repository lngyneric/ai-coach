def test_query_order(app):
    from flaskr.service.order import OrderView

    OrderView.query(app, 1, 20, {})
