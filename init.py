import os

import yaml


# 读取配置文件
try:
    yamlPath = 'config.yml'
    with open(yamlPath, 'rb') as f:
        config = yaml.safe_load(f)
        
        _cfg_simulate_streaming_random_sleep = config['simulate_streaming_random_sleep']
        SIM_STM_MIN = _cfg_simulate_streaming_random_sleep['min']
        SIM_STM_MAX = _cfg_simulate_streaming_random_sleep['max']

        _cfg_llm = config['llm']
        _cfg_openai = _cfg_llm['openai']
        OPENAI_MODEL = _cfg_openai['model']
        OPENAI_ORG = _cfg_openai['organization']

        _cfg_lark = config['lark']
        LARK_APP_TOKEN = _cfg_lark['app_token']
        LARK_TABLE_ID = _cfg_lark['table_id']
        LARK_VIEW_ID = _cfg_lark['view_id']

        _cfg_fileupload = config['fileupload']
        IMG_LOCAL_DIR = _cfg_fileupload['img_local_dir']
        os.makedirs(IMG_LOCAL_DIR) if not os.path.exists(IMG_LOCAL_DIR) else None
        IMG_OSS_ANAME = _cfg_fileupload['img_oss_aname']
        IMG_OSS_ENDPOINT = _cfg_fileupload['img_oss_endpoint']
        IMG_OSS_BUCKET = _cfg_fileupload['img_oss_bucket']

        print('Load Config OK!')
except Exception as e:
    print('====!!!! Load Config ERROR !!!!====')
    raise e
