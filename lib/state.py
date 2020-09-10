import threading
from typing import Optional
from types import SimpleNamespace


# anything in a child thread shouldn't touch this
# instead, use an argument
class State(SimpleNamespace):
    handle_thread: Optional[threading.Thread] = None
    req_id: int = 0


state = State()
