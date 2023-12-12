from metagpt.provider.openai_api import OpenAIGPTAPI, RateLimiter, CostManager
from metagpt.config import CONFIG
import openai


class OpenLLMGPTAPI(OpenAIGPTAPI):

    def __init__(self, model=None):
        self.model = model
        self.__init_openllm(CONFIG)
        self.auto_max_tokens = False
        self._cost_manager = CostManager()
        RateLimiter.__init__(self, rpm=self.rpm)

    def __init_openllm(self, config: CONFIG):

        if config.model_list:
            openai.api_base = config.model_list[self.model]['open_llm_api_base']
        else:
            openai.api_base = config.open_llm_api_base

        # due to use openai sdk, set the api_key but it will not be used.
        openai.api_key = "sk-xx"
        self.rpm = int(config.get("RPM", 10))
