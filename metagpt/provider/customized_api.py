from metagpt.provider.openai_api import OpenAIGPTAPI,RateLimiter,CostManager
from metagpt.config import CONFIG
import openai
class CustomizedGPTAPI(OpenAIGPTAPI):

    def __init__(self,model = None):
        self.model = model
        self.__start_model(CONFIG)
        self.auto_max_tokens = False
        self._cost_manager = CostManager()
        RateLimiter.__init__(self, rpm=self.rpm)

    def __start_model(self,config: CONFIG):

        if config.multi_llm:
            openai.api_base = config.model_list[self.model]
        else:
            openai.api_base = config.customized_api_base

        openai.api_key = config.openai_api_key # due to use openai sdk, set the api_key but it will't be used.
        self.rpm = int(config.get("RPM", 10))
