from flask import Flask, request

from route.common import bypass_token_validation, make_common_response

def register_callback_handler(app: Flask, path_prefix: str):
     
    @app.route(path_prefix+'/pingxx-callback', methods=['POST'])
    @bypass_token_validation
    def pingxx_callback():
        # order_id = request.get_json().get('order_id', '')
        # return make_common_response(success_buy_record(app, order_id))
        body = request.get_json( )
        app.logger.info('pingxx-callback: %s',body)
        return make_common_response({'status':'ok'})
    return app