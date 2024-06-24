import time

import streamlit as st

from chapter import *
from tools.auth import login

# ==================== 各种初始化工作 ====================
# 设置页面标题和图标
st.set_page_config(
    page_title="Chapters Setting",
    page_icon="🧙‍♂️",
)

'# 章节剧本文档管理 📚📜📚 '
"""
> 查看/修改/添加剧本文档，以便调试剧本时选择不同的剧本文档
>
> 🚧 未来推送章节文档到正式环境的功能也会放在这
"""
'---'

# 需要登录
if login():

    '### 查看教研平台剧本文档信息'
    df_chapters = DataFrame([chapter.__dict__ for chapter in load_chapters_from_sqlite()])
    df_chapters.set_index('id', inplace=True)
    df_chapters.sort_values('rank', inplace=True)
    event = st.dataframe(
        df_chapters,
        column_config={
            'name': '章节名称',
            'lark_table_id': '飞书表格 ID',
            'lark_view_id': '飞书表格 ViewID',
            'rank': '排序权重',
        },
        use_container_width=True,
        hide_index=True,
        on_select='rerun',
        selection_mode='single-row'
    )


    @st.experimental_dialog('✏️ 修改 章节剧本文档')
    def edit_chapter(chapter_id):
        with st.form('edit_row'):
            params = {
                'name': st.text_input('章节名称'),
                'lark_table_id': st.text_input('飞书表格 ID', df_chapters.loc[chapter_id, 'lark_table_id']),
                'lark_view_id': st.text_input('飞书表格 ViewID', df_chapters.loc[chapter_id, 'lark_view_id']),
                'rank': st.number_input('排序权重', value=df_chapters.loc[chapter_id, 'rank']),
            }

            submit_button = st.form_submit_button('提交修改', type='primary', use_container_width=True)
            if submit_button:
                params
                conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
                cursor = conn.cursor()
                c = cursor.execute('UPDATE `chapters` SET name=?, lark_table_id=?, lark_view_id=?, rank=? WHERE id=?',
                                   (params['name'], params['lark_table_id'], params['lark_view_id'], params['rank'],
                                    chapter_id))
                conn.commit()
                conn.close()
                st.rerun()


    @st.experimental_dialog('⚠️ 确认删除吗?')
    def delete_chapter(chapter_id):
        with st.form('delete_row'):
            st.text_input('章节名称', df_chapters.loc[chapter_id, 'name'], disabled=True)
            st.text_input('飞书表格 ID', df_chapters.loc[chapter_id, 'lark_table_id'], disabled=True)
            st.text_input('飞书表格 ViewID', df_chapters.loc[chapter_id, 'lark_view_id'], disabled=True)
            st.number_input('排序权重', value=df_chapters.loc[chapter_id, 'rank'], disabled=True)

            submit_button = st.form_submit_button('确认删除', type='primary', use_container_width=True)
            if submit_button:
                conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
                cursor = conn.cursor()
                c = cursor.execute('DELETE FROM `chapters` WHERE id=?', (chapter_id,))
                conn.commit()
                conn.close()
                st.rerun()


    if event.selection['rows']:
        selected_chapter = df_chapters.iloc[event.selection['rows'][0]]

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f'✏️ 修改 {selected_chapter["name"]}', use_container_width=True):
                edit_chapter(int(selected_chapter.name))

        with col2:
            if st.button(f'❌ 删除 {selected_chapter["name"]}', use_container_width=True):
                delete_chapter(int(selected_chapter.name))


    # 添加 章节剧本文档
    with st.expander('➕ 添加 章节剧本文档'):
        with st.form('add_row'):
            max_rank = df_chapters['rank'].max() if not df_chapters.empty else 0
            params = {
                'name': st.text_input('章节名称'),
                'lark_table_id': st.text_input('飞书表格 ID'),
                'lark_view_id': st.text_input('飞书表格 ViewID', value='vewlGkI2Jp'),
                'rank': st.number_input('排序权重', value=max_rank + 1),
            }

            submit_button = st.form_submit_button('添加', type='primary', use_container_width=True)
            if submit_button:
                conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
                cursor = conn.cursor()
                c = cursor.execute('INSERT INTO `chapters` (name, lark_table_id, lark_view_id, rank) VALUES (?, ?, ?, ?)',
                                   (params['name'], params['lark_table_id'], params['lark_view_id'], params['rank']))
                conn.commit()
                conn.close()
                st.rerun()
