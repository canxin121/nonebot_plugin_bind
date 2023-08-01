from nonebot.adapters import Bot, Event
from nonebot.params import Depends

from .user_sql import User
from .user_sql import get_user as get_sql_user


def get_params(bot: Bot, event: Event):
    conn_dict = {"OneBot V11": "qq_account", "Telegram": "telegram_account", "Kaiheila": "kook_account",
                 "Discord": "discord_account", "ding": "dingtalk_account", "feishu": "feishu_account",
                 "大别野": "mihoyo_account"}
    if bot.type in conn_dict.keys():
        account_key = conn_dict[bot.type]
        params = {account_key: event.get_user_id()}
        return params


async def get_user(bot: Bot, event: Event, auto_create: bool = True):
    params = get_params(bot, event)
    return await get_sql_user(auto_create=auto_create, **params)


def GetUser(auto_create=True):
    async def dependency(bot: Bot, event: Event) -> User:
        return await get_user(bot, event, auto_create=auto_create)

    return Depends(dependency)


def _is_private_(event: Event, bot: Bot):
    """不完整"""
    _event_name = event.get_event_name()
    _adapter_name = bot.adapter.get_name()
    if _adapter_name in ("OneBot V11", "Telegram", "Kaiheila"):
        return _event_name.startswith("message.private")
    elif _adapter_name == 'Feishu':
        return _event_name == "message.p2p"
    elif _adapter_name == 'Discord':
        return not bool(hasattr(event, "member") and event.member)
    else:
        return False
