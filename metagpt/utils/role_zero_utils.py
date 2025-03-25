from __future__ import annotations

import json
import re
import traceback
from typing import Tuple

from metagpt.const import IMAGES
from metagpt.logs import logger
from metagpt.prompts.di.role_zero import (
    ASK_HUMAN_COMMAND,
    ASK_HUMAN_GUIDANCE_FORMAT,
    END_COMMAND,
    JSON_REPAIR_PROMPT,
    REGENERATE_PROMPT,
    SUMMARY_PROBLEM_WHEN_DUPLICATE,
)
from metagpt.schema import Message, UserMessage
from metagpt.utils.common import CodeParser, extract_and_encode_images
from metagpt.utils.repair_llm_raw_output import (
    RepairType,
    repair_escape_error,
    repair_llm_raw_output,
)


async def parse_browser_actions(memory: list[Message], browser) -> list[Message]:
    if not browser.is_empty_page:
        pattern = re.compile(r"Command Browser\.(\w+) executed")
        for index, msg in zip(range(len(memory), 0, -1), memory[::-1]):
            if pattern.search(msg.content):
                memory.insert(index, UserMessage(cause_by="browser", content=await browser.view()))
                break
    return memory


async def parse_editor_result(memory: list[Message], keep_latest_count=5) -> list[Message]:
    """Retain the latest result and remove outdated editor results."""
    pattern = re.compile(r"Command Editor\.(\w+?) executed")
    new_memory = []
    i = 0
    for msg in reversed(memory):
        matches = pattern.findall(msg.content)
        if matches:
            i += 1
            if i > keep_latest_count:
                new_content = msg.content[: msg.content.find("Command Editor")]
                new_content += "\n".join([f"Command Editor.{match} executed." for match in matches])
                msg = UserMessage(content=new_content)
        new_memory.append(msg)
    # Reverse the new memory list so the latest message is at the end
    new_memory.reverse()
    return new_memory


async def parse_images(memory: list[Message], llm) -> list[Message]:
    if not llm.support_image_input():
        return memory
    for msg in memory:
        if IMAGES in msg.metadata or msg.role != "user":
            continue
        images = extract_and_encode_images(msg.content)
        if images:
            msg.add_metadata(IMAGES, images)
    return memory


async def check_duplicates(
    req: list[dict], command_rsp: str, rsp_hist: list[str], llm, respond_language: str, check_window: int = 10
) -> str:
    past_rsp = rsp_hist[-check_window:]
    if command_rsp in past_rsp and '"command_name": "end"' not in command_rsp:
        # Normal response with thought contents are highly unlikely to reproduce
        # If an identical response is detected, it is a bad response, mostly due to LLM repeating generated content
        # In this case, ask human for help and regenerate
        # TODO: switch to llm_cached_aask

        #  Hard rule to ask human for help
        if past_rsp.count(command_rsp) >= 3:
            if '"command_name": "Plan.finish_current_task",' in command_rsp:
                # Detect the duplicate of the 'Plan.finish_current_task' command, and use the 'end' command to finish the task.
                logger.warning(f"Duplicate response detected: {command_rsp}")
                return END_COMMAND
            problem = await llm.aask(
                req + [UserMessage(content=SUMMARY_PROBLEM_WHEN_DUPLICATE.format(language=respond_language))]
            )
            ASK_HUMAN_COMMAND[0]["args"]["question"] = ASK_HUMAN_GUIDANCE_FORMAT.format(problem=problem).strip()
            ask_human_command = "```json\n" + json.dumps(ASK_HUMAN_COMMAND, indent=4, ensure_ascii=False) + "\n```"
            return ask_human_command
        # Try correction by self
        logger.warning(f"Duplicate response detected: {command_rsp}")
        regenerate_req = req + [UserMessage(content=REGENERATE_PROMPT)]
        regenerate_req = llm.format_msg(regenerate_req)
        command_rsp = await llm.aask(regenerate_req)
    return command_rsp


async def parse_commands(command_rsp: str, llm, exclusive_tool_commands: list[str]) -> Tuple[list[dict], bool]:
    """Retrieves commands from the Large Language Model (LLM).

    This function attempts to retrieve a list of commands from the LLM by
    processing the response (`command_rsp`). It handles potential errors
    during parsing and LLM response formats.

    Returns:
        A tuple containing:
            - A boolean flag indicating success (True) or failure (False).
    """
    try:
        commands = CodeParser.parse_code(block=None, lang="json", text=command_rsp)
        if commands.endswith("]") and not commands.startswith("["):
            commands = "[" + commands
        commands = json.loads(repair_llm_raw_output(output=commands, req_keys=[None], repair_type=RepairType.JSON))
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON for: {command_rsp}. Trying to repair...")
        commands = await llm.aask(msg=JSON_REPAIR_PROMPT.format(json_data=command_rsp, json_decode_error=str(e)))
        try:
            commands = json.loads(CodeParser.parse_code(block=None, lang="json", text=commands))
        except json.JSONDecodeError:
            # repair escape error of code and math
            commands = CodeParser.parse_code(block=None, lang="json", text=command_rsp)
            new_command = repair_escape_error(commands)
            commands = json.loads(
                repair_llm_raw_output(output=new_command, req_keys=[None], repair_type=RepairType.JSON)
            )
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        error_msg = str(e)
        return error_msg, False, command_rsp

    # 为了对LLM不按格式生成进行容错
    if isinstance(commands, dict):
        commands = commands["commands"] if "commands" in commands else [commands]

    # Set the exclusive command flag to False.
    command_flag = [command["command_name"] not in exclusive_tool_commands for command in commands]
    if command_flag.count(False) > 1:
        # Keep only the first exclusive command
        index_of_first_exclusive = command_flag.index(False)
        commands = commands[: index_of_first_exclusive + 1]
        command_rsp = "```json\n" + json.dumps(commands, indent=4, ensure_ascii=False) + "\n```"
        logger.info("exclusive command more than one in current command list. change the command list.\n" + command_rsp)
    return commands, True, command_rsp


def get_plan_status(planner) -> Tuple[str, str]:
    plan_status = planner.plan.model_dump(include=["goal", "tasks"])
    current_task = (
        planner.plan.current_task.model_dump(exclude=["code", "result", "is_success"])
        if planner.plan.current_task
        else ""
    )
    # format plan status
    # Example:
    # [GOAL] create a 2048 game
    # [TASK_ID 1] (finished) Create a Product Requirement Document (PRD) for the 2048 game. This task depends on tasks[]. [Assign to Alice]
    # [TASK_ID 2] (        ) Design the system architecture for the 2048 game. This task depends on tasks[1]. [Assign to Bob]
    formatted_plan_status = f"[GOAL] {plan_status['goal']}\n"
    if len(plan_status["tasks"]) > 0:
        formatted_plan_status += "[Plan]\n"
        for task in plan_status["tasks"]:
            formatted_plan_status += f"[TASK_ID {task['task_id']}] ({'finished' if task['is_finished'] else '    '}){task['instruction']} This task depends on tasks{task['dependent_task_ids']}. [Assign to {task['assignee']}]\n"
    else:
        formatted_plan_status += "No Plan \n"
    return formatted_plan_status, current_task


def format_terminal_output(cmd: dict, raw_output: str) -> str:
    if len(raw_output) <= 10:
        command_output = f"\n[command]: {cmd['args']['cmd']} \n[command output] : {raw_output} (pay attention to this.)"
    else:
        command_output = f"\n[command]: {cmd['args']['cmd']} \n[command output] : {raw_output}"
    return command_output
