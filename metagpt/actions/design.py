# -*- coding: utf-8 -*-
# @Date    : 2023/8/17 13:43
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

# Standard library imports
from functools import wraps
from typing import Callable, Any, List, Optional, Tuple

# Local library imports
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from metagpt.prompts.sd_design import (
    SD_PROMPT_KW_OPTIMIZE_TEMPLATE,
    SD_PROMPT_IMPROVE_OPTIMIZE_TEMPLATE,
    FORMAT_INSTRUCTIONS,
    PROMPT_OUTPUT_MAPPING
)
from metagpt.utils.resp_parse import flatten_json_structure, try_parse_json

# A default template for the system primer.
SYSTEM_PRIMER_TEMPLATE = "Act like you are a terminal and always format your response as json. Always return exactly {answer_count} answers per question in English."


class Tool:
    """Define a tool with its name, function and description."""
    
    def __init__(self, name: str, func: Callable, description: str) -> None:
        """Initialize tool."""
        self.name = name
        self.func = func
        self.description = description


# Decorator for the BaseModelAction to wrap it with system primer details
def system_primer_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        system_primer = SYSTEM_PRIMER_TEMPLATE.format(answer_count=kwargs.get('answer_count', 1))
        logger.info(system_primer)
        return await func(*args, system_primer=system_primer, **kwargs)
    
    return wrapper


class BaseModelAction(Action):
    
    def __init__(self, name: str = "", description: str = "", *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.desc = description
    
    async def handle_response(self, resp: str) -> Any:
        """Handle JSON response and extract value."""
        try:
            resp_json = flatten_json_structure(try_parse_json(resp))
            logger.info(resp_json)
            return resp_json
        
        except Exception as exp:
            logger.error(f" JSON response {exp}")
            return None
    
    @system_primer_decorator
    async def run_optimize_or_improve(self, query: str, domain: str, template: str, answer_count: int = 1,
                                      system_primer=None) -> List[str]:
        """Run optimization or improvement based on the given template."""
        prompt = template.format(messages=query, domain=domain, answer_count=answer_count)
        resp: str = await self._aask(prompt=prompt, system_msgs=[system_primer])
        result = await self.handle_response(resp)
        return result or [query]


class SDPromptOptimize(BaseModelAction):
    """
    Optimize graphical prompts based on keywords.
    扩充画图的提示词，根据keyword
    """
    
    def __init__(self, name: str = "", *args, **kwargs):
        super().__init__(name, description="PromptOptimize", *args, **kwargs)
    
    async def run(self, query: str, domain: str = "realistic", answer_count: int = 1) -> List[str]:
        """Run the optimization for the given query."""
        return await self.run_optimize_or_improve(query, domain, SD_PROMPT_KW_OPTIMIZE_TEMPLATE,
                                                  answer_count=answer_count)


class SDPromptImprove(BaseModelAction):
    """Enhance the input prompt (recommended when the input prompt is long).
    fixme: 接入提示词优化的FT模型
    """
    
    def __init__(self, name: str = "", *args, **kwargs):
        super().__init__(name, description="PromptImprove", *args, **kwargs)
    
    async def run(self, query: str, domain: str = "realistic", answer_count: int = 1) -> List[str]:
        """Run the improvement for the given query."""
        return await self.run_optimize_or_improve(query, domain, SD_PROMPT_IMPROVE_OPTIMIZE_TEMPLATE,
                                                  answer_count=answer_count)


class SDPromptExtend(BaseModelAction):
    """Action class to extend the prompt."""
    
    def __init__(self, name: str = "", tools: Optional[List[Tool]] = [], **kwargs):
        super().__init__(name, description="Prompt Extend", **kwargs)
        self.tools = tools
        logger.info(self.tools)
    
    def _parse_tools(self) -> Tuple[str, str]:
        """Parse tool names and descriptions."""
        tool_strings = [f"{tool.name}: {tool.description}" for tool in self.tools]
        formatted_tools = "\n".join(tool_strings)
        tool_names = ", ".join(tool.name for tool in self.tools)
        return tool_names, formatted_tools
    
    async def run(self, query: str, answer_count: int = 1, domain: str = "realistic",
                  model_name="realisticVisionV30_v30VAE") -> str:
        """Extend the prompt and get the "Final Action" from the output."""
        tool_names, formatted_tools = self._parse_tools()
        msg = FORMAT_INSTRUCTIONS.format(query=query, tool_names=tool_names,
                                         tool_description=formatted_tools,
                                         model_name=model_name, domain=domain)
        
        resp = await self._aask(msg)
        output_block = OutputParser.parse_data_with_mapping(resp, PROMPT_OUTPUT_MAPPING)
        return output_block["Final Action"]


