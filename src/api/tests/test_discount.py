

def test_discount(app):
    from  flaskr.service.order.discount import  generate_discount_code 
    from  flaskr.service.lesson.models import AICourse
    from flaskr.service.order.models import Discount
    with app.app_context():
        course = AICourse.query.first()
        course_id = course.course_id
        discount = Discount.query.first()
        if not discount:
            discount_id = generate_discount_code(app, 100, course_id, '2021-01-01', '2028-12-31', 'channel')
        else:
            pass

def test_create_discount(app):
    from  flaskr.service.order.discount import  generate_discount_code_by_rule 
    from  flaskr.service.order.models import Discount
    with app.app_context():
        discount = Discount.query.first()
        discount_id = discount.discount_id
        for i in range(10):
            generate_discount_code_by_rule(app, discount_id)