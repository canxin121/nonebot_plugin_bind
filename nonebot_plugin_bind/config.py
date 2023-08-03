from typing import List

from nonebot import get_driver
from pydantic import BaseSettings


class Config(BaseSettings):
    bind_superuser: List = []
    bind_group_admin: bool = False

    class Config:
        extra = "ignore"


config = Config.parse_obj(get_driver().config)
