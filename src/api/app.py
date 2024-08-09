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



def create_app()->Flask:

    import pymysql
    pymysql.install_as_MySQLdb()
    load_dotenv()
    # 在程序开始时调用 patch_pyppeteer()
    app = Flask(__name__, instance_relative_config=True)
    CORS(app, resources={r"/*": {"supports_credentials": True}})
    from flaskr.common import Config,init_log
    app.config = Config(app.config,app)
    ## 初始化日志
    init_log(app)
    ## 初始化数据库
    from flaskr import dao
    dao.init_db(app)
    dao.init_redis(app)
    Migrate(app,dao.db)

    ## 初始化其他API
    from flaskr import api
    api.init_langfuse(app)
    # 初始化route
    from flaskr import route

    prefix = app.config.get('PATH_PREFIX','')
    app = route.register_common_handler(app)
    app = route.register_user_handler(app,prefix+'/user')
    app = route.register_lesson_handler(app,prefix+'/lesson')
    app = route.register_study_handler(app,prefix+'/study')
    app = route.register_dict_handler(app,prefix+'/dict')
    app = route.register_tools_handler(app,prefix+'/tools')
    app = route.register_order_handler(app,prefix+'/order')
    ## 初始化swagger
    if app.config.get('SWAGGER_ENABLED',False):
        from flaskr.common import swagger_config
        app.logger.info('swagger init ...')
        swagger = Swagger(app,config=swagger_config,merge=True)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0',port=5000,debug=True)
else:
    app = create_app()