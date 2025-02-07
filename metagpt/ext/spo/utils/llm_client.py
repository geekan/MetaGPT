import re
from typing import Optional
from metagpt.configs.models_config import ModelsConfig
from metagpt.llm import LLM
import asyncio


class SPO_LLM:
    _instance: Optional['SPO_LLM'] = None

    def __init__(self, optimize_kwargs=None, evaluate_kwargs=None, execute_kwargs=None):
        self.evaluate_llm = LLM(llm_config=self._load_llm_config(evaluate_kwargs))
        self.optimize_llm = LLM(llm_config=self._load_llm_config(optimize_kwargs))
        self.execute_llm = LLM(llm_config=self._load_llm_config(execute_kwargs))

    def _load_llm_config(self, kwargs: dict):
        model = kwargs.get('model')
        if not model:
            raise ValueError("'model' parameter is required")

        try:
            model_config = ModelsConfig.default().get(model)
            if model_config is None:
                raise ValueError(f"Model '{model}' not found in configuration")

            config = model_config.model_copy()

            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            return config

        except AttributeError as e:
            raise ValueError(f"Model '{model}' not found in configuration")
        except Exception as e:
            raise ValueError(f"Error loading configuration for model '{model}': {str(e)}")

    async def responser(self, type: str, messages):
        if type == "optimize":
            response = await self.optimize_llm.acompletion(messages)
        elif type == "evaluate":
            response = await self.evaluate_llm.acompletion(messages)
        elif type == "execute":
            response = await self.execute_llm.acompletion(messages)
        else:
            raise ValueError("Please set the correct name: optimize, evaluate or execute")

        rsp = response.choices[0].message.content
        return rsp

    @classmethod
    def initialize(cls, optimize_kwargs, evaluate_kwargs, execute_kwargs):
        """Initialize the global instance"""
        cls._instance = cls(optimize_kwargs, evaluate_kwargs, execute_kwargs)

    @classmethod
    def get_instance(cls):
        """Get the global instance"""
        if cls._instance is None:
            raise RuntimeError("SPO_LLM not initialized. Call initialize() first.")
        return cls._instance

def extract_content(xml_string, tag):
    pattern = rf'<{tag}>(.*?)</{tag}>'
    match = re.search(pattern, xml_string, re.DOTALL)
    return match.group(1).strip() if match else None


async def spo():
    # test LLM
    SPO_LLM.initialize(
        optimize_kwargs={"model": "gpt-4o", "temperature": 0.7},
        evaluate_kwargs={"model": "gpt-4o-mini", "temperature": 0.3},
        execute_kwargs={"model": "gpt-4o-mini", "temperature": 0.3}
    )

    llm = SPO_LLM.get_instance()

    # test messages
    hello_msg = [{"role": "user", "content": "hello"}]
    response = await llm.responser(type='execute', messages=hello_msg)
    print(f"AI: {response}")
    response = await llm.responser(type='optimize', messages=hello_msg)
    print(f"AI: {response}")
    response = await llm.responser(type='evaluate', messages=hello_msg)
    print(f"AI: {response}")


if __name__ == "__main__":
    asyncio.run(spo())



