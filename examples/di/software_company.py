#!/usr/bin/env python
# -*- coding: utf-8 -*-
import fire

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main():
    prompt = """
This is a software requirement:
```text
write a snake game
```
---
1. Writes a PRD based on software requirements.
2. Writes a design to the project repository, based on the PRD of the project.
3. Writes a project plan to the project repository, based on the design of the project.
4. Writes codes to the project repository, based on the project plan of the project.
5. Run QA test on the project repository.
6. Stage and commit changes for the project repository using Git.
Note: All required dependencies and environments have been fully installed and configured.
"""
    di = DataInterpreter(
        tools=[
            "WritePRD",
            "WriteDesign",
            "WritePlan",
            "WriteCode",
            "RunCode",
            "DebugError",
            # "git_archive",
        ]
    )

    await di.run(prompt)


if __name__ == "__main__":
    fire.Fire(main)
