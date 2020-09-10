import os
from typing import NamedTuple


class _ENV(NamedTuple):
    BUILD_DIR: str = os.environ["BUILD_DIR"]
    DATA_FILE: str = os.environ["DATA_FILE"]
    DATA_HIST: int = int(os.environ.get("DATA_HIST", 100))
    LOG_DIR: str = os.environ["LOG_DIR"]
    PORT: int = int(os.environ["PORT"])
    REPO_URL: str = os.environ["REPO_URL"]


ENV = _ENV()
