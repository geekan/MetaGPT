#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   PPTmaker.py
@Time    :   2025/05/14 18:16:47
@Author  :   Deng Mingyi 
@Desc    :   A role to create LaTeX-based presentations.
"""

import os
from typing import List, Dict, Any
from metagpt.logs import logger
from metagpt.actions import Action
from metagpt.actions.generate_latex import LatexGeneratorAction, ValidatorAction
from metagpt.roles.di.role_zero import RoleZero
from metagpt.roles.role import RoleReactMode
from metagpt.schema import Message
from metagpt.utils.common import handle_exception
from metagpt.actions.add_requirement import UserRequirement


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
    is_completed: bool = False

    optimized_result: str = ""
    validator_feedback: str = ""
    curr_step: int = 0 

    ACTION_SEQUENCE_METADATA: List[Dict[str, Any]] = [
        {"action_class": LatexGeneratorAction, "save_result": True, "name": "latexgenerator"},
        {"action_class": ValidatorAction, "save_result": False, "name": "validator"},
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([meta["action_class"] for meta in self.ACTION_SEQUENCE_METADATA])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER, max_react_loop=self.max_steps)
        self.use_fixed_sop = False
        self._reset_state()

    def _reset_state(self):
        """Reset internal state to prepare for a new task"""
        self.curr_step = 0
        self.is_completed = False
        self.validator_feedback = ""
        self.optimized_result = ""
        logger.info(f"{self.name} state has been reset")

    @staticmethod
    @handle_exception(exception_msg="Fail to save markdown file", default_return="Error Occurred")
    def save_md(content: str, filename: str = "presentation.md"):
        """
        Save the generated LaTeX content to a file in the workspace directory.
        """
        workspace_dir = os.path.join(os.getcwd(), "workspace")
        os.makedirs(workspace_dir, exist_ok=True)
        save_path = os.path.join(workspace_dir, filename)

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Markdown file saved at {save_path}")
        return save_path

    async def _think(self) -> bool:
        """
        Decide the next action or if the task should stop.
        This is called by the base RoleZero's _react loop.
        Manages cycling through actions for BY_ORDER mode up to max_steps.
        """
        if self.is_completed:
            logger.info(f"{self.name} task marked as completed. Stopping.")
            return False

        if self.curr_step >= self.max_steps:
            logger.info(f"{self.name} reached maximum steps ({self.max_steps}). Stopping.")
            return False

        # Determine the next action index in the sequence based on current step
        next_action_idx_in_sequence = self.curr_step % len(self.ACTION_SEQUENCE_METADATA)
        self._set_state(next_action_idx_in_sequence) # Set self.rc.state and self.rc.todo

        if self.rc.todo:
            logger.info(f"{self.name} decided next action: {self.rc.todo.name} (Current Step: {self.curr_step + 1}, Action Index: {next_action_idx_in_sequence})")
        else:
            logger.error(f"{self.name} _think decided no action despite conditions to continue. Action index: {next_action_idx_in_sequence}")
            return False 
        return True 

    async def _act(self) -> Message:
        """
        Perform the current action decided by _think and process its result.
        This is called by the base RoleZero's _react loop.
        """
        action_idx_in_sequence = self.rc.state 
        
        if not (0 <= action_idx_in_sequence < len(self.actions)): 
            logger.error(f"Invalid action index {action_idx_in_sequence} in _act. Stopping.")
            return Message(content=f"Error: Invalid action index {action_idx_in_sequence}.", role=self.profile)

        current_action_meta = self.ACTION_SEQUENCE_METADATA[action_idx_in_sequence] 
        tool_instance: Action = self.actions[action_idx_in_sequence]
        
        tool_name = current_action_meta["name"]
        save_result_flag = current_action_meta["save_result"]
        
        logger.info(f"{self.name} performing action: {tool_name} (Overall Step: {self.curr_step + 1}, Action Index: {action_idx_in_sequence})")
        
        result_content_str = ""
        try:
            initial_request_str = self.rc.history[0].content if self.rc.history else ""
            input_for_action = self.optimized_result if isinstance(tool_instance, ValidatorAction) else initial_request_str
            
            if isinstance(tool_instance, LatexGeneratorAction) and self.validator_feedback:
                # Append feedback to the original request for the generator
                input_for_action = f"Original Request:\n{initial_request_str}\n\nFeedback for improvement:\n{self.validator_feedback}"

            result_content_str = await tool_instance.run(
                request=input_for_action, 
                history=self.rc.history 
            )
            
            if save_result_flag: # update self.optimized_result
                self.optimized_result = result_content_str
            
            if isinstance(tool_instance, ValidatorAction):
                self.validator_feedback = result_content_str 
                if "No further feedback" in result_content_str:
                    self.is_completed = True
                    logger.info(f"{self.name} task deemed completed by validator.")
            elif isinstance(tool_instance, LatexGeneratorAction): 
                self.validator_feedback = "" 

            # Add action's direct result to memory
            self.rc.memory.add(Message(content=result_content_str, role=self.profile, cause_by=type(tool_instance), sent_from=self.name))

        except Exception as e:
            logger.error(f"Error executing {tool_name} in {self.name}: {e}", exc_info=True)
            self.curr_step += 1 
            return Message(content=f"Error executing {tool_name}: {str(e)}", role=self.profile, cause_by=type(tool_instance))

        self.curr_step += 1
        
        display_content = result_content_str 

        return Message(
            content=display_content or f"Step {self.curr_step}/{self.max_steps} ({tool_name}) completed.", # self.curr_step is already incremented
            role=self.profile,
            cause_by=type(tool_instance)
        )

    @handle_exception(exception_msg="Error in PPTMaker execution", default_return=Message(content="Error occurred", role="system"))
    async def run(self, prompt: Message) -> Message:
        """
        Launch the PPTMaker role execution flow.
        """
        self._reset_state()
        
        logger.info(f"{self.name} run: Starting with prompt: '{prompt.content[:50]}...'")
        
        prompt.role = "user"
        prompt.cause_by = UserRequirement
        prompt.sent_from = self.name
        
        self.rc.memory.add(prompt)
        self.rc.news.append(prompt)
        
        logger.info(f"{self.name} run: Added prompt to memory and news. Memory: {len(self.rc.history)}, News: {len(self.rc.news)}")
        
        await self._react()
        
        # Finalize the task and save the result
        final_content_to_save = self.optimized_result
        status_message = "Unknown"

        if self.is_completed:
            logger.info(f"{self.name} task completed successfully.")
            status_message = "Completed"
        elif self.curr_step >= self.max_steps:
            logger.info(f"{self.name} reached maximum steps ({self.max_steps}).")
            status_message = "Reached max steps"
        else: 
            logger.info(f"{self.name} task did not complete normally (curr_step: {self.curr_step}, is_completed: {self.is_completed}).")
            status_message = "Stopped or Errored"
                
        if not final_content_to_save:
            final_content_to_save = "No content was finalized."
        
        final_report_str = f"Generation task status: {status_message}.\n\n"
        if self.is_completed or self.optimized_result:
            final_report_str += f"Final LaTeX content:\n\n{final_content_to_save}"
        else:
            final_report_str += f"Last relevant output:\n\n{final_content_to_save}"
        
        self.save_md(final_content_to_save, filename="presentation_output.md")
        logger.info(f"Final result saved. Optimized result length: {len(final_content_to_save)}")
        
        return Message(content=final_report_str, role=self.profile)

    