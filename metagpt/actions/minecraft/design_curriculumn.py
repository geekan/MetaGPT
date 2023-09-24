# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 14:56
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from metagpt.logs import logger
from metagpt.actions import Action


class DesignTask(Action):
    """
    Action class for decomposing a task.
    Refer to the code in the voyager/agents/curriculum.py for implementation details.
    """
    
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
    
    def decompose_task(self, query):
        # Implement the logic to decompose a task here.
        return ""
    
    async def propose_next_ai_task(self, prompts, system_msg):
        """
        Refer to the code in the voyager/agents/curriculum.py propose_next_ai_task() for implementation details.
        Returns:

        """
        curriculum = await self._aask(prompt=prompts, system_msgs=system_msg)
        
        logger.info(f"\033[31m****Curriculum Agent ai message****\n{curriculum}\033[0m")
    
    def parse_llm_response(self, llm_resp):
        # Implement the logic to parse the LLM response here.
        return "", ""
    
    async def run(self, human_msg, system_msg, *args, **kwargs):
        logger.info(f"run {self.__repr__()}")
        
        # Call the language model to generate a response.
        
        llm_response = await self.propose_next_ai_task(prompts=human_msg, system_msg=system_msg)
        
        # Parse the response from the language model.
        task, context = self.parse_llm_response(llm_response)
        
        return task, context


class DesignCurriculum(Action):
    """
    Action class for designing curriculum-related questions.
    Refer to the code in the voyager/agents/curriculum.py for implementation details.
    """
    
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.vect_db = ""
    
    def get_task_context(self):
        # Implement the logic for a specific task in generating context.
        return ""
    
    def generate_qa(self):
        # Implement the logic to generate curriculum-related questions and answers.
        question = ""
        answer = ""
        context = f"Question: {question}\n{answer}"
        return context
    
    def generate_qa_step1(self):
        # Implement the logic for a specific step in generating questions and answers.
        return ""
    
    def generate_qa_step2(self):
        # Implement the logic for another specific step in generating questions and answers.
        return ""
    
    async def run(self, *args, **kwargs):
        logger.info(f"run {self.__repr__()}")
        # Generate curriculum-related questions and answers.
        curriculum_qa = self.generate_qa()
        
        # Return the generated questions and answers.
        return curriculum_qa
