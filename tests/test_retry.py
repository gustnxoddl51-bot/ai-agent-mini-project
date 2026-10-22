import asyncio
import unittest
from unittest.mock import AsyncMock

from langsmith import tracing_context

from agent.retry import with_retry


class TestRetry(unittest.IsolatedAsyncioTestCase):
    async def test_success_without_retry(self):
        operation = AsyncMock(return_value="성공")

        with tracing_context(enabled=False):
            result = await with_retry(operation, base_delay=0)

        self.assertEqual(result, ("성공", 0))
        operation.assert_awaited_once()

    async def test_timeout_then_success(self):
        operation = AsyncMock(
            side_effect=[asyncio.TimeoutError(), "성공"]
        )

        with tracing_context(enabled=False):
            result = await with_retry(operation, base_delay=0)

        self.assertEqual(result, ("성공", 1))
        self.assertEqual(operation.await_count, 2)

    async def test_stop_after_three_attempts(self):
        operation = AsyncMock(side_effect=asyncio.TimeoutError())

        with tracing_context(enabled=False):
            with self.assertRaises(asyncio.TimeoutError):
                await with_retry(operation, retries=3, base_delay=0)

        self.assertEqual(operation.await_count, 3)

    async def test_no_retry_for_value_error(self):
        operation = AsyncMock(side_effect=ValueError("잘못된 입력"))

        with tracing_context(enabled=False):
            with self.assertRaises(ValueError):
                await with_retry(operation, base_delay=0)

        operation.assert_awaited_once()