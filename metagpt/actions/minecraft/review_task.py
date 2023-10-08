# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 14:56
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.logs import logger
from metagpt.actions import Action
from metagpt.utils.minecraft import fix_and_parse_json


class VerifyTask(Action):
    """
    Action class for verifying a task.
    Refer to the code in the voyager/agents/critic.py for implementation details.
    """
    
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.llm.model = "gpt-3.5-turbo"

    async def run(self,human_msg, system_msg, max_retries=5, *args, **kwargs):
        # Implement the logic to verify the task here.

        # Example: Verify the completion of a task.

        # If verification is successful, return a success message.
        # task, status, review_info = "", True, "Task verified successfully."

        if max_retries == 0:
            logger.info(f"Failed to parse Critic Agent response. Consider updating your prompt.")
            return False, ""

        if human_msg is None:
            logger.warning(f"Failed to get human_msg or system_msg.")
            return False, ""
        critic = await self._aask(prompt=human_msg, system_msgs=system_msg)
        try:
            response = fix_and_parse_json(critic)
            assert response["success"] in [True, False]
            if "critique" not in response:
                response["critique"] = ""
            logger.info("Task verified successfully.")
            return response["success"], response["critique"]
        except Exception as e:
            logger.error(f"Error verifying the task: {str(e)}")
            return await self.run(human_msg, system_msg, max_retries=max_retries-1)


