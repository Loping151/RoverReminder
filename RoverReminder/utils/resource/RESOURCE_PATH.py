import sys

from gsuid_core.data_store import get_res_path
from pathlib import Path
from shutil import copyfile

MAIN_PATH = get_res_path() / "RoverReminder"
sys.path.append(str(MAIN_PATH))

# 配置文件
CONFIG_PATH = MAIN_PATH / "config.json"

# 邮件日志目录
LOG_PATH = MAIN_PATH / "log"

# 状态文件
STATUS_PATH = MAIN_PATH / "status.json"

# 邮件配置
MAIL_CONFIG_PATH = MAIN_PATH / "mail_config.json"

# 邮件模板目录
MAIL_PATH = MAIN_PATH / "mail"
MAIL_CONFIG_TARGET = MAIL_PATH / "config.json"
MAIL_TEMPLATE_TARGET = MAIL_PATH / "template.html"

PLUGIN_MAIL_PATH = Path(__file__).resolve().parents[2] / "mail"
MAIL_CONFIG_TEMPLATE = PLUGIN_MAIL_PATH / "config.json.template"
MAIL_TEMPLATE_EXAMPLE = PLUGIN_MAIL_PATH / "template.html.example"


def init_dir():
    for i in [MAIN_PATH, LOG_PATH, MAIL_PATH]:
        i.mkdir(parents=True, exist_ok=True)

    if not MAIL_CONFIG_TARGET.exists() and MAIL_CONFIG_TEMPLATE.exists():
        copyfile(MAIL_CONFIG_TEMPLATE, MAIL_CONFIG_TARGET)

    if not MAIL_TEMPLATE_TARGET.exists() and MAIL_TEMPLATE_EXAMPLE.exists():
        copyfile(MAIL_TEMPLATE_EXAMPLE, MAIL_TEMPLATE_TARGET)


init_dir()
