#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   gernerate_latex.py
@Time    :   2025/05/20 20:15:13
@Author  :   Deng Mingyi 
@Desc    :   Action to generate LaTeX content for presentations. Action to validate LaTeX content.
"""
from metagpt.prompts.PPTmaker import (
    SYSTEM_PROMPT,
    USER_CONTENT,
    TEXT_VALIDATION_PROMPT,
    USER_VALIDATION_CONTENT,
)
from metagpt.actions import Action
from metagpt.logs import logger
from typing import List
from metagpt.schema import Message


class LatexGeneratorAction(Action):
    """
    Action to generate LaTeX content for presentations.
    """

    name: str = "latexgenerator"
    description: str = """
        This agent generates complete, high-quality LaTeX documents with a focus on Beamer presentations. It accepts topic-specific input and produces fully self-contained LaTeX source code, including all required packages, structures, and rich content elements such as equations, figures, and formatted text. The agent ensures completeness by avoiding any placeholders or incomplete sections.

        In addition to generation, the agent supports iterative refinement: it evaluates and improves the generated LaTeX code based on validation feedback to ensure correctness, formatting quality, and logical structure. The final output is ready for immediate compilation and professional presentation use.
        """

    async def generate(self, request: str, history_messages: List[Message]) -> str:
        """
        Generate LaTeX content.
        Args:
            request: Initial user request or refined request with feedback.
            history_messages: List of historical messages for context.
        Returns:
            Generated LaTeX code as string
        """
        logger.info(f"Actual max_tokens used: {self.llm.config.max_token}")
        logger.info(f"Executing {self.name} Action: Generating LaTeX content for request \n'{request}'")

        system_content = SYSTEM_PROMPT
        history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in history_messages])
        user_content = USER_CONTENT.format(request=request, history=history_str)

        generated_latex = await self._aask(user_content, [system_content])

        logger.debug(f"Generated LaTeX content: {generated_latex}")
        return generated_latex

    async def run(self, request: str, history: List[Message]) -> str:
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
        If the result is satisfactory or improvements are minimal, it returns "No further feedback." or "The step result has already reached the requirement.".
        Otherwise, it provides detailed feedback and a revised version of the result that meets all requirements and is ready for downstream use.
        """

    async def validate(self, request: str, current_latex_to_validate: str, history_messages: List[Message]) -> str:
        """
        Validate the generated content.
        Args:
            request: Initial user request.
            current_latex_to_validate: The LaTeX content to be validated.
            history_messages: List of historical messages for context.
        Returns:
            Validation feedback string
        """
        logger.info(f"Executing {self.name} Action: Validating current content")

        system_content = TEXT_VALIDATION_PROMPT
        history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in history_messages])
        validation_input_for_prompt = f"Initial Request: {request}\n\nLaTeX to Validate:\n{current_latex_to_validate}\n\nConversation History:\n{history_str}"

        user_content = USER_VALIDATION_CONTENT.format(request=validation_input_for_prompt, history="") # Adjust as per prompt needs

        feedback = await self._aask(user_content, [system_content])
        logger.debug(f"Validation feedback: {feedback}")

        return feedback

    async def run(self, request: str, history: List[Message]) -> str:
        """Execute the current action.
           'request' here is the 'input_for_action' passed from PPTMaker._act,
           which is self.optimized_result for ValidatorAction.
        """
        initial_user_request = history[0].content if history else ""
        content_to_validate = request 
        return await self.validate(initial_user_request, content_to_validate, history)