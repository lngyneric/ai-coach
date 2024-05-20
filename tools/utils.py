import base64
import random
import time
import logging
import json
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
import streamlit as st
import validators
from streamlit_chatbox import *
from langchain_core.prompts import PromptTemplate


from init import *

_ = load_dotenv(find_dotenv())


def get_current_time(*args, **kwargs):
    return f'现在时间是{time.strftime("%H:%M:%S", time.localtime())}'


def random_placeholder_text():
    text_list = [
        'Your message',
        'Say something',
        '你从何处来 又往何处去',
        '请先搞清楚你自己的定位',
        '月下旅途，终将抵达心之彼岸',
        '心之所向即是归处',
    ]
    return text_list[int(time.time()) % len(text_list)]


# 头像配置
ICON_AI = 'static/didi.png'
ICON_USER = 'user'
ICON_SIFU = 'static/sunner_icon.jpg'


def append_and_show(role, content):
    """
    将消息添加到st的messages列表中，并显示出来
    :param role: 角色，暂时就两个：assistant和user
    :param content: 消息内容
    :return:
    """

    st.session_state.messages.append({"role": role, "content": content})
    st.chat_message(role, avatar=ICON_AI if role == 'assistant' else ICON_USER).write(content)


def fix_sidebar_add_logo(logo_url: str):
    if validators.url(logo_url) is True:
        logo = f"url({logo_url})"
    else:
        logo = f"url(data:image/png;base64,{base64.b64encode(Path(logo_url).read_bytes()).decode()})"

    st.markdown(
        f"""
        <style>
            [data-testid="stSidebarNav"] {{
                background-image: {logo};
                background-repeat: no-repeat;
                background-size: contain;
                padding-top: 70px;
                background-position: 0px 0px;
            }}
            [data-testid="stSidebar"] {{
                max-width: 300px !important;
                min-width: 300px !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def simulate_streaming(chat_box, template: str, variables=None,
                       random_min=cfg.SIM_STM_MIN, random_max=cfg.SIM_STM_MAX, update=False):
    """
    模拟流式输出
    :param chat_box: ChatBox 对象
    :param template: 模版内容
    :param variables: 变量字典
    :param random_min: 随机sleep的最小值
    :param random_max: 随机sleep的最大值
    :param update: 是否更新之前的 chat_box 输出，默认是开启一段新对话
    """
    if not update:
        chat_box.ai_say(Markdown('', in_expander=False))
        
    if variables:
        # 变量字典
        vars = {}
        for v in variables:
            vars[v] = st.session_state[v]
        prompt_template = PromptTemplate(input_variables=list(vars.keys()), template=template)
        template = prompt_template.format(**vars)
        
    current_text = ''
    for t in template:
        current_text += t
        chat_box.update_msg(current_text, element_index=0, streaming=True)
        time.sleep(random.uniform(random_min / 4 if st.session_state.DEV_MODE else random_min,
                                  random_max / 4 if st.session_state.DEV_MODE else random_max))

    chat_box.update_msg(current_text, element_index=0, streaming=False, state="complete")
    return current_text


def streaming_from_template(chat_box, template, variables, 
                            input_done_with=None, parse_keys=None, update=False,
                            model=None):
    """
    通过给定模版和遍历调用LLM，并流式输出（作为AI身份输出）。
    :param chat_box: ChatBox 对象
    :param template: 模版内容（Langchain的PromptTemplate）
    :param variables: 变量字典（支持同时传入多个变量）
    :param input_done_with: 输入完成的标志
    :param parse_keys: 解析JSON的key列表
    :param update: 是否更新之前的 chat_box 输出，默认是开启一段新对话
    :param model: 使用指定的自定义模型，提供模型名称（config.yml 中有支持的模型）
    """

    llm = load_llm() if not model else load_llm(model)

    if not update:
        chat_box.ai_say(Markdown('', in_expander=False))

    if variables:
        prompt = PromptTemplate(input_variables=list(variables.keys()), template=template)
        prompt = prompt.format(**variables)
    else:
        prompt = template

    full_result = ''
    parse_json = ''
    need_streaming_complete = False
    count = 0
    for chunk in llm.stream(prompt):
        if len(chunk.content) == 0:
            continue
        full_result += chunk.content
        if logging.getLogger().level == logging.DEBUG:
            # print(chunk.content, end='', flush=True)
            print(f'{count}: {chunk.content}, len:{len(full_result)}')
            count += 1
            
        if input_done_with and full_result.startswith(input_done_with):
            chat_box.update_msg(input_done_with, element_index=0, streaming=False, state="complete")
        else:
            chat_box.update_msg(full_result, element_index=0, streaming=True)
            need_streaming_complete = True
    
    if need_streaming_complete:
        chat_box.update_msg(full_result, element_index=0, streaming=False, state="complete")

    if logging.getLogger().level == logging.DEBUG:
        print()
    
    if parse_keys:
        # 清理字符串
        parse_json = full_result.replace(input_done_with, '').strip()
        
        logging.debug(f'解析JSON：{parse_json}')
        try:
            parse_json = json.loads(parse_json)
            for k in parse_keys:
                st.session_state[k] = parse_json[k]
                logging.debug(f'已将"{parse_json[k]}"存入session："{k}"中')
        except Exception as e:
            logging.error(f'解析JSON失败：{e}')
        
    return full_result


if __name__ == '__main__':
    # print(get_current_time())
    print(random_placeholder_text())