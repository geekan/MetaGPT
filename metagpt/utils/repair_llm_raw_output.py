#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : repair llm raw output with particular conditions

import copy
from enum import Enum
from typing import Union
import regex as re

from metagpt.logs import logger
from metagpt.config import CONFIG
from metagpt.utils.custom_decoder import CustomDecoder


class RepairType(Enum):
    CS = "case sensitivity"
    SCM = "special character missing"  # Usually the req_key appear in pairs like `[key] xx [/key]`
    RKPM = "required key pair missing"  # condition like `[key] xx` which lacks `[/key]`
    JSON = "json format"


def repair_case_sensitivity(output: str, req_key: str) -> str:
    """
    usually, req_key is the key name of expected json or markdown content, it won't appear in the value part.
    fix target string `"Shared Knowledge": ""` but `"Shared knowledge": ""` actually
    """
    if req_key in output:
        return output

    output_lower = output.lower()
    req_key_lower = req_key.lower()
    if req_key_lower in output_lower:
        # find the sub-part index, and replace it with raw req_key
        lidx = output_lower.find(req_key_lower)
        source = output[lidx: lidx + len(req_key_lower)]
        output = output.replace(source, req_key)
        logger.info(f"repair_case_sensitivity: {req_key}")

    return output


def repair_special_character_missing(output: str, req_key: str) -> str:
    """
    fix target string `[CONTENT]xxx[/CONTENT]` lacks [/CONTENT]
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
            logger.info(f"repair_special_character_missing: {req_key}")

    return output


def repair_required_key_pair_missing(output: str, req_key: str) -> str:
    """
    implement the req_key pair in the begin or end of the content
        req_key format
            1. `[req_key]`, and its pair `[/req_key]`
            2. `[/req_key]`, and its pair `[req_key]`
    """
    if req_key.startswith("[") and req_key.endswith("]"):
        if "/" in req_key:
            left_key = req_key.replace("/", "")        # `[/req_key]` -> `[req_key]`
            right_key = req_key
        else:
            left_key = req_key
            right_key = f"{req_key[0]}/{req_key[1:]}"  # `[req_key]` -> `[/req_key]`

        if left_key not in output:
            output = left_key + output
        if right_key not in output:
            output = output + right_key

    return output


def repair_json_format(output: str) -> str:
    """
    fix extra `[` or `}` in the end
    """
    output = output.strip()

    if output.startswith("[{"):
        output = output[1:]
        logger.info(f"repair_json_format: {'[{'}")
    elif output.endswith("}]"):
        output = output[:-1]
        logger.info(f"repair_json_format: {'}]'}")
    elif output.startswith("{") and output.startswith("]"):
        output = output[:-1] + "}"

    return output


def _repair_llm_raw_output(output: str, req_key: str, repair_type: RepairType = None) -> str:
    repair_types = [repair_type] if repair_type else [item for item in RepairType if item not in [RepairType.JSON]]
    for repair_type in repair_types:
        if repair_type == RepairType.CS:
            output = repair_case_sensitivity(output, req_key)
        elif repair_type == RepairType.SCM:
            output = repair_special_character_missing(output, req_key)
        elif repair_type == RepairType.JSON:
            output = repair_json_format(output)
        elif repair_type == RepairType.RKPM:
            output = repair_required_key_pair_missing(output, req_key)
    return output


def repair_llm_raw_output(output: str, req_keys: list[str], repair_type: RepairType = None) -> str:
    """
    in open-source llm model, it usually can't follow the instruction well, the output may be incomplete,
    so here we try to repair it and use all repair methods by default.
    typical case
        1. case sensitivity
            target: "Original Requirements"
            output: "Original requirements"
        2. special character missing
            target: [/CONTENT]
            output: [CONTENT]
        3. json format
            target: { xxx }
            output: { xxx }]
    """
    if not CONFIG.repair_llm_output:
        return output

    # do the repairation usually for non-openai models
    for req_key in req_keys:
        output = _repair_llm_raw_output(output=output,
                                        req_key=req_key,
                                        repair_type=repair_type)
    return output


def repair_invalid_json(output: str, error: str) -> str:
    """
    repair the situation like there are extra chars like
    error examples
        example 1. json.decoder.JSONDecodeError: Expecting ',' delimiter: line 154 column 1 (char 2765)
        example 2. xxx.JSONDecodeError: Expecting property name enclosed in double quotes: line 14 column 1 (char 266)
    """
    pattern = r"line ([0-9]+)"

    matches = re.findall(pattern, error, re.DOTALL)
    if len(matches) > 0:
        line_no = int(matches[0]) - 1

        # due to CustomDecoder can handle `"": ''` or `'': ""`, so convert `"""` -> `"`, `'''` -> `'`
        output = output.replace('"""', '"').replace("'''", '"')
        arr = output.split("\n")
        line = arr[line_no].strip()
        # different general problems
        if line.endswith("],"):
            # problem, redundant char `]`
            line = line.replace("]", "")
        elif line.endswith("},"):
            # problem, redundant char `}`
            line = line.replace("}", "")
        elif '",' not in line:
            line = f'{line}",'
        elif "," not in line:
            # problem, miss char `,` at the end.
            line = f"{line},"

        arr[line_no] = line
        output = "\n".join(arr)
        logger.info(f"repair_invalid_json, raw error: {error}")

    return output


def retry_parse_json_text(output: str, retry: int = 5) -> Union[list, dict]:
    """
    repair the json-text situation like there are extra chars like [']', '}']
    """
    parsed_data = {}
    for idx in range(retry):
        raw_output = copy.deepcopy(output)

        try:
            parsed_data = CustomDecoder(strict=False).decode(output)
            break
        except Exception as exp:
            if not CONFIG.repair_llm_output:
                # if repair_llm_output is False, break from the retry loop
                break

            logger.warning(f"decode content into json failed, try to fix it. exp: {exp}")
            error = str(exp)
            output = repair_invalid_json(output, error)

    return parsed_data


def extract_content_from_output(content: str, right_key: str = "[/CONTENT]"):
    """ extract xxx from [CONTENT](xxx)[/CONTENT] using regex pattern """
    def re_extract_content(cont: str, pattern: str) -> str:
        matches = re.findall(pattern, cont, re.DOTALL)
        for match in matches:
            if match:
                cont = match
                break
        return cont.strip()

    raw_content = copy.deepcopy(content)
    pattern = r"\[CONTENT\]([\s\S]*)\[/CONTENT\]"
    new_content = re_extract_content(raw_content, pattern)

    if not new_content.startswith("{"):
        # TODO find a more general pattern
        # # for `[CONTENT]xxx[CONTENT]xxxx[/CONTENT] situation
        logger.warning(f"extract_content try another pattern: {pattern}")
        raw_content = copy.deepcopy(new_content + right_key)
        # # pattern = r"\[CONTENT\](\s*\{.*?\}\s*)\[/CONTENT\]"
        new_content = re_extract_content(raw_content, pattern)
    else:
        if right_key in new_content:
            idx = new_content.find(right_key)
            new_content = new_content[:idx]

    return new_content


def extract_state_value_from_output(content: str) -> str:
    """
    For openai models, they will always return state number. But for open llm models, the instruction result maybe a
    long text contain target number, so here add a extraction to improve success rate.

    Args:
        content (str): llm's output from `Role._think`
    """
    content = content.strip()  # deal the output cases like " 0", "0\n" and so on.
    pattern = r"([0-9])"  # TODO find the number using a more proper method not just extract from content using pattern
    matches = re.findall(pattern, content, re.DOTALL)
    matches = list(set(matches))
    state = matches[0] if len(matches) > 0 else "-1"
    return state
