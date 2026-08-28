import logging
import logging.config


class RequestFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", "-")
        method = getattr(record, "method", "-")
        path = getattr(record, "path", "-")
        status_code = getattr(record, "status_code", "-")
        client_ip = getattr(record, "client_ip", "-")
        duration_ms = getattr(record, "duration_ms", "-")

        return (
            f"{self.formatTime(record)} | "
            f"{record.levelname:<8} | "
            f"request_id={request_id} | "
            f"{method} {path} | "
            f"status={status_code} | "
            f"client={client_ip} | "
            f"duration={duration_ms}ms | "
            f"{record.getMessage()}"
        )


def setup_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "app.core.logging.RequestFormatter",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "app": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
            "root": {
                "handlers": ["console"],
                "level": "INFO",
            },
        }
    )