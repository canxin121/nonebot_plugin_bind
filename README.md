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

| 命令                  | 限制    | 含义                          |
|---------------------|-------|-----------------------------|
| 'bind' 或 '绑定'       | 群聊或私聊 | 将其他通用账户绑定至当前通用账户            |
| 'bindinfo' 或 '绑定信息' | 仅私聊   | 查看当前通用账户的平台账户绑定信息           |
| 'rebind' 或 '取消绑定'   | 仅私聊   | 取消本平台账户和通用账户的绑定,并形成一个新的通用账户 |

具体使用请看下图流程示例  
(如果是在群聊中发起的绑定,不会显示下面的绑定信息,只会显示其他内容)  
![使用qq发送bind命令](https://raw.githubusercontent.com/canxin121/nonebot_plugin_bind/main/src/1.png)  
![使用discord发送bind命令和token](https://raw.githubusercontent.com/canxin121/nonebot_plugin_bind/main/src/2.png)  
![使用qq发送密钥确认绑定](https://raw.githubusercontent.com/canxin121/nonebot_plugin_bind/main/src/3.png)  
![取消绑定](https://raw.githubusercontent.com/canxin121/nonebot_plugin_bind/main/src/4.png)  

## 开发者说明
使用依赖注入获取用户信息的示例  
注入后获得的user是一个通用账户的class,其属性id是可以用来区分不同通用账户的唯一值,另一个属性platform_users储存通用账户绑定的所有的平台账户的信息  

```python
from typing import Annotated

from nonebot import require
require('nonebot_plugin_bind')

from nonebot_plugin_bind import GetUser

_bind_info_ = on_command("bindinfo", aliases={"绑定信息"})


@_bind_info_.handle()
async def _bind_info____(event: Event, bot: Bot, matcher: Matcher, user: Annotated[User, GetUser()]):
    if _is_private_(event, bot):
        await matcher.finish(f"当前通用账户的绑定的平台账户如下:\n{str(user)}")
    else:
        await matcher.finish("账户绑定信息只能在私聊中查看")
```
