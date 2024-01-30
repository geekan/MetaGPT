#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : repair llm raw output with particular conditions

import copy
from enum import Enum
from typing import Callable, Union

import regex as re
from tenacity import RetryCallState, retry, stop_after_attempt, wait_fixed

from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.utils.custom_decoder import CustomDecoder


class RepairType(Enum):
    CS = "case sensitivity"
    RKPM = "required key pair missing"  # condition like `[key] xx` which lacks `[/key]`
    SCM = "special character missing"  # Usually the req_key appear in pairs like `[key] xx [/key]`
    JSON = "json format"


def repair_case_sensitivity(output: str, req_key: str) -> str:
    """Repairs case sensitivity issues in the output string based on the required key.

    Args:
        output: The output string to be repaired.
        req_key: The required key to match in the output string.

    Returns:
        The repaired output string with case sensitivity issues fixed.
    """
    if req_key in output:
        return output

    output_lower = output.lower()
    req_key_lower = req_key.lower()
    if req_key_lower in output_lower:
        # find the sub-part index, and replace it with raw req_key
        lidx = output_lower.find(req_key_lower)
        source = output[lidx : lidx + len(req_key_lower)]
        output = output.replace(source, req_key)
        logger.info(f"repair_case_sensitivity: {req_key}")

    return output


def repair_special_character_missing(output: str, req_key: str = "[/CONTENT]") -> str:
    """Repairs missing special characters in the output string based on the required key.

    Args:
        output: The output string to be repaired.
        req_key: The required key to match in the output string, defaults to '[/CONTENT]'.

    Returns:
        The repaired output string with missing special characters fixed.
    """
    sc_arr = ["/"]

    if req_key in output:
        return output

    for sc in sc_arr:
        req_key_pure = req_key.replace(sc, "")
        appear_cnt = output.count(req_key_pure)
        if req_key_pure in output and appear_cnt > 1:
            # req_key with special_character usually in the tail side
            ridx = output.rfind(req_key_pure)
            output = f"{output[:ridx]}{req_key}{output[ridx + len(req_key_pure):]}"
            logger.info(f"repair_special_character_missing: {sc} in {req_key_pure} as position {ridx}")

    return output


def repair_required_key_pair_missing(output: str, req_key: str = "[/CONTENT]") -> str:
    """Repairs missing required key pairs in the output string based on the required key.

    Args:
        output: The output string to be repaired.
        req_key: The required key to match in the output string, defaults to '[/CONTENT]'.

    Returns:
        The repaired output string with required key pairs fixed.
    """
    sc = "/"  # special char
    if req_key.startswith("[") and req_key.endswith("]"):
        if sc in req_key:
            left_key = req_key.replace(sc, "")  # `[/req_key]` -> `[req_key]`
            right_key = req_key
        else:
            left_key = req_key
            right_key = f"{req_key[0]}{sc}{req_key[1:]}"  # `[req_key]` -> `[/req_key]`

        if left_key not in output:
            output = left_key + "\n" + output
        if right_key not in output:

            def judge_potential_json(routput: str, left_key: str) -> Union[str, None]:
                ridx = routput.rfind(left_key)
                if ridx < 0:
                    return None
                sub_output = routput[ridx:]
                idx1 = sub_output.rfind("}")
                idx2 = sub_output.rindex("]")
                idx = idx1 if idx1 >= idx2 else idx2
                sub_output = sub_output[: idx + 1]
                return sub_output

            if output.strip().endswith("}") or (output.strip().endswith("]") and not output.strip().endswith(left_key)):
                # # avoid [req_key]xx[req_key] case to append [/req_key]
                output = output + "\n" + right_key
            elif judge_potential_json(output, left_key) and (not output.strip().endswith(left_key)):
                sub_content = judge_potential_json(output, left_key)
                output = sub_content + "\n" + right_key

    return output


def repair_json_format(output: str) -> str:
    """Repairs JSON format issues in the output string.

    Args:
        output: The output string to be repaired.

    Returns:
        The repaired output string with JSON format issues fixed.
    """
    output = output.strip()

    if output.startswith("[{"):
        output = output[1:]
        logger.info(f"repair_json_format: {'[{'}")
    elif output.endswith("}]"):
        output = output[:-1]
        logger.info(f"repair_json_format: {'}]'}")
    elif output.startswith("{") and output.endswith("]"):
        output = output[:-1] + "}"

    # remove `#` in output json str, usually appeared in `glm-4`
    arr = output.split("\n")
    new_arr = []
    for line in arr:
        idx = line.find("#")
        if idx >= 0:
            line = line[:idx]
        new_arr.append(line)
    output = "\n".join(new_arr)
    return output


def _repair_llm_raw_output(output: str, req_key: str, repair_type: RepairType = None) -> str:
    """Internal function to repair LLM raw output based on the specified repair type.

    Args:
        output: The raw output string from the LLM.
        req_key: The required key to match in the output string.
        repair_type: The type of repair to apply. If None, applies all repairs except JSON format.

    Returns:
        The repaired output string.
    """
    repair_types = [repair_type] if repair_type else [item for item in RepairType if item not in [RepairType.JSON]]
    for repair_type in repair_types:
        if repair_type == RepairType.CS:
            output = repair_case_sensitivity(output, req_key)
        elif repair_type == RepairType.RKPM:
            output = repair_required_key_pair_missing(output, req_key)
        elif repair_type == RepairType.SCM:
            output = repair_special_character_missing(output, req_key)
        elif repair_type == RepairType.JSON:
            output = repair_json_format(output)
    return output


def repair_llm_raw_output(output: str, req_keys: list[str], repair_type: RepairType = None) -> str:
    """Repairs LLM raw output for common issues based on the specified repair type and required keys.

    Args:
        output: The raw output string from the LLM.
        req_keys: A list of required keys to match in the output string.
        repair_type: The type of repair to apply. If None, applies all repairs by default.

    Returns:
        The repaired output string.
    """
    if not config.repair_llm_output:
        return output

    # do the repairation usually for non-openai models
    for req_key in req_keys:
        output = _repair_llm_raw_output(output=output, req_key=req_key, repair_type=repair_type)
    return output


def repair_invalid_json(output: str, error: str) -> str:
    """Repairs invalid JSON in the output string based on the error message.

    Args:
        output: The output string containing invalid JSON.
        error: The error message indicating the nature of the JSON issue.

    Returns:
        The repaired output string with invalid JSON fixed.
    """
    pattern = r"line ([0-9]+) column ([0-9]+)"

    matches = re.findall(pattern, error, re.DOTALL)
    if len(matches) > 0:
        line_no = int(matches[0][0]) - 1
        col_no = int(matches[0][1]) - 1

        # due to CustomDecoder can handle `"": ''` or `'': ""`, so convert `"""` -> `"`, `'''` -> `'`
        output = output.replace('"""', '"').replace("'''", '"')
        arr = output.split("\n")
        rline = arr[line_no]  # raw line
        line = arr[line_no].strip()
        # different general problems
        if line.endswith("],"):
            # problem, redundant char `]`
            new_line = line.replace("]", "")
        elif line.endswith("},") and not output.endswith("},"):
            # problem, redundant char `}`
            new_line = line.replace("}", "")
        elif line.endswith("},") and output.endswith("},"):
            new_line = line[:-1]
        elif (rline[col_no] in ["'", '"']) and (line.startswith('"') or line.startswith("'")) and "," not in line:
            # problem, `"""` or `'''` without `,`
            new_line = f",{line}"
        elif '",' not in line and "," not in line and '"' not in line:
            new_line = f'{line}",'
        elif not line.endswith(","):
            # problem, miss char `,` at the end.
            new_line = f"{line},"
        elif "," in line and len(line) == 1:
            new_line = f'"{line}'
        elif '",' in line:
            new_line = line[:-2] + "',"
        else:
            new_line = line

        arr[line_no] = new_line
        output = "\n".join(arr)
        logger.info(f"repair_invalid_json, raw error: {error}")

    return output


def run_after_exp_and_passon_next_retry(logger: "loguru.Logger") -> Callable[["RetryCallState"], None]:
    """Generates a function to run after an exception and pass on the next retry attempt.

    Args:
        logger: The logger object to log warnings and information.

    Returns:
        A function that takes a RetryCallState object and processes it for the next retry attempt.
    """

    def run_and_passon(retry_state: RetryCallState) -> None:
        """
        RetryCallState example
            {
                "start_time":143.098322024,
                "retry_object":"<Retrying object at 0x7fabcaca25e0 (stop=<tenacity.stop.stop_after_attempt ... >)>",
                "fn":"<function retry_parse_json_text_v2 at 0x7fabcac80ee0>",
                "args":"(\"tag:[/CONTENT]\",)",  # function input args
                "kwargs":{},                     # function input kwargs
                "attempt_number":1,              # retry number
                "outcome":"<Future at xxx>",  # type(outcome.result()) = "str", type(outcome.exception()) = "class"
                "outcome_timestamp":143.098416904,
                "idle_for":0,
                "next_action":"None"
            }
        """
        if retry_state.outcome.failed:
            if retry_state.args:
                # # can't be used as args=retry_state.args
                func_param_output = retry_state.args[0]
            elif retry_state.kwargs:
                func_param_output = retry_state.kwargs.get("output", "")
            exp_str = str(retry_state.outcome.exception())

            fix_str = "try to fix it, " if config.repair_llm_output else ""
            logger.warning(
                f"parse json from content inside [CONTENT][/CONTENT] failed at retry "
                f"{retry_state.attempt_number}, {fix_str}exp: {exp_str}"
            )

            repaired_output = repair_invalid_json(func_param_output, exp_str)
            retry_state.kwargs["output"] = repaired_output

    return run_and_passon


@retry(
    stop=stop_after_attempt(3 if config.repair_llm_output else 0),
    wait=wait_fixed(1),
    after=run_after_exp_and_passon_next_retry(logger),
)
def retry_parse_json_text(output: str) -> Union[list, dict]:
    """Attempts to parse JSON text from the output string, retrying on failure if configured.

    Args:
        output: The output string containing JSON text to be parsed.

    Returns:
        The parsed data as a list or dictionary.
    """
    # logger.debug(f"output to json decode:\n{output}")

    # if CONFIG.repair_llm_output is True, it will try to fix output until the retry break
    parsed_data = CustomDecoder(strict=False).decode(output)

    return parsed_data


def extract_content_from_output(content: str, right_key: str = "[/CONTENT]"):
    """Extracts content from the output string based on the specified right key.

    Args:
        content: The output string from which to extract content.
        right_key: The right key indicating the end of the content to extract, defaults to '[/CONTENT]'.

    Returns:
        The extracted content string.
    """

    def re_extract_content(cont: str, pattern: str) -> str:
        matches = re.findall(pattern, cont, re.DOTALL)
        for match in matches:
            if match:
                cont = match
                break
        return cont.strip()

    # TODO construct the extract pattern with the `right_key`
    raw_content = copy.deepcopy(content)
    pattern = r"\[CONTENT\]([\s\S]*)\[/CONTENT\]"
    new_content = re_extract_content(raw_content, pattern)

    if not new_content.startswith("{"):
        # TODO find a more general pattern
        # # for `[CONTENT]xxx[CONTENT]xxxx[/CONTENT] situation
        logger.warning(f"extract_content try another pattern: {pattern}")
        if right_key not in new_content:
            raw_content = copy.deepcopy(new_content + "\n" + right_key)
        # # pattern = r"\[CONTENT\](\s*\{.*?\}\s*)\[/CONTENT\]"
        new_content = re_extract_content(raw_content, pattern)
    else:
        if right_key in new_content:
            idx = new_content.find(right_key)
            new_content = new_content[:idx]
            new_content = new_content.strip()

    return new_content


def extract_state_value_from_output(content: str) -> str:
    """Extracts a state value from the output string.

    Args:
        content: The output string from which to extract the state value.

    Returns:
        The extracted state value as a string.
    """
    content = content.strip()  # deal the output cases like " 0", "0\n" and so on.
    pattern = r"([0-9])"  # TODO find the number using a more proper method not just extract from content using pattern
    matches = re.findall(pattern, content, re.DOTALL)
    matches = list(set(matches))
    state = matches[0] if len(matches) > 0 else "-1"
    return state
