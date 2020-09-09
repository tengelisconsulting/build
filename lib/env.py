import os
from typing import NamedTuple


class _ENV(NamedTuple):
    BUILD_DIR: str = os.environ["BUILD_DIR"]
    PORT: int = int(os.environ["PORT"])
    REPO_URL: str = os.environ["REPO_URL"]


ENV = _ENV()
