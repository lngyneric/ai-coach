import base64
import random
import time
from pathlib import Path

import streamlit as st
import validators
from streamlit_chatbox import *
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from init import *
from script import *

_ = load_dotenv(find_dotenv())


# 头像配置
ICON_USER = 'user'
ICON_SIFU = 'static/sunner_icon.jpg'


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
        time.sleep(random.uniform(random_min / 20 if st.session_state.DEV_MODE else random_min,
                                  random_max / 20 if st.session_state.DEV_MODE else random_max))

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
    logging.debug(f'调用LLM（Human）：{prompt}')
    llm_input = [HumanMessage(prompt)]
    if 'system_role' in st.session_state:
        llm_input.append(SystemMessage(st.session_state.system_role))
        logging.debug(f'调用LLM（System）：{st.session_state.system_role}')

    full_result = ''
    parse_json = ''
    need_streaming_complete = False
    count = 0
    # for chunk in llm.stream(prompt, system=st.session_state.system_role):
    for chunk in llm.stream(llm_input):
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
    
    if parse_keys is not None and full_result.startswith(input_done_with):
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
            full_result = '抱歉出现错误，请再次尝试~'
            chat_box.update_msg(full_result, element_index=0, streaming=False, state="complete")
        
    return full_result


def distribute_elements(btns, max_cols, min_cols):
    num_elements = len(btns)
    if num_elements < min_cols:
        raise ValueError("元素数量不足以满足最小列要求")

    result = []
    row = []

    # 按行填充元素，满了就新起一行
    for btn in btns:
        row.append(btn)
        if len(row) == max_cols:
            result.append(row)
            row = []

    # 处理剩余的不满一行的元素
    if row:
        result.append(row)

    # 检查最后一行是否满足最小列数要求，如果不满足，则尝试从前面的行借元素
    while len(result[-1]) < min_cols:
        # 从倒数第二行开始借元素
        for i in range(len(result) - 2, -1, -1):
            while len(result[i]) > min_cols and len(result[-1]) < min_cols:
                result[-1].insert(0, result[i].pop())  # 从前一行的末尾取元素到最后一行的开头
            if len(result[-1]) >= min_cols:
                break
        else:
            # 如果所有行都无法借出更多元素，则抛出异常
            raise ValueError("无法满足最小列要求，元素过少或分布不均")

    return result


def load_scripts_and_system_role(
        app_token=cfg.LARK_APP_TOKEN,
        table_id=cfg.DEF_LARK_TABLE_ID,
        view_id=cfg.DEF_LARK_VIEW_ID
):
    if 'script_list' not in st.session_state:
        with st.spinner('正在加载剧本...'):
            st.session_state.script_list = load_scripts_from_bitable(app_token, table_id, view_id)
            if st.session_state.script_list[0].type == ScriptType.SYSTEM:
                system_role_script = st.session_state.script_list.pop(0)
                template = system_role_script.template
                variables = {v: st.session_state[v] for v in system_role_script.template_vars} if system_role_script.template_vars else None

                if variables:
                    prompt = PromptTemplate(input_variables=list(variables.keys()), template=template)
                    prompt = prompt.format(**variables)
                else:
                    prompt = template

                st.session_state.system_role = prompt

            st.session_state.script_list_len = len(st.session_state.script_list)


if __name__ == '__main__':
    # print(get_current_time())
    pass
