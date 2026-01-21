"""init"""

from gsuid_core.sv import Plugins
from gsuid_core.logger import logger

Plugins(name="RoverReminder", force_prefix=["ww"], allow_empty_prefix=False)

logger.info("[RoverReminder] 初始化插件...")

# 注册指令与定时任务
from . import roverreminder_config as _  # noqa: F401
from . import roverreminder_push as _  # noqa: F401
from . import roverreminder_status as _  # noqa: F401

logger.info("[RoverReminder] 插件初始化完成")
