import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from .resource.RESOURCE_PATH import LOG_PATH


def get_mail_logger() -> logging.Logger:
    logger = logging.getLogger("RoverReminderMail")
    if logger.handlers:
        return logger

    log_file = Path(LOG_PATH) / "mail.log"
    handler = TimedRotatingFileHandler(
        log_file,
        when="D",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
