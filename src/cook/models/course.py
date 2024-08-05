import requests
import sqlite3

import streamlit as st
from pandas import DataFrame

from init import cfg


class Course:
    def __init__(self, course_id, user_name, course_name, lark_app_token):
        self.course_id = course_id
        self.user_name = user_name
        self.course_name = course_name
        self.lark_app_token = lark_app_token

    def __repr__(self):
        return f'{self.course_name}  (app_token:{self.lark_app_token}  --by {self.user_name})'


def get_all_courses_from_sqlite() -> list[Course]:
    all_courses = []
    conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM `courses`')
    for row in cursor.fetchall():
        all_courses.append(Course(*row))
    conn.close()
    return all_courses


@st.cache_data(show_spinner="Get courses from DB...")
def get_courses_by_user_from_sqlite(user_name) -> list[Course]:
    courses = []
    conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM `courses` WHERE user_name=?', (user_name,))
    for row in cursor.fetchall():
        courses.append(Course(*row))
    conn.close()
    return courses


def insert_course(user_name, course_name, lark_app_token):
    conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO `courses` (user_name, course_name, lark_app_token) VALUES (?, ?, ?)',
                   (user_name, course_name, lark_app_token))
    conn.commit()
    conn.close()

    get_courses_by_user_from_sqlite.clear()


def del_course_by_course_id(course_id):
    conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM `courses` WHERE id=?', (course_id,))
    conn.commit()
    conn.close()

    get_courses_by_user_from_sqlite.clear()


def update_course_by_course_id(course_id, user_name, course_name, lark_app_token):
    conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
    cursor = conn.cursor()
    print(f'UPDATE `courses` SET user_name={user_name}, course_name={course_name}, lark_app_token={lark_app_token} WHERE id={course_id}')
    cursor.execute('UPDATE `courses` SET user_name=?, course_name=?, lark_app_token=? WHERE id=?',
                   (user_name, course_name, lark_app_token, course_id))
    conn.commit()
    conn.close()

    get_courses_by_user_from_sqlite.clear()


if __name__ == '__main__':
    # print(load_all_courses_from_sqlite())
    # print(load_courses_by_user_from_sqlite('zhangsan'))
    # insert_course('zhangsan', 'Python', '123456')
    # del_course_by_course_id(1)
    # update_course_by_course_id(2, 'zhangsan', 'Python', '123456')
    pass

    # moke 10 courses
    # for i in range(10):
    #     insert_course('zhangsan', f'Python{i}', f'123456{i}')
    #     insert_course('lisi', f'Java{i}', f'123456{i}')
    #     insert_course('wangwu', f'C{i}', f'123456{i}')

    courses = get_courses_by_user_from_sqlite('kenrick')
    print(courses)
