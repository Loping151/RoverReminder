from ..utils.mail_logger import get_mail_logger

mail_logger = get_mail_logger()

try:
    from . import template  # noqa: F401
except Exception as e:
    mail_logger.warning(f"[体力推送·邮件] 模板加载失败: {e}")

try:
    from . import send  # noqa: F401
except Exception as e:
    mail_logger.warning(f"[体力推送·邮件] 发送模块加载失败: {e}")
