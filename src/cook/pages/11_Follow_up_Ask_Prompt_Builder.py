import sqlite3

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

整理总结后输出内容格式如下（摘要内容在200字以内；教学要点总结不要超过5条）：
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
# 现在学员在学习上述教学内容时，产生了一些疑问，你需要恰当的回答学员的追问。
**你就是老师本人，不要打招呼，直接用第一人称回答！**

如果学员的追问内容与当前章节教学内容有关，请优先结合当前章节中已经输出的内容进行回答。

如果学员的追问内容与当前章节教学内容关系不大，但与该课程的其他章节有关，你可以简要回答并友好的告知学员稍安勿躁，后续xx章节有涉及学员追问问题的详细教学内容。

如果学员的追问内容与课程教学内容无关，但与教学平台有关（平台使用问题；售卖、订单、退费等；账号、密码、登录等），请耐心的告知学员通过「哎师傅-AI学习社区」服务号找到我们进行相应的解决。

如果学员的追问内容与课程教学内容无关，也与教学平台无关，请友好的回绝学员的追问，并请学员专注在该课程内容的学习上。


学员的追问是：
`{follow_up_ask}`

"""


def update_follow_up_ask_prompt_template(lark_app_token, lark_table_id, prompt_template):
    conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO `chapters_follow_up_ask_prompt` (lark_app_token, lark_table_id, prompt_template) '
                   'VALUES (?, ?, ?) ON CONFLICT (lark_app_token, lark_table_id) DO UPDATE SET prompt_template=?',
                   (lark_app_token, lark_table_id, prompt_template, prompt_template))
    conn.commit()
    conn.close()


with login():
    courses = get_courses_by_user_from_sqlite(st.session_state["username"])
    if not courses:
        st.warning(' No courses available, please go to `My Account` to create a new course.。  ⬇️ ⬇️ ⬇️', icon='⚠️')
        if st.button('Go to `My Account`', type='primary', use_container_width=True):
            st.switch_page("pages/100_My_Account.py")
        st.stop()

    selected_course = st.selectbox('Select Course:', (course.course_name for course in courses))

    if st.button('Generate all chapters follow-up ask prompt template', use_container_width=True):
        st.session_state.lark_app_token = next(
            (course.lark_app_token for course in courses if course.course_name == selected_course), None)
        tables = get_bitable_tables(st.session_state.lark_app_token)

        chapters_summary = {}
        for table in tables:
            if table.name.startswith('字典-'):
                continue

            load_scripts(st.session_state.lark_app_token, table.table_id)

            scripts_content = ""
            for index, script in enumerate(st.session_state.script_list):
                scripts_content += f'#### 第{index}小节: {script.desc}:\n'
                scripts_content += script.template + '\n\n\n'

            variables = {
                'course_name': selected_course,
                'chapter_name': table.name,
                'scripts_content': scripts_content
            }

            llm = load_llm('gpt-4o-2024-05-13')
            prompt = PromptTemplate(input_variables=list(variables.keys()), template=prompt_summarize_chapter)
            prompt = prompt.format(**variables)

            with st.spinner(f'Chapter {table.name} is summarizing...'):
                response = llm.invoke([HumanMessage(prompt)])
                print(response.content)
                st.write(f'### Chapter {table.name} Summary:')
                st.write(response.content)
                st.write('-----')
                chapters_summary[table.name] = response.content

            del st.session_state['script_list']  # clear before next iteration

        for table in tables:
            if table.name.startswith('字典-'):
                continue

            follow_up_ask_prompt_template = prompt_follow_up_ask
            follow_up_ask_prompt_template += "当前章节的内容是：\n"
            follow_up_ask_prompt_template += chapters_summary[table.name] + "\n\n"
            follow_up_ask_prompt_template += "课程其他章节的内容是：\n"
            for chapter_name, summary in chapters_summary.items():
                if chapter_name != table.name:
                    follow_up_ask_prompt_template += summary + "\n\n"

            update_follow_up_ask_prompt_template(st.session_state.lark_app_token,
                                                 table.table_id,
                                                 follow_up_ask_prompt_template)


