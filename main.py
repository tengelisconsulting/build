#!/usr/bin/env python3.8

import asyncio
from datetime import datetime
import json
import logging
import os
import pprint
from queue import Queue
import re
import subprocess
import threading
from typing import Optional
from types import SimpleNamespace

from aiohttp import web

from lib.build import BuildConf
from lib.build import do_build
import lib.data as data
from lib.env import ENV
from lib.mail import init_mail
from lib.sec import verify_git_hook_sha1


routes = web.RouteTableDef()
failure_q: Queue = Queue()
job_q: Queue = Queue()

LOG_FILE_DATE_FORMAT = "%Y-%m-%d__%H.%M"
GIT_HEAD_REF_REGEX = re.compile(
    r".*/([^/]*)")
NO_BUILD_BRANCH_NAME = "no_build"


class State(SimpleNamespace):
    handle_thread: Optional[threading.Thread] = None
    mail_thread: Optional[threading.Thread] = None
    req_id: int = 0


state = State()


def setup_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format=f"%(asctime)s.%(msecs)03d "
        "%(levelname)s %(module)s - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return


def handle_loop() -> None:
    while True:
        handler, build_conf = job_q.get()
        try:
            data.set_status(build_conf, "BUILDING")
            result = handler(build_conf)
            data.set_status(build_conf, result)
            if result == "FAILED":
                logging.error("build failure: %s", build_conf)
                failure_q.put_nowait(build_conf)
        except subprocess.CalledProcessError as e:
            data.set_status(build_conf, "FAILED")
            logging.exception("server handling job failed: {}".format(e))
            logging.error("subprocess output:\n%s\n%s", e.stdout, e.stderr)
            failure_q.put_nowait(build_conf)
        except Exception as e:
            data.set_status(build_conf, "FAILED")
            logging.exception("server handling job failed: {}".format(e))
            failure_q.put_nowait(build_conf)
    return


def check_handle_loop() -> None:
    def reset():
        logging.info("restarting handle thread")
        state.handle_thread = threading.Thread(
            target=handle_loop, daemon=True)
        state.handle_thread.start()
    if not state.handle_thread:
        reset()
        return
    if state.handle_thread and not state.handle_thread.is_alive():
        logging.exception("prev request handle died: {}".format(
            state.handle_thread))
        reset()
    return


@web.middleware
async def every_req(request, handler):
    state.req_id = state.req_id + 1
    check_handle_loop()
    return await handler(request)


@routes.post("/on-push")
async def on_push(req: web.Request):
    payload = await req.read()
    signature = req.headers.get("x-hub-signature")
    if not verify_git_hook_sha1(payload, signature):
        return web.Response(status=401, body="Bad signature")
    body = json.loads(payload)
    branch_match = re.search(GIT_HEAD_REF_REGEX, body["ref"])
    if branch_match:
        if branch_match.groups()[0] == NO_BUILD_BRANCH_NAME:
            logging.info("push was on branch %s, skipping build",
                         NO_BUILD_BRANCH_NAME)
            return web.Response(body="OK")
    rev = body["after"]
    proj_name = body["repository"]["name"]
    repo_url = body["repository"]["ssh_url"]
    time_s = datetime.now().strftime(LOG_FILE_DATE_FORMAT)
    log_dir = os.path.join(ENV.LOG_DIR, proj_name)
    if not os.path.exists(log_dir):
        subprocess.run(["mkdir", "-p", log_dir]).check_returncode()
    build_conf = BuildConf(
        build_dir=os.path.join(
            ENV.BUILD_DIR, f"{proj_name}_{state.req_id}"),
        log_file=os.path.join(log_dir, f"{rev}__{time_s}"),
        proj_name=proj_name,
        repo_url=repo_url,
        req_id=state.req_id,
        rev=rev,
    )
    data.set_status(build_conf, "PENDING")
    job_q.put_nowait((do_build, build_conf))
    return web.Response(body=json.dumps("OK"))


@routes.get("/status")
async def display_status(req: web.Request):
    res = pprint.pformat(
        json.dumps(data.get_status()))
    return web.Response(text=res)


async def init() -> web.Application:
    logging.info("build server startup")
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except Exception as e:
        logging.exception("failed to use uvloop: {}".format(e))
    if ENV.GMAIL_CREDS_F:
        state.mail_thread = threading.Thread(
            target=init_mail, args=[failure_q], daemon=True)
        state.mail_thread.start()
    if not os.path.exists(ENV.BUILD_DIR):
        subprocess.run(["mkdir", "-p", ENV.BUILD_DIR]).check_returncode()
    app = web.Application(middlewares=[every_req])
    app.add_routes(routes)
    return app


def main():
    setup_logging()
    logging.info("build server starting on port %s", ENV.PORT)
    web.run_app(init(), port=ENV.PORT)
    return


if __name__ == '__main__':
    main()
