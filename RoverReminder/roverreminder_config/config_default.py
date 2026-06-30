from typing import Dict

from gsuid_core.utils.plugins_config.models import GSC, GsBoolConfig, GsIntConfig

CONFIG_DEFAULT: Dict[str, GSC] = {
    "EnableStaminaPush": GsBoolConfig(
        "开启体力推送",
        "全局体力推送开关",
        False,
    ),
    "StaminaPushThreshold": GsIntConfig(
        "体力推送阈值",
        "达到该体力值将尝试推送邮件",
        230,
        240,
    ),
    "ActiveUserDays": GsIntConfig(
        "活跃账号认定天数",
        "在此天数内有使用记录的账号才进行推送",
        42,
        10000,
    ),
    "HideUid": GsBoolConfig(
        "隐藏uid",
        "开启后，推送邮件中显示的UID将以 前2位 + **** + 后2位 的形式显示",
        False,
    ),
}
