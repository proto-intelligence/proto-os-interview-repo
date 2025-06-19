from loguru import logger
from loguru._defaults import LOGURU_FORMAT
import sys
import logging
# local imports
from app.core.config import settings


class InterceptHandler(logging.Handler):
    """
    A logging handler that intercepts standard Python logging module records
    and forwards them to Loguru, enabling to use Loguru's advanced logging
    features while maintaining compatibility with existing logging infrastructure.

    Methods
    -------
    emit(record: logging.LogRecord) -> None
        Forwards the log record to Loguru, preserving the log level and exception information.

    References
    ----------
    Loguru documentation: https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """
    def emit(self, record: logging.LogRecord) -> None:
        # Omit logs that come from pytest execution
        if record.name.startswith("pytest") or "pytest" in record.pathname:
            return

        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.opt(depth=_get_log_depth(), exception=record.exc_info).log(
            level, record.getMessage()
        )


def _get_log_depth() -> int:
    """
    Find the correct depth in the call stack to identify the origin of a log message.

    Returns:
        int: The depth in the call stack where the actual logging call originated,
        skipping internal frames from the logging module.
    """
    frame = logging.currentframe()
    depth = 1
    while frame and frame.f_globals.get("__name__") == "logging":
        frame = frame.f_back
        depth += 1
    return depth


def configure_logging():
    """
    Set up application logging by:

    - Replacing the root logger's handlers with the above custom InterceptHandler
    to route standard logs to Loguru.
    - Configuring Loguru to log to stdout with the desired format and log level.
    - Optionally adding a file sink for logs if enabled in settings, and logging an error if this fails.
    """
    logging.getLogger().handlers = [InterceptHandler()]

    # set format for scripts
    logger.configure(
        handlers=[{
            "sink"  : sys.stdout,
            "level" : settings.LOGS_LEVEL,
            "format": LOGURU_FORMAT
        }]
    )

    try:
        if settings.ENABLE_LOGGING_FILE:
            logger.add(
                settings.LOGS_FILE_NAME,
                rotation  = settings.LOGS_FILE_ROTATION,
                backtrace = True,
                diagnose  = True,
                serialize = settings.LOGS_FILE_SERIALIZE
            )
    except Exception as e:
        logger.error(f"Failed to add log file sink: {e}")

# Enable detailed urllib3 logging
logging.getLogger("urllib3").setLevel(settings.LOGS_LEVEL)

configure_logging()
