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

        print('Load Config OK!')
except Exception as e:
    print('====!!!! Load Config ERROR !!!!====')
    raise e