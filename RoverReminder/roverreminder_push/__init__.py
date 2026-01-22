import asyncio
import time
from datetime import datetime
from typing import Dict, Optional

from gsuid_core.aps import scheduler
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.api.model import AccountBaseInfo, DailyData
from ..utils.api.request_util import KuroApiResp
from ..utils.api.requests import waves_api
from ..utils.database.models import WavesStaminaRecord
from ..utils.mail_logger import get_mail_logger
from ..utils.status_store import record_fail, record_success
from ..utils.database.waves_user_activity import WavesUserActivity
from ..roverreminder_config.roverreminder_config import RoverReminderConfig

mail_logger = get_mail_logger()
_check_lock = asyncio.Lock()


async def process_uid(uid, ev):
    ck = await waves_api.get_self_waves_ck(uid, ev.user_id, ev.bot_id)
    if not ck:
        try:
            await WavesStaminaRecord.update_ck_valid(
                user_id=ev.user_id,
                bot_id=ev.bot_id,
                bot_self_id=ev.bot_self_id or "",
                uid=uid,
                is_ck_valid=False,
            )
        except Exception:
            logger.exception("[鸣潮][每日信息]体力记录CK有效状态更新失败")
        return None

    results = await asyncio.gather(
        waves_api.get_daily_info(uid, ck),
        waves_api.get_base_info(uid, ck),
        return_exceptions=True,
    )

    (daily_info_res, account_info_res) = results
    if not isinstance(daily_info_res, KuroApiResp) or not daily_info_res.success:
        return None

    if not isinstance(account_info_res, KuroApiResp) or not account_info_res.success:
        return None

    daily_info = DailyData.model_validate(daily_info_res.data)
    account_info = AccountBaseInfo.model_validate(account_info_res.data)

    try:
        mr_value = daily_info.energyData.cur if daily_info.energyData else None
        await WavesStaminaRecord.upsert_stamina_query(
            user_id=ev.user_id,
            bot_id=ev.bot_id,
            bot_self_id=ev.bot_self_id or "",
            uid=uid,
            mr_query_time=int(time.time()),
            mr_value=mr_value,
            is_ck_valid=True,
        )
    except Exception:
        logger.exception("[鸣潮][每日信息]体力查询记录写入失败")

    return {
        "daily_info": daily_info,
        "account_info": account_info,
    }


def _calc_current_stamina(record: WavesStaminaRecord, now_ts: int) -> Optional[int]:
    if record.mr_query_time is None or record.mr_value is None:
        return None
    delta = max(0, now_ts - record.mr_query_time)
    return record.mr_value + int(delta // 360)


def _should_try_send(record: WavesStaminaRecord, threshold: int, now_ts: int) -> bool:
    if record.email_last_success_time is None:
        return True
    cooldown_hours = max(1, threshold // 10 - 1)
    return (now_ts - record.email_last_success_time) >= cooldown_hours * 3600


async def _handle_record(record: WavesStaminaRecord, threshold_default: int, now_ts: int) -> None:
    if not record.uid:
        return
    if record.stamina_push_switch != "on":
        logger.debug(f"[RoverReminder] 跳过 uid={record.uid}：推送未开启")
        return
    if not record.user_email:
        logger.debug(f"[RoverReminder] 跳过 uid={record.uid}：未设置邮箱")
        return
    if record.email_fail_count is not None and record.email_fail_count >= 5:
        logger.debug(f"[RoverReminder] 跳过 uid={record.uid}：连续失败次数过多 ({record.email_fail_count})")
        return

    active_days = RoverReminderConfig.get_config("ActiveUserDays").data
    if active_days and active_days > 0:
        is_active = await WavesUserActivity.is_user_active(
            record.user_id,
            record.bot_id,
            record.bot_self_id or "",
            active_days,
        )
        if not is_active:
            logger.debug(f"[RoverReminder] 跳过 uid={record.uid}：不活跃")
            return

    threshold = record.stamina_threshold or threshold_default
    if threshold < 120:
        threshold = 120
    if threshold > 240:
        threshold = 240

    if not _should_try_send(record, threshold, now_ts):
        cooldown_hours = max(1, threshold // 10 - 1)
        last_try = record.email_last_success_time or 0
        logger.debug(
            f"[RoverReminder] uid={record.uid} 未到发送间隔，跳过发送 last_success={last_try} cooldown_hours={cooldown_hours}"
        )
        return

    current_stamina = _calc_current_stamina(record, now_ts)
    if current_stamina is None:
        logger.debug(f"[RoverReminder] uid={record.uid} 缺少本地体力记录，尝试查询")
        ev = Event(
            user_id=record.user_id,
            bot_id=record.bot_id,
            bot_self_id=record.bot_self_id or "",
        )
        data = await process_uid(record.uid, ev)
        if not data:
            logger.debug(f"[RoverReminder] uid={record.uid} API查询失败或CK失效，未发送邮件")
            return
        daily_info = data["daily_info"]
        stamina_value = daily_info.energyData.cur if daily_info.energyData else 0
        if stamina_value < threshold:
            logger.debug(
                f"[RoverReminder] uid={record.uid} API体力={stamina_value} 未达阈值={threshold}，不发送邮件"
            )
            return
        current_stamina = stamina_value

    will_check_api = current_stamina >= threshold
    logger.debug(
        f"[RoverReminder] uid={record.uid} 本地推测体力={current_stamina} 阈值={threshold} 预计请求API={will_check_api}"
    )
    if not will_check_api:
        return

    ev = Event(
        user_id=record.user_id,
        bot_id=record.bot_id,
        bot_self_id=record.bot_self_id or "",
    )
    data = await process_uid(record.uid, ev)
    if not data:
        logger.debug(f"[RoverReminder] uid={record.uid} API查询失败或CK失效，未发送邮件")
        return

    daily_info = data["daily_info"]
    stamina_value = daily_info.energyData.cur if daily_info.energyData else 0
    if stamina_value < threshold:
        logger.debug(
            f"[RoverReminder] uid={record.uid} API体力={stamina_value} 未达阈值={threshold}，不发送邮件"
        )
        return

    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        from ..mail.send import send_stamina_email
    except Exception as e:
        logger.warning(f"[RoverReminder] 邮件发送模块未就绪: {e}")
        return

    ok = False
    msg = ""
    try:
        logger.debug(
            f"[RoverReminder] 准备发送邮件 uid={record.uid} email={record.user_email} stamina={stamina_value} threshold={threshold}"
        )
        ok, msg = await send_stamina_email(
            record.user_email,
            record.uid,
            stamina_value,
            threshold,
            now_text,
            daily_info,
            data.get("account_info"),
            record.user_id,
            record.bot_id,
            record.bot_self_id or "",
        )
    except Exception as e:
        msg = str(e)
        logger.debug(f"[RoverReminder] 邮件发送异常 uid={record.uid} reason={msg}")

    new_fail_count = 0 if ok else (record.email_fail_count or 0) + 1
    success_time = now_ts if ok else None
    try:
        await WavesStaminaRecord.update_email_status(
            user_id=record.user_id,
            bot_id=record.bot_id,
            bot_self_id=record.bot_self_id or "",
            uid=record.uid,
            email_last_try_time=now_ts,
            email_send_success=ok,
            email_fail_count=new_fail_count,
            email_last_success_time=success_time,
        )
    except Exception:
        logger.exception("[RoverReminder] 更新邮件状态失败")

    if ok:
        record_success()
        logger.debug(f"[RoverReminder] uid={record.uid} 邮件发送成功")
        mail_logger.info(
            f"发送成功 uid={record.uid} user_id={record.user_id} email={record.user_email} stamina={stamina_value}"
        )
    else:
        record_fail()
        logger.debug(f"[RoverReminder] uid={record.uid} 邮件发送失败 reason={msg}")
        mail_logger.warning(
            f"发送失败 uid={record.uid} user_id={record.user_id} email={record.user_email} stamina={stamina_value} reason={msg}"
        )


@scheduler.scheduled_job("interval", minutes=6, id="roverreminder_check")
async def roverreminder_check_task():
    if _check_lock.locked():
        logger.debug("[RoverReminder] 定时检查跳过：已有任务运行中")
        return

    async with _check_lock:
        if not RoverReminderConfig.get_config("EnableStaminaPush").data:
            logger.debug("[RoverReminder] 定时检查跳过：体力推送未开启")
            return
        try:
            records = await WavesStaminaRecord.get_all_records()
        except Exception:
            logger.exception("[RoverReminder] 查询体力记录失败")
            return

        if not records:
            logger.debug("[RoverReminder] 定时检查结束：无体力记录")
            return

        threshold_default = RoverReminderConfig.get_config("StaminaPushThreshold").data
        now_ts = int(time.time())
        logger.debug(f"[RoverReminder] 开始定时检查，记录数={len(records)} 默认阈值={threshold_default}")

        for record in records:
            try:
                await _handle_record(record, threshold_default, now_ts)
            except Exception:
                logger.exception(f"[RoverReminder] 处理记录失败 uid={record.uid}")
