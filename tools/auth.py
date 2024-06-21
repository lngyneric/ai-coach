import streamlit as st
import streamlit_authenticator as stauth

import yaml
from yaml.loader import SafeLoader


def login():

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
        st.toast(f'欢迎回来，{st.session_state["name"]}', icon='🎈')
        return login_result
    else:
        return False



