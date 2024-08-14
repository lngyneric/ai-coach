import json
import os
from re import A, M
import time
import logging
from flask import Flask, Response, g,request,send_from_directory,make_response
from flask_cors import CORS
from dotenv import load_dotenv
from flask_migrate import Migrate
from flasgger import Swagger


# 设置时区
# fix windows platform
if os.name == "nt":
    os.system('tzutil /s "UTC"')
else:
    os.environ['TZ'] = 'UTC'
    time.tzset()
app = None
def create_app()->Flask:
    global app
    if app:
        return app
    import pymysql
    pymysql.install_as_MySQLdb()
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    CORS(app, resources={r"/*": {"supports_credentials": True}})
    from flaskr.common import Config,init_log
    app.config = Config(app.config,app)
    ## 初始化日志
    init_log(app)
    ## 初始化数据库
    from flaskr import dao
    dao.init_db(app)
    # 初始化r 和ADMIN相关的表逻辑
    from flaskr.service import admin
    dao.init_redis(app)
    Migrate(app,dao.db)

    ## 初始化其他API
    from flaskr import api
    api.init_langfuse(app)
    # 初始化route
    from flaskr.route import register_route
    app = register_route(app)
    
    ## 初始化swagger
    if app.config.get('SWAGGER_ENABLED',False):
        from flaskr.common import swagger_config
        app.logger.info('swagger init ...')
        swagger = Swagger(app,config=swagger_config,merge=True)

    return app



print('main in app'+__name__)
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0',port=5800,debug=True)
else:
    app = create_app()