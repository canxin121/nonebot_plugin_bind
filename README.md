<div align="center">
  <a href="https://github.com/canxin121">
    <img src="https://socialify.git.ci/canxin121/nonebot_plugin_bind/image?font=Raleway&forks=1&issues=1&language=1&logo=https%3A%2F%2Fcanxin121.github.io%2Fdocs%2Flogo.png&name=1&owner=1&pattern=Charlie%20Brown&pulls=1&stargazers=1&theme=Auto" width="700" height="350">
  </a>
  <h1>nonebot_plugin_bind</h1>
</div>

<p align="center">
    <a href="https://pypi.python.org/pypi/nonebot-plugin-bind">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-bind" alt="pypi">
    </a>
    <img src="https://img.shields.io/pypi/pyversions/nonebot-plugin-bind" alt="python">
    <img src="https://img.shields.io/pypi/dm/nonebot-plugin-bind" alt="pypi">
    <br />
    <a href="https://github.com/canxin121/nonebot_plugin_bind/releases/">
    <a href="https://img.shields.io/github/last-commit/canxin121/nonebot_plugin_bind">
    </a>
</p>
<div align="left">

# 适配支持

- onebotv11
- telegram
- discord
- kook(开黑啦)
- villa(大别野)
- 飞书

# 使用说明

## 用户使用说明

| 命令                | 限制    | 含义                          |
|-------------------|-------|-----------------------------|
| 'bind'            | 群聊或私聊 | 将其他通用账户绑定至当前通用账户            |
| 'bindinfo'        | 仅私聊   | 查看当前通用账户的平台账户绑定信息           |
| 'rebind'          | 仅私聊   | 取消本平台账户和通用账户的绑定,并形成一个新的通用账户 |
| 'bind -group'     | 群聊或私聊 | 将其他通用群组绑定至当前通用群组            |
| 'bindinfo -group' | 仅私聊   | 查看当前通用群组的平台群组绑定信息           |
| 'rebind -group'   | 仅私聊   | 取消本平台群组和通用尊祖的绑定,并形成一个新的通用群组 |

## 配置项

请使用[Webui](https://github.com/canxin121/nonebot_plugin_web_config)
进行配置,默认端口为8666,ip为主机对应ip,默认本地地址为http:
//127.0.0.1:8666

| 配置名              | 默认    | 含义                                                               |
|------------------|-------|------------------------------------------------------------------|
| bind_superuser   | []    | bind的superuser,用以管理群组绑定,注意填写的值应该是通过bindinfo查询出的id,而不是你的某个社交平台的账户 |
| bind_group_admin | False | 是否允许某社交平台的群组的管理员直接管理其群组绑定,不管他是否是bind_superuser                   |

具体使用请看下图流程示例(群聊绑定同理)  
(如果是在群聊中发起的绑定,不会显示下面的绑定信息,只会显示其他内容)  
![使用qq发送bind命令](https://raw.githubusercontent.com/canxin121/nonebot_plugin_bind/master/src/1.png)  
![使用discord发送bind命令和token](https://raw.githubusercontent.com/canxin121/nonebot_plugin_bind/master/src/2.png)  
![使用qq发送密钥确认绑定](https://raw.githubusercontent.com/canxin121/nonebot_plugin_bind/master/src/3.png)  
![取消绑定](https://raw.githubusercontent.com/canxin121/nonebot_plugin_bind/master/src/4.png)

## 开发者说明

主要提供两个依赖注入

1. GetUser:返回一个User实例,其属性id为一个通用账户的唯一标识,其属性platform_users中包含绑定的所有平台账户的信息
2. GetGroup:返回一个Group实例,其属性id为一个通用群组的唯一标识,其属性platform_groups中包含所有绑定的平台群组的信息(
   其中groupid是对应平台群组的id)(如果不想在匹配非群组消息时跳过matcher,请使用Optional类型注释)

示例代码如下

```python
from typing import Annotated

from nonebot import require

require('nonebot_plugin_bind')

from nonebot_plugin_bind import GetUser, GetGroup, GetGroupId, User, Group

# 此处省略了部分import

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
    # 如果在私聊中发送此命令,得到的group会是None,groupid也是如此 
    if group is None:
        await matcher.finish("本命令只能在各平台的群聊中使用,私聊中无法使用")
    group_str = "\n".join(
        pg + "  √" if groupid in pg else pg for pg in str(group).split("\n")
    )
    await matcher.send(f"当前通用群组的绑定的平台群组如下:\n{group_str}")


_bind_ = on_alconna(
    Alconna(Command_Start, "bind", Option("token", Args["token_value", str]))
)

```
