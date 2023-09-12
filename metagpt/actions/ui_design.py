# -*- coding: utf-8 -*-
# @Date    : 2023/8/17 13:43
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from typing import List, Union

from metagpt.tools.sd_engine import SDEngine

from metagpt.actions.design import BaseModelAction
from metagpt.prompts.sd_design import MODEL_SELECTION_PROMPT


class SDPromptRanker(BaseModelAction):
    """
    Class responsible for ranking multiple prompts based on current requirements and
    the underlying model to determine the most suitable prompt.
    
    """
    
    def __init__(self, name: str = "", *args, **kwargs):
        super().__init__(name, description="Prompt ranker", *args, **kwargs)


class SDImgScorer(BaseModelAction):
    """
    根据多个SD的生成结果，进行美学评分，选出评分最高的图片
    Class responsible for aesthetically scoring multiple SD generated results and
    selecting the highest scoring image.
    
    """
    
    def __init__(self, name: str = "", *args, **kwargs):
        super().__init__(name, description="Image Scorer", *args, **kwargs)


class LoraSelection(BaseModelAction):
    """
    Class responsible for selecting the most suitable Lora based on the
    current model and requirements.
    """
    
    def __init__(self, name: str = "", *args, **kwargs):
        super().__init__(name, *args, **kwargs)


class ModelSelection(BaseModelAction):
    DEFAULT_MODEL_INFO = {
        "realisticVisionV30_v30VAE": "Real Effects, Real Photo/Photography, v3.0",
        "pixelmix_v10": "an anime model merge with finetuned lineart and eyes."
    }
    
    def __init__(self, name="ModelSelection", *args, **kwargs):
        super().__init__(name, description="Select models", *args, **kwargs)
    
    def add_models(self, model_name="", model_desc=""):
        updated_info = {model_name: model_desc} if model_name else {}
        return {**self.DEFAULT_MODEL_INFO, **updated_info}
    
    async def run(self, query: str, system_text: str = "model selection"):
        prompt = MODEL_SELECTION_PROMPT.format(query=query, model_info=self.add_models())
        resp = await self._aask(prompt=prompt, system_msgs=[system_text])
        result = resp.split("||")
        model_name = result[0].replace("Model:", "").strip()
        domain = result[-1].replace("Domain:", "").strip()
        return model_name, domain


class SDGeneration(BaseModelAction):
    """Generates an image via the sd t2i API."""
    
    def __init__(self, name: str = "", *args, **kwargs):
        super().__init__(name, description="Stable Diffusion Generator", *args, **kwargs)
        self.engine = SDEngine()
        self.negative_prompts = {"realisticVisionV30_v30VAE": "worst quality, low quality, easynegative",
                                 "pixelmix_v10": ""}
    
    def _construct_prompt(self, query: str, model_name: str) -> str:
        """Constructs a prompt for the provided query and model."""
        negative_prompt = self.negative_prompts.get(model_name, "")
        return self.engine.construct_payload(query, negative_prompt=negative_prompt, sd_model=model_name)
    
    async def _generate_image(self, queries: List[str], model_name: str, img_name: str) -> None:
        """Generates image(s) using the provided queries and model name."""
        prompts = [self._construct_prompt(query, model_name) for query in queries]
        await self.engine.run_t2i(prompts, save_name=img_name)
    
    async def run(self, query: Union[str, List[str]], model_name: str, **kwargs) -> None:
        """
        Generate image via sd t2i API.
        """
        img_name = kwargs.get("image_name", "")
        
        queries = [query] if isinstance(query, str) else query
        await self._generate_image(queries, model_name, img_name)
