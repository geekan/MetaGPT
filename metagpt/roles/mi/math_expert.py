from pydantic import BaseModel, ConfigDict, Field
from metagpt.logs import logger
from metagpt.schema import Message, MessageQueue, SerializationMixin
from metagpt.roles.role import Role, RoleReactMode
from metagpt.strategy.math_planner import MathPlanner
from metagpt.actions.mi.execute_nb_code import ExecuteNbCode
from metagpt.actions.mi.debug_code import DebugCode
from metagpt.actions.mi.math_write_code import MathWriteCode
from metagpt.actions.mi.code_self_verification import CodeSelfVerification
from metagpt.actions.mi.code_reflection import CodeReflection
from metagpt.actions.mi.math_output_answer import MathOutputAnswer


class MathExpert(Role):
    name: str = "Gauss"
    profile: str = "MathExpert"
    found_answer: bool = False
    answer: str = ''
    csv_result: str = ''

    planner: MathPlanner = Field(default_factory=MathPlanner)
    execute_code: ExecuteNbCode = Field(default_factory=ExecuteNbCode, exclude=True)

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(auto_run=True, use_tools=False, tools=[], **kwargs)
        self.set_react_mode(react_mode="plan_and_act", auto_run=True, use_tools=False)

    @property
    def working_memory(self):
        return self.rc.working_memory

    def set_react_mode(self, react_mode: str, max_react_loop: int = 1, auto_run: bool = True, use_tools: bool = False):
        assert react_mode in RoleReactMode.values(), f"react_mode must be one of {RoleReactMode.values()}"
        self.rc.react_mode = react_mode
        if react_mode == RoleReactMode.REACT:
            self.rc.max_react_loop = max_react_loop
        elif react_mode == RoleReactMode.PLAN_AND_ACT:
            self.planner = MathPlanner(
                goal=self.goal, working_memory=self.rc.working_memory, auto_run=auto_run, use_tools=use_tools
            )

    async def _plan_and_act(self) -> Message:
        """first plan, then execute an action sequence, i.e. _think (of a plan) -> _act -> _act -> ... Use llm to come up with the plan dynamically."""

        # create initial plan and update it until confirmation
        goal = self.rc.memory.get()[-1].content  # retreive latest user requirement
        await self.planner.update_plan(goal=goal)

        # take on tasks until all finished
        found_answer = False
        plan_count = 0
        max_retry = 3
        answer = ''
        csv_result = ''
        while not found_answer and plan_count < max_retry:
            found_answer, answer, csv_result = await self.act_on_plan()
            if not found_answer:
                await self.planner.update_plan()
                plan_count += 1

        self.working_memory.clear()
        self.answer = answer
        self.csv_result = csv_result

        msg = Message(content=answer, cause_by=MathWriteCode)
        self.rc.memory.add(msg)
        return msg

    async def act_on_plan(self):
        code, result, success = await self._write_and_exec_code()

        rsp = Message(content="Runtime solve result: " + result, cause_by=MathWriteCode)
        answer = await MathOutputAnswer().run([rsp])

        csv_code, csv_code_result, csv_success = await CodeSelfVerification().run(
            plan=self.planner.plan, answer=answer, execute_code=self.execute_code
        )
        csv_result_is_true = 'true' in csv_code_result.lower()
        csv_result_is_false = 'false' in csv_code_result.lower()

        if csv_result_is_true:
            csv_result = 'true'
        elif csv_result_is_false:
            csv_result = 'false'
        else:
            csv_result = 'likely'

        if not csv_success or not csv_result_is_true:
            code_summary, code_reflection_confirmed, suggestion = \
                await CodeReflection().run(
                    plan=self.planner.plan,
                    code=code,
                    code_result=result,
                )

            self.planner.working_memory.add(
                Message(
                    content=result + '\n' + '--------' + '\n' + 'suggestion : ' + suggestion,
                    role="user",
                    cause_by=ExecuteNbCode
                )
            )

            success = False
        else:
            success = True

        return success, answer, csv_result

    async def _write_and_exec_code(self, max_retry: int = 3):
        counter = 0
        success = False

        result = ""
        code = {"code": ""}
        while not success and counter < max_retry:
            context = self.planner.get_last_useful_memories(num=3)

            if counter > 0:
                logger.warning('We got a bug code, now start to debug...')
                code = await DebugCode().run(
                    context=None,
                    code=code,
                    runtime_result=result,
                )
                logger.info(f"new code \n{code}")
                cause_by = DebugCode
                # break
            else:
                code = await MathWriteCode().run(context=context, plan=self.planner.plan,)
                cause_by = MathWriteCode

            self.planner.working_memory.add(
                Message(content=code["code"], role="assistant", cause_by=cause_by)
            )

            result, success = await self.execute_code.run(**code)
            counter += 1

        return code["code"], result, success

