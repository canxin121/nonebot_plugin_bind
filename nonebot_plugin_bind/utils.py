from nonebot.adapters import Bot, Event
from nonebot.params import Depends

from .config import config
from .group_sql import Group
from .group_sql import get_group as get_sql_group
from .user_sql import User
from .user_sql import get_user as get_sql_user


async def get_user(bot: Bot, event: Event, auto_create: bool = True):
    _adapter_name = bot.adapter.get_name()
    return await get_sql_user(platform=_adapter_name, account=event.get_user_id(), auto_create=auto_create)


async def get_group(bot: Bot, event: Event, auto_create: bool = True):
    if _is_private_(event, bot):
        return None
    _adapter_name = bot.adapter.get_name()
    groupid = get_groupid(event, bot)
    group = await get_sql_group(platform=_adapter_name, groupid=groupid, auto_create=auto_create)
    return group


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


async def _is_superuser_(event: Event, bot: Bot):
    """不完整"""
    user = await get_user(bot, event)
    if user.id in config.bind_superuser:
        return True
    if config.bind_group_admin:
        if _is_private_(event, bot):
            raise Exception("本命令只能在各平台的群聊中使用,无法在私聊中使用")
        _event_name = event.get_event_name()
        _adapter_name = bot.adapter.get_name()
        if _adapter_name == "OneBot V11":
            if event.sender.role in ("owner", "admin"):
                return True
            else:
                raise Exception("你没有QQ群组中 管理员 的权限,无权使用本命令")
        elif _adapter_name == "Kaiheila":
            """以拥有管理员权限(1)为准"""
            try:
                data = await bot.call_api("guild-role/list", guild_id=event.event.guild_id)
            except Exception as e:
                if e.message == '你没有权限进行此操作':
                    raise Exception("机器人权限不足以判断用户是否为管理员,请先将机器人设置为kook频道管理员") from e
                else:
                    raise Exception("获取Kook群组用户权限列表失败") from e
            for role_id in event.extra.author.roles:
                for role in data.roles:
                    if role.role_id == role_id:
                        if role.permissions & 1 == 1:
                            return True
                        else:
                            raise Exception("你没有Kook群组中 管理员 的权限,无权使用本命令")
            raise Exception("你没有Kook群组中 管理员 的权限,无权使用本命令")
        elif _adapter_name == 'Discord':
            """以拥有 Manage Channle 权限(0x10)为管理员"""
            try:
                data = await bot.call_api('get_guild_roles', guild_id=event.guild_id)
            except Exception as e:
                raise Exception("获取Discord群组用户权限列表失败") from e
            for role in data:
                if role.name == event.author.username[1:]:
                    if int(role.permissions) & 0x10 == 0x10:
                        return True
                    else:
                        raise Exception("你没有Discord群组中 Manage Channle的权限,无权使用本命令")

            raise Exception("你没有Discord群组中 Manage Channle的权限,无权使用本命令")
        elif _adapter_name == 'Telegram':
            data = await bot.call_api('get_chat_administrators', chat_id=event.chat.id)
            if event.get_user_id() in [str(one.user.id) for one in data]:
                return True
            else:
                raise Exception("你没有Telegram群组中的 管理员 权限,无权使用本命令")
        else:
            return False
    else:
        raise Exception('Bind插件未开启允许群组管理员使用本命令,而你也并非Bind管理员,无权使用此命令')


def get_groupid(event: Event, bot: Bot):
    if _is_private_(event, bot):
        return None
    _event_name = event.get_event_name()
    _adapter_name = bot.adapter.get_name()
    if _adapter_name in ("OneBot V11", "Kaiheila", "Feishu", "大别野"):
        return str(event.group_id)
    elif _adapter_name in ('Discord'):
        return str(event.channel_id)
    elif _adapter_name == 'Telegram':
        return str(event.chat.id)
    else:
        raise Exception("暂时不支持获取这个adapter的groupid")


def GetUser(auto_create=True):
    async def dependency(bot: Bot, event: Event) -> User:
        return await get_user(bot, event, auto_create=auto_create)

    return Depends(dependency)


def GetGroup(auto_create=True):
    async def dependency(bot: Bot, event: Event) -> Group:
        return await get_group(bot, event, auto_create=auto_create)

    return Depends(dependency)


def GetGroupId():
    def dependency(bot: Bot, event: Event):
        return get_groupid(event, bot)

    return Depends(dependency)
