from collections import defaultdict, deque
from time import time

from fastapi import HTTPException


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self.windows: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str, limit: int, period_seconds: int) -> None:
        now = time()
        window = self.windows[key]
        while window and now - window[0] > period_seconds:
            window.popleft()
        if len(window) >= limit:
            raise HTTPException(status_code=429, detail="Too many requests")
        window.append(now)


rate_limiter = SlidingWindowLimiter()
