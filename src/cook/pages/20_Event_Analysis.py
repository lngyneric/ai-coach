from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st


from models.script import ScriptType
from tools.umami_event_analysis import get_trail_script_count
from tools.utils import load_scripts

st.set_page_config(
    page_title="Event Analysis",
    page_icon="🧙‍♂️",
    layout="wide"
)

''

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

# 获取当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 使用Plotly绘制漏斗图
fig = px.funnel(df, x='数量', y='剧本简述', title=f'体验课剧本漏洞 ({current_time})', height=script_num*50)

# 显示图表
# fig.show()
st.plotly_chart(fig, use_container_width=True)
