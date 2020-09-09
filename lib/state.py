import threading
from types import SimpleNamespace


# anything in a child thread shouldn't touch this
# instead, use an argument
class State(SimpleNamespace):
    build_path: str = None
    handle_thread: threading.Thread = None
    req_id: int = 0


state = State()
