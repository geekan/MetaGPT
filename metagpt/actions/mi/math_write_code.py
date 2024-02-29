from metagpt.schema import Message, Plan, SystemMessage
from metagpt.actions import Action
from metagpt.utils.common import CodeParser


DEFAULT_SYSTEM_MSG = """As a professional mathematics assistant, you are good at solving mathematical problems with various methods.
Please help me solve the problem using Python code, and Output in Python Block
```python
import os
print('hi')
```end

Attention: Please refrain from using the "while true" statement in your code.
Instead, please set specific break conditions that will allow your program to exit the loop when necessary.
This will improve the efficiency and safety of your code.
You should always use the 'print' function for the output and use fractions/radical forms instead of decimals
"""


class MathWriteCode(Action):
    """Ask LLM to generate codes to solve math problem"""

    async def run(
            self,
            context: list[Message],
            plan: Plan = None,
            **kwargs,
    ) -> str:

        def message_to_str(message: Message) -> str:
            return f"{message.role}: {message.content}"

        def messages_to_str(messages: list[Message]) -> str:
            return "\n".join([message_to_str(message) for message in messages])

        context.append(Message(role="system", content=DEFAULT_SYSTEM_MSG))
        prompt = messages_to_str(context)
        code_rsp = await self.llm.aask(prompt)
        code = CodeParser().parse_code(block="", text=code_rsp)
        return {"code": code}
