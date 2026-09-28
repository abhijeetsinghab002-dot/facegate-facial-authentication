import time
from collections import defaultdict, deque


class LoginLimiter:
    def __init__(self, max_attempts=5, window_seconds=300, lock_seconds=60, clock=time.monotonic):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lock_seconds = lock_seconds
        self.clock = clock
        self.attempts = defaultdict(deque)
        self.locked_until = {}

    def _prune(self, key, now):
        cutoff = now - self.window_seconds
        while self.attempts[key] and self.attempts[key][0] <= cutoff:
            self.attempts[key].popleft()

    def check(self, key):
        now = self.clock()
        until = self.locked_until.get(key, 0)
        if until > now:
            return False, max(1, int(until - now + 0.999))
        self.locked_until.pop(key, None)
        self._prune(key, now)
        return True, 0

    def fail(self, key):
        now = self.clock()
        self._prune(key, now)
        self.attempts[key].append(now)
        if len(self.attempts[key]) >= self.max_attempts:
            self.locked_until[key] = now + self.lock_seconds
            self.attempts[key].clear()
            return self.lock_seconds
        return 0

    def success(self, key):
        self.attempts.pop(key, None)
        self.locked_until.pop(key, None)
