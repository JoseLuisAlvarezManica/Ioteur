import logging
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

SERVICE_NAME = "telemetry-service"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        request_id = request_id_var.get()
        event = getattr(record, "event", record.name)
        level = record.levelname
        message = record.getMessage()

        line = f"{timestamp} | {level:<8} | {SERVICE_NAME} | {event} | [{request_id}] {message}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        elif getattr(record, "error", None):
            line += f" | error={record.error}"

        return line
