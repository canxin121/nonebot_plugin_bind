from nonebot.adapters import Bot, Event
from nonebot.params import Depends

from .user_sql import User
from .user_sql import get_user as get_sql_user


async def get_user(bot: Bot, event: Event, auto_create: bool = True):
    _adapter_name = bot.adapter.get_name()
    return await get_sql_user(platform=_adapter_name, account=event.get_user_id(), auto_create=auto_create)


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
