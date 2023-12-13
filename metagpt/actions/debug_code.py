from typing import Dict, List, Union, Tuple, Optional, Any

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message, Plan
from metagpt.utils.common import CodeParser, create_func_config
from metagpt.actions.write_analysis_code import BaseWriteAnalysisCode

DEBUG_REFLECTION_EXAMPLE = '''Example 1:
                           [previous impl]:
                           ```python
                           def add(a: int, b: int) -> int:
                               """
                               Given integers a and b, return the total value of a and b.
                               """
                               return a - b
                           ```

                           [runtime Error]:
                           Tested passed:

                           Tests failed:
                           assert add(1, 2) == 3 # output: -1
                           assert add(1, 2) == 4 # output: -1

                           [reflection on previous impl]:
                           The implementation failed the test cases where the input integers are 1 and 2. The issue arises because the code does not add the two integers together, but instead subtracts the second integer from the first. To fix this issue, we should change the operator from `-` to `+` in the return statement. This will ensure that the function returns the correct output for the given input.

                           [improved impl]:
                           ```python
                           def add(a: int, b: int) -> int:
                               """
                               Given integers a and b, return the total value of a and b.
                               """
                               return a + b
                           ```
                           '''

REFLECTION_PROMPT = """
                       Here is an example for you.
                       {debug_example}
                       [context]
                       {context}
                       
                       [previous impl]
                       {code}
                       [runtime Error]
                       {runtime_result}

                        Analysis the error step by step, provide me improve method and code. Remember to follow [context] requirement.
                        [reflection on previous impl]:
                        xxx

                       """

CODE_REFLECTION = {
    "name": "execute_reflection_code",
    "description": "Execute reflection code.",
    "parameters": {
        "type": "object",
        "properties": {
            "reflection": {
                "type": "string",
                "description": "Reflection on previous impl.",
            },
            "improved_impl": {
                "type": "string",
                "description": "Refined code after reflection.",
            },
        },
        "required": ["reflection", "improved_impl"],
    },
}


def message_to_str(message: Message) -> str:
    return f"{message.role}: {message.content}"


def messages_to_str(messages: List[Message]) -> str:
    return "\n".join([message_to_str(message) for message in messages])


class DebugCode(BaseWriteAnalysisCode):
    name: str = "debugcode"
    context: Optional[str] = None
    llm: None
    
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
    
    async def run_reflection(
        self,
        # goal,
        # finished_code,
        # finished_code_result,
        context: List[Message],
        code,
        runtime_result,
    ) -> dict:
        info = []
        # finished_code_and_result = finished_code + "\n [finished results]\n\n" + finished_code_result
        reflection_prompt = REFLECTION_PROMPT.format(debug_example=DEBUG_REFLECTION_EXAMPLE,
                                                     context=context,
                                                     # goal=goal,
                                                     # finished_code=finished_code_and_result,
                                                     code=code,
                                                     runtime_result=runtime_result
                                                     )
        system_prompt = "You are an AI Python assistant. You will be given your previous implementation code of a task, runtime error results, and a hint to change the implementation appropriately. Write your full implementation "
        info.append(Message(role="system", content=system_prompt))
        info.append(Message(role="user", content=reflection_prompt))
        
        # msg = messages_to_str(info)
        # resp = await self.llm.aask(msg=msg)
        resp = await self.llm.aask_code(messages=info, **create_func_config(CODE_REFLECTION))
        logger.info(f"reflection is {resp}")
        return resp
    
    # async def rewrite_code(self, reflection: str = "", context: List[Message] = None) -> str:
    #     """
    #     根据reflection重写代码
    #     """
    #     info = context
    #     # info.append(Message(role="assistant", content=f"[code context]:{code_context}"
    #     #                                               f"finished code are executable, and you should based on the code to continue your current code debug and improvement"
    #     #                                               f"[reflection]: \n {reflection}"))
    #     info.append(Message(role="assistant", content=f"[reflection]: \n {reflection}"))
    #     info.append(Message(role="user", content=f"[improved impl]:\n Return in Python block"))
    #     msg = messages_to_str(info)
    #     resp = await self.llm.aask(msg=msg)
    #     improv_code = CodeParser.parse_code(block=None, text=resp)
    #     return improv_code
    
    async def run(self,
                  context: List[Message] = None,
                  plan: str = "",
                  # finished_code: str = "",
                  # finished_code_result: str = "",
                  code: str = "",
                  runtime_result: str = "") -> str:
        """
        根据当前运行代码和报错信息进行reflection和纠错
        """
        reflection = await self.run_reflection(
            # plan,
            # finished_code=finished_code,
            # finished_code_result=finished_code_result,
            code=code,
            context=context,
            runtime_result=runtime_result,
        )
        # 根据reflection结果重写代码
        # improv_code = await self.rewrite_code(reflection, context=context)
        improv_code = reflection['improved_impl']
        return improv_code
