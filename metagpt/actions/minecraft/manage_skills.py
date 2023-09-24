# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 14:56
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

from metagpt.logs import logger
from metagpt.actions import Action


class RetrieveSkills(Action):
    """
    Action class for retrieving skills.
    Refer to the code in the voyager/agents/skill.py for implementation details.
    """
    
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.vect_db = ""
    
    async def run(self, *args, **kwargs):
        # Implement the logic for retrieving skills here.
        return []


class AddNewSkills(Action):
    """
    Action class for adding new skills.
    Refer to the code in the voyager/agents/skill.py for implementation details.
    """
    
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
    
    async def run(self, *args, **kwargs):
        # Implement the logic for adding new skills here.
        pass


class GenerateSkillDescription(Action):
    """
    Action class for generating skill descriptions.
    Refer to the code in the voyager/agents/skill.py for implementation details.
    """
    
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
    
    async def run(self, *args, **kwargs):
        # Implement the logic for generating skill descriptions here.
        pass

    
    