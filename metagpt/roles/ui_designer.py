# -*- coding: utf-8 -*-
# @Date    : 2023/8/16 13:58
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from functools import wraps
import json5

from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message

from metagpt.actions.design import Tool, SDPromptExtend, SDPromptOptimize, SDPromptImprove
from metagpt.actions.ui_design import ModelSelection, SDGeneration


def retrieve(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        content, keyword = func(*args, **kwargs)
        info = content.replace(keyword, "")
        return info
    
    return wrapper


class Designer(Role):
    """Class representing the UI designer Role."""
    
    def __init__(
            self,
            name="Catherine",
            profile="UI Design",
            goal="Generate UI icon",
            constraints="Give clear icon description and generate images to finish the design",
            actions=[ModelSelection, SDPromptExtend, SDGeneration]):
        super().__init__(name, profile, goal, constraints)
        
        self._init_actions(actions)

    @property
    def memory_model_name(self):
        return "MODEL_NAME: "
    
    @property
    def memory_user_input(self):
        return "User Input: "
    
    @property
    def memory_domain(self):
        return "Domain: "
    
    def memory_property(self, memory_keyword: str, memory_content: str):
        self._rc.memory.add(Message(f"{memory_keyword}{memory_content}", role=self.profile))
    
    @retrieve
    def get_important_memory(self, keyword: str):
        query_memory = self._rc.memory.get_by_content(keyword)[0]
        return query_memory.content, keyword
    
    async def _plan_and_select(self):
        """
        这里实现的是二选一的option，action在这里进行了选择
        理论上应该可以实现4种选择 (&：表示串行顺序），目前只选择了前2种
        1) action1
        2) action2
        3) action1 & action2
        4) action2 & action1
        """
        msg = self._rc.memory.get(k=1)[0]
        query = msg.content
        logger.info(query)
        if query == "PromptImprove":
            self._actions.insert(self._rc.state + 1, SDPromptImprove())
        elif query == "PromptOptimize":
            self._actions.insert(self._rc.state + 1, SDPromptOptimize())
        return self._rc.state
    
    async def _think(self) -> None:
        logger.info(self._rc.state)
        if self._rc.todo is None:
            self._set_state(0)
            return
        
        if self._rc.state == 1:
            await self._plan_and_select()
            self._set_state(self._rc.state + 1)
        
        elif self._rc.state + 1 < len(self._actions):
            self._set_state(self._rc.state + 1)
        else:
            self._rc.todo = None
    
    async def handle_model_selection(self, query, **kwargs):
        ms = ModelSelection()
        model_name, domain = await ms.run(query)
        logger.info(f"{model_name}, {domain}")
        
        self.memory_property(self.memory_user_input, query)
        self.memory_property(self.memory_model_name, model_name)
        self.memory_property(self.memory_domain, domain)
        return f"{model_name}||{domain}"
    
    async def handle_sd_prompt_extend(self, *args, **kwargs):
        tools = [
            Tool(name="PromptOptimize",
                 func=SDPromptOptimize().run,
                 description="Find 3 keywords related to the prompt that are not found in the prompt. The keywords should be related to each other. Each keyword is a single word. useful for when you need to add extra keywords for input prompt, specially for long enough input"),
            
            Tool(name="PromptImprove",
                 func=SDPromptImprove().run,
                 description="Take the prompt and improve it. useful for when you need to add improve and extend the prompt for input prompt, specially for short input"),
        
        ]
        
        query = self.get_important_memory(self.memory_user_input)
        domain = self.get_important_memory(self.memory_domain)
        sd_exd = SDPromptExtend(tools=tools)
        resp = await sd_exd.run(query=query, domain=domain, answer_count=1)
        return resp
    
    async def handle_sd_prompt_improve(self, *args, **kwargs):
        query = self.get_important_memory(self.memory_user_input)
        domain = self.get_important_memory(self.memory_domain)
        sd_pi = SDPromptImprove()
        resp = await sd_pi.run(query=query, domain=domain, answer_count=1)
        return resp
    
    async def handle_sd_prompt_optimize(self, *args, **kwargs):
        query = self.get_important_memory(self.memory_user_input)
        domain = self.get_important_memory(self.memory_domain)
        sd_op = SDPromptOptimize()
        resp = await sd_op.run(query=query, domain=domain, answer_count=1)
        return resp
    
    async def handle_sd_generation(self, *args, **kwargs):    
        msg = self._rc.memory.get_by_action(SDPromptImprove)[0]
        image_name = self.get_important_memory(self.memory_user_input)
        logger.info(type(msg.content))
        logger.info(msg.content)
        resp = json5.loads(msg.content)
        logger.info(resp)
        model_name = self.get_important_memory(self.memory_model_name)
        await SDGeneration().run(query=resp, model_name=model_name, **{"image_name":image_name})
        return resp
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        todo = self._rc.todo
        msg = self._rc.memory.get(k=1)[0]
        query = msg.content
        logger.info(msg.cause_by)
        logger.info(query)
        logger.info(todo)
        
        handler_map = {
            ModelSelection: self.handle_model_selection,
            SDPromptExtend: self.handle_sd_prompt_extend,
            
            SDPromptImprove: self.handle_sd_prompt_improve,
            SDPromptOptimize: self.handle_sd_prompt_optimize,
            
            SDGeneration: self.handle_sd_generation,
        }
        
        handler = handler_map.get(type(todo))
        if handler:
            resp = await handler(query)
            if type(todo) in [SDPromptImprove, SDPromptOptimize]:
                ret = Message(f"{resp}", role=self.profile, cause_by=SDPromptImprove)
            else:
                ret = Message(f"{resp}", role=self.profile, cause_by=type(todo))
            self._rc.memory.add(ret)
            return ret
        
        raise ValueError(f"Unknown todo type: {type(todo)}")
    
    async def _react(self) -> Message:
        while True:
            await self._think()
            if self._rc.todo is None:
                break
            
            msg = await self._act()
        return msg


if __name__ == "__main__":
    import asyncio
    import platform
    test_queries = ["Flappy Bird",
                    "Clash of Clans",
                    "Subway Surfers",
                    "Pokémon Go",
                    "Super Mario",
                    "Tetris",
                    "Call of Duty"
                    ]
    
    for prompt in test_queries:
        
        designer = Designer()
        if platform.system() == "Windows":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(designer.run(prompt))
    