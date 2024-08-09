from flask import Flask, request

from .common import bypass_token_validation, make_common_response

def register_callback_handler(app: Flask, path_prefix: str):

    # pingxx支付回调
    @app.route(path_prefix+'/pingxx-callback', methods=['POST'])
    @bypass_token_validation
    def pingxx_callback():
        body = request.get_json( )
        app.logger.info('pingxx-callback: %s',body)
        return 'pingxx callback success'
    return app