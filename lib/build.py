import logging
import os
import pprint
import subprocess

from .apptypes import BuildConf
from .data import set_status


class State:
    def __init__(self, build: BuildConf):
        self.build = build
        return

    def log(self, text) -> None:
        if type(text) == bytes:
            text = text.decode("utf-8")
        with open(self.build.log_file, "a") as f:
            f.write((text or "") + "\n")

    def run(self, cmd, **kwargs):
        with open(self.build.log_file, "ab", buffering=0) as f:
            args = {**kwargs, **{
                "stdout": f,
                "stderr": f,
                "env": os.environ,
            }}
            res = subprocess.run(cmd, **args)
            return res


HOOKS = [
    "pre_build",
    "build",
    "test",
    "push",
    "post_push",
]


def do_build(build: BuildConf) -> None:
    logging.info("begin build %s", pprint.pformat(build))
    state = State(build=build)
    setup(state, build)
    state.log("BEGIN {}".format(build))
    for hook in HOOKS:
        success = run_hook(state, build, hook)
        if not success:
            state.log("\n\nBUILD IS NOT SUCCESS - ABORTING")
            set_status(build, "FAILED")
            return finish_build(state, build)
    set_status(build, "SUCCESS")
    return finish_build(state, build)


def finish_build(state: State, build: BuildConf) -> None:
    state.run(["rm", "-rf", build.build_dir]) \
         .check_returncode()
    state.log("DONE {}".format(build))
    logging.info("done build %s", pprint.pformat(build))
    return


# util
def setup(state: State, build: BuildConf):
    if os.path.exists(build.build_dir):
        state.run(["rm", "-rf", build.build_dir]) \
            .check_returncode()
    state.run(["git", "clone", build.repo_url, build.build_dir]) \
        .check_returncode()
    state.run(["git", "fetch", "--all"], cwd=build.build_dir) \
         .check_returncode()
    state.run(["git", "checkout", build.rev], cwd=build.build_dir) \
         .check_returncode()
    return


# hooks
def on_hook_fail(build: BuildConf, hook: str):
    return


def run_hook(state: State, build: BuildConf, hook: str) -> bool:
    "returns success"
    hook_path = os.path.join(build.build_dir, "hooks", hook)
    if os.path.exists(hook_path):
        state.log(f"\n--------RUNNING HOOK {hook}--------")
        res = state.run([f"hooks/{hook}"], cwd=build.build_dir)
        if res.returncode != 0:
            state.log(f"""
------------------------------------------------------------------------------
BUILD HOOK {hook} FAILED""")
            return False
    return True
