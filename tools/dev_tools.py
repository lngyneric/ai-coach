import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space

from chapter import *
from script import *


def load_process_controller():
    if not st.session_state.has_started:
        nickname = st.query_params.get('nickname')
        industry = st.query_params.get('industry')
        occupation = st.query_params.get('occupation')

        if progress := st.query_params.get('progress'):
            st.session_state.progress = int(progress) - 1
            st.session_state.nickname = nickname if nickname else '小明'
            st.session_state.industry = industry if industry else '互联网'
            st.session_state.occupation = occupation if occupation else '产品经理'
            st.session_state.has_started = True
            logging.debug(f'从 {st.session_state.progress} 开始剧本')
            st.rerun()

        with st.sidebar:
            with st.expander('默认用户Profile'):
                st.session_state.nickname = st.text_input('默认昵称', value=nickname if nickname else '小明')
                st.session_state.industry = st.text_input('默认行业', value=industry if industry else '互联网')
                st.session_state.occupation = st.text_input('默认职业', value=occupation if occupation else '产品经理')

            default_model = st.selectbox('默认 LLM：', cfg.SUPPORT_MODELS)
            cfg.set_default_model(default_model)

            add_vertical_space(2)
            st.write('## 剧本')
            chapter = st.selectbox('选择剧本：', load_chapters_from_sqlite())
            print(chapter)
            print(chapter.lark_table_id)
            progress = st.number_input('开始位置：', value=1, step=1) - 1
            if st.button(f'开始', type='primary', use_container_width=True) or progress:
                if 'script_list' not in st.session_state:
                    with st.spinner('正在加载剧本...'):
                        st.session_state.script_list = load_scripts_from_bitable(
                            cfg.LARK_APP_TOKEN, chapter.lark_table_id, chapter.lark_view_id)
                        st.session_state.script_list_len = len(st.session_state.script_list)
                st.session_state.progress = progress
                st.session_state.has_started = True
                logging.debug(f'从 {st.session_state.progress} 开始剧本')
                st.rerun()


def show_current_script(script):
    with st.sidebar:
        st.write(f'当前剧本ID：{script.id}')
        with st.expander('查看剧本内容', expanded=True):
            st.write(script)

