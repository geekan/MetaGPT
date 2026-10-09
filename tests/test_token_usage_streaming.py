#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for shared TokenUsage tracker + StreamAccumulator (MEO twins)."""

import unittest

from metagpt.provider.streaming import StreamAccumulator, create_stream_collector, estimate_tokens
from metagpt.provider.token_usage import TokenUsageTracker, get_token_usage_tracker, normalize_usage


class TestNormalizeUsage(unittest.TestCase):
    def test_openai_chat_shape(self):
        n = normalize_usage({"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
        self.assertEqual(n["promptTokens"], 10)
        self.assertEqual(n["completionTokens"], 5)
        self.assertEqual(n["totalTokens"], 15)

    def test_anthropic_aliases(self):
        n = normalize_usage({"input_tokens": 8, "output_tokens": 4})
        self.assertEqual(n["promptTokens"], 8)
        self.assertEqual(n["completionTokens"], 4)
        self.assertEqual(n["totalTokens"], 12)

    def test_total_from_parts(self):
        n = normalize_usage(prompt_tokens=3, completion_tokens=7)
        self.assertEqual(n["totalTokens"], 10)


class TestTokenUsageTracker(unittest.TestCase):
    def test_record_and_totals(self):
        t = TokenUsageTracker()
        t.record(promptTokens=10, completionTokens=5, model="gpt-4o-mini", provider="openai")
        t.record(totalTokens=20, model="gpt-4o-mini", provider="openai")
        totals = t.totals()
        self.assertEqual(totals["promptTokens"], 10)
        self.assertEqual(totals["completionTokens"], 25)  # 5 + 20 (total as completion)
        self.assertEqual(totals["calls"], 2)
        self.assertEqual(t.last()["totalTokens"], 20)

    def test_by_model_provider(self):
        t = TokenUsageTracker()
        t.record(totalTokens=10, model="m", provider="litellm")
        snap = t.snapshot()
        self.assertEqual(snap["byModel"]["m"]["totalTokens"], 10)
        self.assertEqual(snap["byProvider"]["litellm"]["calls"], 1)

    def test_reset(self):
        t = TokenUsageTracker()
        t.record(totalTokens=5)
        t.reset()
        self.assertEqual(t.totals()["totalTokens"], 0)

    def test_singleton(self):
        self.assertIs(get_token_usage_tracker(), get_token_usage_tracker())


class TestStreamAccumulator(unittest.TestCase):
    def test_collect_text_and_on_token(self):
        seen = []
        acc = create_stream_collector(on_token=seen.append, model="m", provider="p")
        for ch in ["He", "llo", " ", "world"]:
            acc.push(ch)
        final = acc.end()
        self.assertEqual(final["text"], "Hello world")
        self.assertEqual(seen, ["He", "llo", " ", "world"])
        self.assertEqual(final["chunks"], 4)

    def test_usage_from_provider(self):
        acc = StreamAccumulator()
        acc.push("hi")
        acc.set_usage({"prompt_tokens": 2, "completion_tokens": 1})
        final = acc.end()
        self.assertEqual(final["usage"]["totalTokens"], 3)

    def test_estimate_usage_when_missing(self):
        acc = StreamAccumulator()
        acc.push("x" * 40)  # ~10 tokens
        final = acc.end()
        self.assertGreaterEqual(final["usage"]["completionTokens"], 5)

    def test_estimate_tokens(self):
        self.assertEqual(estimate_tokens(""), 0)
        self.assertGreaterEqual(estimate_tokens("hello world"), 1)

    def test_on_token_error_ignored(self):
        def bad(_):
            raise RuntimeError("boom")

        acc = create_stream_collector(on_token=bad)
        acc.push("ok")
        self.assertEqual(acc.text, "ok")


if __name__ == "__main__":
    unittest.main()
