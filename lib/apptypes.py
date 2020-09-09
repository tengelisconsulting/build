from typing import NamedTuple
from typing import Optional


class BuildConf(NamedTuple):
    req_id: int
    rev: Optional[str] = None
