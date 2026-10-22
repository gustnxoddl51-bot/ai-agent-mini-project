import asyncio
import json
import unittest

from agent.streaming import safe_stream


class TestSafeStream(unittest.IsolatedAsyncioTestCase):
    async def test_normal_stream(self):
        expected = [
            'data: {"type": "AnswerToken", "token": "안녕"}\n\n',
            'data: {"type": "Metrics", "retry_count": 0}\n\n',
            'data: {"type": "FinalAnswer", "reply": "안녕"}\n\n',
            "data: [DONE]\n\n",
        ]

        async def source():
            for chunk in expected:
                yield chunk

        actual = [chunk async for chunk in safe_stream(source())]
        self.assertEqual(actual, expected)

    async def test_error_before_response(self):
        async def source():
            raise RuntimeError("내부 테스트 오류")
            yield ""

        with self.assertLogs("agent.streaming", level="ERROR") as logs:
            actual = [chunk async for chunk in safe_stream(source())]

        self.assertEqual(len(actual), 2)
        self.assertTrue(actual[0].startswith("data: "))
        event = json.loads(actual[0].removeprefix("data: ").strip())

        self.assertEqual(event["type"], "Error")
        self.assertTrue(event["message"])
        self.assertNotIn("내부 테스트 오류", "".join(actual))
        self.assertIn("내부 테스트 오류", "\n".join(logs.output))
        self.assertEqual(actual[1], "data: [DONE]\n\n")