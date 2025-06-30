import time
from flaskr.service.shifu.funcs import get_shifu_summary

# from .test_utils import dump, dump_detailed


# tests/test_shifu_funcs.py::test_get_shifu_abstract
def test_get_shifu_abstract(app):
    with app.app_context():
        start_time = time.time()
        get_shifu_summary(app, "a9165dd395004775ba8886395c782fa3")
        end_time = time.time()
        print(f"get_shifu_summary takes: {end_time - start_time}s")
        # for i in data:
        #     dump_detailed(i.outline, include_methods=False)
        # for j in i.children:
        #     dump_detailed(j.outline, include_methods=False)
