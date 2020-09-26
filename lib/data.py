import logging
import shelve
from threading import Lock
import time
from typing import Literal
from typing import Union


from .apptypes import BuildConf
from .env import ENV

data_lock = Lock()

BuildStatus = Union[
    Literal["PENDING"],
    Literal["BUILDING"],
    Literal["FAILED"],
    Literal["SUCCESS"],
]


def get_build_key(build: BuildConf) -> str:
    return f"{build.rev}__{build.req_id}"


def trim_shelf(s: shelve.Shelf) -> None:
    key_count = len(s.keys())
    if key_count <= ENV.DATA_HIST:
        return
    updated = [(key, s[key]["updated"]) for key in s.keys()]
    oldest = sorted(updated, key=lambda x: x[1])
    for i in range(0, key_count - ENV.DATA_HIST):
        key = oldest[i][0]
        del s[key]
    return


def get_status():
    with data_lock:
        with shelve.open(ENV.DATA_FILE) as s:
            if not s:
                return {}
            return sorted(s.items(), key=lambda x: x[1]["updated"])


def set_status(build: BuildConf, status: BuildStatus):
    key = get_build_key(build)
    with data_lock:
        with shelve.open(ENV.DATA_FILE) as s:
            s[key] = {
                "status": status,
                "updated": time.time(),
            }
            trim_shelf(s)
    return
