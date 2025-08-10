"""
Contains custom logger and logg formatter for dwcom to log server events.
"""

import logging
from logging.handlers import RotatingFileHandler
import json
import os
from time import localtime, gmtime

class jsonFormatter(logging.Formatter):
    def __init__(self, useTwelveHour = False, useUtc =False):
        if useTwelveHour:
            datefmt = "%Y-%m-%d %I:%M:%S %p"
        else:
            datefmt = "%Y-%m-%d %H:%M:%S"
        self.converter = gmtime if useUtc else localtime
        super().__init__(datefmt = datefmt)

    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(log_record, ensure_ascii=False)


_loggers = {}

def getServerLogger(serverId: str, logDir: str = "./logs/servers", maxBytes: int = 4 * 1024 * 1024, backupCount: int = 5, useTwelveHourTime: bool = False, useUtcTime = False) -> logging.Logger:
    """
    Get or create a per-server logger.
    Each server's log file will be named logs/servers/<serverId>.json
    """
    if serverId in _loggers:
        return _loggers[serverId]

    logDir = os.path.join(logDir, serverId)
    os.makedirs(logDir, exist_ok=True)
    logPath = os.path.join(logDir, f"{serverId}.json")

    logger = logging.getLogger(f"ttcom.server.{serverId}")
    logger.setLevel(logging.INFO)

    if not logger.hasHandlers():
        handler = RotatingFileHandler(logPath, maxBytes=maxBytes, backupCount=backupCount, encoding="utf-8")
        handler.setFormatter(jsonFormatter(useTwelveHour = useTwelveHourTime, useUtc = useUtcTime))
        logger.addHandler(handler)
        logger.propagate = False  # We do this because we do not want to log to root, events will get printed twice if we don't do this.

    _loggers[serverId] = logger
    return logger