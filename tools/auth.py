import streamlit as st
import streamlit_authenticator as stauth

import yaml
from yaml.loader import SafeLoader


def login():

    # 初始化登录成功欢迎记录
    if 'is_login_welcome' not in st.session_state:
        st.session_state.is_login_welcome = False

    with open('auth_config.yml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['pre-authorized']
    )

    login_result = authenticator.login(
        max_login_attempts=5,
        fields={
            'Form name': '管理员登录',
            'Username': '用户名',
            'Password': '密码',
            'Login': '登录'
        }
    )

    if login_result[1]:
        if not st.session_state.is_login_welcome:
            st.toast(f'欢迎回来，{st.session_state["name"]}', icon='🎈')
            st.session_state.is_login_welcome = True
        return login_result
    else:
        return False



