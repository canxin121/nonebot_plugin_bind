import asyncio
from pathlib import Path

from sqlalchemy import UniqueConstraint, Index
from sqlalchemy import select, Integer, String
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

ROOT = Path().parent / 'data'
ROOT.mkdir(exist_ok=True)
PATH = (ROOT / "bind.db").absolute()
PATH.touch(exist_ok=True)
Engine_Arg = f"sqlite+aiosqlite{PATH.as_uri()[4:]}"
Engine = create_async_engine(Engine_Arg)
async_session = async_sessionmaker(Engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(type_=Integer, primary_key=True)
    qq_account: Mapped[str] = mapped_column(type_=String, nullable=True)
    wechat_account: Mapped[str] = mapped_column(type_=String, nullable=True)
    telegram_account: Mapped[str] = mapped_column(type_=String, nullable=True)
    discord_account: Mapped[str] = mapped_column(type_=String, nullable=True)
    kook_account: Mapped[str] = mapped_column(type_=String, nullable=True)
    feishu_account: Mapped[str] = mapped_column(type_=String, nullable=True)
    dingtalk_account: Mapped[str] = mapped_column(type_=String, nullable=True)
    mihoyo_account: Mapped[str] = mapped_column(type_=String, nullable=True)
    __table_args__ = (
        UniqueConstraint('qq_account'),
        UniqueConstraint('wechat_account'),
        UniqueConstraint('telegram_account'),
        UniqueConstraint('discord_account'),
        UniqueConstraint('kook_account'),
        UniqueConstraint('feishu_account'),
        UniqueConstraint('dingtalk_account'),
        UniqueConstraint('mihoyo_account'),
        Index('ix_accounts_qq', 'qq_account', unique=True),
        Index('ix_account_wechat', 'wechat_account', unique=True),
        Index('ix_accounts_tg', 'telegram_account', unique=True),
        Index('ix_accounts_discord', 'discord_account', unique=True),
        Index('ix_accounts_kook', 'kook_account', unique=True),
        Index('ix_accounts_feishu', 'feishu_account', unique=True),
        Index('ix_accounts_dingtalk', 'dingtalk_account', unique=True),
        Index('ix_accounts_mihoyo', 'mihoyo_account', unique=True),
    )

    def __str__(self):
        result = ""
        for attr in sorted(self.__dict__, key=len):
            if not attr.startswith("_"):
                value = getattr(self, attr)
                if value is not None:
                    result += f"{attr}: {value}\n"
        return result


def build_params(qq_account, telegram_account, discord_account, kook_account,
                 feishu_account, dingtalk_account, mihoyo_account):
    # 使用字典推导式来构建参数字典
    params = {field: param for param, field in zip([qq_account, telegram_account, discord_account, kook_account,
                                                    feishu_account, dingtalk_account, mihoyo_account],
                                                   ["qq_account", "telegram_account", "discord_account", "kook_account",
                                                    "feishu_account", "dingtalk_account", "mihoyo_account"])
              if param}
    return params


def set_params(user, qq_account, telegram_account, discord_account, kook_account,
               feishu_account, dingtalk_account, mihoyo_account):
    params = {
        "qq_account": qq_account,
        "telegram_account": telegram_account,
        "discord_account": discord_account,
        "kook_account": kook_account,
        "feishu_account": feishu_account,
        "dingtalk_account": dingtalk_account,
        "mihoyo_account": mihoyo_account
    }
    for attr, value in params.items():
        if value is not None:
            setattr(user, attr, value)


async def get_user(
        qq_account: str = None,
        telegram_account: str = None,
        discord_account: str = None,
        kook_account: str = None,
        feishu_account: str = None,
        dingtalk_account: str = None,
        mihoyo_account: str = None,
        auto_create: bool = True, ):
    if not any([qq_account, telegram_account, discord_account, kook_account,
                feishu_account, dingtalk_account, mihoyo_account]):
        raise ValueError("At least one account parameter must be provided")

    params = build_params(qq_account, telegram_account, discord_account, kook_account,
                          feishu_account, dingtalk_account, mihoyo_account)

    async with async_session() as session:
        stmt = select(User).filter_by(**params)
        result = await session.scalars(stmt)
        user = result.one_or_none()
        if user is not None or (not auto_create):
            return user
        else:
            user = User()
            set_params(user, qq_account, telegram_account, discord_account,
                       kook_account, feishu_account, dingtalk_account, mihoyo_account)
            session.add(user)
            await session.commit()
            result = await session.scalars(select(User).filter_by(**params))
            return result.one_or_none()


async def del_user(
        user: User = None,
        qq_account: str = None,
        telegram_account: str = None,
        discord_account: str = None,
        kook_account: str = None,
        feishu_account: str = None,
        dingtalk_account: str = None,
        mihoyo_account: str = None):
    if user is None:
        user = await get_user(qq_account, telegram_account, discord_account, kook_account,
                              feishu_account, dingtalk_account, mihoyo_account)
    async with async_session() as session:
        await session.delete(user)
        await session.commit()


async def edit_user(
        user: User,
        qq_account: str = None,
        telegram_account: str = None,
        discord_account: str = None,
        kook_account: str = None,
        feishu_account: str = None,
        dingtalk_account: str = None,
        mihoyo_account: str = None,
):
    async with async_session() as session:
        set_params(user, qq_account, telegram_account, discord_account, kook_account,
                   feishu_account, dingtalk_account, mihoyo_account)
        session.add(user)
        await session.commit()
        return user


async def create_all():
    async with Engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(create_all())

if __name__ == '__main__':
    async def async_main() -> None:
        # account = await get_user(discord_account='2187291322')
        # print(account)
        # print(account.id)
        await get_user(discord_account='2187291322111')
        await del_user(discord_account='2187291322')


    asyncio.run(async_main())
