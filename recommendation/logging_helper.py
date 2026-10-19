import datetime
from flask import request
from google.cloud import logging as cloud_logging

SERVICE_NAME = "recommendation"

_client = None
_cloud_logger = None


def _get_cloud_logger():
    global _client, _cloud_logger
    if _cloud_logger is None:
        _client = cloud_logging.Client()
        _cloud_logger = _client.logger(SERVICE_NAME)
    return _cloud_logger


def log_event(logger, message):
    corr_id = request.headers.get("Correlation-Id", "none")
    timestamp = datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")
    formatted = f"[{timestamp}, {corr_id}, {SERVICE_NAME}]: {message}"

    logger.info(formatted)

    try:
        cloud_logger = _get_cloud_logger()
        cloud_logger.log_struct({
            "message": message,
            "correlation_id": corr_id,
            "service": SERVICE_NAME,
            "timestamp": timestamp,
        })
    except Exception as e:
        logger.warning(f"Cloud logging failed: {e}")

    return formatted