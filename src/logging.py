import json
import logging
from datetime import datetime, timezone

from .config import settings


class JsonFormatter(logging.Formatter):
  def format(self, record: logging.LogRecord) -> str:
    payload = {
      "timestamp": datetime.now(timezone.utc).isoformat(),
      "level": record.levelname,
      "logger": record.name,
      "message": record.getMessage(),
    }
    if record.exc_info:
      payload["exception"] = self.formatException(record.exc_info)
    if hasattr(record, "request_id"):
      payload["request_id"] = record.request_id
    return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
  root_logger = logging.getLogger()
  if root_logger.handlers:
    return

  handler = logging.StreamHandler()
  handler.setFormatter(JsonFormatter())

  root_logger.setLevel(settings.log_level.upper())
  root_logger.addHandler(handler)

  for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logger = logging.getLogger(logger_name)
    logger.handlers.clear()
    logger.propagate = True