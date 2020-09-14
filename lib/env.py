import os
from typing import NamedTuple
from typing import Optional


class _ENV(NamedTuple):
    BUILD_DIR: str = os.environ["BUILD_DIR"]
    BUILD_FAILURE_SUBSCRIBERS: str = os.environ.get(
        "BUILD_FAILURE_SUBSCRIBERS", "")
    DATA_FILE: str = os.environ["DATA_FILE"]
    DATA_HIST: int = int(os.environ.get("DATA_HIST", 100))
    GIT_SECRET: bytes = os.environ["GIT_SECRET"].encode("utf-8")
    GMAIL_CREDS_F: Optional[str] = os.environ.get("GMAIL_CREDS_F", None)
    GMAIL_SEND_ADDR: Optional[str] = os.environ.get("GMAIL_SEND_ADDR", None)
    LOG_DIR: str = os.environ["LOG_DIR"]
    PORT: int = int(os.environ["PORT"])


ENV = _ENV()
