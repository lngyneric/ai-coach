import enum
from prompt import agent, trial

class InputFor(enum):
    SAVE_PROFILE = 'save_profile'

class BtnFor(enum):
    CONTINUE = 'continue'
    


SCRIPT = [
    {'id': 1, 'type': 'fixed', 'format': 'Markdown', 'content': trial.HELLO, 
     'show_input': False, 'show_btn': False},
    {'id': 2, 'type': 'fixed', 'format': 'Markdown', 'content': trial.WELCOME,
     'show_input': True, 'input_placeholder': '请输入你的昵称（仅昵称）', 
     'check_input': agent.CHECK_NICKNAME, 'input_ok_with': 'OK',
     'input_for': InputFor.SAVE_PROFILE, 'save_key': 'nickname',
     'show_btn': False},
    {'id': 3, 'type': 'prompt', 'prompt': agent.SAY_HELLO, 'show_input': False,
     'show_btn': True, 'btn_label': '继续', 'btn_type': 'primary', 'use_container_width': True,
     'btn_for': BtnFor.CONTINUE},
    {'id': 4, 'type': 'fixed', 'format': 'Markdown', 'content': trial.TELL_ME_YOUR_BUSINESS,
     'show_input': True, 'input_placeholder': '请输入你在什么行业从事什么岗位', 
     'check_input': agent.CHECK_BUSINESS, 'input_ok_with': '好的。',
     'input_for': InputFor.SAVE_PROFILE, 'save_key': 'business',
     'show_btn': False},
]