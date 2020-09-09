import logging
import subprocess

from .apptypes import BuildConf


def do_build(build: BuildConf):
    logging.info("begin build %s", build)
    res = subprocess.run(["sleep", "2"])
    success = res.returncode == 0
    logging.info("done build %s", build)
    return
