import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space

from models.chapter import *
from models.script import *
from tools.utils import load_scripts_and_system_role


def show_current_script(script):
    with st.sidebar:
        st.write(f'当前剧本ID：{script.id}')
        with st.expander('查看剧本内容', expanded=True):
            st.write(script)

