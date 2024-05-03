import time


def get_next_tick(tick_interval: int):
    """Given a tick interval (in seconds), returns a function that gives the time to sleep until next tick based on the last tick timestamp."""

    def _next_tick(last_tick: float):
        time_since = time.time() - last_tick
        return tick_interval - time_since

    return _next_tick
