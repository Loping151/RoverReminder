from typing import Any, Dict, Optional, Type, TypeVar

from sqlmodel import Field, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import and_, or_

from gsuid_core.utils.database.base_models import BaseBotIDModel, with_session

T_WavesUserActivity = TypeVar("T_WavesUserActivity", bound="WavesUserActivity")


class WavesUserActivity(BaseBotIDModel, table=True):
    """用户活跃度记录表"""

    __tablename__ = "WavesUserActivity"
    __table_args__: Dict[str, Any] = {"extend_existing": True}

    user_id: str = Field(default="", title="用户ID")
    bot_self_id: str = Field(default="", title="BotSelfID")
    last_active_time: Optional[int] = Field(default=None, title="最后活跃时间")

    @classmethod
    @with_session
    async def get_user_last_active_time(
        cls: Type[T_WavesUserActivity],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        bot_self_id: str,
    ) -> Optional[int]:
        sql = select(cls).where(
            and_(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
                cls.bot_self_id == bot_self_id,
            )
        )
        result = await session.execute(sql)
        record = result.scalars().first()
        if record:
            return record.last_active_time

        legacy_sql = select(cls).where(
            and_(
                cls.user_id == user_id,
                cls.bot_id == bot_self_id,
                or_(cls.bot_self_id == "", cls.bot_self_id.is_(None)),
            )
        )
        legacy_result = await session.execute(legacy_sql)
        legacy = legacy_result.scalars().first()
        return legacy.last_active_time if legacy else None

    @classmethod
    @with_session
    async def is_user_active(
        cls: Type[T_WavesUserActivity],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        bot_self_id: str,
        active_days: int,
    ) -> bool:
        import time

        last_active_time = await cls.get_user_last_active_time(user_id, bot_id, bot_self_id)
        if last_active_time is None:
            return False

        current_time = int(time.time())
        threshold_time = current_time - (active_days * 24 * 60 * 60)
        return last_active_time >= threshold_time
