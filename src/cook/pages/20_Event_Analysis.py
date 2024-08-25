from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st


from models.script import ScriptType
from tools.auth import login
from tools.umami_event_analysis import get_trail_script_count
from tools.utils import load_scripts

st.set_page_config(
    page_title="Event Analysis",
    page_icon="🧙‍♂️",
    layout="wide"
)

# 页面内的大标题小标题
'# 埋点事件分析器 📊📈📉'
st.caption('')

with login():

    system_role_script = load_scripts()
    if st.session_state.script_list[0].type == ScriptType.SYSTEM:
        system_role_script = st.session_state.script_list.pop(0)

    # print(st.session_state.script_list[0])

    df = pd.DataFrame(columns=['剧本简述', '数量'])

    for script in st.session_state.script_list:
        df.loc[len(df)] = [script.desc, 0]

    umami_event_count = get_trail_script_count()
    for index, row in umami_event_count.iterrows():
        for i, script in enumerate(st.session_state.script_list):
            if script.desc == row['string_value']:
                df.loc[i, '数量'] = row['count(*)']
    print(umami_event_count)
    print(df)

    script_num = len(df)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 绘制漏斗图
    fig = px.funnel(df, x='数量', y='剧本简述', title=f'体验课剧本漏斗 ({current_time})', height=script_num*50)
    st.plotly_chart(fig, use_container_width=True)

    # 计算下降比例
    df['下降比例'] = df['数量'].pct_change().fillna(0)
    df.loc[0, '下降比例'] = 0

    # 绘制图表
    fig = px.line(df, x='剧本简述', y='下降比例', title=f'剧本间下降比例 ({current_time})',
                  labels={'剧本简述': '剧本简述', '下降比例': '下降比例'},
                  markers=True)
    st.plotly_chart(fig, use_container_width=True)
