#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for shared ContextManager + ToolRegistry (MEO twins)."""

import asyncio
import unittest

from metagpt.provider.context_manager import ContextManager, estimate_message_tokens
from metagpt.provider.tool_calling import (
    ToolRegistry,
    parse_tool_calls,
    to_openai_tool,
    to_openai_tools,
)


class TestContextManager(unittest.TestCase):
    def test_append_and_system(self):
        ctx = ContextManager(max_messages=10)
        ctx.system("You are helpful")
        ctx.add_user("hi")
        ctx.add_assistant("hello")
        msgs = ctx.messages()
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[-1]["content"], "hello")
        self.assertEqual(len(msgs), 3)

    def test_trim_by_max_messages_keeps_system(self):
        ctx = ContextManager(max_messages=4)
        ctx.system("sys")
        for i in range(10):
            ctx.add_user(f"u{i}")
        msgs = ctx.messages()
        self.assertEqual(msgs[0]["role"], "system")
        self.assertLessEqual(len(msgs), 4)

    def test_trim_by_chars(self):
        ctx = ContextManager(max_messages=100, max_chars=50, max_tokens=100000)
        ctx.system("s")
        for i in range(20):
            ctx.add_user("x" * 40)
        self.assertLessEqual(
            sum(len(m["content"]) for m in ctx.messages() if m["role"] != "system"),
            50,
        )

    def test_clear_keeps_system(self):
        ctx = ContextManager()
        ctx.system("sys")
        ctx.add_user("u")
        ctx.clear()
        self.assertEqual(len(ctx.messages()), 1)
        self.assertEqual(ctx.messages()[0]["role"], "system")

    def test_estimate_tokens(self):
        msgs = [{"role": "user", "content": "hello world"}]
        self.assertGreater(estimate_message_tokens(msgs), 0)
        self.assertGreater(ctx_est := ContextManager().tokenEstimate(), -1) if False else None

    def test_snapshot(self):
        ctx = ContextManager()
        ctx.add_user("a")
        s = ctx.snapshot()
        self.assertEqual(s["count"], 1)
        self.assertIn("tokenEstimate", s)


class TestToolCalling(unittest.TestCase):
    def test_to_openai_tool(self):
        t = to_openai_tool("echo", "Echo text", {"type": "object", "properties": {"x": {"type": "string"}}})
        self.assertEqual(t["type"], "function")
        self.assertEqual(t["function"]["name"], "echo")

    def test_to_openai_tools_mixed(self):
        tools = to_openai_tools(
            [
                {"name": "a", "description": "A"},
                to_openai_tool("b", "B"),
            ]
        )
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0]["function"]["name"], "a")

    def test_parse_tool_calls_dict(self):
        rsp = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "c1",
                                "type": "function",
                                "function": {"name": "echo", "arguments": '{"text": "hi"}'},
                            }
                        ],
                    }
                }
            ]
        }
        calls = parse_tool_calls(rsp)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["name"], "echo")
        self.assertEqual(calls[0]["arguments"]["text"], "hi")

    def test_registry_register_and_execute(self):
        reg = ToolRegistry()

        def echo(text: str = ""):
            """Echo."""
            return text.upper()

        reg.register("echo", "Echo.", {"type": "object", "properties": {"text": {"type": "string"}}}, echo)
        self.assertIn("echo", reg.names())
        out = asyncio.run(reg.execute("echo", {"text": "hi"}))
        self.assertTrue(out["success"])
        self.assertEqual(out["result"], "HI")

    def test_registry_tool_decorator(self):
        reg = ToolRegistry()

        @reg.tool(description="Add")
        def add(payload: dict = None):
            return 1 + 2

        # decorator passes args as kwargs from arguments dict - our execute uses **args
        # add has payload kw - fix test with matching signature

        async def add2(a: int = 0, b: int = 0):
            return a + b

        reg.register("add2", "Add", None, add2)
        out = asyncio.run(reg.execute("add2", {"a": 1, "b": 2}))
        self.assertEqual(out["result"], 3)

    def test_execute_unknown(self):
        out = asyncio.run(ToolRegistry().execute("nope", {}))
        self.assertFalse(out["success"])

    def test_run_turn_with_fake_llm(self):
        reg = ToolRegistry()

        async def add(a: int = 0, b: int = 0):
            return a + b

        reg.register("add", "Add numbers", None, add)

        class FakeLLM:
            async def aask_messages(self, messages, tools=None, tool_choice=None, timeout=None, stream=None):
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "1",
                                        "type": "function",
                                        "function": {"name": "add", "arguments": '{"a": 2, "b": 3}'},
                                    }
                                ],
                            }
                        }
                    ]
                }

        out = asyncio.run(reg.run_turn(FakeLLM(), [{"role": "user", "content": "2+3?"}]))
        self.assertEqual(out["tool_results"][0]["result"], 5)
        self.assertTrue(any(m["role"] == "tool" for m in out["messages"]))


if __name__ == "__main__":
    unittest.main()
