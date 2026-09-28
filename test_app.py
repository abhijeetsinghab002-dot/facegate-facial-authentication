import unittest

from rate_limit import LoginLimiter


class Clock:
    def __init__(self): self.value = 0
    def __call__(self): return self.value


class LimiterTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.limiter = LoginLimiter(3, 10, 20, self.clock)

    def test_initially_allowed(self):
        self.assertEqual(self.limiter.check('x'), (True, 0))

    def test_locks_after_limit(self):
        self.limiter.fail('x'); self.limiter.fail('x'); self.limiter.fail('x')
        self.assertFalse(self.limiter.check('x')[0])

    def test_unlocks_after_delay(self):
        for _ in range(3): self.limiter.fail('x')
        self.clock.value = 21
        self.assertEqual(self.limiter.check('x'), (True, 0))

    def test_success_clears_failures(self):
        self.limiter.fail('x'); self.limiter.success('x')
        self.assertEqual(self.limiter.check('x'), (True, 0))


if __name__ == '__main__':
    unittest.main()
