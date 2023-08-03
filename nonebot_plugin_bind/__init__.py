import secrets
from datetime import timedelta, datetime
from typing import Annotated, Optional

from nonebot import get_driver
from nonebot import require
from nonebot.adapters import Event, Bot
from nonebot.matcher import Matcher
from nonebot.params import ArgStr, T_State
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_datastore")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_alconna")

from ._types import Bind  # noqa: E402
from .group_sql import Group, merge_group, del_platform_group  # noqa: E402
from .user_sql import User, merge_user, del_platform_user  # noqa: E402
from .utils import (
    GetUser,
    GetGroup,
    get_groupid,
    _is_private_,
    _is_superuser_,
    GetGroupId,
)  # noqa: E402

from nonebot_plugin_alconna import (  # noqa: E402
    on_alconna,
    CommandResult,
    AlconnaResult,
    Match,
    AlconnaMatch,
)
from arclet.alconna import Alconna, Option, Args  # noqa: E402
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

__plugin_meta__ = PluginMetadata(
    name="跨平台账户绑定",
    description="nonebot多适配器通用的跨平台账户绑定插件",
    usage="1.使用'bind'或'绑定'命令可以将其他通用账户绑定至当前通用账户\n2.使用'bindinfo'或'绑定信息'查看通用账户的平台账户绑定信息\n3.使用'rebind'或者'取消绑定'可以取消本平台账户和通用账户的绑定,并形成一个新的通用账户",
    type="library",
    homepage="https://github.com/canxin121/nonebot_plugin_bind",
    supported_adapters={"~onebot.v11", "~telegram", "~kaiheila", "~feishu", "~villa"},
)

Command_Start = list(get_driver().config.command_start)
SECONDS = str(get_driver().config.session_expire_timeout.seconds)
Binds: dict = {}


def del_Bind(_token):
    if _token in Binds.keys():
        del Binds[_token]


bind_info = on_alconna(Alconna(Command_Start, "bindinfo", Option("-group")))


@bind_info.assign("$main")
async def bind_info_(
        event: Event, bot: Bot, matcher: Matcher, user: Annotated[User, GetUser()]
):
    user_str = "\n".join(
        pg + "  √" if event.get_user_id() in pg else pg for pg in str(user).split("\n")
    )
    if _is_private_(event, bot):
        await matcher.finish(f"当前通用账户的绑定的平台账户如下:\n{str(user_str)}")
    else:
        await matcher.finish("账户绑定信息只能在私聊中查看")


@bind_info.assign("group")
async def bind_info_group(
        matcher: Matcher,
        group: Optional[Group] = GetGroup(),
        groupid: Optional[str] = GetGroupId(),
):
    if group is None:
        await matcher.finish("本命令只能在各平台的群聊中使用,私聊中无法使用")
    group_str = "\n".join(
        pg + "  √" if groupid in pg else pg for pg in str(group).split("\n")
    )
    await matcher.send(f"当前通用群组的绑定的平台群组如下:\n{group_str}")


_bind_ = on_alconna(
    Alconna(Command_Start, "bind", Option("token", Args["token_value", str]))
)


@_bind_.handle()
async def _bind__(
        bot: Bot,
        event: Event,
        matcher: Matcher,
        state: T_State,
        user: Annotated[User, GetUser()],
        crt: CommandResult = AlconnaResult(),
        _token: Match[str] = AlconnaMatch("token_value"),
):
    global Binds
    cmd = crt.source.command
    if _token.available:
        _token = str(_token.result).replace(" ", "").replace("\n", "")
        if len(_token) == 6:
            if _token in Binds.keys():
                msg = ""
                Binds[_token].origin_ = user
                if _is_private_(event, bot):
                    user_str = "\n".join(
                        pg + "  √" if event.get_user_id() in pg else pg
                        for pg in str(user).split("\n")
                    )
                    msg += f"当前通用账户的绑定的平台账户如下:\n{str(user_str)}"
                msg += f"\n注意事项:\n1.此命令是将本通用账户的绑定信息迁移到刚才发送'{str(cmd)}'命令通用账户\n2.本命令会丢失以当前通用账户身份存储的所有数据,且不可逆,所以请小心使用\n\n使用方式:\n如果确认绑定,请用刚才发送'{str(cmd)}'命令的平台的账户在{SECONDS}秒内直接发送以下密钥:\n{Binds[_token]._key}"
                await matcher.finish(msg)
            else:
                await matcher.finish("密钥错误或已过期")
        else:
            await matcher.finish(f"密钥格式错误 或 请勿在初次发送'{str(cmd)}'命令时追加信息")
    else:
        _token = str(secrets.token_hex(3))
        scheduler.add_job(
            del_Bind,
            "date",
            run_date=datetime.now() + timedelta(seconds=int(SECONDS)),
            args=[_token],
        )
        bind = Bind()
        bind.to_ = user
        state["_token"] = _token
        Binds[_token] = bind
        user_str = "\n".join(
            pg + "  √" if event.get_user_id() in pg else pg
            for pg in str(user).split("\n")
        )

        if _is_private_(event, bot):
            msg = f"当前通用账户的绑定的平台账户如下:\n{str(user_str)}"
        else:
            msg = ""
        msg += f'\n注意事项:\n1.一个通用账户可以绑定多个平台账户\n2.此命令是将另一个通用账户的绑定信息合并到当前通用账户\n3.本命令会丢失以另一个通用账户身份存储的所有数据,且不可逆,所以请小心使用\n\n使用方式:\n请用需要绑定的另一个平台的账号在{SECONDS}秒内发送以下内容:\n{Command_Start[0]}{str(cmd)} token {_token}\n\n发送"取消"或"算了"可以终止绑定'
        await matcher.send(msg)


@_bind_.got("key")
async def bind___(state: T_State, matcher: Matcher, args: str = ArgStr("key")):
    if '_token' in state.keys():
        _token = state["_token"]
    else:
        await matcher.finish()
    key = str(args).replace(" ", "").replace("\n", "")
    if key == Binds[_token]._key:
        try:
            await merge_user(Binds[_token].to_, Binds[_token].origin_)
        except Exception as e:
            if "already present" in str(e):
                await matcher.finish("禁止重复绑定同一个平台群组到不同的通用群组")
            else:
                await matcher.finish(f"绑定失败:{str(e)}")
        finally:
            del Binds[_token]
        await matcher.finish("成功绑定至本通用账户")
    elif key in ["取消", "算了", "结束"]:
        del_Bind(_token)
        await matcher.finish("取消绑定")
    else:
        await matcher.finish("发送信息有误,终止绑定")


_bind_group_ = on_alconna(
    Alconna(
        Command_Start,
        "bind",
        Option("-group"),
        Option("token", Args["token_value", str]),
    )
)


@_bind_group_.assign("group")
async def __bind_group__(
        bot: Bot,
        event: Event,
        matcher: Matcher,
        state: T_State,
        group: Optional[Group] = GetGroup(),
        groupid: Optional[str] = GetGroupId(),
        _token: Match[str] = AlconnaMatch("token_value"),
        crt: CommandResult = AlconnaResult(),
):
    if group is None:
        await matcher.finish("本命令只能在各平台的群聊中使用,私聊中无法使用")

    global Binds
    cmd = crt.source.command
    try:
        await _is_superuser_(event, bot)
    except Exception as e:
        await matcher.finish(str(e))
    if _token.available:
        _token = str(_token.result).replace(" ", "").replace("\n", "")
        if len(_token) == 6:
            if _token in Binds.keys():
                Binds[_token].origin_ = group
                msg = f"当前通用群组绑定的平台群组如下:\n{str(group)}\n注意事项:\n1.此命令是将本通用群组的绑定信息迁移到刚才发送'{str(cmd)}'命令通用群组\n2.本命令会丢失以当前通用群组身份存储的所有数据,且不可逆,所以请小心使用\n\n使用方式:\n如果确认绑定,请在刚才发送'{str(cmd)}'命令的平台群组中在{SECONDS}秒内直接发送以下密钥:\n{Binds[_token]._key}"
                await matcher.finish(msg)
            else:
                await matcher.finish("密钥错误或已过期")
        else:
            await matcher.finish(f"密钥格式错误 或 请勿在初次发送'{str(cmd)}'命令时追加信息")
    else:
        _token = str(secrets.token_hex(3))
        scheduler.add_job(
            del_Bind,
            "date",
            run_date=datetime.now() + timedelta(seconds=int(SECONDS)),
            args=[_token],
        )
        bind = Bind()
        bind.to_ = group
        state["_token"] = _token
        Binds[_token] = bind

        group_str = "\n".join(
            pg + "  √" if groupid in pg else pg for pg in str(group).split("\n")
        )

        msg = f'当前通用群组的绑定的平台群组如下:\n{str(group_str)}\n注意事项:\n1.一个通用群组可以绑定多个平台群组\n2.此命令是将另一个通用群组的绑定信息合并到当前通用群组\n3.本命令会丢失以另一个通用群组身份存储的所有数据,且不可逆,所以请小心使用\n\n使用方式:\n请在需要绑定的另一个平台群组中在{SECONDS}秒内发送以下内容:\n{Command_Start[0]}{str(cmd)} -group token {_token}\n\n发送"取消"或"算了"可以终止绑定'
        await matcher.send(msg)


@_bind_group_.got("key")
async def _bind_group___(state: T_State, matcher: Matcher, args: str = ArgStr("key")):
    if '_token' in state.keys():
        _token = state["_token"]
    else:
        await matcher.finish()
    key = str(args).replace(" ", "").replace("\n", "")
    if key == Binds[_token]._key:
        try:
            await merge_group(Binds[_token].to_, Binds[_token].origin_)
        except Exception as e:
            if "already present" in str(e):
                await matcher.finish("禁止重复绑定同一个平台群组到不同的通用群组")
            else:
                await matcher.finish(f"绑定失败:{str(e)}")
        finally:
            del Binds[_token]
        await matcher.finish("成功绑定至本通用群组")
    elif key in ["取消", "算了", "结束"]:
        del_Bind(_token)
        await matcher.finish("取消绑定")
    else:
        await matcher.finish("发送信息有误,终止绑定")


_re_bind_ = on_alconna(Alconna(Command_Start, "rebind"))


@_re_bind_.handle()
async def _re_bind___(
        event: Event,
        bot: Bot,
        state: T_State,
        matcher: Matcher,
        user: Annotated[User, GetUser()],
):
    state["user"] = user
    msg = ""
    if _is_private_(event, bot):
        msg += f"当前账户的绑定信息如下:\n{str(user)}\n\n"
    msg += "注意事项:\n1.取消绑定仅是将本平台账户独立开来,并形成新的通用账户,而不会影响剩余绑定在一起的平台账户\n2.取消绑定是可逆的,只需要再次绑定即可\n\n确定要将本平台账户独立开来吗?\n输入'确定' 或 'ok'来确认执行,其他任意语句取消操作"
    await matcher.send(msg)


@_re_bind_.got("arg")
async def _re_bind_confirm(
        event: Event, bot: Bot, state: T_State, matcher: Matcher, arg: str = ArgStr("arg")
):
    if 'user' in state.keys():
        user = state["user"]
    else:
        await matcher.finish()
    if str(arg) in ["确定", "ok"]:
        await del_platform_user(
            user, platform=bot.adapter.get_name(), account=event.get_user_id()
        )
        await matcher.finish("成功取消绑定")
    else:
        await matcher.finish("取消操作")


_re_bind_group_ = on_alconna(Alconna(Command_Start, "rebind", Option("-group")))


@_re_bind_group_.assign("group")
async def _re_bind_group__(
        event: Event,
        bot: Bot,
        state: T_State,
        matcher: Matcher,
        group: Optional[Group] = GetGroup(),
):
    if group is None:
        await matcher.finish("本命令只能在各平台的群聊中使用,私聊中无法使用")

    try:
        await _is_superuser_(event, bot)
    except Exception as e:
        await matcher.finish(str(e))
    state["group"] = group
    msg = f"当前通用群组绑定的平台群组如下:\n{str(group)}\n注意事项:\n1.取消绑定仅是将本平台群组独立开来,并形成新的通用群组,而不会影响剩余绑定在一起的平台群组\n2.取消绑定是可逆的,只需要再次绑定即可\n\n确定要将本平台群组独立开来吗?\n输入'确定' 或 'ok'来确认执行,其他任意语句取消操作"
    await matcher.send(msg)


@_re_bind_group_.got("arg")
async def _re_bind_group_confirm_(
        event: Event, bot: Bot, state: T_State, matcher: Matcher, arg: str = ArgStr("arg")
):
    if 'group' in state.keys():
        group = state["group"]
    else:
        await matcher.finish()
    if str(arg) in ["确定", "ok"]:
        await del_platform_group(
            group, platform=bot.adapter.get_name(), groupid=get_groupid(event, bot)
        )
        await matcher.finish("成功取消绑定")
    else:
        await matcher.finish("取消操作")
