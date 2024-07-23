from .funs import update_lesson_info,get_lessons
from .const import *
from .models import *
from ..common.dicts import register_dict

register_dict('script_types','剧本类型',SCRIPT_TYPES)
register_dict('content_types','内容类型',CONTENT_TYPES)
register_dict('lesston_types','课程类型',LESSON_TYPES)