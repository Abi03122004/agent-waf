import time
from contextlib import contextmanager
from typing import Generator

class Timer:
    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    @property
    def elapsed_ms(self) -> float:
        duration = self.end_time - self.start_time
        return round(duration * 1000.0, 2)

@contextmanager
def execution_timer() -> Generator[Timer, None, None]:
    t = Timer()
    t.start_time = time.perf_counter()
    try:
        yield t
    finally:
        t.end_time = time.perf_counter()
