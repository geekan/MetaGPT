#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : integration reflect action 

import re
from ..roles.st_role import STRole
from ..actions.st_action import STAction
from ..memory.agent_memory import BasicMemory

# run_gpt_prompt_focal_pt方法
class AgentFocusPt(STAction):

    def __init__(self, name="AgentFocusPt", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try: 
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False 

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> str:
        llm_resp = "1) " + llm_resp.strip()
        ret = []
        for i in llm_resp.split("\n"): 
            ret += [i.split(") ")[-1]]
        return ret

    def _func_fail_default_resp(self) -> str:
        pass

    async def run(self, role: STRole, statements: str, n: int, test_input = None) -> str:
        def create_prompt_input(role: STRole, statements, n, test_input=None): 
            prompt_input = [statements, str(n)]
            return prompt_input
        
        prompt_input = create_prompt_input(role, statements,n)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "generate_focal_pt_v1.txt")

        example_output = '["What should Jane do for lunch", "Does Jane like strawberry", "Who is Jane"]'
        special_instruction = "Output must be a list of str."
        output = await self._run_v2(prompt,
                                    example_output,
                                    special_instruction)

        return output[0]
    

# run_gpt_prompt_insight_and_guidance
class AgentInsightAndGuidance(STAction):

    def __init__(self, name="AgentInsightAndGuidance", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try: 
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False 

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> str:
        llm_resp = "1. " + llm_resp.strip()
        ret = dict()
        for i in llm_resp.split("\n"): 
            row = i.split(". ")[-1]
            thought = row.split("(because of ")[0].strip()
            evi_raw = row.split("(because of ")[1].split(")")[0].strip()
            evi_raw = re.findall(r'\d+', evi_raw)
            evi_raw = [int(i.strip()) for i in evi_raw]
            ret[thought] = evi_raw
        return ret 

    def _func_fail_default_resp(self) -> str:
        pass

    async def run(self, role: STRole, statements: str, n: int, test_input = None) -> str:
        def create_prompt_input(role: STRole, statements, n, test_input=None): 
            prompt_input = [statements, str(n)]
            return prompt_input
    
        prompt_input = create_prompt_input(role, statements,n)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "insight_and_evidence_v1.txt")

        output = await self._run_v1(prompt)

        return output[0]

# run_gpt_prompt_event_triple
class AgentEventTriple(STAction):
    def __init__(self, name="AgentEventTriple", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try: 
            llm_resp = self._func_cleanup(llm_resp, prompt="")
            if len(llm_resp) != 2: 
                return False
        except: return False
        return True 

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> str:
        cr = llm_resp.strip()
        cr = [i.strip() for i in cr.split(")")[0].split(",")]
        return cr

    def _func_fail_default_resp(self) -> str:
        pass
    
    async def run(self, statements: str, role: STRole, verbose = False) -> str:
        def create_prompt_input(statements, role): 
            if "(" in statements: 
                statements = statements.split("(")[-1].split(")")[0]
                prompt_input = [role._rc.scratch.name, 
                            statements,
                            role._rc.scratch.name]
                return prompt_input
    
        prompt_input = create_prompt_input(statements, role)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "generate_event_triple_v1.txt")

        output = await self._run_v1(prompt)

        return output[0]

# run_gpt_prompt_event_poignancy
class AgentEventPoignancy(STAction):
    def __init__(self, name="AgentEventPoignancy", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try: 
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False 

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> str:
        llm_resp = int(llm_resp.strip())
        return llm_resp

    def _func_fail_default_resp(self) -> str:
        pass

    async def run(self, role: STRole, statements: str, test_input = None, verbose = False) -> str:
        def create_prompt_input(role: STRole, statements: str, test_input=None): 
            prompt_input = [role._rc.scratch.name,
                            role._rc.scratch.get_str_iss(),
                            role._rc.scratch.name,
                            statements]
            return prompt_input
        
        prompt_input = create_prompt_input(role, statements)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "poignancy_event_v1.txt")

        example_output = "5" ########
        special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."
        output = await self._run_v2(prompt,
                                    example_output,
                                    special_instruction)

        return output[0]

# run_gpt_prompt_chat_poignancy
class AgentChatPoignancy(STAction):
    def __init__(self, name="AgentChatPoignancy", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try: 
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False 

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> str:
        llm_resp = int(llm_resp.strip())
        return llm_resp

    def _func_fail_default_resp(self) -> str:
        pass

    async def run(self, role: STRole, statements: str, test_input = None, verbose = False) -> str:
        def create_prompt_input(role: STRole, statements, test_input=None): 
            prompt_input = [role._rc.scratch.name,
                            role._rc.scratch.get_str_iss(),
                            role._rc.scratch.name,
                            statements]
            return prompt_input
        
        prompt_input = create_prompt_input(role, statements)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "poignancy_chat_v1.txt")

        example_output = "5" ########
        special_instruction = "The output should ONLY contain ONE integer value on the scale of 1 to 10."
        output = await self._run_v2(prompt,
                                    example_output,
                                    special_instruction)

        return output[0]

# run_gpt_prompt_planning_thought_on_convo
class AgentPlanThoughtOnConvo(STAction):
    def __init__(self, name="AgentPlanThoughtOnConvo", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try: 
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False 

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> str:
        return llm_resp.split('"')[0].strip()

    def _func_fail_default_resp(self) -> str:
        pass

    async def run(self, role: STRole, statements: str, test_input = None, verbose = False) -> str:
        def create_prompt_input(role, statements, test_input=None): 
            prompt_input = [statements, 
                            role._rc.scratch.name, 
                            role._rc.scratch.name, 
                            role._rc.scratch.name]
            return prompt_input
        
        prompt_input = create_prompt_input(role, statements)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "planning_thought_on_convo_v1.txt")

        output = await self._run_v1(prompt)

        return output[0]

# run_gpt_prompt_memo_on_convo
class AgentMemoryOnConvo(STAction):
    def __init__(self, name="AgentMemoryOnConvo", context: list[BasicMemory] = None, llm=None):
        super().__init__(name, context, llm)

    def _func_validate(self, llm_resp: str, prompt: str) -> bool:
        try: 
            self._func_cleanup(llm_resp, prompt)
            return True
        except:
            return False 

    def _func_cleanup(self, llm_resp: str, prompt: str = "") -> str:
        return llm_resp.split('"')[0].strip()

    def _func_fail_default_resp(self) -> str:
        pass

    async def run(self, role: STRole, statements: str, test_input = None, verbose = False) -> str:
        def create_prompt_input(role, statements, test_input=None): 
            prompt_input = [statements, 
                            role._rc.scratch.name, 
                            role._rc.scratch.name, 
                            role._rc.scratch.name]
            return prompt_input
        
        prompt_input = create_prompt_input(role, statements)
        prompt = self.generate_prompt_with_tmpl_filename(prompt_input,
                                                         "memo_on_convo_v1.txt")
        example_output = 'Jane Doe was interesting to talk to.' 
        special_instruction = 'The output should ONLY contain a string that summarizes anything interesting that the agent may have noticed'
        output = await self._run_v2(prompt,
                                    example_output,
                                    special_instruction)

        return output[0]