# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 15:44
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.logs import logger
from metagpt.actions import Action
from metagpt.utils.minecraft import parse_action_response


class GenerateActionCode(Action):
    """
    Action class for generating action code.
    Refer to the code in the voyager/agents/action.py for implementation details.
    """

    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def generate_code(self, human_msg, system_msg=[]):
        """
        Generate action code logic.

        Implement the logic for generating action code here.
        """
        rsp = await self._aask(prompt=human_msg, system_msgs=system_msg)
        parsed_result = parse_action_response(rsp)
        # logger.info(f"parsed_result is HERE: {parsed_result}")

        try:
            return (
                parsed_result["program_code"] + "\n" + parsed_result["exec_code"],
                parsed_result["program_name"],
            )
        except:
            logger.error(f"Failed to parse response: {parsed_result}")
            return None, None

    async def run(self, human_msg, system_msg, *args, **kwargs):
        logger.info(f"run {self.__repr__()}")
        # Generate action code.
        generated_code, program_name = await self.generate_code(
            human_msg=human_msg, system_msg=system_msg
        )

        # Return the generated code.
        return generated_code, program_name


class SummarizeLog(Action):
    """
    Action class for parsing and summarizing logs.
    Refer to the code in the voyager/agents/action.py for implementation details.
    """

    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def summarize_logs(self):
        """
        Summarize chatlogs.

        Implement the logic for summarizing chatlogs here.
        """
        return ""

    async def run(self, *args, **kwargs):
        # Summarize chatlogs.
        summary = await self.summarize_logs()

        # Return the summary.
        return summary
