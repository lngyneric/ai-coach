

def test_query_order(app):
    from flaskr.service.view.modes import OrderView


    OrderView.query(app,1,20,{})