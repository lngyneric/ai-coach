import os

import connectorx as cx
import pandas as pd
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())
db_url = (f'mysql://{os.getenv("DB_USERNAME")}:{os.getenv("DB_PASSWORD")}'
          f'@{os.getenv("DB_HOST")}:3306/{os.getenv("DB_DATABASE")}')

def get_trail_script_count():
    sql = """
    select count(*), string_value from umami.event_data where 1=1
        and data_key = 'progress_desc'
    group by string_value;
    """

    df: pd.DataFrame = cx.read_sql(db_url, sql, index_col=None)

    return df



if __name__ == "__main__":
    df = get_trail_script_count()
    print(df)
