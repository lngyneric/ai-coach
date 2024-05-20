import sqlite3
from pandas import DataFrame

from init import cfg


class Chapter:
    def __init__(self, id, name, lark_table_id, lark_view_id, rank):
        self.id = id
        self.name = name
        self.lark_table_id = lark_table_id
        self.lark_view_id = lark_view_id
        self.rank = rank

    def __repr__(self):
        return f'{self.name}  (id: {self.id})'


def load_chapters_from_sqlite() -> list[Chapter]:
    chapters = []
    conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM `chapters`'
                   'ORDER BY `rank` ASC')
    for row in cursor.fetchall():
        chapters.append(Chapter(*row))
    conn.close()
    return chapters



if __name__ == '__main__':
    chapters = load_chapters_from_sqlite()

    for chapter in chapters:
        print(chapter.id, chapter.name, chapter.lark_table_id, chapter.lark_view_id, chapter.rank)

    chapters_df = DataFrame([chapter.__dict__ for chapter in chapters])
    print(chapters_df)
