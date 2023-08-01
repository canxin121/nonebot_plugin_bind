import asyncio
from pathlib import Path
from typing import Optional, List

from sqlalchemy import select, ForeignKey, UniqueConstraint
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column, joinedload

ROOT = Path().parent / 'data'
ROOT.mkdir(exist_ok=True)
PATH = (ROOT / "bind.db")
PATH.touch(exist_ok=True)
Engine_Arg = make_url(f"sqlite+aiosqlite:///{str(PATH)}")
Engine = create_async_engine(Engine_Arg)
Async_Session = async_sessionmaker(Engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_users: Mapped[List['PlatFormUser']] = relationship(back_populates='user', cascade='all, delete-orphan')

    def __str__(self):
        pu_str = "\n".join(str(pu) for pu in self.platform_users)
        return pu_str

    def __repr__(self):
        return f"id={self.id}\n{str(self)}"


class PlatFormUser(Base):
    __tablename__ = "platform_user"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped["User"] = relationship(back_populates='platform_users')
    platform: Mapped[str]
    account: Mapped[str]

    __table_args__ = (
        UniqueConstraint('platform', 'account', name='uc_platform_account'),
    )

    def __str__(self):
        return f"{self.platform}:{self.account}"

    def __repr__(self):
        return str(self)


async def add_user(platform: str, account: str):
    """添加一个新的user"""
    async with Async_Session() as session:
        user = User()
        PlatFormUser(user=user, platform=platform, account=account)
        session.add(user)
        await session.commit()


async def get_user(platform: str, account: str, auto_create: bool = True):
    """获取指定user,如无则创建新的"""
    args = {}
    for key, value in {"platform": platform, "account": account}.items():
        if value is not None:
            args[key] = value
    if not args:
        raise Exception("至少需要提供id或account中的一个")
    async with Async_Session() as session:
        result = await session.scalars(
            select(User).options(joinedload(User.platform_users)).join(PlatFormUser).filter_by(**args))
        user = result.first()
        if user is not None or (not auto_create):
            return user
        else:
            await add_user(platform, account)
            result = await session.scalars(
                select(User).options(joinedload(User.platform_users)).join(PlatFormUser).filter_by(**args))
            return result.first()


async def del_user(
        platform: str,
        account: Optional[str] = None,
        user: User = None, ):
    """删掉指定user"""
    if user is None:
        user = await get_user(platform, account, False)
    if user is not None:
        async with Async_Session() as session:
            await session.delete(user)
            await session.commit()
    else:
        return


async def merge_user(to_user: User, origin_user: User):
    """将origin_user的绑定信息迁移合并到to_user种"""
    args_set = set()
    for pu in to_user.platform_users + origin_user.platform_users:
        args = (pu.platform, pu.account)
        args_set.add(args)

    async with Async_Session() as session:
        new_user = User(id=to_user.id)
        platform_users = [PlatFormUser(user=new_user, platform=platform, account=account) for platform, account in
                          args_set]
        await session.delete(to_user)
        await session.delete(origin_user)
        await session.flush()
        session.add_all(platform_users)
        await session.commit()


async def del_platform_user(user: User, platform: str, account: str):
    """三者都是同一个platform_user的值"""
    async with Async_Session() as session:
        if len(user.platform_users) == 1:
            await session.delete(user)
            await session.commit()
            return
        else:
            result1 = await session.scalars(select(PlatFormUser).filter_by(platform=platform, account=account))
            platform_user = result1.one_or_none()
            await session.delete(platform_user)
            await session.commit()
            return


async def add_platform_user(
        user: User,
        platform: str,
        account: str,
):
    """将后两者绑定到前者"""
    async with Async_Session() as session:
        platform_user = PlatFormUser(user=user, platform=platform, account=account)
        session.add(platform_user)
        await session.commit()
        return


async def create_all():
    async with Engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(create_all())
if __name__ == '__main__':
    async def main():
        user1 = await get_user('qq', '123')
        user2 = await get_user('wechat', '456')

        # 合并两个用户
        await merge_user(user1, user2)
        user = await get_user('qq', '123')
        print(user)


    asyncio.run(main())
