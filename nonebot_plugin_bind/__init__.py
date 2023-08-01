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

from .types import Bind
from .user_sql import edit_user, del_user, User
from .utils import get_params, get_user, GetUser, _is_private_

__plugin_meta__ = PluginMetadata(
    name="跨平台账户绑定",
    description="nonebot多适配器通用的跨平台账户绑定插件",
    usage="1.使用'bind'或'绑定'命令发起绑定事件\n2.使用'bindinfo'或'绑定信息'查看绑定信息",
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
                  _token=CommandArg(), ):
    global Binds
    if str(_token):
        token = str(_token).replace(" ", "").replace("\n", "")
        if len(token) == 6:
            if token in Binds.keys():
                Binds[token].params = get_params(bot, event)
                user = await get_user(bot, event)
                msg = ""
                if user is not None:
                    Binds[token].orgin_user = user
                    if _is_private_(event, bot):
                        msg += f"当前账户的绑定信息如下:\n{str(user)}"
                msg += f"\n注意事项:\n1.绑定是将本平台账户绑定至刚才发送'{str(cmd)}'命令的平台的账户\n2.绑定后本平台账户所绑定的其他账户和信息都将丢失,替换至刚才发送'{str(cmd)}'命令的平台的账户的绑定信息\n\n使用方式:\b\n如果确认绑定,请用刚才发送'{str(cmd)}'命令的平台的账户在{SECONDS}秒内直接发送以下密钥:\n {Binds[token]._key}"
                await matcher.finish(msg)
            else:
                await matcher.finish("密钥错误或已过期")
        else:
            await matcher.finish("密钥格式错误 或 请勿在初次发送bind命令时追加信息")
    user = await get_user(bot, event)
    _token = str(secrets.token_hex(3))
    scheduler = AsyncIOScheduler()
    scheduler.add_job(del_Bind, 'date', run_date=datetime.now() + timedelta(seconds=120), args=[_token])
    scheduler.start()
    bind = Bind(user)
    state['_token'] = _token
    Binds[_token] = bind
    if _is_private_(event, bot):
        msg = f"当前账户的绑定信息如下:\n{str(user)}"
    else:
        msg = ""
    msg += f'\n注意事项:\n1.绑定是将其他平台账户绑定至当前平台账户身份\n2.绑定后其他平台的账户所绑定的其他账户和信息都将丢失,替换为当前平台用户绑定信息\n\n使用方式:\b\n请用需要绑定的另一个平台的账号在{SECONDS}秒内发送以下内容:\n{str(cmd)} {_token}\n\n发送"取消"或"算了"可以终止绑定'
    await matcher.send(msg)


@_bind_.got("key")
async def bind___(
        state: T_State,
        matcher: Matcher,
        args: str = ArgStr("key")):
    _token = state['_token']
    key = str(args).replace(" ", "").replace("\n", "")
    if key == Binds[_token]._key:
        if Binds[_token].orgin_user is not None:
            await del_user(Binds[_token].orgin_user)
        await edit_user(Binds[_token].user, **Binds[_token].params)
        del Binds[_token]
        await matcher.finish("成功绑定至本平台账户")
    elif key in ["取消", "算了", "结束"]:
        del_Bind(_token)
        await matcher.finish("取消绑定")


_bind_info_ = on_command("bindinfo", aliases={"绑定信息"})


@_bind_info_.handle()
async def __(event: Event, bot: Bot, matcher: Matcher, user: Annotated[User, GetUser()]):
    if _is_private_(event, bot):
        await matcher.finish(f"当前账户的绑定信息如下:\n{str(user)}")
    else:
        await matcher.finish("账户绑定信息只能在私聊中查看")
