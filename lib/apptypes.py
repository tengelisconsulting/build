from typing import NamedTuple
from typing import Optional


class BuildConf(NamedTuple):
    build_dir: str
    log_file: str
    repo_url: str
    req_id: int
    rev: str
