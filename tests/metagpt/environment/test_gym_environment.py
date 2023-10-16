#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of gym environment

from metagpt.environment.gym_environment import GymEnvironment


def test_gym_environment():
    gym_env = GymEnvironment(name="CartPole-v1")
    gym_env.init_register_funcs()

    observation, info = gym_env.call_func("reset", seed=42)
    for _ in range(2):
        action = gym_env.call_func("sample_action")
        observation, reward, terminated, truncated, info = gym_env.call_func("step", action=action)
        if terminated or truncated:
            observation, info = gym_env.call_func("reset")
    assert len(observation) == 4
    gym_env.call_func("close")
