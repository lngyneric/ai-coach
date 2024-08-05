import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space

from models.chapter import *
from models.script import *
from tools.utils import load_scripts_and_system_role


def load_process_controller():
    if not st.session_state.has_started:
        nickname = st.query_params.get('nickname')
        industry = st.query_params.get('industry')
        occupation = st.query_params.get('occupation')
        ai_tools = st.query_params.get('ai_tools')
        style = st.query_params.get('style')
        q_model = st.query_params.get('model')
        q_temperature = st.query_params.get('temperature')
        table = st.query_params.get('table')

        if progress := st.query_params.get('progress'):
            st.session_state.progress = int(progress) - 1
            st.session_state.nickname = nickname if nickname else '小明'
            st.session_state.industry = industry if industry else '互联网'
            st.session_state.occupation = occupation if occupation else '产品经理'
            st.session_state.ai_tools = ai_tools if ai_tools else 'GitHub_Copilot'
            st.session_state.style = style if style else '幽默风趣'
            cfg.set_default_model(q_model if q_model else cfg.ORIGINAL_DEFAULT_MODEL)
            if q_temperature:
                cfg.set_openai_default_temperature(q_temperature)
                cfg.set_qianfan_default_temperature(q_temperature)
            st.session_state.table = table if table else None
            if st.session_state.table:
                load_scripts_and_system_role(cfg.LARK_APP_TOKEN, st.session_state.table, cfg.DEF_LARK_VIEW_ID)
                if 'system_role' in st.session_state:
                    st.session_state.progress -= 1
                logging.debug(f'从 {st.session_state.progress} 开始剧本（{st.session_state.table}）')
            else:
                logging.debug(f'从 {st.session_state.progress} 开始默认剧本（{cfg.DEF_LARK_TABLE_ID}）')
            st.session_state.has_started = True
            st.rerun()

        with st.sidebar:
            with st.expander('默认用户Profile'):
                st.session_state.nickname = st.text_input('默认昵称', value=nickname if nickname else '小明')
                st.session_state.industry = st.text_input('默认行业', value=industry if industry else '互联网')
                st.session_state.occupation = st.text_input('默认职业', value=occupation if occupation else '产品经理')
                st.session_state.ai_tools = st.text_input('默认AI工具', value=ai_tools if ai_tools else 'GitHub_Copilot')
                st.session_state.style = st.text_input('默认风格', value=style if style else '幽默风趣')

            with st.expander('默认 LLM 配置'):
                # default_model = st.selectbox('默认 LLM：', cfg.SUPPORT_MODELS,
                #                              index=cfg.SUPPORT_MODELS.index(cfg.DEFAULT_MODEL))
                cfg.set_default_model(st.selectbox('默认 LLM：', cfg.SUPPORT_MODELS,
                                                   index=cfg.SUPPORT_MODELS.index(cfg.DEFAULT_MODEL)))
                cfg.set_qianfan_default_temperature(st.number_input('QianFan 默认温度：', value=cfg.QIANFAN_DEF_TMP))
                cfg.set_openai_default_temperature(st.number_input('OpenAI 默认温度：', value=cfg.OPENAI_DEF_TMP))


            add_vertical_space(1)
            # st.write('## 剧本')
            chapter = st.selectbox('选择剧本：', load_chapters_from_sqlite())
            progress = st.number_input('开始位置：', value=2, min_value=1, step=1) - 2
            if st.button(f'开始', type='primary', use_container_width=True) or progress:
                # 加载剧本及系统角色
                load_scripts_and_system_role(cfg.LARK_APP_TOKEN, chapter.lark_table_id, chapter.lark_view_id)

                progress += 1 if 'system_role' not in st.session_state else 0
                st.session_state.progress = progress
                st.session_state.has_started = True
                logging.debug(f'从 {st.session_state.progress} 开始剧本')
                st.rerun()


def show_current_script(script):
    with st.sidebar:
        st.write(f'当前剧本ID：{script.id}')
        with st.expander('查看剧本内容', expanded=True):
            st.write(script)

