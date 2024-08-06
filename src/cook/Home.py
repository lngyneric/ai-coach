from PIL import Image
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space

st.set_page_config(
    page_title="Assistants Demo",
    page_icon="🧬",
)

"""
# 哎！师傅：课程制作中心
> 请收藏该网址 http://cook.ai-shifu.com/
"""

add_vertical_space(2)
"""
## 首次使用
前往个人中心，使用初始密码登录后，修改密码，然后开始使用。
"""
if st.button('前往个人中心', type='primary', use_container_width=True):
    st.switch_page("pages/100_My_Account.py")

add_vertical_space(2)
"""
## 管理课程
在个人中心中，可以管理课程，包括创建、修改、删除课程。

这里配置的课程将会出现在各个调试器页面中以供选择。

![](https://img.agiclass.cn/WX20240806-230115.png)
"""
