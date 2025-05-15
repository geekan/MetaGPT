#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   PPTmaker.py
@Time    :   2025/05/14 18:16:47
@Author  :   Deng Mingyi 
@Desc    :   A role to create LaTeX-based presentations.
"""

from typing import List, Dict, Any
from metagpt.actions import Action
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.prompts.PPTmaker import SYSTEM_PROMPT, USER_CONTENT, TEXT_VALIDATION_PROMPT, USER_VALIDATION_CONTENT


class LatexGeneratorAction(Action):
    """
    Action to generate LaTeX content for presentations.
    """
    name: str = "latexgenerator" 
    description: str = """
        This agent generates complete, high-quality LaTeX documents with a focus on Beamer presentations. It accepts topic-specific input and produces fully self-contained LaTeX source code, including all required packages, structures, and rich content elements such as equations, figures, and formatted text. The agent ensures completeness by avoiding any placeholders or incomplete sections.

        In addition to generation, the agent supports iterative refinement: it evaluates and improves the generated LaTeX code based on validation feedback to ensure correctness, formatting quality, and logical structure. The final output is ready for immediate compilation and professional presentation use.
        """
    
    async def generate(self, request: str, history: str) -> str:
        """
        Generate LaTeX content.
        Args:
            request: Initial user request
            history: String representation of historical messages
        Returns:
            Generated LaTeX code as string
        """
        logger.info(f"Executing {self.name} Action: Generating LaTeX content for request '{request[:50]}...'")
        
        system_content = SYSTEM_PROMPT
        user_content = USER_CONTENT.format(request=request, history=history)
        
        generated_latex = await self._aask(user_content, [system_content])
        
        logger.debug(f"Generated LaTeX content (partial): {generated_latex[:200]}...")
        return generated_latex
    
    async def run(self, request: str, history: str) -> str:
        """Execute the current action"""
        return await self.generate(request, history)


class ValidatorAction(Action):
    """
    Action to validate LaTeX content.
    """
    name: str = "validator" 
    description: str = """
        This tool evaluates the quality and completeness of a subtask result against a set of predefined criteria.
        It checks whether the result fully satisfies task requirements, maintains high quality in terms of clarity, accuracy, and formatting,
        and determines whether improvements have been made in comparison to prior versions.
        If the result is satisfactory or improvements are minimal, it returns "The step result has already reached the requirement.".
        Otherwise, it provides detailed feedback and a revised version of the result that meets all requirements and is ready for downstream use.
        """ 
    
    async def validate(self, request: str, history: str) -> str:
        """
        Validate the generated content.
        Args:
            request: Initial user request
            history: String representation of historical messages
        Returns:
            Validation feedback string
        """
        logger.info(f"Executing {self.name} Action: Validating current content")
        
        system_content = TEXT_VALIDATION_PROMPT
        user_content = USER_VALIDATION_CONTENT.format(request=request, history=history)
        
        feedback = await self._aask(user_content, [system_content])
        logger.debug(f"Validation feedback: {feedback[:200]}...")

        return feedback
    
    async def run(self, request: str, history: str) -> str:
        """Execute the current action"""
        return await self.validate(request, history)


class PPTMaker(RoleZero):
    """
    Role responsible for creating LaTeX format presentations. Calls tools in a fixed sequence
    and may terminate early based on validator feedback.
    """
    name: str = "PPTMaker"
    profile: str = "LaTeX Presentation Generator"
    goal: str = "Generate high-quality LaTeX presentations in Beamer format"
    constraints: str = "Call tools in predefined order, may terminate early based on validation feedback"

    max_steps: int = 7
    curr_step: int = 0
    
    accumulated_latex: str = ""
    is_completed: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_actions([LatexGeneratorAction, ValidatorAction])
        self._reset_state()

    def _reset_state(self):
        """Reset internal state to prepare for a new task"""
        self.curr_step = 0
        self.accumulated_latex = ""
        self.is_completed = False
        logger.info(f"{self.name} state has been reset")

    async def react(self) -> Message:
        """
        Process current state, decide next action, execute and return a Message.
        """
        if self.curr_step >= self.max_steps or self.is_completed:
            logger.info(f"{self.name} task completed or reached maximum steps ({self.max_steps})")
            final_message = f"Generation task completed.\nGenerated LaTeX content:\n\n{self.accumulated_latex}"
            self._reset_state()
            return Message(content=final_message, role=self.profile, cause_by=self.__class__)
        
        tool_idx = self.curr_step % len(self.rc.actions)
        tool_class = [LatexGeneratorAction, ValidatorAction][tool_idx] 
        tool_name = ["latexgenerator", "validator"][tool_idx]
        
        logger.info(f"{self.name} selected tool: {tool_name}")
        
        request = self.rc.history[0].content if self.rc.history else "No topic provided"
        payload = {
            "request": request,
            "history": self.accumulated_latex,  
        }
        
        result = None
        try:
            if tool_name == "latexgenerator":
                result = await self.rc.run_action(
                    LatexGeneratorAction, 
                    request=payload["request"], 
                    history=payload["history"]
                    )
                if result:
                    if not self.accumulated_latex:
                        self.accumulated_latex = result
                    else:
                        self.accumulated_latex += "\n" + result
                    logger.info(f"LaTeX content generated, current total length: {len(self.accumulated_latex)}")
                message_content = f"Step {self.curr_step+1}/{self.max_steps}: Used tool {tool_name} to generate content"
            
            elif tool_name == "validator":
                result = await self.rc.run_action(
                    ValidatorAction,
                    request=payload["request"], 
                    history=payload["history"]
                    )
                message_content = f"Step {self.curr_step+1}/{self.max_steps}: Used tool {tool_name} to validate content"
                
                if "The step result has already reached the requirement." in result:
                    logger.info(f"{self.name}: Validator indicates task is complete")
                    self.is_completed = True
                    final_msg = f"Validation complete, task requirements met. Final LaTeX content:\n\n{self.accumulated_latex}"
                    self._reset_state()
                    return Message(content=final_msg, role=self.profile, cause_by=tool_class)
        
            else:
                message_content = f"Unknown tool type: {tool_name}"
                logger.warning(message_content)
        
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            message_content = f"Error executing tool {tool_name}: {str(e)}"
        
        self.curr_step += 1
        
        return Message(content=message_content, role=self.profile, cause_by=tool_class)
