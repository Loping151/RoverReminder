import asyncio
import json
import smtplib
from email.header import Header
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any, Dict, Tuple

from ..utils.resource.RESOURCE_PATH import MAIN_PATH
from .template import build_stamina_html

CONFIG_PATH = MAIN_PATH / "mail" / "config.json"


def get_mail_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _build_message(sender: str, to_email: str, subject: str, html: str, sender_name: str = "") -> EmailMessage:
    sender_email = sender
    display_name = sender_name
    if display_name and sender_email:
        from_addr = formataddr((str(Header(display_name, "utf-8")), sender_email))
    else:
        from_addr = sender_email or display_name

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["Subject"] = str(Header(subject, "utf-8"))
    msg.set_content("您的体力已达到提醒阈值，请及时上线使用体力。")
    if html:
        msg.add_alternative(html, subtype="html")
    return msg


def _send_via_smtp(config: Dict[str, Any], to_email: str, subject: str, html: str) -> Tuple[bool, str]:
    host = config.get("host")
    port = int(config.get("port", 465))
    user = config.get("user")
    password = config.get("password")
    sender = config.get("sender") or user
    sender_name = config.get("sender_name", "")
    if sender and "@" not in sender and user:
        sender_name = sender
        sender = user
    use_ssl = bool(config.get("use_ssl", True))
    starttls = bool(config.get("starttls", False))

    if not host or not user or not password:
        return False, "邮件配置不完整"

    msg = _build_message(sender, to_email, subject, html, sender_name=sender_name)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=10) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                if starttls:
                    server.starttls()
                server.login(user, password)
                server.send_message(msg)
        return True, "ok"
    except Exception as e:
        return False, str(e)

def _send_via_qq(config: Dict[str, Any], to_email: str, subject: str, html: str) -> Tuple[bool, str]:
    """QQ邮箱发送：password 使用授权码"""
    qq_config = dict(config or {})
    qq_config.setdefault("host", "smtp.qq.com")
    qq_config.setdefault("port", 465)
    qq_config.setdefault("use_ssl", True)
    if not qq_config.get("password") and qq_config.get("auth_code"):
        qq_config["password"] = qq_config.get("auth_code")
    return _send_via_smtp(qq_config, to_email, subject, html)


async def send_stamina_email(
    to_email: str,
    uid: str,
    stamina: int,
    threshold: int,
    now_text: str,
    daily_info: Any = None,
    account_info: Any = None,
    user_id: str = "",
    bot_id: str = "",
    bot_self_id: str = "",
) -> Tuple[bool, str]:
    config = get_mail_config()
    provider = config.get("provider", "smtp")

    subject, html = await build_stamina_html(
        uid,
        stamina,
        threshold,
        now_text,
        daily_info,
        account_info,
        user_id,
        bot_id,
        bot_self_id,
    )

    if provider == "qq":
        cfg = config.get("qq", {})
        return await asyncio.to_thread(_send_via_qq, cfg, to_email, subject, html)

    cfg = config.get("smtp", {})
    return await asyncio.to_thread(_send_via_smtp, cfg, to_email, subject, html)
