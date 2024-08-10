from flask import Flask, request
from flaskr.route.common import make_common_response
from flaskr.service.order import success_buy_record, generate_charge,query_buy_record



def register_order_handler(app: Flask, path_prefix: str):
     
    @app.route(path_prefix+'/order-test', methods=['POST'])
    def order_test():
        order_id = request.get_json().get('order_id', '')
        
        return make_common_response(success_buy_record(app, order_id))
    @app.route(path_prefix+'/reqiure-to-pay', methods=['POST'])
    def reqiure_to_pay():
        """
        请求支付
        ---
        tags:
            - 订单
        parameters:
            - in: body
              name: body
              required: true
              schema:
                type: object
                properties:
                    order_id:
                        type: string
                        description: 订单id
                    channel:
                        type: string
                        description: 支付渠道,目前支持wx_pub_qr,alipay_qr
        responses:
            200:
                description: 请求支付成功
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
                                    $ref: "#/components/schemas/BuyRecordDTO"

        """
        order_id = request.get_json().get('order_id', '')
        channel = request.get_json().get('channel', '')
        client_ip = request.client_ip
        return make_common_response(generate_charge(app, order_id, channel, client_ip))
    
    @app.route(path_prefix+'/init-order', methods=['POST'])
    def init_buy_record():
        user_id = request.get_json().get('user_id', '')
        course_id  = request.get_json().get('course_id', '')
        return make_common_response(success_buy_record(app, user_id, lesson_id))
    @app.route(path_prefix+'/query-order', methods=['POST'])
    def query_order():
        """
        查询订单
        ---
        tags:
            - 订单
        parameters:
            - in: body
              name: body
              required: true
              schema:
                type: object
                properties:
                    order_id:
                        type: string
                        description: 订单id
        responses:

            200:
                description: 查询订单成功
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
                                    $ref: "#/components/schemas/BuyRecordDTO"
    
                        """
        order_id = request.get_json().get('order_id', '')
        return make_common_response(query_buy_record(app, order_id))
    
    return app


