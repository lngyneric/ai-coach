import json
import logging
import random

from streamlit_chatbox import *
from langchain_openai import ChatOpenAI

from tools.utils import *
from prompt import trial, agent


# ========== 基础初始化工作 ==========
# 日志级别设置
logging.basicConfig(level=logging.DEBUG)  # 如需要更细致的观察run状态时可以将 `level` 的值改为 `logging.DEBUG`

chat_box = ChatBox(
    assistant_avatar=ICON_SIFU,
)


# llm = ChatOpenAI(model='gpt-4', organization='org-fC5Q2f4MQIEaTOa3k8vTQu6G')

# ========== Streamlit 初始化 ==========
# 设置页面标题和图标
st.set_page_config(
    page_title="CodeSifu",
    page_icon="🧙‍♂️",  # 👨‍🏫
)

'# Code Sifu ⌨️🧙‍♂️⌨️'  # 📚
st.caption('📚 你的专属AI编程私教')


with st.sidebar:
    st.subheader('start to chat using streamlit')
    streaming = st.checkbox('streaming', True)
    in_expander = st.checkbox('show messages in expander', True)

chat_box.init_session()
chat_box.output_messages()


# # ========== Streamlit 对话框架初始化 ==========
# # 初始化messages列表到Streamlit的session_state中
# if "messages" not in st.session_state:
#     st.session_state["messages"] = [{"role": "assistant", "content": trial.HELLO}]

# # 将st中的messages列表中的消息显示出来
# for msg in st.session_state.messages:
#     st.chat_message(msg["role"], avatar=ICON_SIFU if msg["role"] == 'assistant' else ICON_USER).write(msg["content"])

if "has_welcome" not in st.session_state:
    st.session_state['has_welcome'] = False
if "has_nickname" not in st.session_state:
    st.session_state['has_nickname'] = False


nick_name = ''
# ========== 固定的欢迎部分 ==========
if not st.session_state['has_welcome']:
    st.session_state['has_welcome'] = True
    text = trial.HELLO
    chat_box.ai_say(
        Markdown(text, in_expander=False)
    )

    simulate_streaming(chat_box, trial.WELCOME)


if not st.session_state['has_nickname']:        
    # 开始出现输入框
    if user_prompt := st.chat_input('请输入你的名字'):
        chat_box.user_say(user_prompt)
        
        
        full_result = streaming_from_template(chat_box, agent.CHECK_NICKNAME, {"input": user_prompt})
        logging.debug(f'CHECK_NICKNAME: {full_result}')
        
        if full_result == 'OK':
            nick_name = user_prompt
            logging.info(f'用户昵称：{nick_name}')
            st.session_state['has_nickname'] = True
            
            full_result = streaming_from_template(chat_box, agent.SAY_HELLO, {"nickname": user_prompt}, update=True)
            logging.debug(f'SAY_HELLO: {full_result}')
            st.rerun()
            

if st.session_state['has_nickname']:
    st.button('继续', type='primary', use_container_width=True)