from enum import Enum
from prompt import agent, trial


class Type(Enum):
    FIXED = 'fixed'
    PROMPT = 'prompt'


class Format(Enum):
    MARKDOWN = 'markdown'
    IMAGE = 'image'


class InputFor(Enum):
    SAVE_PROFILE = 'save_profile'


class BtnFor(Enum):
    CONTINUE = 'continue'
    

SCRIPT_LIST = [
    {'id': 1, 'type': Type.FIXED, 'format': Format.MARKDOWN, 
     'template': trial.HELLO, 'template_vars': None,
     'show_input': False, 
     'show_btn': False},
    
    {'id': 2, 'type': Type.FIXED, 'format': Format.MARKDOWN, 
     'template': trial.WELCOME, 'template_vars': None,
     'show_input': True, 
     'input_placeholder': '请输入你的昵称（仅昵称）', 
     'check_input': agent.CHECK_NICKNAME, 'input_done_with': 'OK',  # 目前 check_input 仅支持传递一个变量，固定名称为 input 
     'parse_keys': None,
     'input_for': InputFor.SAVE_PROFILE, 'save_key': 'nickname',
     'show_btn': False},
    
    {'id': 3, 'type': Type.PROMPT, 
     'template': trial.SAY_HELLO, 'template_vars': ['nickname'],  # 目前 prompt_var 仅支持传递一个变量
     'show_input': False,
     'show_btn': True, 
     'btn_label': '继续', 'btn_type': 'primary', 'use_container_width': True,
     'btn_for': BtnFor.CONTINUE},
    
    {'id': 4, 'type': Type.FIXED, 'format': Format.MARKDOWN, 
     'template': trial.TELL_ME_YOUR_BUSINESS, 'template_vars': ['nickname'],
     'show_input': True, 
     'input_placeholder': '请输入你在什么行业从事什么岗位', 
     'check_input': agent.CHECK_BUSINESS, 'input_done_with': 'OK',
     'parse_keys': ['industry', 'occupation'],
     #  'input_for': InputFor.SAVE_PROFILE, 'save_key': 'business',
     'input_for': None, 'save_key': None,
     'show_btn': False},
    
    {'id': 5, 'type': Type.PROMPT, 
     'template': trial.PRAISE_INDUSTRY_OCCUPATION, 'template_vars': ['industry', 'occupation'],  # 目前 prompt_var 仅支持传递一个变量
     'show_input': False,
     'show_btn': True, 
     'btn_label': '继续', 'btn_type': 'primary', 'use_container_width': True,
     'btn_for': BtnFor.CONTINUE},  # TODO：需要新增again按钮功能
    
    {'id': 6, 'type': Type.FIXED, 'format': Format.MARKDOWN, 
     'template': trial.FIXED_6, 'template_vars': None,
     'show_input': False, 
     'show_btn': True, 
     'btn_label': '真的吗？', 'btn_type': 'primary', 'use_container_width': True,
     'btn_for': BtnFor.CONTINUE},
    
    {'id': 7, 'type': Type.FIXED, 'format': Format.MARKDOWN, 
     'template': trial.FIXED_7, 'template_vars': None,
     'show_input': False, 
     'show_btn': True, 
     'btn_label': '有道理！继续~', 'btn_type': 'primary', 'use_container_width': True,
     'btn_for': BtnFor.CONTINUE},
    
    {'id': 8, 'type': Type.FIXED, 'format': Format.MARKDOWN, 
     'template': trial.FIXED_8, 'template_vars': None,
     'show_input': False, 
     'show_btn': True, 
     'btn_label': '有啥用？', 'btn_type': 'primary', 'use_container_width': True,
     'btn_for': BtnFor.CONTINUE},
    
    {'id': 9, 'type': Type.PROMPT, 
     'template': trial.WHATS_USE_OF, 'template_vars': ['industry', 'occupation'],  # 目前 prompt_var 仅支持传递一个变量
     'show_input': False,
     'show_btn': True, 
     'btn_label': '太好了！我要学！', 'btn_type': 'primary', 'use_container_width': True,
     'btn_for': BtnFor.CONTINUE},  # TODO：需要新增again按钮功能
    
    {'id': 10, 'type': Type.FIXED, 'format': Format.MARKDOWN, 
     'template': trial.PROMOTE, 'template_vars': None,
     'show_input': False, 
     'show_btn': True, 
     'btn_label': '出发！', 'btn_type': 'primary', 'use_container_width': True,
     'btn_for': BtnFor.CONTINUE},
    
    # {'id': 11, 'type': Type.FIXED, 'format': Format.MARKDOWN,
    #  'template': trial.PAY_URL, 'template_vars': None,
    #  'show_input': False,
    #  'show_btn': False},

    {'id': 11, 'type': Type.FIXED, 'format': Format.IMAGE,
     # 'template': trial.PAY_URL, 'template_vars': None,
     'media_url': trial.PAY_IMAGE_URL,
     'show_input': False,
     'show_btn': False},
]