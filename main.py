#!/usr/bin/env python3

import asyncio
from datetime import datetime
import json
import logging
import os
from queue import Queue
import subprocess
import threading

from aiohttp import web

from lib.apptypes import BuildConf
import lib.build as build
import lib.data as data
from lib.env import ENV
from lib.state import state


routes = web.RouteTableDef()
job_q: Queue = Queue()

LOG_FILE_DATE_FORMAT = "%Y-%m-%d__%H.%M"


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
        handler, build = job_q.get()
        try:
            data.set_status(build, "BUILDING")
            handler(build)
        except Exception as e:
            data.set_status(build, "FAILED")
            logging.exception("server handling job failed: {}".format(e))
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
    # validate...
    rev = "50c6bc6"
    time_s = datetime.now().strftime(LOG_FILE_DATE_FORMAT)
    build_conf = BuildConf(
        build_dir=os.path.join(
            state.build_path, f"build_{state.req_id}"),
        log_file=os.path.join(
            ENV.LOG_DIR, f"{rev}__{time_s}"
        ),
        repo_url=ENV.REPO_URL,
        req_id=state.req_id,
        rev=rev,
    )
    data.set_status(build_conf, "PENDING")
    job_q.put_nowait((build.do_build, build_conf))
    return web.Response(body=json.dumps("OK"))


@routes.get("/status")
async def display_status(req: web.Request):
    res = json.dumps(data.get_status())
    return web.Response(body=res)


async def init() -> web.Application:
    logging.info("build server startup for repo url %s", ENV.REPO_URL)
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except Exception as e:
        logging.exception("failed to use uvloop: {}".format(e))
    state.build_path = os.path.abspath(ENV.BUILD_DIR)
    if not os.path.exists(state.build_path):
        subprocess.check_call(["mkdir", "-p", state.build_path])
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
