import logging
import os
import json
from enum import Enum

from dotenv import load_dotenv, find_dotenv
import lark_oapi as lark
from lark_oapi.api.auth.v3 import *
from lark_oapi.api.bitable.v1 import *


_ = load_dotenv(find_dotenv())
LARK_APP_ID = os.environ.get('LARK_APP_ID')
LARK_APP_SECRET = os.environ.get('LARK_APP_SECRET')


class ScriptType(Enum):
    FIXED = '固定剧本'
    PROMPT = 'Prompt'



class ScriptFormat(Enum):
    MARKDOWN = '文本'
    IMAGE = '图片'
    NONE = '无'


class BtnFor(Enum):
    CONTINUE = '继续'


class NextAction(Enum):
    ShowInput = '显示 输入框'
    ShowBtn = '显示 按钮'
    ShowBtnGroup = '显示 按钮组'
    NoAction = '无'


class Script:
    """ 单条剧本

    """
    def __init__(self, id, desc, type, format,
                 template, template_vars, media_url,
                 next_action, btn_label, input_placeholder,
                 check_template, check_ok_sign, parse_vars,
                 custom_model):
        """ 剧本对象

        :param id: 【必填】在使用飞书多维表格时，填写其记录的ID
        :param desc: 【必填】剧本简述
        :param type: 【必填】剧本类型，可选值：ScriptType.FIXED, ScriptType.PROMPT
        :param format: 仅固定剧本时必填，可选值：ScriptFormat.MARKDOWN, ScriptFormat.IMAGE
        :param template: 【必填】剧本模版。 固定剧本时直接输出给用户；Prompt剧本时，将内容提交给AI，AI返回结果后输出
        :param template_vars: 模版变量，需要时提供变量名称列表
        :param media_url: 仅图片剧本时必填，图片地址
        :param next_action: 【必填】后续交互，可选值：NextAction.ShowInput, NextAction.ShowBtn, NextAction.NoAction
        :param btn_label: 后续交互为按钮时，按钮的标签
        :param input_placeholder: 后续交互为输入时，输入框的提示语
        :param check_template: 后续交互为输入时，提供检查模版，用于检查用户输入是否符合要求
        :param check_ok_sign: 后续交互为输入时，检查通过的标志
        :param parse_vars: 后续交互为输入时，提供解析变量名列表，用于解析用户输入
        :param custom_model: 单条剧本指定使用自定义模型时，提供模型名称
        """

        self.id: str = id
        self.desc: str = desc
        self.type: ScriptType = type
        self.format: Optional[ScriptFormat] = format
        self.template: Optional[str] = template
        self.template_vars: Optional[List[str]] = template_vars
        self.media_url: Optional[str] = media_url
        self.next_action: NextAction = next_action
        self.btn_label: Optional[str] = btn_label
        self.input_placeholder: Optional[str] = input_placeholder
        self.check_template: Optional[str] = check_template
        self.check_ok_sign: Optional[str] = check_ok_sign
        self.parse_vars: Optional[List[str]] = parse_vars
        self.custom_model: Optional[str] = custom_model





def get_lark_client() -> lark.Client:
    """ 获取 飞书 client 对象
    :return: client
    """
    client = (lark.Client.builder()
              .app_id(LARK_APP_ID)
              .app_secret(LARK_APP_SECRET)
              .log_level(lark.LogLevel.DEBUG)
              .build())
    return client


def get_tenant_access_token():
    client = get_lark_client()

    # 构造请求对象
    request = (InternalTenantAccessTokenRequest.builder()
               .request_body(InternalTenantAccessTokenRequestBody.builder()
                             .app_id(LARK_APP_ID)
                             .app_secret(LARK_APP_SECRET)
                             .build())
               .build())

    # 发起请求
    response: InternalTenantAccessTokenResponse = client.auth.v3.tenant_access_token.internal(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.auth.v3.tenant_access_token.internal failed, "
            f"code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.raw.content, indent=4))

    # 解析 token
    data = json.loads(response.raw.content)
    token = data.get('tenant_access_token', "Tenant access token not found")

    return token


def load_scripts_from_bitable(app_token, table_id, view_id):
    logging.info(f'开始加载剧本记录：app_token={app_token}, table_id={table_id}, view_id={view_id}')
    client = get_lark_client()

    # 构造请求对象
    request = (SearchAppTableRecordRequest.builder()
               .app_token(app_token)
               .table_id(table_id)
               .page_size(100)
               .request_body(SearchAppTableRecordRequestBody.builder()
                             .view_id(view_id)
                             .build())
               .build())

    # 发起请求
    response: SearchAppTableRecordResponse = client.bitable.v1.app_table_record.search(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.bitable.v1.app_table_record.search failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))


    logging.info(f"是否有更多：{response.data.has_more}")
    logging.info(f"共有 {response.data.total} 条记录")

    script_list = []
    for item in response.data.items:
        try:
            id = item.record_id
            if not item.fields:
                logging.warn(f'剧本记录为空，ID：{id}')
                continue

            desc = ''.join(item["text"] for item in item.fields.get('剧本简述', [{"text": "未填写！"}]))
            script_type = ScriptType(item.fields.get('剧本类型', '固定剧本'))
            script_format = ScriptFormat(item.fields.get('内容格式', '文本'))
            template = ''.join(item["text"] for item in item.fields.get('模版内容', [{"text": "未填写！"}]))
            template_vars = item.fields.get('模版变量')
            media_url = item.fields.get('媒体URL')['text'] if item.fields.get('媒体URL') else None
            next_action = NextAction(item.fields.get('后续交互', '无'))
            btn_label = ''.join(item["text"] for item in item.fields.get('按钮标题', [{"text": "继续"}]))
            input_placeholder = ''.join(item["text"] for item in item.fields.get('输入框提示', [{"text": "请输入"}]))
            check_template = ''.join(item["text"] for item in item.fields.get('检查模版内容', [{"text": "未填写！"}]))
            check_ok_sign = ''.join(item["text"] for item in item.fields.get('输入成功标识', [{"text": "OK"}]))
            parse_vars = item.fields.get('解析用户输入内容')
            custom_model = item.fields.get('自定义模型', None)

            script_list.append(Script(
                id, desc, script_type, script_format,
                template, template_vars, media_url,
                next_action, btn_label, input_placeholder,
                check_template, check_ok_sign, parse_vars,
                custom_model
            ))
        except Exception as e:
            logging.error(f'加载剧本记录失败，剧本ID：{id}')
            logging.error(f'剧本内容：{item.fields}')
            logging.error(f'异常信息：{e}')
            continue

    return script_list





if __name__ == '__main__':
    token = get_tenant_access_token()
    print(token)

    from init import cfg
    script_list = load_scripts_from_bitable(cfg.LARK_APP_TOKEN, cfg.DEF_LARK_TABLE_ID, cfg.DEF_LARK_VIEW_ID)
    print(script_list)

