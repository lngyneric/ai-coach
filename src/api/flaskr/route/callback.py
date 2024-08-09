from flask import Flask, make_response, request
from h11 import Response

from .common import bypass_token_validation, make_common_response

def register_callback_handler(app: Flask, path_prefix: str):

    # pingxx支付回调
    @app.route(path_prefix+'/pingxx-callback', methods=['POST'])
    @bypass_token_validation
    def pingxx_callback():
        body = request.get_json( )
        app.logger.info('pingxx-callback: %s',body)
        response = make_response("pingxx callback success")
        response.mimetype = 'text/plain'
        return response
    
        
    return app