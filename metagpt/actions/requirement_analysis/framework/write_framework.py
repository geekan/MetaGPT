#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/6/13
@Author  : mashenquan
@File    : write_framework.py
@Desc    : The implementation of Chapter 2.1.8 of RFC243. https://deepwisdom.feishu.cn/wiki/QobGwPkImijoyukBUKHcrYetnBb
"""
import json

from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import general_after_log, to_markdown_code_block


@register_tool(include_functions=["run"])
class WriteFramework(Action):
    """WriteFramework deal with the following situations:
    1. Given a TRD, write out the software framework.
    """

    async def run(
        self,
        *,
        use_case_actors: str,
        trd: str,
        acknowledge: str,
        legacy_output: str,
        evaluation_conclusion: str,
        additional_technical_requirements: str,
    ) -> str:
        """
        Run the action to generate a software framework based on the provided TRD and related information.

        Args:
            use_case_actors (str): Description of the use case actors involved.
            trd (str): Technical Requirements Document detailing the requirements.
            acknowledge (str): External acknowledgements or acknowledgements required.
            legacy_output (str): Previous version of the software framework returned by `WriteFramework.run`.
            evaluation_conclusion (str): Conclusion from the evaluation of the requirements.
            additional_technical_requirements (str): Any additional technical requirements.

        Returns:
            str: The generated software framework as a string.

        Example:
            >>> write_framework = WriteFramework()
            >>> use_case_actors = "- Actor: game player;\\n- System: snake game; \\n- External System: game center;"
            >>> trd = "## TRD\\n..."
            >>> acknowledge = "## Interfaces\\n..."
            >>> legacy_output = '{"path":"balabala", "filename":"...", ...'
            >>> evaluation_conclusion = "Balabala..."
            >>> constraint = "Using Java language, ..."
            >>> framework = await write_framework.run(
            >>>    use_case_actors=use_case_actors,
            >>>    trd=trd,
            >>>    acknowledge=acknowledge,
            >>>    legacy_output=framework,
            >>>    evaluation_conclusion=evaluation_conclusion,
            >>>    additional_technical_requirements=constraint,
            >>> )
            >>> print(framework)
            {"path":"balabala", "filename":"...", ...

        """
        acknowledge = await self._extract_external_interfaces(trd=trd, knowledge=acknowledge)
        prompt = PROMPT.format(
            use_case_actors=use_case_actors,
            trd=to_markdown_code_block(val=trd),
            acknowledge=to_markdown_code_block(val=acknowledge),
            legacy_output=to_markdown_code_block(val=legacy_output),
            evaluation_conclusion=evaluation_conclusion,
            additional_technical_requirements=to_markdown_code_block(val=additional_technical_requirements),
        )
        return await self._write(prompt)

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _write(self, prompt: str) -> str:
        rsp = await self.llm.aask(prompt)
        # Do not use `CodeParser` here.
        tags = ["```json", "```"]
        bix = rsp.find(tags[0])
        eix = rsp.rfind(tags[1])
        if bix >= 0:
            rsp = rsp[bix : eix + len(tags[1])]
        json_data = rsp.removeprefix("```json").removesuffix("```")
        json.loads(json_data)  # validate
        return json_data

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
        after=general_after_log(logger),
    )
    async def _extract_external_interfaces(self, trd: str, knowledge: str) -> str:
        prompt = f"## TRD\n{to_markdown_code_block(val=trd)}\n\n## Knowledge\n{to_markdown_code_block(val=knowledge)}\n"
        rsp = await self.llm.aask(
            prompt,
            system_msgs=[
                "You are a tool that removes impurities from articles; you can remove irrelevant content from articles.",
                'Identify which interfaces are used in "TRD"? Remove the relevant content of the interfaces NOT used in "TRD" from "Knowledge" and return the simplified content of "Knowledge".',
            ],
        )
        return rsp


PROMPT = """
## Actor, System, External System
{use_case_actors}

## TRD
{trd}

## Acknowledge
{acknowledge}

## Legacy Outputs
{legacy_output}

## Evaluation Conclusion
{evaluation_conclusion}

## Additional Technical Requirements
{additional_technical_requirements}

---
You are a tool that generates software framework code based on TRD.
The content of "Actor, System, External System" provides an explanation of actors and systems that appear in UML Use Case diagram;
The descriptions of the interfaces of the external system used in the "TRD" can be found in the "Acknowledge" section; Do not implement the interface of the external system in "Acknowledge" section until it is used in "TRD";
"Legacy Outputs" contains the software framework code generated by you last time, which you can improve by addressing the issues raised in "Evaluation Conclusion";
"Additional Technical Requirements" specifies the additional technical requirements that the generated software framework code must meet;
Develop the software framework based on the "TRD", the output files should include:
- The `README.md` file should include:
  - The folder structure diagram of the entire project;
  - Correspondence between classes, interfaces, and functions with the content in the "TRD" section；
  - Prerequisites if necessary;
  - Installation if necessary;
  - Configuration if necessary;
  - Usage if necessary;
- The `CLASS.md` file should include the class diagram in PlantUML format based on the "TRD";
- The `SEQUENCE.md` file should include the sequence diagram in PlantUML format based on the "TRD";
- The source code files that implement the "TRD" and "Additional Technical Requirements"; do not add comments to source code files;
- The configuration files that required by the source code files, "TRD" and "Additional Technical Requirements";
  
Return a markdown JSON object list, each object containing:
- a "path" key with a value specifying its path;
- a "filename" key with a value specifying its file name;
- a "content" key with a value containing its file content;
"""
