from ..utils.mail_logger import get_mail_logger

mail_logger = get_mail_logger()

try:
    from . import template  # noqa: F401
except Exception as e:
    mail_logger.warning(f"[RoverReminderMail] 模板加载失败: {e}")

try:
    from . import send  # noqa: F401
except Exception as e:
    mail_logger.warning(f"[RoverReminderMail] 发送模块加载失败: {e}")
