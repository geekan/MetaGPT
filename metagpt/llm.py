#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""

from metagpt.logs import logger
from metagpt.config import CONFIG
from metagpt.provider.anthropic_api import Claude2 as Claude
from metagpt.provider.openai_api import OpenAIGPTAPI
from metagpt.provider.zhipuai_api import ZhiPuAIGPTAPI
from metagpt.provider.spark_api import SparkAPI
from metagpt.provider.human_provider import HumanProvider
from metagpt.provider.customized_api import CustomizedGPTAPI

def LLM(name = None) -> "BaseGPTAPI":
    """ initialize different LLM instance according to the key field existence"""
    if CONFIG.multi_llm:
        model = CONFIG._get(name)
        # If a model has been configured, it will be instantiated for the model
        if model:
            logger.info(f"{name}  will use {CONFIG._get(name)}")
            if model == 'openai' and CONFIG.openai_api_key:
                llm = OpenAIGPTAPI()
            elif model == 'claude' and CONFIG.claude_api_key:
                llm = Claude()
            elif model == 'spark' and CONFIG.spark_api_key:
                llm = SparkAPI()
            elif model =='zhipu' and CONFIG.zhipuai_api_key:
                llm = ZhiPuAIGPTAPI()
            elif CONFIG.model_list.get(model):
                llm = CustomizedGPTAPI(model)
            else:
                raise RuntimeError("You should config a LLM configuration first/"
                                   "Next, you need to check for any omissions or /"
                                   "errors in the multi-LLM configuration")
            return llm

        # Action\Role has no configuration information,
        # it is configured as follows
        else:
            if CONFIG.openai_api_key:
                llm = OpenAIGPTAPI()
            elif CONFIG.claude_api_key:
                llm = Claude()
            elif CONFIG.spark_api_key:
                llm = SparkAPI()
            elif CONFIG.zhipuai_api_key:
                llm = ZhiPuAIGPTAPI()
            else:
                llm = CustomizedGPTAPI(model)
            logger.info(f'{name} LLM is undefined and will use {model}')
            return llm

    else:
        if CONFIG.openai_api_key and not CONFIG.customized_api_base:
            llm = OpenAIGPTAPI()
        elif CONFIG.claude_api_key:
            llm = Claude()
        elif CONFIG.spark_api_key:
            llm = SparkAPI()
        elif CONFIG.zhipuai_api_key:
            llm = ZhiPuAIGPTAPI()
        elif CONFIG.customized_api_base and CONFIG.customized_api_model:
            llm = CustomizedGPTAPI(CONFIG.customized_api_model)
        else:
            raise RuntimeError("You should config a LLM configuration first")

        return llm
