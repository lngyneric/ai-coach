import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate

from init import *
from models.course import get_courses_by_user_from_sqlite
from tools.auth import login
from tools.lark import get_bitable_tables
from tools.utils import load_scripts

# ==================== Initialization ====================
# Set page title and icon
st.set_page_config(
    page_title="Follow-up Ask Prompt Builder",
    page_icon="🧙‍♂️",  # 👨‍🏫
)

# The main title and subtitle on the page
'# Follow-up Ask Prompt Builder 🛠️📝🛠️'
st.caption('Help build follow-up ask prompt templates for each chapter')


prompt_summarize_chapter = """
你需要总结AI个性化教学课程 `{course_name}` 中某个章节的主要内容和教学要点，以便后续制作该章节的追问 Prompt 模版。

当前要整理的章节是： `{chapter_name}`

整理总结后输出内容格式如下（摘要内容在200-500字；教学要点总结不要超过8条）：
```
### 章节 `xxx`：
#### 章节 `xxx` 的摘要：
【一段文本概述章节内容】
#### 章节 `xxx` 的教学要点有：
1. 【要点1】
2. 【要点2】
3. 【要点3】
...
```

该章节中的具体AI教学剧本内容如下：
{scripts_content}

"""

prompt_follow_up_ask = """
学员在学习上述教学内容时，产生了一些疑问，你需要恰当的回答学员的追问。

如果学员的追问内容与当前章节教学内容有关，请优先结合当前章节中已经输出的内容进行回答。

如果学员的追问内容与当前章节教学内容关系不大，但与该课程的其他章节有关，你可以简要回答并友好的告知学员稍安勿躁，后续xx章节有涉及学员追问问题的详细教学内容。

如果学员的追问内容与课程教学内容无关，但与教学平台有关（平台使用问题；售卖、订单、退费等；账号、密码、登录等），请耐心的告知学员通过「哎师傅-AI学习社区」服务号找到我们进行相应的解决。

如果学员的追问内容与课程教学内容无关，也与教学平台无关，请友好的回绝学员的追问，并请学员专注在该课程内容的学习上。


学员的追问是：
`{follow_up_ask}`

当前章节的内容是：
{current_chapter_summary}

课程其他章节的内容是：
{other_chapters_summary}
"""


with login():
    courses = get_courses_by_user_from_sqlite(st.session_state["username"])
    if not courses:
        st.warning(' No courses available, please go to `My Account` to create a new course.。  ⬇️ ⬇️ ⬇️', icon='⚠️')
        if st.button('Go to `My Account`', type='primary', use_container_width=True):
            st.switch_page("pages/100_My_Account.py")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        selected_course = st.selectbox('Select Course:', (course.course_name for course in courses))

    if selected_course:
        st.session_state.lark_app_token = next(
            (course.lark_app_token for course in courses if course.course_name == selected_course), None)
        tables = get_bitable_tables(st.session_state.lark_app_token)

        with col2:
            select_table = st.selectbox('Select Chapter:', (
                table.name for table in tables if not table.name.startswith('字典-')))
            st.session_state.lark_table_id = next(
                (table.table_id for table in tables if table.name == select_table), None)
            # Load script and system roles
            if 'script_list' in st.session_state:
                del st.session_state['script_list']  # clear before load
            load_scripts(st.session_state.lark_app_token, st.session_state.lark_table_id)


    if st.button('Summarize chapter content and teaching points', use_container_width=True):

        # st.write(st.session_state.script_list)

        scripts_content = ""
        for index, script in enumerate(st.session_state.script_list):
            # st.write(f'#### {index} {script.desc}({script.type}):')
            # st.write(script.template)
            # st.write('-----')

            scripts_content += f'#### 第{index}小节: {script.desc}:\n'
            scripts_content += script.template + '\n\n\n'

        print(scripts_content)

        variables = {
            'course_name': selected_course,
            'chapter_name': select_table,
            'scripts_content': scripts_content
        }

        llm = load_llm('gpt-4o-2024-05-13')
        prompt = PromptTemplate(input_variables=list(variables.keys()), template=prompt_summarize_chapter)
        prompt = prompt.format(**variables)

        with st.spinner('Summary in progress...'):
            response = llm.invoke([HumanMessage(prompt)])
            print(response.content)
            st.write(response.content)

