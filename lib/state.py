import threading
from types import SimpleNamespace


class State(SimpleNamespace):
    build_path: str = None
    handle_thread: threading.Thread = None
    req_id: int = 0


state = State()
