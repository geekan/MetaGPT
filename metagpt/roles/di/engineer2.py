from __future__ import annotations

import asyncio
import json
import traceback
from typing import Literal

from pydantic import model_validator

from metagpt.actions import Action
from metagpt.actions.di.write_analysis_code import WriteAnalysisCode
from metagpt.logs import logger
from metagpt.prompts.di.engineer2 import CMD_PROMPT
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.schema import Message, TaskResult
from metagpt.strategy.experience_retriever import KeywordExpRetriever
from metagpt.strategy.planner import Planner
from metagpt.tools.libs.editor import Editor
from metagpt.tools.tool_recommend import BM25ToolRecommender
from metagpt.utils.common import CodeParser
from test3 import design_doc_2048, design_doc_snake, task_doc_2048, task_doc_snake


class Engineer2(DataInterpreter):
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = ""
    react_mode: Literal["react"] = "react"
    max_react_loop: int = 20  # used for react mode
    # task_result: TaskResult = None
    command_rsp: str = ""  # the raw string containing the commands
    commands: list[dict] = []  # commands to be executed
    editor: Editor = Editor()

    @model_validator(mode="after")
    def set_plan_and_tool(self) -> "DataInterpreter":
        # We force using this parameter for DataAnalyst
        assert self.react_mode == "react"
        assert self.auto_run
        assert self.use_plan

        # Roughly the same part as DataInterpreter.set_plan_and_tool
        self._set_react_mode(react_mode=self.react_mode, max_react_loop=self.max_react_loop, auto_run=self.auto_run)
        if self.tools and not self.tool_recommender:
            self.tool_recommender = BM25ToolRecommender(tools=self.tools, force=True)
        self.set_actions([WriteAnalysisCode])
        self._set_state(0)

        # HACK: Init Planner, control it through dynamic thinking; Consider formalizing as a react mode
        self.planner = Planner(goal="", working_memory=self.rc.working_memory, auto_run=True)

        return self

    async def _think(self) -> bool:
        """Useful in 'react' mode. Use LLM to decide whether and what to do next."""
        if not self.rc.todo and not self.rc.news:
            return False

        self._set_state(0)
        example = ""
        if not self.planner.plan.goal:
            self.user_requirement = self.get_memories()[-1].content
            self.planner.plan.goal = self.user_requirement
            example = KeywordExpRetriever().retrieve(self.user_requirement)
        else:
            # self.working_memory.add_batch(self.rc.news)
            self.rc.memory.add_batch(self.rc.news)
            # TODO: implement experience retrieval in multi-round setting
            # if self.planner.plan.current_task:
            #     experience = KeywordExpRetriever().retrieve(self.planner.plan.current_task.instruction, exp_type="task")
            #     if experience and experience not in [msg.content for msg in self.rc.memory.get()]:
            #         exp_msg = Message(content=experience, role="assistant")
            #         self.rc.memory.add(exp_msg)
            #     example = KeywordExpRetriever().retrieve(self.planner.plan.current_task.instruction, exp_type="task")

        plan_status = self.planner.plan.model_dump(include=["goal", "tasks"])
        for task in plan_status["tasks"]:
            task.pop("code")
            task.pop("result")
            task.pop("is_success")
        # print(plan_status)
        current_task = (
            self.planner.plan.current_task.model_dump(exclude=["code", "result", "is_success"])
            if self.planner.plan.current_task
            else ""
        )

        tools = await self.tool_recommender.recommend_tools()
        tool_info = json.dumps({tool.name: tool.schemas for tool in tools})
        prompt = CMD_PROMPT.format(
            plan_status=plan_status,
            current_task=current_task,
            example=example,
            # available_commands=prepare_command_prompt(self.available_commands),
            available_commands=tool_info,
        )
        # context = self.llm.format_msg(self.working_memory.get() + [Message(content=prompt, role="user")])
        context = self.llm.format_msg(self.rc.memory.get(10) + [Message(content=prompt, role="user")])

        print(*context, sep="\n" + "*" * 5 + "\n")

        self.command_rsp = await self.llm.aask(context)

        # self.rc.working_memory.add(Message(content=rsp, role="assistant"))
        self.rc.memory.add(Message(content=self.command_rsp, role="assistant"))

        return True

    async def _act(self) -> Message:
        try:
            commands = json.loads(CodeParser.parse_code(block=None, lang="json", text=self.command_rsp))
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            error_msg = Message(content=str(e), role="user")
            self.rc.memory.add(error_msg)
            return error_msg
        outputs = await self.run_commands(commands)
        # self.rc.working_memory.add(Message(content=outputs, role="user"))
        self.rc.memory.add(Message(content=outputs, role="user"))
        return Message(content="Task completed", role="assistant", sent_from=self._setting, cause_by=WriteAnalysisCode)

    async def _react(self) -> Message:
        actions_taken = 0
        rsp = Message(content="No actions taken yet", cause_by=Action)  # will be overwritten after Role _act
        while actions_taken < self.rc.max_react_loop:
            # NOTE: difference here, keep observing within react
            await self._observe()
            # think
            has_todo = await self._think()
            if not has_todo:
                break
            # act
            logger.debug(f"{self._setting}: {self.rc.state=}, will do {self.rc.todo}")
            rsp = await self._act()
            actions_taken += 1
        return rsp  # return output from the last action

    async def run_commands(self, commands) -> list:
        tool_execute_map = {
            "Plan.append_task": self.planner.plan.append_task,
            "Plan.reset_task": self.planner.plan.reset_task,
            "Plan.replace_task": self.planner.plan.replace_task,
            "Editor.write": self.editor.write,
            "Editor.write_content": self.editor.write_content,
            "Editor.read": self.editor.read,
        }

        # print(*commands, sep="\n")

        is_success = True
        outputs = ["Commands executed."]
        for cmd in commands:
            if cmd["command_name"] in tool_execute_map:
                try:
                    output = tool_execute_map[cmd["command_name"]](**cmd["args"])
                    if output:
                        outputs.append(f"Output for {cmd['command_name']}: {str(output)}")
                except Exception as e:
                    tb = traceback.format_exc()
                    print(e, tb)
                    outputs.append(tb)
                    is_success = False
                    break  # Stop executing if any command fails
        outputs = "\n\n".join(outputs)

        # Handle finish_current_task and end individually as a last step
        for cmd in commands:
            if (
                is_success
                and cmd["command_name"] == "Plan.finish_current_task"
                and not self.planner.plan.is_plan_finished()
            ):
                task_result = TaskResult(code=str(commands), result=outputs, is_success=is_success)
                self.planner.plan.current_task.update_task_result(task_result=task_result)
                self.planner.plan.finish_current_task()
                # self.rc.working_memory.clear()

            elif cmd["command_name"] == "Common.end":
                self._set_state(-1)

        return outputs


WINE_REQ = "Run data analysis on sklearn Wine recognition dataset, and train a model to predict wine class (20% as validation), and show validation accuracy."

GAME_REQ_2048 = f"""
Create a 2048 game, follow the design doc and task doc. Write your code under /Users/gary/Files/temp/workspace/2048_game/src.
After writing all codes, write a code review for the codes, make improvement or adjustment based on the review.
Notice: You MUST implement the full code, don't leave comment without implementation!
Design doc:
{task_doc_2048}
Task doc:
{design_doc_2048}
"""
GAME_REQ_SNAKE = f"""
Create a snake game, follow the design doc and task doc. Write your code under /Users/gary/Files/temp/workspace/snake_game/src.
After writing all codes, write a code review for the codes, make improvement or adjustment based on the review.
Notice: You MUST implement the full code, don't leave comment without implementation!
Design doc:
{task_doc_snake}
Task doc:
{design_doc_snake}
"""
GAME_INC_REQ_2048 = """
I found an issue with the 2048 code: when tiles are merged, no new tiles pop up.
Write code review for the codes (game.py, main.py, ui.py) under under /Users/gary/Files/temp/workspace/2048_game_bugs/src.
Then correct any issues you find. You can review all code in one time, and solve issues in one time.
"""
GAME_INC_REQ_SNAKE = """
Based on the design doc at /Users/gary/Files/temp/workspace/snake_game_bugs/docs/20240513200737.json,
Write code review for the codes (food.py, game.py, main.py, snake.py, ui.py) under under /Users/gary/Files/temp/workspace/snake_game_bugs/src.
Then correct any issues you find. You can read the design doc first, then review all code in one time, and solve issues in one time.
"""

if __name__ == "__main__":
    engineer2 = Engineer2(tools=["Plan", "Editor:write,read,write_content", "MGXEnv:ask_human,reply_to_human"])
    asyncio.run(engineer2.run(GAME_INC_REQ_2048))
