import logging
import time

from streamlit_extras.bottom_container import bottom

from models.course import get_courses_by_user_from_sqlite
from tools.lark import get_bitable_tables
from tools.utils import *
from tools.dev_tools import *
from models.script import *
from tools.auth import login


# ==================== 各种初始化工作 ====================
# 设置页面标题和图标
st.set_page_config(
    page_title="Chapter Debugger",
    page_icon="🧙‍♂️",  # 👨‍🏫
)
# 页面内的大标题小标题
'# Chapter Debugger ⌨️🧙‍♂️⌨️'  # 📚
st.caption('📚 加载章节剧本模拟用户体验进行线性调试')


# ========== Debug 初始化 ==========
# 日志级别设置
logging.basicConfig(level=logging.DEBUG)  # 如需要更细致的观察run状态时可以将 `level` 的值改为 `logging.DEBUG`
# 是否开启开发模式
st.session_state.DEV_MODE = True if st.query_params.get('dev') else False
logging.info(f'DEV_MODE: {st.session_state.DEV_MODE}')

# ========== chat_box 初始化 ==========
chat_box = ChatBox(assistant_avatar=ICON_SIFU)
chat_box.init_session()
chat_box.output_messages()

# ========== session 初始化 ==========
# 初始化进展ID
if 'progress' not in st.session_state:
    st.session_state.progress = 0

# 记录剧本是否输出
if 'script_has_output' not in st.session_state:
    st.session_state.script_has_output = set()

if 'has_started' not in st.session_state:
    st.session_state.has_started = False

# if 'lark_app_token' not in st.session_state:
#     st.session_state.lark_app_token = ''

if 'miss_vars' not in st.session_state:
    st.session_state.miss_vars = False

# ======================================================

# ==================== Sidebar ====================
with st.sidebar:
    st.caption('飞书中更新后可以点击清除缓存')
    if st.button('Clean all cache', use_container_width=True):
        st.cache_data.clear()


# ==================== 主体框架 ====================
# 需要登录
import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth



if not st.session_state.has_started:

    with open('auth_config.yml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Pre-hashing all plain text passwords once
    # Hasher.hash_passwords(config['credentials'])

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['pre-authorized']
    )

    authenticator.login()

    if st.session_state['authentication_status']:
        # authenticator.logout()
        # st.write(f'Welcome *{st.session_state["name"]}*')
        # st.title('Some content')


        courses = get_courses_by_user_from_sqlite(st.session_state["username"])
        # courses = get_courses_by_user_from_sqlite('kenrick')
        if not courses:
            st.warning(' 暂无课程，请前往我的账户新建课程。  ⬇️ ⬇️ ⬇️', icon='⚠️')
            if st.button('前往我的账户', type='primary', use_container_width=True):
                st.switch_page("pages/100_My_Account.py")
            st.stop()

        col1, col2, col3 = st.columns(3)
        with col1:
            selected_course = st.selectbox('选择课程:', (course.course_name for course in courses))

        if selected_course:
            st.session_state.lark_app_token = next(
                (course.lark_app_token for course in courses if course.course_name == selected_course), None)
            tables = get_bitable_tables(st.session_state.lark_app_token)

            with col2:
                select_table = st.selectbox('选择章节:', (
                    table.name for table in tables if not table.name.startswith('字典-')))
                st.session_state.lark_table_id = next(
                    (table.table_id for table in tables if table.name == select_table), None)
                # 加载剧本及系统角色
                if 'script_list' in st.session_state:
                    del st.session_state['script_list']  # clear before load
                load_scripts_and_system_role(st.session_state.lark_app_token, st.session_state.lark_table_id)

            with (col3):
                # st.session_state.select_progress = st.number_input('开始位置:', value=2, min_value=1, step=1)
                # st.session_state.select_progress
                select_script = st.selectbox('开始位置:', st.session_state.script_list)
                st.session_state.progress = st.session_state.script_list.index(select_script)
                # st.write(f'选中的剧本在列表中的位置序号是: {index}')

                # st.session_state.progress = st.session_state.select_progress - (
                #     2 if 'system_role' in st.session_state else 1)

        if select_script:
            st.text_area('剧本内容', select_script.template, disabled=True, height=200)

        if st.button('启动剧本', type='primary', use_container_width=True):
            st.session_state.has_started = True
            # st.rerun()

    elif st.session_state['authentication_status'] is False:
        st.error('Username/password is incorrect')
    elif st.session_state['authentication_status'] is None:
        st.warning('Please enter your username and password')

# 非开发者模式直接开始，若在开发者模式则等待配置后开始
# if not st.session_state.DEV_MODE or st.session_state.has_started:
else:

    # 获取剧本总长度，并在结束时停止
    if st.session_state.progress >= st.session_state.script_list_len:
        # chat_box.ai_say('别再犹豫了，马上把我带回家吧~')
        with bottom():
            st.write('')
        st.stop()

    # 根据当前进度ID，获取对应的剧本
    script: Script = st.session_state.script_list[st.session_state.progress]
    logging.debug(f'当前剧本：\n{script}')
    # if st.session_state.DEV_MODE:
    #     show_current_script(script)

    needed_vars = extract_variables(script.template)
    # st.session_state
    if needed_vars:
        logging.debug('=== need vars')
        missing_vars = [var for var in needed_vars if var not in st.session_state]

        has_empty_val = False
        for var in needed_vars:
            if not st.session_state.get(var):
                has_empty_val = True
                break

        if missing_vars or has_empty_val:
            logging.debug('=== if missing_vars or has_empty_val')
            st.session_state.miss_vars = True

            # with st.form('missing_vars'):
            with st.expander('Now Script Template:', expanded=True):
                st.text_area('剧本内容', script.template, disabled=True, height=300)
            st.write(f'需要变量: **{needed_vars}**,   缺失: **{missing_vars}**')
            with st.form('missing_vars'):
                for var in missing_vars:
                    val = st.text_input(f'输入 {var} 的值：')
                    if val != '':
                        st.session_state[var] = val

                submitted = st.form_submit_button('提交变量继续', type='primary', use_container_width=True)
                if submitted:
                    st.session_state.miss_vars = False
                    # time.sleep(5)
                    # st.rerun()
        else:
            st.session_state.miss_vars = False

    # 没有缺失的 vars 时才能继续：
    if not st.session_state.miss_vars:

        # ========== 内容输出部分 ==========
        # 如果剧本没有输出过，则进行输出
        if script.id not in st.session_state.script_has_output:
            full_result = None

            # ===【固定剧本】：模拟流式输出
            if script.type == ScriptType.FIXED:
                if script.format == ScriptFormat.MARKDOWN:
                    logging.debug('=== 打算模拟输出了')
                    full_result = simulate_streaming(chat_box, script.template, script.template_vars)
                elif script.format == ScriptFormat.IMAGE:
                    chat_box.ai_say(Image(script.media_url))
                    full_result = script.media_url

            # == 【Prompt】：剧本内容提交给 LLM，获得AI回复输出
            elif script.type == ScriptType.PROMPT:
                full_result = streaming_from_template(
                    chat_box, script.template,
                    {v: st.session_state[v] for v in script.template_vars} if script.template_vars else None,
                    model=script.custom_model, temperature=script.temperature
                )

            # 最后记录下已输出的剧本ID，避免重复输出
            st.session_state.script_has_output.add(script.id)
            logging.debug(f'script id: {script.id}, chat result: {full_result}')

        # ========== 处理【后续交互】 ==========
        # === 显示 输入框
        if script.next_action == NextAction.ShowInput:
            # 获取用户输入
            if user_input := st.chat_input(script.input_placeholder):
                chat_box.user_say(user_input)  # 展示用户输入信息

                # 通过 `检查模版` 提取变量（JSON mode）
                is_ok = parse_vars_from_template(chat_box, script.check_template, {'input': user_input},
                                                 parse_keys=script.parse_vars,
                                                 model=script.custom_model, temperature=script.temperature)

                # 如果正常执行，则进入下一个剧本
                if is_ok:
                    st.session_state.progress += 1
                    st.rerun()

        # === 显示 按钮
        elif script.next_action == NextAction.ShowBtn:
            with bottom():
                if st.button(script.btn_label, type='primary', use_container_width=True):
                    st.session_state.progress += 1
                    st.rerun()

        # === 显示 按钮组
        elif script.next_action == NextAction.ShowBtnGroup:
            with bottom():
                btns = distribute_elements(script.btn_group_cfg['btns'], 3, 2)
                for row in btns:
                    st_cols = st.columns(len(row))
                    for i, btn in enumerate(row):
                        if st_cols[i].button(btn['label'], key=btn['value'], type='primary',
                                             use_container_width=True):
                            # 获取用户点击按钮的 value
                            st.session_state[script.btn_group_cfg['var_name']] = btn['value']
                            st.session_state.progress += 1
                            st.rerun()

        # === 跳转按钮
        elif script.next_action == NextAction.JumpBtn:
            if st.button(script.btn_label, type='primary', use_container_width=True):
                # 获取需要判断的变量值
                var_value = st.session_state.get(script.btn_jump_cfg['var_name'])
                # == 如果是静默跳转
                if script.btn_jump_cfg['jump_type'] == 'silent':
                    # 找到要跳转的子剧本
                    lark_table_id, lark_view_id = None, None
                    for jump_rule in script.btn_jump_cfg['jump_rule']:
                        if var_value == jump_rule['value']:
                            lark_table_id = jump_rule['lark_table_id']
                            lark_view_id = jump_rule['lark_view_id']

                    # 如果找到了则加载，否则报错
                    if lark_table_id:
                        sub_script_list = load_scripts_from_bitable(cfg.LARK_APP_TOKEN, lark_table_id,
                                                                    lark_view_id)
                        # 将子剧本插入到原剧本中
                        st.session_state.script_list = (
                                st.session_state.script_list[:st.session_state.progress + 1]
                                + sub_script_list
                                + st.session_state.script_list[st.session_state.progress + 1:]
                        )
                        # 更新剧本总长度
                        st.session_state.script_list_len = len(st.session_state.script_list)
                        # 更新剧本进度
                        st.session_state.progress += 1
                        # 重新运行
                        st.rerun()

                    else:
                        raise ValueError('未找到对应的子剧本')

        # === 显示 付款码
        elif script.next_action == NextAction.ShowPayQR:
            pass

        # === 输入 手机号
        elif script.next_action == NextAction.InputPhoneNum:
            # 获取用户输入
            if user_input := st.chat_input(script.input_placeholder):
                chat_box.user_say(user_input)  # 展示用户输入信息

                # 暂时不做任何处理，直接下一步
                st.info('暂时不做任何处理，直接下一步', icon="ℹ️")
                time.sleep(1)
                st.session_state.progress += 1
                st.rerun()

        # === 输入 验证码
        elif script.next_action == NextAction.InputVerifyCode:
            # 获取用户输入
            if user_input := st.chat_input(script.input_placeholder):
                chat_box.user_say(user_input)  # 展示用户输入信息

                # 暂时不做任何处理，直接下一步
                st.info('暂时不做任何处理，直接下一步', icon="ℹ️")
                time.sleep(1)
                st.session_state.progress += 1
                st.rerun()

        else:
            st.session_state.progress += 1
            st.rerun()



    # st.session_state

    # # 开发者模式要做的事情
    # if st.session_state.DEV_MODE:
    #     # 加载进度控制器
    #     load_process_controller()




