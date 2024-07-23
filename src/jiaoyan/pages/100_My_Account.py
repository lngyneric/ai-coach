import streamlit as st
import streamlit_authenticator as stauth
from streamlit_extras.add_vertical_space import add_vertical_space

import yaml
from yaml.loader import SafeLoader

with open('auth_config.yml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

authenticator.login(
    max_login_attempts=5,
    fields={
        'Form name': '管理员登录',
        'Username': '用户名',
        'Password': '密码',
        'Login': '登录'
    }
)
# st.toast('登录成功！', icon='🎈')


if st.session_state["authentication_status"]:
    st.write('# 个人帐户管理 🧑‍💼🔐🧑‍💼')
    st.caption(f'欢迎 *{st.session_state["name"]}*')

    # 退出登录
    if st.button('退出登录', use_container_width=True):
        authenticator.logout(location='unrendered')
        st.session_state.is_login_welcome = False

    add_vertical_space(2)

    # 修改用户信息
    if st.session_state["authentication_status"]:
        try:
            if authenticator.update_user_details(
                username=st.session_state["username"],
                fields={
                    'Form name': '更新用户信息',
                    'Field': '要更新的字段',
                    'Name': '用户名',
                    'Email': '邮箱',
                    'New value': '更新为',
                    'Update': '更新'
                }
            ):
                with open('auth_config.yml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
                st.success('用户信息更新成功')
        except Exception as e:
            st.error(e)

    add_vertical_space(2)

    # 重置密码
    try:
        if authenticator.reset_password(
            username=st.session_state["username"],
            fields={
                'Form name': '重置密码',
                'Current password': '当前密码',
                'New password': '新密码',
                'Repeat password': '重复新密码',
                'Reset': '重置'
            }
        ):
            with open('auth_config.yml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
            st.success('密码重置成功')
    except Exception as e:
        st.error(e)


elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
