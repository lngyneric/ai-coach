import os
import yaml


class ConfigManager:
    def __init__(self, config_path='config.yml'):
        self.config_path = config_path

        with open(self.config_path, 'rb') as f:
            config = yaml.safe_load(f)

            _cfg_simulate_streaming_random_sleep = config['simulate_streaming_random_sleep']
            self.SIM_STM_MIN = _cfg_simulate_streaming_random_sleep['min']
            self.SIM_STM_MAX = _cfg_simulate_streaming_random_sleep['max']

            _cfg_llm = config['llm']
            # DEFAULT_VENDOR = _cfg_openai['default_vendor']
            self.DEFAULT_MODEL = _cfg_llm['default_model']
            self.WENXIN_MODELS = _cfg_llm['wenxin']['models']
            self.OPENAI_MODELS = _cfg_llm['openai']['models']
            self.OPENAI_ORG = _cfg_llm['openai']['organization']
            self.SUPPORT_MODELS = self.WENXIN_MODELS + self.OPENAI_MODELS

            _cfg_lark = config['lark']
            self.LARK_APP_TOKEN = _cfg_lark['app_token']
            self.DEF_LARK_TABLE_ID = _cfg_lark['default_table_id']
            self.DEF_LARK_VIEW_ID = _cfg_lark['default_view_id']

            _cfg_fileupload = config['fileupload']
            self.IMG_LOCAL_DIR = _cfg_fileupload['img_local_dir']
            os.makedirs(self.IMG_LOCAL_DIR) if not os.path.exists(self.IMG_LOCAL_DIR) else None
            self.IMG_OSS_ANAME = _cfg_fileupload['img_oss_aname']
            self.IMG_OSS_ENDPOINT = _cfg_fileupload['img_oss_endpoint']
            self.IMG_OSS_BUCKET = _cfg_fileupload['img_oss_bucket']

            _cfg_db = config['db']
            self.SQLITE_DB_PATH = _cfg_db['sqlite']['path']


    def set_default_model(self, model):
        self.DEFAULT_MODEL = model
