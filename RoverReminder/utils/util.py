import random
import string

import httpx


async def get_public_ip(host: str = "127.127.127.127") -> str:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://event.kurobbs.com/event/ip", timeout=4)
            return r.text
    except Exception:
        pass

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.ipify.org/?format=json", timeout=4)
            return r.json()["ip"]
    except Exception:
        pass

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://httpbin.org/ip", timeout=4)
            return r.json()["origin"]
    except Exception:
        pass

    return host


def generate_random_string(length: int = 32) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choice(characters) for _ in range(length))


def hide_uid(uid, user_pref: str = "") -> str:
    """user_pref: 该 uid 对应 WavesUser.hide_uid_self_value, 由 caller 传入。

    "on" 强制隐藏 / "off" 强制不隐藏 / "" 跟随全局 HideUid。
    """
    from ..roverreminder_config.roverreminder_config import RoverReminderConfig

    uid_str = str(uid) if uid is not None else ""
    if user_pref == "off":
        return uid_str
    if user_pref != "on":
        if not RoverReminderConfig.get_config("HideUid").data:
            return uid_str
    if len(uid_str) < 2:
        return uid_str
    return uid_str[:2] + "*" * 4 + uid_str[-2:]


async def get_hide_uid_pref(uid: str, user_id: str, bot_id: str) -> str:
    """读 WavesUser.hide_uid_self_value, 没绑定就回空 (走全局 HideUid)。"""
    from .constants import WAVES_GAME_ID
    from .database.models import WavesUser

    try:
        user = await WavesUser.select_waves_user(
            uid, user_id, bot_id, game_id=WAVES_GAME_ID
        )
        return user.hide_uid_self_value if user else ""
    except Exception:
        return ""
