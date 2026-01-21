import re

from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.sv import SV, get_plugin_available_prefix

from ..utils.database.models import WavesBind, WavesStaminaRecord
from ..utils.api.requests import waves_api
from .roverreminder_config import RoverReminderConfig

sv_rover_reminder = SV("RoverReminder配置")

PREFIX = get_plugin_available_prefix("RoverReminder")


@sv_rover_reminder.on_prefix(("开启", "关闭"))
async def switch_push(bot: Bot, ev: Event):
    if ev.text not in ("推送", "体力推送"):
        return
    at_sender = True if ev.group_id else False
    if not RoverReminderConfig.get_config("EnableStaminaPush").data:
        msg = "体力推送功能未开启，请先在配置中启用"
        return await bot.send((" " if at_sender else "") + msg, at_sender)
    uid = await WavesBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        msg = f"您还未绑定鸣潮特征码, 请使用【{PREFIX}绑定uid】完成绑定！"
        return await bot.send((" " if at_sender else "") + msg, at_sender)

    ck = await waves_api.get_self_waves_ck(uid, ev.user_id, ev.bot_id)
    try:
        await WavesStaminaRecord.update_ck_valid(
            user_id=ev.user_id,
            bot_id=ev.bot_id,
            bot_self_id=ev.bot_self_id or "",
            uid=uid,
            is_ck_valid=bool(ck),
        )
    except Exception:
        logger.exception("[RoverReminder] 更新CK有效状态失败")
    if not ck:
        msg = f"uid {uid} 登录状态无效！无法设置推送开关"
        return await bot.send((" " if at_sender else "") + msg, at_sender)

    logger.info(f"[{ev.user_id}]尝试[{ev.command[0:2]}]了[{ev.text}]功能")

    enable = "开启" in ev.command
    record = await WavesStaminaRecord.get_record(
        user_id=ev.user_id,
        bot_id=ev.bot_id,
        bot_self_id=ev.bot_self_id or "",
        uid=uid,
    )
    auto_email_msg = ""
    if enable and (not record or not record.user_email):
        if ev.user_id.isdigit():
            auto_email = f"{ev.user_id}@qq.com"
            await WavesStaminaRecord.upsert_user_settings(
                user_id=ev.user_id,
                bot_id=ev.bot_id,
                bot_self_id=ev.bot_self_id or "",
                uid=uid,
                user_email=auto_email,
                email_fail_count=0,
            )
            auto_email_msg = f"\n已设置默认邮箱：{auto_email}"
        else:
            msg = f"uid {uid} 未设置邮箱，请先使用【{PREFIX}推送邮箱 邮箱】设置邮箱"
            return await bot.send((" " if at_sender else "") + msg, at_sender)

    if enable:
        await WavesStaminaRecord.upsert_user_settings(
            user_id=ev.user_id,
            bot_id=ev.bot_id,
            bot_self_id=ev.bot_self_id or "",
            uid=uid,
            stamina_push_switch="on",
        )
    else:
        await WavesStaminaRecord.upsert_user_settings(
            user_id=ev.user_id,
            bot_id=ev.bot_id,
            bot_self_id=ev.bot_self_id or "",
            uid=uid,
            stamina_push_switch="off",
        )

    msg = f"uid {uid} 已开启体力推送！{auto_email_msg}" if enable else f"uid {uid} 已关闭体力推送！"
    await bot.send((" " if at_sender else "") + msg, at_sender)


@sv_rover_reminder.on_prefix(("推送邮箱","体力推送邮箱",))
async def set_push_email(bot: Bot, ev: Event):
    at_sender = True if ev.group_id else False
    email = ev.text.strip()
    if not email:
        msg = f"请输入邮箱，例如【{PREFIX}推送邮箱 123456789@qq.com】"
        return await bot.send((" " if at_sender else "") + msg, at_sender)
    if not re.match(r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\\.[A-Za-z0-9-.]+$", email):
        msg = "邮箱格式不正确，请检查后重试"
        return await bot.send((" " if at_sender else "") + msg, at_sender)

    uid = await WavesBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        msg = f"您还未绑定鸣潮特征码, 请使用【{PREFIX}绑定uid】完成绑定！"
        return await bot.send((" " if at_sender else "") + msg, at_sender)

    ck = await waves_api.get_self_waves_ck(uid, ev.user_id, ev.bot_id)
    if not ck:
        msg = f"uid {uid} 登录状态无效！无法查询！"
        return await bot.send((" " if at_sender else "") + msg, at_sender)

    try:
        await WavesStaminaRecord.upsert_user_settings(
            user_id=ev.user_id,
            bot_id=ev.bot_id,
            bot_self_id=ev.bot_self_id or "",
            uid=uid,
            user_email=email,
            email_fail_count=0,
        )
    except Exception:
        logger.exception("[RoverReminder] 设置邮箱失败")
        msg = f"uid {uid} 邮箱设置失败，请稍后重试"
        return await bot.send((" " if at_sender else "") + msg, at_sender)

    msg = f"uid {uid} 邮箱设置成功"
    return await bot.send((" " if at_sender else "") + msg, at_sender)


@sv_rover_reminder.on_prefix(("推送阈值","体力阈值","体力推送阈值",))
async def set_push_threshold(bot: Bot, ev: Event):
    at_sender = True if ev.group_id else False
    raw_value = ev.text.strip()
    if not raw_value.isdigit():
        msg = f"请输入正确的体力阈值，例如【{PREFIX}推送阈值 180】"
        return await bot.send((" " if at_sender else "") + msg, at_sender)

    value = int(raw_value)
    if value < 120 or value > 240:
        msg = "体力阈值范围为120~240"
        return await bot.send((" " if at_sender else "") + msg, at_sender)

    uid = await WavesBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        msg = f"您还未绑定鸣潮特征码, 请使用【{PREFIX}绑定uid】完成绑定！"
        return await bot.send((" " if at_sender else "") + msg, at_sender)

    ck = await waves_api.get_self_waves_ck(uid, ev.user_id, ev.bot_id)
    if not ck:
        msg = f"uid {uid} 登录状态无效，请重新登录后再设置阈值"
        return await bot.send((" " if at_sender else "") + msg, at_sender)

    await WavesStaminaRecord.upsert_user_settings(
        user_id=ev.user_id,
        bot_id=ev.bot_id,
        bot_self_id=ev.bot_self_id or "",
        uid=uid,
        stamina_threshold=value,
    )
    msg = f"uid {uid} 体力阈值已设置为 {value}"
    return await bot.send((" " if at_sender else "") + msg, at_sender)
