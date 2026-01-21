from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlmodel import Field, col, select
from sqlalchemy import delete, null, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import and_

from gsuid_core.logger import logger
from gsuid_core.utils.database.base_models import Bind, User, BaseModel, with_session

# 插件未发布阶段不执行迁移

T_WavesBind = TypeVar("T_WavesBind", bound="WavesBind")
T_WavesUser = TypeVar("T_WavesUser", bound="WavesUser")
T_WavesStaminaRecord = TypeVar("T_WavesStaminaRecord", bound="WavesStaminaRecord")


class WavesBind(Bind, table=True):
    __table_args__: Dict[str, Any] = {"extend_existing": True}
    uid: Optional[str] = Field(default=None, title="鸣潮UID")
    pgr_uid: Optional[str] = Field(default=None, title="战双UID")


class WavesUser(User, table=True):
    __table_args__: Dict[str, Any] = {"extend_existing": True}
    cookie: str = Field(default="", title="Cookie")
    uid: str = Field(default=None, title="鸣潮UID")
    record_id: Optional[str] = Field(default=None, title="记录ID")
    platform: str = Field(default="", title="ck平台")
    stamina_bg_value: str = Field(default="", title="体力背景")
    bbs_sign_switch: str = Field(default="off", title="自动社区签到")
    bat: str = Field(default="", title="bat")
    did: str = Field(default="", title="did")
    game_id: int = Field(default=3, title="GameID")
    is_login: bool = Field(default=False, title="是否waves登录")
    created_time: Optional[int] = Field(default=None, title="创建时间")
    last_used_time: Optional[int] = Field(default=None, title="最后使用时间")

    @classmethod
    @with_session
    async def mark_cookie_invalid(
        cls: Type[T_WavesUser], session: AsyncSession, uid: str, cookie: str, mark: str
    ) -> bool:
        sql = update(cls).where(col(cls.uid) == uid).where(col(cls.cookie) == cookie).values(status=mark)
        await session.execute(sql)
        return True

    @classmethod
    @with_session
    async def select_waves_user(
        cls: Type[T_WavesUser],
        session: AsyncSession,
        uid: str,
        user_id: str,
        bot_id: str,
        game_id: Optional[int] = None,
    ) -> Optional[T_WavesUser]:
        filters: List[Any] = [
            cls.user_id == user_id,
            cls.uid == uid,
            cls.bot_id == bot_id,
        ]
        if game_id is not None:
            filters.append(cls.game_id == game_id)
        sql = select(cls).where(*filters)
        result = await session.execute(sql)
        data = result.scalars().all()
        return data[0] if data else None

    @classmethod
    @with_session
    async def select_data_by_cookie(
        cls: Type[T_WavesUser], session: AsyncSession, cookie: str
    ) -> Optional[T_WavesUser]:
        sql = select(cls).where(cls.cookie == cookie)
        result = await session.execute(sql)
        data = result.scalars().all()
        return data[0] if data else None

    @classmethod
    @with_session
    async def select_data_by_cookie_and_uid(
        cls: Type[T_WavesUser],
        session: AsyncSession,
        cookie: str,
        uid: str,
        game_id: Optional[int] = None,
    ) -> Optional[T_WavesUser]:
        filters = [cls.cookie == cookie, cls.uid == uid]
        if game_id is not None:
            filters.append(cls.game_id == game_id)
        sql = select(cls).where(*filters)
        result = await session.execute(sql)
        data = result.scalars().all()
        return data[0] if data else None

    @classmethod
    @with_session
    async def update_last_used_time(
        cls,
        session: AsyncSession,
        uid: str,
        user_id: str,
        bot_id: str,
        game_id: Optional[int] = None,
    ) -> bool:
        import time

        current_time = int(time.time())
        filters = [
            cls.user_id == user_id,
            cls.uid == uid,
            cls.bot_id == bot_id,
        ]
        if game_id is not None:
            filters.append(cls.game_id == game_id)

        result = await session.execute(select(cls).where(*filters))
        user = result.scalars().first()

        if user and user.cookie:
            user.last_used_time = current_time
            if user.created_time is None:
                user.created_time = current_time
            return True
        return False


class WavesStaminaRecord(BaseModel, table=True):
    """体力查询记录表"""

    __tablename__ = "WavesStaminaRecord"
    __table_args__: Dict[str, Any] = {"extend_existing": True}

    uid: str = Field(default="", title="鸣潮UID")
    bot_self_id: str = Field(default="", title="BotSelfID")
    mr_query_time: Optional[int] = Field(default=None, title="体力查询时间")
    mr_value: Optional[int] = Field(default=None, title="结晶波片值")
    user_email: str = Field(default="", title="用户邮箱")
    email_last_try_time: Optional[int] = Field(default=None, title="邮件上次尝试发送时间")
    email_send_success: Optional[bool] = Field(default=None, title="邮箱发送成功")
    email_last_success_time: Optional[int] = Field(default=None, title="邮件上次发送成功时间")
    email_fail_count: int = Field(default=0, title="连续发送失败次数")
    stamina_push_switch: str = Field(default="off", title="体力推送开关")
    stamina_threshold: Optional[int] = Field(default=None, title="体力阈值")
    is_ck_valid: Optional[bool] = Field(default=None, title="CK是否有效")

    @classmethod
    @with_session
    async def upsert_stamina_query(
        cls: Type[T_WavesStaminaRecord],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        bot_self_id: str,
        uid: str,
        mr_query_time: int,
        mr_value: Optional[int],
        is_ck_valid: Optional[bool],
    ) -> bool:
        sql = select(cls).where(
            and_(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
                cls.uid == uid,
            )
        )
        result = await session.execute(sql)
        record = result.scalars().first()

        if record:
            record.bot_self_id = bot_self_id
            record.mr_query_time = mr_query_time
            record.mr_value = mr_value
            record.is_ck_valid = is_ck_valid
            session.add(record)
            return True

        session.add(
            cls(
                user_id=user_id,
                bot_id=bot_id,
                bot_self_id=bot_self_id,
                uid=uid,
                mr_query_time=mr_query_time,
                mr_value=mr_value,
                is_ck_valid=is_ck_valid,
            )
        )
        return True

    @classmethod
    @with_session
    async def update_ck_valid(
        cls: Type[T_WavesStaminaRecord],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        bot_self_id: str,
        uid: str,
        is_ck_valid: bool,
    ) -> bool:
        sql = select(cls).where(
            and_(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
                cls.uid == uid,
            )
        )
        result = await session.execute(sql)
        record = result.scalars().first()

        if record:
            record.bot_self_id = bot_self_id
            record.is_ck_valid = is_ck_valid
            session.add(record)
            return True

        session.add(
            cls(
                user_id=user_id,
                bot_id=bot_id,
                bot_self_id=bot_self_id,
                uid=uid,
                is_ck_valid=is_ck_valid,
            )
        )
        return True

    @classmethod
    @with_session
    async def update_email_status(
        cls: Type[T_WavesStaminaRecord],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        bot_self_id: str,
        uid: str,
        email_last_try_time: int,
        email_send_success: bool,
        email_fail_count: int,
        email_last_success_time: Optional[int] = None,
    ) -> bool:
        sql = select(cls).where(
            and_(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
                cls.uid == uid,
            )
        )
        result = await session.execute(sql)
        record = result.scalars().first()

        if record:
            record.bot_self_id = bot_self_id
            record.email_last_try_time = email_last_try_time
            record.email_send_success = email_send_success
            record.email_fail_count = email_fail_count
            if email_last_success_time is not None:
                record.email_last_success_time = email_last_success_time
            session.add(record)
            return True

        session.add(
            cls(
                user_id=user_id,
                bot_id=bot_id,
                bot_self_id=bot_self_id,
                uid=uid,
                email_last_try_time=email_last_try_time,
                email_send_success=email_send_success,
                email_fail_count=email_fail_count,
                email_last_success_time=email_last_success_time,
            )
        )
        return True

    @classmethod
    @with_session
    async def upsert_user_settings(
        cls: Type[T_WavesStaminaRecord],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        bot_self_id: str,
        uid: str,
        **data,
    ) -> bool:
        sql = select(cls).where(
            and_(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
                cls.uid == uid,
            )
        )
        result = await session.execute(sql)
        record = result.scalars().first()

        if record:
            record.bot_self_id = bot_self_id
            for k, v in data.items():
                if hasattr(record, k):
                    setattr(record, k, v)
            session.add(record)
            return True

        session.add(
            cls(
                user_id=user_id,
                bot_id=bot_id,
                bot_self_id=bot_self_id,
                uid=uid,
                **data,
            )
        )
        return True

    @classmethod
    @with_session
    async def get_record(
        cls: Type[T_WavesStaminaRecord],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        bot_self_id: str,
        uid: str,
    ) -> Optional[T_WavesStaminaRecord]:
        sql = select(cls).where(
            and_(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
                cls.uid == uid,
            )
        )
        result = await session.execute(sql)
        record = result.scalars().first()
        return record

    @classmethod
    @with_session
    async def get_all_records(
        cls: Type[T_WavesStaminaRecord],
        session: AsyncSession,
    ) -> List[T_WavesStaminaRecord]:
        result = await session.execute(select(cls))
        data = result.scalars().all()
        return list(data) if data else []

    @classmethod
    @with_session
    async def delete_by_uid(
        cls: Type[T_WavesStaminaRecord],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        uid: str,
    ) -> int:
        sql = delete(cls).where(
            and_(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
                cls.uid == uid,
            )
        )
        result = await session.execute(sql)
        return result.rowcount

    @classmethod
    @with_session
    async def delete_by_user(
        cls: Type[T_WavesStaminaRecord],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
    ) -> int:
        sql = delete(cls).where(
            and_(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
            )
        )
        result = await session.execute(sql)
        return result.rowcount
