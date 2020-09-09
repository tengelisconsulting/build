#!/usr/bin/env python3

import asyncio
import json
import logging
import os
from queue import Queue
import subprocess
import threading

from aiohttp import web

from lib.apptypes import BuildConf
import lib.build as build
from lib.env import ENV
from lib.state import state


routes = web.RouteTableDef()
job_q: Queue = Queue()


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
        job = job_q.get()
        job()
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
    build_conf = BuildConf(
        req_id=state.req_id,
        rev=None,
    )
    job_q.put_nowait(lambda: build.do_build(build_conf))
    return web.Response(body=json.dumps("OK"))


async def init() -> web.Application:
    logging.info("build server startup for repo url %s", ENV.REPO_URL)
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except Exception as e:
        logging.exception("failed to use uvloop: {}".format(e))
    state.build_path = os.path.abspath(ENV.BUILD_DIR)
    if not os.path.exists(state.build_path):
        subprocess.check_call(["mkdir", state.build_path])
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
