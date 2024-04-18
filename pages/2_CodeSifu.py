from streamlit_extras.bottom_container import bottom

from tools.utils import *
from tools.dev_tools import *
from script import *


# ==================== 各种初始化工作 ====================
# 设置页面标题和图标
st.set_page_config(
    page_title="CodeSifu",
    page_icon="🧙‍♂️",  # 👨‍🏫
)
# 固定侧边栏宽度并添加Logo
fix_sidebar_add_logo("static/CodeSifu_logo_w300.jpg")
# 页面内的大标题小标题
'# Code Sifu ⌨️🧙‍♂️⌨️'  # 📚
st.caption('📚 你的专属AI编程私教')


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

# 初始化剧本
if 'script_list' not in st.session_state:
    with st.spinner('正在加载剧本...'):
        st.session_state.script_list = load_scripts_from_bitable(LARK_APP_TOKEN, LARK_TABLE_ID, LARK_VIEW_ID)
        st.session_state.script_list_len = len(st.session_state.script_list)

# 记录剧本是否输出
if 'script_has_output' not in st.session_state:
    st.session_state.script_has_output = set()

if 'has_started' not in st.session_state:
    st.session_state.has_started = False

# ======================================================


# ==================== 主体框架 ====================
# 开发者模式要做的事情
if st.session_state.DEV_MODE:
    # 加载进度控制器
    load_process_controller()

if st.session_state.has_started or not st.session_state.DEV_MODE:

    # 获取剧本总长度，并在结束时停止
    if st.session_state.progress >= st.session_state.script_list_len:
        # chat_box.ai_say('别再犹豫了，马上把我带回家吧~')
        with bottom():
            st.write('')
        st.stop()

    # 根据当前进度ID，获取对应的剧本
    script: Script = st.session_state.script_list[st.session_state.progress]
    logging.debug(f'当前剧本：\n{script}')
    if st.session_state.DEV_MODE:
        show_current_script(script)


    # ========== 内容输出部分 ==========
    # 如果剧本没有输出过，则进行输出
    if script.id not in st.session_state.script_has_output:
        full_result = None
        if script.type == ScriptType.FIXED:
            if script.format == ScriptFormat.MARKDOWN:
                full_result = simulate_streaming(chat_box, script.template, script.template_vars)
            elif script.format == ScriptFormat.IMAGE:
                chat_box.ai_say(Image(script.media_url))
                full_result = script.media_url
        elif script.type == ScriptType.PROMPT:
            full_result = streaming_from_template(chat_box, script.template, {v: st.session_state[v] for v in script.template_vars})
        # elif script['type'] == ScriptType.XXXX:  # TODO: 其他类型？

        # 记录已输出的剧本ID，避免重复输出
        st.session_state.script_has_output.add(script.id)
        logging.debug(f'script id: {script.id}, chat result: {full_result}')


    # ========== 交互区域部分 ==========
    # 需要用户输入
    if script.next_action == NextAction.ShowInput:
        # 获取用户输入
        if user_input := st.chat_input(script.input_placeholder):
            chat_box.user_say(user_input)  # 展示用户输入信息

            # 通过 `检查模版` 输出AI回复
            full_result = streaming_from_template(chat_box, script.check_template, {'input': user_input},
                                                  input_done_with=script.check_ok_sign,
                                                  parse_keys=script.parse_vars)
            logging.debug(f'scrip id: {script.id}, chat result: {full_result}')

            # 如果AI回复中包含了结束标志，则进入下一个剧本
            if full_result.startswith(script.check_ok_sign):
                # if script['input_for'] == InputFor.SAVE_PROFILE:
                #     st.session_state[script['save_key']] = user_input
                #     logging.debug(f'保存用户输入：{script["save_key"]} = {user_input}')

                st.session_state.progress += 1
                st.rerun()
    # 展示按钮
    elif script.next_action == NextAction.ShowBtn:
        with bottom():
            if st.button(script.btn_label, type=script.btn_type, use_container_width=script.btn_container_width):
                if script.btn_for == BtnFor.CONTINUE:
                    st.session_state.progress += 1
                    st.rerun()
                elif 1:
                    pass  # TODO 其他可能的按钮操作
    else:
        st.session_state.progress += 1
        st.rerun()


