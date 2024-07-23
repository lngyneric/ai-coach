import logging
from flask import Flask,g ,request
import uuid
from logging.handlers import TimedRotatingFileHandler
import threading
thread_local = threading.local()

class RequestFormatter(logging.Formatter):
    def format(self, record):
        # 尝试从请求上下文中获取 URL 和 request_id
        try:
            record.url = getattr(thread_local, 'url', 'No_URL')
            record.request_id = getattr(thread_local, 'request_id', 'No_Request_ID')
        except RuntimeError:
            record.url = "No_URL"
            record.request_id = "No_Request_ID"
        return super().format(record)

def init_log(app:Flask)->Flask:
    @app.before_request
    def setup_logging():
        thread_local.request_id = uuid.uuid4().hex
        thread_local.url = request.path

    log_format = '%(asctime)s [%(levelname)s] com.kattgatt/ai-asisstant %(name)s %(url)s %(request_id)s %(message)s'
    formatter = RequestFormatter(log_format)
    file_handler = TimedRotatingFileHandler(app.config['LOGGING_PATH'], when='midnight', backupCount=7)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    print("app.logger.handlers:{}".format(app.logger.handlers))
    print("main:{}".format(__name__))
    if __name__ != "__main__":
        gunicorn_logger = logging.getLogger('gunicorn.error')
        if len(gunicorn_logger.handlers) > 0:
            for gunicorn_handler in gunicorn_logger.handlers:
                print("gunicorn_handler:{}".format(gunicorn_handler)) 
                app.logger.handlers.append(gunicorn_handler) 
            app.logger.addHandler(file_handler)
            app.logger.setLevel(gunicorn_logger.level)
        # else:
        #     app.logger.setLevel(logging.INFO)
        for handler in app.logger.handlers:
            handler.setFormatter(formatter)
    app.logger.setLevel(logging.INFO)
   
    return app 