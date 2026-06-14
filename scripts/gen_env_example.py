#!/usr/bin/env python3
"""Generate .env.example from .env by replacing all secret values with placeholders."""
import re

with open('docker/.env') as f:
    content = f.read()

# Known secret env vars and their placeholder values
secrets = {
    'ARK_API_KEY': 'YOUR_ARK_API_KEY',
    'DEEPSEEK_API_KEY': 'YOUR_DEEPSEEK_API_KEY',
    'NVIDIA_API_KEY': 'YOUR_NVIDIA_API_KEY',
    'OPENAI_API_KEY': 'YOUR_OPENAI_API_KEY',
    'MINIMAX_API_KEY': 'YOUR_MINIMAX_API_KEY',
    'BAIDU_TTS_API_KEY': 'YOUR_BAIDU_TTS_API_KEY',
    'BAIDU_TTS_SECRET_KEY': 'YOUR_BAIDU_TTS_SECRET_KEY',
    'ALIYUN_AK_ID': 'YOUR_ALIYUN_AK_ID',
    'ALIYUN_AK_SECRET': 'YOUR_ALIYUN_AK_SECRET',
    'ALIYUN_TTS_APPKEY': 'YOUR_ALIYUN_TTS_APPKEY',
    'ALIYUN_TTS_TOKEN': 'YOUR_ALIYUN_TTS_TOKEN',
    'GEMINI_API_KEY': 'YOUR_GEMINI_API_KEY',
    'QWEN_API_KEY': 'YOUR_QWEN_API_KEY',
    'ERNIE_API_KEY': 'YOUR_ERNIE_API_KEY',
    'ERNIE_API_SECRET': 'YOUR_ERNIE_API_SECRET',
    'GLM_API_KEY': 'YOUR_GLM_API_KEY',
    'SILICON_API_KEY': 'YOUR_SILICON_API_KEY',
    'LARK_APP_ID': 'YOUR_LARK_APP_ID',
    'LARK_APP_SECRET': 'YOUR_LARK_APP_SECRET',
    'FEISHU_APP_ID': 'YOUR_FEISHU_APP_ID',
    'FEISHU_APP_SECRET': 'YOUR_FEISHU_APP_SECRET',
    'ERNIE_API_ID': 'YOUR_ERNIE_API_ID',
    'MINIMAX_GROUP_ID': 'YOUR_MINIMAX_GROUP_ID',
    'WECHATPAY_BASE_URL': 'https://api.mch.weixin.qq.com',
}

for key, placeholder in secrets.items():
    pattern = re.compile(r'^(' + re.escape(key) + r'=).*$', re.MULTILINE)
    content = pattern.sub(r'\1' + placeholder, content)

with open('docker/.env.example', 'w') as f:
    f.write(content)

print('Created docker/.env.example')
print(f'Lines: {len(content.splitlines())}')
