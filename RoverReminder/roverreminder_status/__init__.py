from gsuid_core.status.plugin_status import register_status

from ..utils.image import get_ICON
from ..utils.status_store import get_today_counts, get_yesterday_counts


async def get_today_success():
    return get_today_counts().get("success", 0)


async def get_today_fail():
    return get_today_counts().get("fail", 0)


async def get_yesterday_total():
    data = get_yesterday_counts()
    return data.get("success", 0) + data.get("fail", 0)


register_status(
    get_ICON(),
    "RoverReminder",
    {
        "今日发送成功": get_today_success,
        "今日发送失败": get_today_fail,
        "昨日发送": get_yesterday_total,
    },
)
