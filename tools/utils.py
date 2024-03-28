import random
import time
import logging

import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(model='gpt-4', organization='org-fC5Q2f4MQIEaTOa3k8vTQu6G')

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


def simulate_streaming(text: str):
    for t in text:
        yield t
        # 随机sleep 0.1~0.5 秒
        # time.sleep(random.uniform(0.001, 0.1))
        time.sleep(random.uniform(0.001, 0.01))


def streaming_from_template(chat_box, template, variables, update=False):
    if not update:
        chat_box.ai_say('')
    prompt_template = PromptTemplate(input_variables=list(variables.keys()), template=template)
    full_result = ''
    for chunk in llm.stream(prompt_template.format(**variables)):
        full_result += chunk.content
        chat_box.update_msg(full_result, element_index=0, streaming=True)
        if logging.getLogger().level == logging.DEBUG:
            print(chunk.content, end='', flush=True)
    chat_box.update_msg(full_result, element_index=0, streaming=False, state="complete")

    if logging.getLogger().level == logging.DEBUG:
        print()
    return full_result

if __name__ == '__main__':
    # print(get_current_time())
    print(random_placeholder_text())