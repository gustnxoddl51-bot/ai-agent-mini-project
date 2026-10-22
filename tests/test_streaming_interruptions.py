import asyncio
import json
import unittest

from agent.streaming import safe_stream


class TestStreamInterruptions(unittest.IsolatedAsyncioTestCase):
    async def test_error_during_response(self):
        first = 'data: {"type": "AnswerToken", "token": "안녕"}\n\n'

        async def source():
            yield first
            raise RuntimeError("답변 도중 테스트 오류")

        with self.assertLogs("agent.streaming", level="ERROR") as logs:
            actual = [chunk async for chunk in safe_stream(source())]

        self.assertEqual(len(actual), 3)
        self.assertEqual(actual[0], first)
        self.assertTrue(actual[1].startswith("data: "))
        event = json.loads(actual[1].removeprefix("data: ").strip())
        self.assertEqual(event["type"], "Error")
        self.assertNotIn("답변 도중 테스트 오류", "".join(actual))
        self.assertIn("답변 도중 테스트 오류", "\n".join(logs.output))
        self.assertEqual(actual[2], "data: [DONE]\n\n")

    async def test_cancellation(self):
        async def source():
            raise asyncio.CancelledError()
            yield ""

        received = []
        with self.assertNoLogs("agent.streaming", level="ERROR"):
            with self.assertRaises(asyncio.CancelledError):
                async for chunk in safe_stream(source()):
                    received.append(chunk)

        self.assertEqual(received, [])