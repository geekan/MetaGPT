# -*- coding: utf-8 -*-
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import json
import re

from tenacity import retry, stop_after_attempt, wait_random_exponential
from transformers import AutoTokenizer

from metagpt.logs import logger
from metagpt.utils.exceptions import handle_exception
from metagpt.utils.recovery_util import save_history
from swe_bench.gitagent import GitAgent
from swe_bench.make_datasets.make_dataset import reset_task_env
from swe_bench.utils.retriever import retrieve, bm25_retriever
from swe_bench.utils.unixcoder import UniXcoder
from swe_bench.utils.utils import extract_scripts_from_codetext

PATCH_FORMAT = """
```diff
--- original_file.py
+++ modified_file.py
@@ -line_number,context_lines +line_number,context_lines @@
- original line of code to be replaced or removed
+ new line of code to be added or to replace the original
```
"""


def _prepare(inputs):
    requirement = "Please rewrite the code to address the issues. "
    system_messages = inputs.split("\n", 1)[0]
    user_message = inputs.split("\n", 1)[1]
    # Replace URLs with an empty string
    user_message = re.sub(r'https?://\S+', '', user_message)
    cleaned_user_message = re.sub("<patch>.*?</patch>", "", user_message, flags=re.DOTALL)

    issues = re.findall("<issue>(.*?)</issue>", user_message, flags=re.DOTALL)
    issues_ = re.sub(r"#{3,4} Versions.*?(?=#{3,4}|\Z)", "", issues[0], flags=re.DOTALL)
    traceback = re.findall(r"#{3,4} Actual Results.*", issues_, flags=re.DOTALL)
    issues = traceback if traceback else issues
    code = re.findall("<code>(.*?)</code>", user_message, flags=re.DOTALL)
    issues_and_code = [f"<issue>\n{issues[0]}\n</issue>", f"<code>\n{code[0]}\n</code>"]

    return requirement, system_messages, cleaned_user_message, issues_and_code, issues

def construct_prompt(inputs, script_names):
    prompt = (
        f"You only need to modify the code file listed here {script_names}."
        f"Notice: "
        f"1. Analysis the positioning range and issue, especially for the ValueError, and identify influence code lines.\n"
        f"2. Only change a few lines, and make sure I can use git diff and git apply to resolve the issue .\n"
        f"3. I need you to solve this issue by generating a single patch file that I can apply directly to this repository using git apply.\n"
        f"4. use the format as : {PATCH_FORMAT}"
    )

    requirement, system_messages, cleaned_user_message, issues_and_code, issues = _prepare(inputs)
    return requirement, system_messages, cleaned_user_message, issues_and_code, issues, prompt


@handle_exception(exception_type=Exception)
@retry(wait=wait_random_exponential(min=30, max=600), stop=stop_after_attempt(5))
async def run_agent(inputs, agent, **kwargs):
    script_names = kwargs.get("script_names", [])
    instance_id = kwargs.get("instance_id", "")
    requirement, system_messages, cleaned_user_message, issues_and_code, issues, prompt = construct_prompt(inputs, script_names)
    system_messages = system_messages.replace(" ", "")
    cleaned_user_message = cleaned_user_message.replace(" ", "")
    ranges = None
    identify_scope = kwargs.get("identify_scope")
    # if identify_scope
    if identify_scope == "llm":
        ranges = await get_ranges_by_llm(agent, issues_and_code, ranges, script_names)

    elif identify_scope in ["jaccard", "bm25"]:
        ranges = await get_ranges_by_retrieve(identify_scope, instance_id, issues, issues_and_code, ranges)

    ranges_content = f"\nThe positioning range of code to be modified in file is:\n{ranges}\n" if ranges else ""
    print(f"this is ranges_content: \n{ranges_content}")
    await agent.run([requirement, system_messages, "\n".join(issues_and_code), ranges_content, prompt])
    return agent.get_last_cell_source()


async def run_instance(instance, use_reflection=True, **kwargs):
    ga = GitAgent(use_reflection=use_reflection)
    script_names = extract_scripts_from_codetext(instance["text"])
    ga.script_names = script_names

    patch, repo, repo_path = reset_task_env(instance)
    if repo_path is None:
        return

    response = await run_agent(f"{instance['text']}\n\n", agent=ga, script_names=script_names, instance_id=instance["instance_id"], **kwargs)
    logger.info(f"Final response: {response}")
    save_history(ga)
    return response


async def get_ranges_by_retrieve(identify_scope, instance_id, issues, issues_and_code, ranges):
    with open(r"C:\Users\ASUS\PycharmProjects\MetaGPT_2\swe_bench\inference\symbol_changes_list.json", "r") as f:
        symbol_changes_list = json.load(f)
    sc_value = []
    for sc in symbol_changes_list:
        sc_value = sc.get(instance_id, [])
        if not sc_value:
            continue
        break
    # If there are n files, ranges contain n functions or class
    ranges = []
    if "jaccard" == identify_scope:
        for i in range(len(sc_value)):
            tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-350M-multi", cache_dir="cache")
            model = UniXcoder("microsoft/unixcoder-base")
            retrieved_codes = retrieve(
                code=issues[0],
                candidates=sc_value[i],
                tokenizer=tokenizer,
                model=model,
                max_length=10000,
            )
            ranges.append(sc_value[i][retrieved_codes[0]] if sc_value and retrieved_codes else "")

        ranges_list = []
        for function_file in ranges:
            function_name = function_file.split(".")[-1]
            # pattern = r'(def\s+{function_name}\s*\(.*?\)\s*:\s*(.*?))def'.format(function_name=re.escape(function_name))
            pattern = r'(def\s+{function_name}\s*\(.*?\)\s*:.*?)def'.format(function_name=re.escape(function_name))
            match = re.search(pattern, issues_and_code[1], re.DOTALL)
            content = match.group(1).strip() if match else ""
            if content:
                ranges_list.append(f"--- {function_file}\n{content}")
        ranges = "\n".join(ranges_list)

    elif "bm25" == identify_scope:
        pass
    return ranges


async def get_ranges_by_llm(agent, issues_and_code, script_names):
    ranges_rsp = await agent.identify_line_ranges(script_names, "\n".join(issues_and_code))
    # split code based on ranges
    # 1. 根据range中的key，即filename，提取出对于文件的代码
    # 2. 根据range中的value，即lines_scope, 提取出filename的代码中的代码片段
    codes = []
    for key, values in ranges_rsp.items():
        pattern = r'\[start of {file}\](.*?)\[end of {file}\]'.format(file=re.escape(key))
        match = re.search(pattern, issues_and_code[1], re.DOTALL)
        content = match.group(1).strip() if match else ""
        code_snippets = []
        for value in values:
            start, end = tuple(int(x) for x in value.split("-"))
            pattern = re.compile(r'^(?:.*\n){%d}(.*(?:\n.*?){%d})' % (start, end - start + 1), re.MULTILINE)
            match = pattern.search(content)
            snippet = match.group(1) if match else ""
            code_snippets.append(snippet)
        code_snippets = "\n".join(code_snippets)
        codes.append(f"--- {key}\n{code_snippets}")
    ranges = "\n".join(codes)
    return ranges
