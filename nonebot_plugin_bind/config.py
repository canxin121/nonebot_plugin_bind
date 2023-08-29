from nonebot import require
from pydantic import Field

require("nonebot_plugin_web_config")
from nonebot_plugin_web_config import WebUiConfigModel


class Config(WebUiConfigModel):
    __config_name__ = "Bind配置"
    __type__ = "dict"
    bind_superuser:list =  Field(
        default=[], description="Bind插件的超级用户,拥有管理群绑定的权限(注意填写的应该是使用bind命令查询得到的通用账户的id)"
    )
    bind_group_admin:bool =  Field(default=False, description="是否允许群管理直接管理群组绑定")
