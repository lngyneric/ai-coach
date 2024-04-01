import logging

import streamlit as st


def load_process_controller():
    if not st.session_state.has_started:
        with st.sidebar:
            with st.expander('默认用户Profile'):
                st.session_state.nickname = st.text_input('默认昵称', value='小明')
                st.session_state.industry = st.text_input('默认行业', value='互联网')
                st.session_state.occupation = st.text_input('默认职业', value='产品经理')
            # add_vertical_space(1)
            st.write('开始位置：')
            st.session_state.progress = st.number_input('', value=0, step=1, label_visibility='collapsed')
            if st.button(f'开始', type='primary', use_container_width=True):
                st.session_state.has_started = True
                logging.debug(f'从 {st.session_state.progress} 开始剧本')
                st.rerun()


def show_current_script(script):
    with st.sidebar:
        st.write(f'当前剧本ID：{script["id"]}')
        with st.expander('查看剧本内容'):
            st.write(script)

