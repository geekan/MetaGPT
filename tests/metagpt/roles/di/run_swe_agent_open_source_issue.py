import asyncio

from metagpt.logs import logger
from metagpt.roles.di.swe_agent import SWEAgent

FIX_ISSUE1 = """
Write a fix for this issue: https://github.com/langchain-ai/langchain/issues/20453, 
you can fix it on this repo https://github.com/garylin2099/langchain
"""
# + "checkout a branch named test-fix, commit your changes, push,
# and create a PR to the master branch of https://github.com/iorisa/langchain"
# """
FIX_ISSUE2 = """
Write a fix for this issue https://github.com/geekan/MetaGPT/issues/1275.
You can fix it on the v0.8-release branch of this repo https://github.com/garylin2099/MetaGPT
"""
# + "during fixing, checkout a branch named test-fix-1275, commit your changes, push,
# and create a PR to the v0.8-release branch of https://github.com/garylin2099/MetaGPT"

FIX_ISSUE3 = """
Write a fix for this issue https://github.com/geekan/MetaGPT/issues/1262.
You can fix it on this repo https://github.com/garylin2099/MetaGPT
"""
# during fixing, checkout a branch named test-fix-1262, commit your changes, push,
# and create a PR to https://github.com/garylin2099/MetaGPT
# """
FIX_ISSUE_SIMPLE = """
Write a fix for this issue: https://github.com/mannaandpoem/simple_calculator/issues/1, 
you can fix it on this repo https://github.com/garylin2099/simple_calculator
"""
# checkout a branch named test, commit your changes, push, and create a PR to the master branch of original repo.
# """


NO_ENV_TIP = """
Because the environment is not available, you DO NOT need to run and modify any existing test case files or
add new test case files to ensure that the bug is fixed.
"""
if __name__ == "__main__":
    swe_agent = SWEAgent()
    logger.info("**** Starting run ****")
    user_requirement_and_issue = FIX_ISSUE1 + NO_ENV_TIP
    asyncio.run(swe_agent.run(user_requirement_and_issue))
    logger.info("**** Finished running ****")
