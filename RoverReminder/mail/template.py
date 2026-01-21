import base64
import io
from pathlib import Path
from typing import Any, Optional, Tuple

from gsuid_core.models import Event

from ..utils.resource.RESOURCE_PATH import MAIN_PATH

TEMPLATE_PATH = MAIN_PATH / "mail" / "template.html"


def _try_import_wwuid_draw():
    try:
        from gsuid_core.plugins.XutheringWavesUID.XutheringWavesUID.wutheringwaves_stamina.draw_waves_stamina import (
            _draw_stamina_img,
        )
        return _draw_stamina_img
    except Exception:
        return None


async def _render_xwuid_image(
    daily_info: Any,
    account_info: Any,
    user_id: str,
    bot_id: str,
    bot_self_id: str,
) -> Optional[str]:
    draw_func = _try_import_wwuid_draw()
    if not draw_func or daily_info is None or account_info is None:
        return None

    ev = Event(
        user_id=user_id or "",
        bot_id=bot_id or "roverreminder",
        bot_self_id=bot_self_id or "",
        sender={},
    )
    try:
        img = await draw_func(ev, {"daily_info": daily_info, "account_info": account_info})
        buff = io.BytesIO()
        img.save(buff, format="PNG")
        return base64.b64encode(buff.getvalue()).decode("ascii")
    except Exception:
        return None


async def build_stamina_html(
    uid: str,
    stamina: int,
    threshold: int,
    now_text: str,
    daily_info: Any = None,
    account_info: Any = None,
    user_id: str = "",
    bot_id: str = "",
    bot_self_id: str = "",
) -> Tuple[str, str]:
    subject = "鸣潮体力推送"
    template = ""
    if TEMPLATE_PATH.exists():
        try:
            template = TEMPLATE_PATH.read_text(encoding="utf-8")
        except Exception:
            template = ""

    if not template:
        template = (
            "<div style=\"font-family:Arial,Helvetica,sans-serif;background:#0f1222;padding:24px;color:#eaeaea\">"
            "<div style=\"max-width:640px;margin:0 auto;background:#161a2f;border-radius:16px;padding:24px\">"
            "<h2 style=\"margin:0 0 12px 0;color:#f6d15e\">鸣潮体力推送</h2>"
            "<p style=\"margin:0 0 8px 0\">漂泊者，您的体力已达到阈值。</p>"
            "<ul style=\"list-style:none;padding:0;margin:12px 0;line-height:1.8\">"
            "<li>UID：{{uid}}</li>"
            "<li>当前体力：{{stamina}}</li>"
            "<li>阈值：{{threshold}}</li>"
            "<li>时间：{{time}}</li>"
            "</ul>"
            "<div style=\"margin-top:12px\">"
            "<img src=\"data:image/png;base64,{{stamina_image}}\" alt=\"stamina\" style=\"width:100%;border-radius:12px\"/>"
            "</div>"
            "<p style=\"margin-top:16px;color:#9aa3c1\">请及时上线使用体力。</p>"
            "</div>"
            "</div>"
        )

    html = (
        template.replace("{{uid}}", str(uid))
        .replace("{{user_id}}", str(user_id))
        .replace("{{bot_id}}", str(bot_id))
        .replace("{{bot_self_id}}", str(bot_self_id))
        .replace("{{stamina}}", str(stamina))
        .replace("{{threshold}}", str(threshold))
        .replace("{{time}}", str(now_text))
    )

    stamina_image = await _render_xwuid_image(
        daily_info,
        account_info,
        user_id,
        bot_id,
        bot_self_id,
    )
    if stamina_image:
        html = html.replace("{{stamina_image}}", stamina_image)
    else:
        html = html.replace("{{stamina_image}}", "")
        html = html.replace('src="data:image/png;base64,"', 'src=""')
    return subject, html


try:
    from .custom_template import build_stamina_html as _custom_build_stamina_html

    build_stamina_html = _custom_build_stamina_html  # type: ignore[assignment]
except Exception:
    pass
