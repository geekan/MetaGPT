# -*- coding: utf-8 -*-
# @Date    : 6/27/2024 18:00 PM
# @Author  : didi
# @Desc    : test on humaneval graph

import asyncio

from examples.ags.benchmark.humaneval import sample_generate, samples_generate

asyncio.run(sample_generate("HumanEval/id", result_path="result_path", mode="alpha_codium"))
asyncio.run(samples_generate(mode="alpha_codium", result_path="result_path"))
