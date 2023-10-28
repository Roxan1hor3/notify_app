import logging.config
from typing import Any


def configure_logging(log_level: str) -> dict[str, Any]:
    synthetic_format = (
        "SLog[%(levelname)s][%(asctime)s][%(process)d][%(thread)d][%(message)s]"
    )

    cfg = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"snt": {"format": synthetic_format}},
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "snt",
                "stream": "ext://sys.stdout",
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "snt",
                "stream": "ext://sys.stderr",
            },
        },
        "root": {
            "level": log_level,
            "handlers": [
                "stdout",
            ],
        },
        "loggers": {
            "gunicorn.error": {
                "level": log_level,
                "handlers": ["stderr"],
                "propagate": False,
            },
            "gunicorn.access": {
                "level": log_level,
                "handlers": ["stdout"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(cfg)
    return cfg
