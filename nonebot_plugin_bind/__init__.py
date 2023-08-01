import secrets
from datetime import timedelta, datetime
from typing import Annotated

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import get_driver
from nonebot import on_command
from nonebot.adapters import Event, Bot
from nonebot.matcher import Matcher
from nonebot.params import ArgStr, T_State, CommandArg, RawCommand
from nonebot.plugin import PluginMetadata

from ._types import Bind
from .user_sql import User, merge_user, del_platform_user
from .utils import GetUser, _is_private_

__plugin_meta__ = PluginMetadata(
    name="跨平台账户绑定",
    description="nonebot多适配器通用的跨平台账户绑定插件",
    usage="1.使用'bind'或'绑定'命令可以将其他通用账户绑定至当前通用账户\n2.使用'bindinfo'或'绑定信息'查看通用账户的平台账户绑定信息\n3.使用'rebind'或者'取消绑定'可以取消本平台账户和通用账户的绑定,并形成一个新的通用账户",
    type="library",
    homepage="https://github.com/canxin121/nonebot_plugin_bind",
    supported_adapters={"~onebot.v11", "~telegram", "~kaiheila", "~feishu", "~villa"},
)

SECONDS = str(get_driver().config.session_expire_timeout.seconds)

Binds: dict = {}


def del_Bind(_token):
    if _token in Binds.keys():
        del Binds[_token]


_bind_ = on_command("bind", aliases={"绑定"})


@_bind_.handle()
async def _bind__(bot: Bot,
                  event: Event,
                  matcher: Matcher,
                  state: T_State,
                  cmd: Annotated[str, RawCommand()],
                  user: Annotated[User, GetUser()],
                  _token=CommandArg(),
                  ):
    global Binds
    if str(_token):
        _token = str(_token).replace(" ", "").replace("\n", "")
        if len(_token) == 6:
            if _token in Binds.keys():
                msg = ""
                Binds[_token].origin_user = user
                if _is_private_(event, bot):
                    msg += f"当前通用账户的绑定的平台账户如下:\n{str(user)}"
                msg += f"\n注意事项:\n1.此命令是将本通用账户的绑定信息迁移到刚才发送'{str(cmd)}'命令通用账户\n2.本命令会丢失以当前通用账户身份存储的所有数据,且不可逆,所以请小心使用\n\n使用方式:\b\n如果确认绑定,请用刚才发送'{str(cmd)}'命令的平台的账户在{SECONDS}秒内直接发送以下密钥:\n{Binds[_token]._key}"
                await matcher.finish(msg)
            else:
                await matcher.finish("密钥错误或已过期")
        else:
            await matcher.finish("密钥格式错误 或 请勿在初次发送bind命令时追加信息")
    else:
        _token = str(secrets.token_hex(3))
        scheduler = AsyncIOScheduler()
        scheduler.add_job(del_Bind, 'date', run_date=datetime.now() + timedelta(seconds=int(SECONDS)), args=[_token])
        scheduler.start()
        bind = Bind()
        bind.to_user = user
        state['_token'] = _token
        Binds[_token] = bind
        if _is_private_(event, bot):
            msg = f"当前通用账户的绑定的平台账户如下:\n{str(user)}"
        else:
            msg = ""
        msg += f'\n注意事项:\n1.一个通用账户可以绑定多个平台账户\n2.此命令是将另一个通用账户的绑定信息合并到当前通用账户\n3.本命令会丢失以另一个通用账户身份存储的所有数据,且不可逆,所以请小心使用\n\n使用方式:\b\n请用需要绑定的另一个平台的账号在{SECONDS}秒内发送以下内容:\n{str(cmd)} {_token}\n\n发送"取消"或"算了"可以终止绑定'
        await matcher.send(msg)


@_bind_.got("key")
async def bind___(
        state: T_State,
        matcher: Matcher,
        args: str = ArgStr("key")):
    _token = state['_token']
    key = str(args).replace(" ", "").replace("\n", "")
    if key == Binds[_token]._key:
        try:
            await merge_user(Binds[_token].to_user, Binds[_token].origin_user)
        except Exception as e:
            raise e
        finally:
            del Binds[_token]
        await matcher.finish("成功绑定至本通用账户")
    elif key in ["取消", "算了", "结束"]:
        del_Bind(_token)
        await matcher.finish("取消绑定")


_bind_info_ = on_command("bindinfo", aliases={"绑定信息"})


@_bind_info_.handle()
async def __(event: Event, bot: Bot, matcher: Matcher, user: Annotated[User, GetUser()]):
    if _is_private_(event, bot):
        await matcher.finish(f"当前通用账户的绑定的平台账户如下:\n{str(user)}")
    else:
        await matcher.finish("账户绑定信息只能在私聊中查看")


_re_bind_ = on_command("rebind", aliases={"取消绑定"})


@_re_bind_.handle()
async def _re_bind___(event: Event, bot: Bot, state: T_State, matcher: Matcher, user: Annotated[User, GetUser()]):
    state['user'] = user
    msg = ""
    if _is_private_(event, bot):
        msg += f"当前账户的绑定信息如下:\n{str(user)}\n\n"
    msg += "注意事项:\n1.取消绑定仅是将本平台账户独立开来,并形成新的通用账户,而不会影响剩余绑定在一起的平台账户\n2.取消绑定是可逆的,只需要再次绑定即可\n\n确定要将本平台账户独立开来吗?\n输入'确定' 或 'ok'来确认执行,其他任意语句取消操作"
    await matcher.send(msg)


@_re_bind_.got("arg")
async def _re_bind_confirm(event: Event, bot: Bot, state: T_State, matcher: Matcher, arg: str = ArgStr("arg")):
    user = state['user']
    if str(arg) in ['确定', 'ok']:
        await del_platform_user(user, platform=bot.adapter.get_name(), account=event.get_user_id())
        await matcher.finish("成功取消绑定")
    else:
        await matcher.finish("取消操作")
