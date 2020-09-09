import logging
import os
import subprocess
from types import SimpleNamespace

from .apptypes import BuildConf


class State:
    _log: str = ""

    def log(self, text) -> None:
        if type(text) == bytes:
            text = text.decode("utf-8")
        self._log = self._log + (text or "") + "\n"

    def get_log(self) -> str:
        return self._log


HOOKS = [
    "pre_build",
    "build",
    "test",
    "push",
    "post_push",
]


def do_build(build: BuildConf) -> None:
    logging.info("begin build %s", build)
    state = State()
    setup(build)
    state.log("BEGIN {}".format(build))
    for hook in HOOKS:
        success = run_hook(state, build, hook)
        if not success:
            state.log("\n\nBUILD IS NOT SUCCESS - ABORTING")
            return finish_build(state, build)
    return finish_build(state, build)


def finish_build(state: State, build: BuildConf) -> None:
    tear_down(build)
    state.log("DONE {}".format(build))
    with open(build.log_file, "w") as f:
        f.write(state.get_log())
    logging.info("done build %s", build)
    return


# util
def setup(build: BuildConf):
    if os.path.exists(build.build_dir):
        subprocess.run(["rm", "-rf", build.build_dir])
    subprocess.run(["git", "clone", build.repo_url, build.build_dir]) \
        .check_returncode()
    subprocess.run(["git", "fetch", "--all"], cwd=build.build_dir) \
              .check_returncode()
    subprocess.run(["git", "checkout", build.rev], cwd=build.build_dir) \
              .check_returncode()
    return


def tear_down(build: BuildConf):
    subprocess.run(["rm", "-rf", build.build_dir]) \
        .check_returncode()
    return


# hooks
def on_hook_fail(build: BuildConf, hook: str):
    return


def run_hook(state: State, build: BuildConf, hook: str) -> bool:
    "returns success"
    hook_path = os.path.join(build.build_dir, "hooks", hook)
    logging.info("looking at hook path %s", hook_path)
    if os.path.exists(hook_path):
        res = subprocess.run([f"hooks/{hook}"], cwd=build.build_dir)
        state.log("\n--------RUNNING HOOK {hook}--------")
        state.log(res.stdout)
        if res.returncode != 0:
            state.log("""
------------------------------------------------------------------------------
BUILD HOOK FAILED""")
            state.log(res.stderr)
            return False
    return True
