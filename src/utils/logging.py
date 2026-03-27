import logging
import os
import sys
from html import escape

from loguru import logger

from src.core.settings import Application as app
LEVEL_BG = {
    "TRACE": "#6f42c1",
    "DEBUG": "#0ea5e9",
    "INFO": "#2563eb",
    "SUCCESS": "#15803d",
    "WARNING": "#d97706",
    "ERROR": "#dc2626",
    "CRITICAL": "#7f1d1d",
    }
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SQLALCHEMY_LOG_LEVEL = os.getenv(
    "SQLALCHEMY_LOG_LEVEL",
    "INFO" if app.debug_mode else "WARNING",
).upper()
LOG_ENQUEUE = os.getenv("LOG_ENQUEUE", "false").lower() in ("true", "1", "yes")
_configured = False


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.bind(module=record.name).opt(exception=record.exc_info).log(level, record.getMessage())


def _format(record):
    bg = LEVEL_BG.get(record["level"].name, "#475569")
    module = record["extra"].get("module") or record["name"]
    return (
        f"<bold><black><bg #aab4be> {{time:HH:mm:ss.SSS}} </bg #aab4be></black></bold> "
        f"<level><bold><white><bg {bg}> {{level:^8}} </bg {bg}></white></bold></level>"
        "<dim><fg #6b7280> • </fg #6b7280></dim>"
        f"<bold><fg #7dd3fc>{module}</fg #7dd3fc></bold>"
        "<dim><fg #6b7280> • </fg #6b7280></dim>"
        "<level><bold>{message}</bold></level>\n"
    )


def color(text: object, tc: str | None = None, bc: str | None = None) -> str:
    content = escape(str(text))
    if bc:
        content = f" {content} "
    opening_tags: list[str] = []
    closing_tags: list[str] = []

    if bc:
        opening_tags.append(f"<bg {bc}>")
        closing_tags.insert(0, f"</bg {bc}>")

    if tc:
        opening_tags.append(f"<fg {tc}>")
        closing_tags.insert(0, f"</fg {tc}>")
    elif bc:
        opening_tags.append("<fg #ffffff>")
        closing_tags.insert(0, "</fg #ffffff>")

    return f"{''.join(opening_tags)}{content}{''.join(closing_tags)}"


def bg_color(text: object, color: str, foreground: str = "#ffffff") -> str:
    return color(text, tc=foreground, bc=color)

def configure_logging(level: str = LOG_LEVEL) -> None:
    global _configured
    if _configured:
        return
    logging.root.handlers = []
    logging.root.setLevel(level)
    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        enqueue=LOG_ENQUEUE,
        backtrace=True,
        diagnose=False,
        format=_format,
    )
    handler = InterceptHandler()
    for name in (
        "",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "watchfiles",
        "watchfiles.main",
        "fastapi",
        "asyncio",
        "slowapi",
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "sqlalchemy.pool",
    ):
        log = logging.getLogger(name)
        log.handlers = [handler]
        if name.startswith("sqlalchemy"):
            log.setLevel(SQLALCHEMY_LOG_LEVEL)
        else:
            log.setLevel(level)
        log.propagate = False
    _configured = True

def get_logger(name: str = app.title):
    configure_logging()
    return logger.bind(module=name)
