from __future__ import annotations
import json
import re
from typing import Any
from metagpt.actions.di.write_plan import (
    precheck_update_plan_from_rsp,
    update_plan_from_rsp,
)
from metagpt.actions.di.ask_review import ReviewConst
from metagpt.strategy.planner import Planner
from metagpt.logs import logger
from metagpt.schema import Message, Plan
from metagpt.actions import Action
from metagpt.utils.common import CodeParser
from metagpt.const import METAGPT_ROOT,DATA_PATH
from metagpt.ext.ai_writer.utils import colored_decorator,TitleHierarchy

class DocumentPlan(Action):
    PROMPT_TEMPLATE: str = """
    # Context:
    {context} 
    # Task:
    Based on the topic, write a outline or modify an existing outline of what you should do to achieve the goal. A outline consists of one to {max_tasks} chapters.
    If you are modifying an existing chapter, carefully follow the instruction, don't make unnecessary changes. Give the whole chapters unless instructed to modify only one chapter of the outline.
    If you encounter errors on the current chapter, revise and output the current single chapter only.
    Output a list of jsons following the format:
    ```json
    [
        {{
            "chapter_id": str = "unique identifier for a chapter in outline, can be an ordinal",
            "chapter_name": str = "current chapter title in the outline",
            "subheadings":list[str] = "this chapter is divided into several smaller sections with a finer level of detail (e.g., 1.1, 1.1.1, 1.1.2, 2.1)."
            
        }},
        ...
    ]
    ```
    """
    
    async def run(self, context: list[Message], max_tasks: int = 7, human_design_planner: bool = False) -> str:
      
        if  human_design_planner:
            with    open(DATA_PATH/ 'ai_writer/outlines/human_design_planner.json', 'r', encoding='utf-8') as file:
                    rsp = json.dumps(json.loads(file.read()), ensure_ascii=False)                
        else:     
            prompt = self.PROMPT_TEMPLATE.format(
                context="\n".join([str(ct) for ct in context]), max_tasks=max_tasks)
            rsp = await self._aask(prompt)
            rsp = CodeParser.parse_code(block=None, text=rsp) 
        return rsp



class WritePlanner(Planner):
    human_design_planner: bool = False
    titlehierarchy:Any = None
    async def update_plan(self, goal: str = "", context: str = "", max_tasks: int = 7, max_retries: int = 3):
        if goal:
            self.plan = Plan(goal=goal, context = context)
        plan_confirmed = False
        while not plan_confirmed:
            context = self.get_useful_memories()
            rsp = await DocumentPlan().run(context, max_tasks, self.human_design_planner)
            self.working_memory.add(Message(content=rsp, role="assistant", cause_by = DocumentPlan))
            
            rsp = self.post_process_chapter_id_or_name(rsp)
            # precheck plan before asking reviews
            is_plan_valid, error = precheck_update_plan_from_rsp(rsp, self.plan)
            plan_valid = self.precheck_from_rsp(rsp)
            if not (is_plan_valid and plan_valid) and max_retries > 0:
                error_msg = f"The generated plan is not valid with error: {error}, try regenerating, remember to generate either the whole plan or the single changed task only"
                logger.warning(error_msg)
                self.working_memory.add(Message(content=error_msg, role="assistant", cause_by= DocumentPlan))
                max_retries -= 1
                continue
            _, plan_confirmed = await self.ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)
        update_plan_from_rsp(rsp=rsp, current_plan=self.plan)
        self.titlehierarchy = self.process_response_and_build_hierarchy(rsp=rsp)
        self.working_memory.clear()


    def post_process_chapter_id_or_name(self,rsp):
        """
        Post-process the response to replace chapter_id and chapter_name with task_id and instruction.
        This method takes a response (rsp) and replaces any occurrences of "chapter_id" with "task_id"
        and "chapter_name" with "instruction". 
        
        This is useful when the response contains references
        to chapter identifiers and names that need to be updated to match the task's attributes.
        """
        # chapter_id save in current_task.task_id
        # chapter_name save in current_task.instruction
        rsp =  rsp.replace("chapter_id","task_id").replace("chapter_name","instruction")
        return rsp
    
    
    def precheck_from_rsp(self, rsp):
        """
        Perform a pre-check on the response data to ensure it meets the expected format.
        """
        try:
            rsp = json.loads(rsp)
            return  all([isinstance(task_config["subheadings"],list) for task_config in rsp])
        except Exception:
            return False

    
    
    def process_response_and_build_hierarchy(self,rsp = '')-> TitleHierarchy:
        """
        Post-process the response data to update the title hierarchy.
        """
        titlehierarchy = TitleHierarchy()
        rsp = json.loads(rsp)
        for element in rsp:  
            task_id = re.sub(r'\.\d+', '', element['task_id'])
            titlehierarchy.add_chapter(task_id, element['instruction'])
            titlehierarchy.add_subheadings(element['subheadings'])  
        return  titlehierarchy  
           


    async def process_task_result(self,task_result):
        """
        Process the task result and ask the user for confirmation.
        This method processes the given task result and prompts the user for confirmation.
        If the user confirms, it calls the `confirm_task` method with the current task,the task result, and the review.
        """
        review, task_result_confirmed = await self.ask_user_instruction(finished = True)
        if  task_result_confirmed:
            await self.confirm_task(self.current_task, task_result, review)
  
  
    async def ask_for_review(self, prompt:str):
        """
        Prompt the user for review input and handle the response.
        This method interacts with the user to collect their review input. If the auto_run
        flag is not set, it prompts the user with the given prompt and waits for their input.
        If the input matches certain exit words, the program will exit. Otherwise, the input
        is processed and returned.
        Parameters:
        prompt (str): The prompt to display to the user. Default is an empty string.
        Returns:
        tuple: A tuple containing the user's response and a boolean indicating whether the input was confirmed.
        """
        if  not self.auto_run:
            rsp = input(prompt)
            if rsp.lower() in ReviewConst.EXIT_WORDS:
                exit()
            confirmed = rsp.lower() in ReviewConst.CONTINUE_WORDS or ReviewConst.CONTINUE_WORDS[0] in rsp.lower()
            if  not confirmed:
                    self.working_memory.add(Message(content=rsp, role="user"))
            else: 
                rsp = '' 
                
            return rsp, confirmed
        else:
            return '' , True
        

    @colored_decorator('\033[1;30;47m') 
    async def ask_user_context(self):
            context = (
                f"Please add detailed writing context to enhance the text.\n"
                f"No relevant content to elaborate on, just respond with 'yes'.\n"
                ) 
            context, c_confirmed = await self.ask_for_review(context)
            return context, c_confirmed 
            
    @colored_decorator('\033[1;30;42m')     
    async def ask_user_instruction(self, finished = False):
            if finished:
                instruction = f"Does the chapter's paragraph meet your requirements? Reply 'yes' or 'no'.\n"
            else:
                instruction = (
                                f"Please add instruction to enhance the text. \n"
                                f"no instruction, simply reply with yes."
                                f"If you wish to revert to the original, just respond with 'redo'.\n" 
                            ) 
            # Calculate confirmed based on the context and instruction received
            instruction, i_confirmed = await self.ask_for_review(instruction)
            return instruction, i_confirmed 
    
    
    async def ask_review_template(self):
            """
            Ask the user for context and instruction to enhance the text of a given task.
            This method prompts the user to provide context and instruction to enhance the text
            of the given task. 
            """ 
            context, c_confirmed = await self.ask_user_context()
            instruction, i_confirmed = await self.ask_user_instruction()
            confirmed = ((c_confirmed or not context) and i_confirmed) or (not context and not instruction)
            return instruction, context, confirmed    

 

