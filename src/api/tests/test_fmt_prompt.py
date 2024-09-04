def test_fmt_prompt(app):
    from flaskr.service.study.utils import get_fmt_prompt

    prompt = """1对1向学员讲解可以把不懂的事情，交还给 AI 让它解释和处理。

把下面的`注意事项`，放回到`代码`里解决，在`代码`直接完成修改后，给到一个完成的 Python 代码。

`注意事项`是：
1. 文件扩展名处理
2. 文件名格式
3. 重命名执行

`代码`是：
```python

import os

def batch_rename(folder_path, new_name_format):
    # 获取文件夹中的所有文件
    files = os.listdir(folder_path)
    files = [f for f in files if os.path.isfile(os.path.join(folder_path, f))]

    for index, filename in enumerate(files):
        file_extension = os.path.splitext(filename)[1]
        new_name = new_name_format.format(index + 1) + file_extension
        old_file_path = os.path.join(folder_path, filename)
        new_file_path = os.path.join(folder_path, new_name)

        os.rename(old_file_path, new_file_path)

    print(f"成功重命名了 {{len(files)}} 个文件。")

if __name__ == "__main__":
    folder_path = input("请输入要批量重命名的文件夹路径：")
    new_name_format = input("请输入新文件名的格式（如 'new_name_{{}}'，{{}} 会被替换为编号）：")
    batch_rename(folder_path, new_name_format)

```"""
    with app.app_context():
        user_id = "e54422e8fe734428b628129330e7dd2d"
        fmt_prompt = get_fmt_prompt(app, user_id, prompt)

        app.logger.info(fmt_prompt)


def test_fmt_prompt_simple(app):
    from flaskr.service.study.utils import get_fmt_prompt

    prompt = """你好， {nickname}，欢迎来到 Python 编程学习。"""
    with app.app_context():
        user_id = "e54422e8fe734428b628129330e7dd2d"
        fmt_prompt = get_fmt_prompt(app, user_id, prompt)

        app.logger.info(fmt_prompt)
