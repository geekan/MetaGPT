#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : RL environment about Gymnasium(forked from openai gym)

from typing import Callable

import gymnasium as gym

from metagpt.logs import logger
from metagpt.environment.general_environment import GeneralEnvironment


class GymEnvironment(GeneralEnvironment):

    def init_register_funcs(self):
        env = gym.make(self.name)
        logger.info(f"init gym environment: {self.name}")
        self.register_func("reset", env.reset)
        self.register_func("sample_action", env.action_space.sample)
        self.register_func("step", env.step)
        self.register_func("close", env.close)
