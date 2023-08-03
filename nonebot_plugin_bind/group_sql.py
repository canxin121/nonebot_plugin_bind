import asyncio
from typing import List, Optional

from nonebot_plugin_datastore.db import get_engine
from sqlalchemy import ForeignKey, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload

from .user_sql import create_session, db


class Group(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_groups: Mapped[List['PlatFormGroup']] = relationship(back_populates='group', cascade='all, delete-orphan')

    def __str__(self):
        pg_str = "\n".join(str(pg) for pg in self.platform_groups)
        return f"id={self.id}\n{pg_str}"

    def __repr__(self):
        return f"id={self.id}\n{str(self)}"


class PlatFormGroup(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey('nonebot_plugin_bind_group.id'))
    group: Mapped[Group] = relationship(Group, back_populates='platform_groups')
    platform: Mapped[str]
    groupid: Mapped[str]

    __table_args__ = (
        UniqueConstraint('platform', 'groupid', name='uc_platform_groupid'),
    )

    def __str__(self):
        return f"{self.platform}:{self.groupid}"

    def __repr__(self):
        return str(self)


Group.platform_groups = relationship(PlatFormGroup, uselist=True, back_populates='group', cascade='all, delete-orphan')


async def add_group(platform: str, groupid: str):
    """添加一个新的group"""
    async with create_session() as session:
        group = Group()
        PlatFormGroup(group=group, platform=platform, groupid=groupid)
        session.add(group)
        await session.commit()


async def get_group(platform: str, groupid: str, auto_create: bool = True):
    """获取指定group,如无则创建新的"""
    args = {}
    for key, value in {"platform": platform, "groupid": groupid}.items():
        if value is not None:
            args[key] = value
    if not args:
        raise Exception("至少需要提供id或groupid中的一个")
    async with create_session() as session:
        result = await session.scalars(
            select(Group).options(joinedload(Group.platform_groups)).join(PlatFormGroup).filter_by(**args))
        group = result.first()
        if group is not None or (not auto_create):
            return group
        else:
            await add_group(platform, groupid)
            result = await session.scalars(
                select(Group).options(joinedload(Group.platform_groups)).join(PlatFormGroup).filter_by(**args))
            return result.first()


async def del_group(
        platform: str,
        groupid: Optional[str] = None,
        group: Group = None, ):
    """删掉指定group"""
    if group is None:
        group = await get_group(platform, groupid, False)
    if group is not None:
        async with create_session() as session:
            await session.delete(group)
            await session.commit()
    else:
        return


async def merge_group(to_group: Group, origin_group: Group):
    """将origin_group的绑定信息迁移合并到to_group种"""
    args_set = set()
    for pu in to_group.platform_groups + origin_group.platform_groups:
        args = (pu.platform, pu.groupid)
        args_set.add(args)

    async with create_session() as session:
        new_group = Group(id=to_group.id)
        platform_groups = [PlatFormGroup(group=new_group, platform=platform, groupid=groupid) for platform, groupid
                           in
                           args_set]
        await session.delete(to_group)
        await session.delete(origin_group)
        await session.flush()
        session.add_all(platform_groups)
        await session.commit()


async def del_platform_group(group: Group, platform: str, groupid: str):
    """三者都是同一个platform_group的值"""
    async with create_session() as session:
        if len(group.platform_groups) == 1:
            await session.delete(group)
            await session.commit()
            return
        else:
            result1 = await session.scalars(select(PlatFormGroup).filter_by(platform=platform, groupid=groupid))
            platform_group = result1.one_or_none()
            await session.delete(platform_group)
            await session.commit()
            return


async def add_platform_group(
        group: Group,
        platform: str,
        groupid: str,
):
    """将后两者绑定到前者"""
    async with create_session() as session:
        platform_group = PlatFormGroup(group=group, platform=platform, groupid=groupid)
        session.add(platform_group)
        await session.commit()
        return


async def _init_():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(db.metadata.create_all)


asyncio.run(_init_())
