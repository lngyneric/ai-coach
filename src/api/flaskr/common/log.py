import logging
import os
from flask import Flask, request
import uuid
from logging.handlers import TimedRotatingFileHandler
import threading
import socket
from datetime import datetime
import pytz

thread_local = threading.local()


class RequestFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # create time zone info
        bj_time = pytz.timezone("Asia/Shanghai")
        # convert record.created (a float timestamp) to beijing time
        ct = datetime.fromtimestamp(record.created, bj_time)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            try:
                s = ct.isoformat(timespec="milliseconds")
            except TypeError:
                s = ct.isoformat()
        return s

    def format(self, record):
        try:
            record.url = getattr(thread_local, "url", "No_URL")
            record.request_id = getattr(thread_local, "request_id", "No_Request_ID")
            record.client_ip = getattr(thread_local, "client_ip", "No_Client_IP")
        except RuntimeError:
            record.url = "No_URL"
            record.request_id = "No_Request_ID"
            record.client_ip = "No_Client_IP"
        return super().format(record)


def init_log(app: Flask) -> Flask:
    @app.before_request
    def setup_logging():
        thread_local.request_id = uuid.uuid4().hex
        thread_local.url = request.path
        # try to get user ip from X-Forwarded-For header
        if "X-Forwarded-For" in request.headers:
            user_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
        else:
            # if no X-Forwarded-For header, use remote_addr
            user_ip = request.remote_addr
        request.client_ip = user_ip
        thread_local.client_ip = user_ip

    host_name = socket.gethostname()

    # log_format = '%(asctime)s [%(levelname)s] ai-shifu.com/ai-sifu '+host_name+' %(client_ip)s %(url)s %(request_id)s %(message)s'
    log_format = (
        "%(asctime)s [%(levelname)s] ai-shifu.com/ai-sifu "
        + host_name
        + " %(client_ip)s %(url)s %(request_id)s %(funcName)s %(message)s"
    )
    formatter = RequestFormatter(log_format)

    log_file = app.config.get("LOGGING_PATH", "logs/ai-sifu.log")
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    # split log by day
    file_handler = TimedRotatingFileHandler(
        app.config["LOGGING_PATH"], when="midnight", backupCount=7
    )
    file_handler.setFormatter(formatter)
    # console log handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    if "gunicorn" in os.getenv("SERVER_SOFTWARE", ""):
        gunicorn_logger = logging.getLogger("gunicorn.info")
        if gunicorn_logger.handlers:
            for handler in gunicorn_logger.handlers:
                handler.setFormatter(formatter)
            app.logger.handlers = (
                gunicorn_logger.handlers.copy()
            )  # use gunicorn's handlers
        else:
            app.logger.handlers = []
            app.logger.addHandler(
                file_handler
            )  # add file handler only if no gunicorn handlers
        app.logger.addHandler(console_handler)  # always add console handler
        app.logger.setLevel(gunicorn_logger.level)
    else:
        app.logger.handlers = []  # clear default handlers
        app.logger.addHandler(file_handler)  # add file handler if not gunicorn
        app.logger.addHandler(console_handler)  # always add console handler
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False  # stop propagation
    app.logger.setLevel(logging.INFO)
    app.logger.error("Logging setup complete")
    return app
